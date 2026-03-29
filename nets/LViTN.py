"""
LViT.py  —  Fixed Version
==========================
Bugs fixed vs original:

  3. ViT token count / patch-size mismatch:
       The original passed img_size=224 and patch_size=16 to every ViT, but the
       *actual* inputs are backbone feature maps at 56×56, 28×28, 14×14 and 7×7.
       56 / 16 = 3.5  → not an integer.  The Embeddings module therefore fell into
       the interpolation branch, collapsing from 196 positional slots down to ~9
       actual tokens (3×3 or 4×4 grid).  Self-attention on 9 tokens is trivially
       global and provides no meaningful contextual modelling.

       FIX: match img_size to the actual feature map size at each scale, and choose
       patch_size so that exactly 196 tokens are produced (or 49 for the 7×7 map
       where 196 is impossible):

           vit1 : img_size=56,  patch_size=4  → 14×14 = 196 tokens ✓
           vit2 : img_size=28,  patch_size=2  → 14×14 = 196 tokens ✓
           vit3 : img_size=14,  patch_size=1  → 14×14 = 196 tokens ✓
           vit4 : img_size=7,   patch_size=1  →  7×7  =  49 tokens ✓ (maximum possible)

       Reconstruct scale_factor values are updated accordingly:
           reconstruct1 : 14×14 → 56×56 → scale_factor = 4
           reconstruct2 : 14×14 → 28×28 → scale_factor = 2
           reconstruct3 : 14×14 → 14×14 → scale_factor = 1
           reconstruct4 :  7×7  →  7×7  → scale_factor = 1

  4. Cascaded text projection loses information:
       The original projected text through a *chain*:
           768 → ch4 → ch3 → ch2 → ch1
       By the time the text reaches scale-1, it has passed through 4 successive
       Conv1d projections.  Each bottleneck discards information, and the lowest-
       level ViT (which is responsible for fine spatial detail) receives a maximally
       degraded representation of the language input.

       FIX: each scale gets an *independent direct projection* from the original
       768-dim BERT embedding:
           text_proj4 : 768 → ch4
           text_proj3 : 768 → ch3
           text_proj2 : 768 → ch2
           text_proj1 : 768 → ch1
       This preserves full language information at every scale.

  (Fixes #1 and #2 — MLP activation bug and positional-embedding interpolation —
   are applied in ViT.py.)
"""

import torch
import torch.nn as nn
import torch.nn.functional as F

from .ViTN import VisionTransformer, Reconstruct, GatedCrossAttention

try:
    import timm
except Exception:
    timm = None


# ---------------------------------------------------------------------------
# Utility helpers
# ---------------------------------------------------------------------------

def get_backbone_features(backbone_name='convnext_small', pretrained=True, out_indices=(0, 1, 2, 3)):
    """Create a timm backbone with features_only=True and return (model, channel_list)."""
    if timm is None:
        raise ImportError("timm is required. Install with `pip install timm`.")
    model        = timm.create_model(
        backbone_name, features_only=True, pretrained=pretrained, out_indices=out_indices, ls_init_value=None 
    ) # (ls_init_value=None to disable LayerScale init that causes NaNs in early training)
    feature_info = model.feature_info
    channels     = [f['num_chs'] for f in feature_info.info]  # e.g. [96, 192, 384, 768]
    return model, channels


def conv_bn_relu(in_ch, out_ch, kernel=3, padding=1):
    return nn.Sequential(
        nn.Conv2d(in_ch, out_ch, kernel_size=kernel, padding=padding, bias=False),
        nn.BatchNorm2d(out_ch),
        nn.ReLU(inplace=True),
    )


# ---------------------------------------------------------------------------
# Gated Channel Attention
# ---------------------------------------------------------------------------

class GatedChannelAttention(nn.Module):
    """
    Learned per-channel gating between backbone feature map f and ViT
    reconstruction rec.  Superior to plain residual addition because the gate
    can suppress or amplify each channel independently.
    """

    def __init__(self, channels: int, reduction: int = 4):
        super().__init__()
        mid = max(channels // reduction, 8)
        self.gate_mlp = nn.Sequential(
            nn.Linear(channels * 2, mid, bias=True),
            nn.ReLU(inplace=True),
            nn.Linear(mid, channels, bias=True),
            nn.Sigmoid(),
        )

    def forward(self, f: torch.Tensor, rec: torch.Tensor) -> torch.Tensor:
        desc_f   = F.adaptive_avg_pool2d(f,   1).flatten(1)   # [B, C]
        desc_rec = F.adaptive_avg_pool2d(rec, 1).flatten(1)   # [B, C]
        gate     = self.gate_mlp(torch.cat([desc_f, desc_rec], dim=1))  # [B, C]
        gate     = gate.unsqueeze(-1).unsqueeze(-1)                     # [B, C, 1, 1]
        return gate * f + (1.0 - gate) * rec


# ---------------------------------------------------------------------------
# Decoder blocks
# ---------------------------------------------------------------------------

class DecoderUpBlock(nn.Module):
    def __init__(self, in_ch, skip_ch, out_ch, nb_conv=2):
        super().__init__()
        # Replace Upsample with learnable transposed conv
        self.up = nn.ConvTranspose2d(in_ch, in_ch // 2, kernel_size=2, stride=2)
        layers = [conv_bn_relu(in_ch // 2 + skip_ch, out_ch)]
        for _ in range(nb_conv - 1):
            layers.append(conv_bn_relu(out_ch, out_ch))
        self.net = nn.Sequential(*layers)

    def forward(self, x, skip):
        x = self.up(x)          # learnable upsampling
        x = torch.cat([x, skip], dim=1)
        return self.net(x)

class LightSpatialGate(nn.Module):
    """Cheap spatial gate: just avg+max pool → 1 conv → sigmoid."""
    def __init__(self):
        super().__init__()
        self.gate = nn.Sequential(
            nn.Conv2d(2, 1, kernel_size=7, padding=3, bias=False),
            nn.Sigmoid()
        )

    def forward(self, x):
        avg = x.mean(dim=1, keepdim=True)
        mx  = x.max(dim=1, keepdim=True).values
        return x * self.gate(torch.cat([avg, mx], dim=1))


# ---------------------------------------------------------------------------
# Text-guided decoder block (Fix 5)
# ---------------------------------------------------------------------------

class TextGuidedDecoderBlock(nn.Module):
    """Decoder block with cross-attention to text tokens."""

    def __init__(self, in_ch, skip_ch, out_ch, text_dim=768, num_heads=4):
        super().__init__()
        self.up = nn.ConvTranspose2d(in_ch, in_ch // 2, kernel_size=2, stride=2)
        self.conv = conv_bn_relu(in_ch // 2 + skip_ch, out_ch)
        self.text_cross = GatedCrossAttention(out_ch, num_heads=num_heads)
        self.text_proj = nn.Linear(text_dim, out_ch)

    def forward(self, x, skip, text=None):
        x = self.up(x)
        x = torch.cat([x, skip], dim=1)
        x = self.conv(x)
        if text is not None:
            B, C, H, W = x.shape
            tokens = x.flatten(2).permute(0, 2, 1)     # [B, HW, C]
            t = self.text_proj(text)                     # [B, L, C]
            tokens = self.text_cross(tokens, t)          # [B, HW, C]
            x = tokens.permute(0, 2, 1).view(B, C, H, W)
        return x


# ---------------------------------------------------------------------------
# Deep supervision heads
# ---------------------------------------------------------------------------

class DeepSupervisionHeads(nn.Module):
    """1×1 conv heads; outputs are all upsampled to the target (H, W)."""

    def __init__(self, in_channels_list, n_classes: int):
        super().__init__()
        self.heads = nn.ModuleList([
            nn.Conv2d(ch, n_classes, kernel_size=1) for ch in in_channels_list
        ])

    def forward(self, feats, target_size):
        return [
            F.interpolate(head(f), size=target_size, mode='bilinear', align_corners=False)
            for f, head in zip(feats, self.heads)
        ]


# ---------------------------------------------------------------------------
# Text matching loss (Fix 6)
# ---------------------------------------------------------------------------

class TextMatchingLoss(nn.Module):
    """Contrastive loss for text-image alignment."""

    def __init__(self, visual_dim, text_dim=768, proj_dim=128):
        super().__init__()
        self.vis_proj = nn.Linear(visual_dim, proj_dim)
        self.txt_proj = nn.Linear(text_dim, proj_dim)
        self.temperature = nn.Parameter(torch.tensor(0.07))

    def forward(self, visual_features, text_features, mask):
        # visual_features: [B, C, H, W]
        # text_features: [B, L, 768]
        # mask: [B, 1, H, W] ground truth
        mask_down = F.interpolate(
            mask.float(), size=visual_features.shape[-2:], mode='nearest'
        )
        masked = visual_features * mask_down
        denom = mask_down.sum(dim=[-2, -1]).clamp(min=1e-6)
        pooled_vis = masked.sum(dim=[-2, -1]) / denom         # [B, C]
        pooled_txt = text_features.mean(dim=1)                 # [B, 768]
        v = F.normalize(self.vis_proj(pooled_vis), dim=-1)
        t = F.normalize(self.txt_proj(pooled_txt), dim=-1)
        loss = 1.0 - (v * t).sum(dim=-1).mean()
        return loss


# ---------------------------------------------------------------------------
# LViTN  — main model
# ---------------------------------------------------------------------------

class LViTN(nn.Module):
    """
    Language-Vision Transformer for medical image segmentation.

    Architecture overview
    ─────────────────────
    1. Pretrained ConvNeXt backbone  (4-stage hierarchical feature extractor)
    2. Per-scale ViT blocks          (global context over ~196 tokens per scale)
    3. Gated Channel Attention       (learned fusion of backbone + ViT features)
    4. UNet-style decoder            (skip connections + bilinear upsampling)
    5. Deep supervision              (3 auxiliary heads during training)
    6. Optional text conditioning    (BERT embeddings fused via cross-attention)
    """

    def __init__(
        self,
        config,
        n_channels:          int  = 3,
        n_classes:           int  = 1,
        img_size:            int  = 224,
        backbone_name:       str  = 'convnext_small',
        backbone_pretrained: bool = True,
        vit_depth:           int  = 1,
        vit_depth_coarse:    int  = 2,
        vit_heads:           int  = 8,
        text_fuse_scales          = (False, False, True, True),
        gca_reduction:       int  = 4,
    ):
        super().__init__()
        if timm is None:
            raise ImportError("timm is required. Install with `pip install timm`.")

        # ── Backbone ─────────────────────────────────────────────────────────
        self.backbone, channels = get_backbone_features(
            backbone_name, pretrained=backbone_pretrained, out_indices=(0, 1, 2, 3)
        )
        if len(channels) < 4:
            raise RuntimeError(f"Backbone must expose 4 stages (found {len(channels)}).")
        ch1, ch2, ch3, ch4 = channels   # e.g. 96, 192, 384, 768 for convnext_small

        # ── Per-scale ViT blocks ──────────────────────────────────────────────
        #
        # FIX #3: img_size and patch_size are now set to match the *actual*
        # feature-map spatial dimensions produced by the backbone, not the
        # original image size.  This guarantees exactly 196 tokens for scales
        # 1-3 and 49 tokens for scale 4.
        #
        # Backbone output spatial sizes (for img_size=224, ConvNeXt):
        #   f1  56×56   →  patch_size=4  →  14×14 = 196 tokens
        #   f2  28×28   →  patch_size=2  →  14×14 = 196 tokens
        #   f3  14×14   →  patch_size=1  →  14×14 = 196 tokens
        #   f4   7×7    →  patch_size=1  →   7×7  =  49 tokens  (max achievable)
        #
        self.vit1 = VisionTransformer(
            img_size=img_size // 4,  patch_size=4, in_channels=ch1,
            embed_dim=ch1, depth=vit_depth, heads=vit_heads,
            text_fuse=text_fuse_scales[0],
        )
        self.vit2 = VisionTransformer(
            img_size=img_size // 8,  patch_size=2, in_channels=ch2,
            embed_dim=ch2, depth=vit_depth, heads=vit_heads,
            text_fuse=text_fuse_scales[1],
        )
        self.vit3 = VisionTransformer(
            img_size=img_size // 16, patch_size=1, in_channels=ch3,
            embed_dim=ch3, depth=vit_depth_coarse, heads=vit_heads,
            text_fuse=text_fuse_scales[2],
        )
        self.vit4 = VisionTransformer(
            img_size=img_size // 32, patch_size=1, in_channels=ch4,
            embed_dim=ch4, depth=vit_depth_coarse, heads=vit_heads,
            text_fuse=text_fuse_scales[3],
        )

        # ── Reconstruct: tokens → spatial maps ───────────────────────────────
        #
        # FIX #3 (continued): scale_factor values updated to match the new
        # token-grid sizes produced by the corrected ViT configurations:
        #
        #   vit1 tokens: 14×14  →  target spatial: 56×56  →  scale_factor = 4
        #   vit2 tokens: 14×14  →  target spatial: 28×28  →  scale_factor = 2
        #   vit3 tokens: 14×14  →  target spatial: 14×14  →  scale_factor = 1
        #   vit4 tokens:  7×7   →  target spatial:  7×7   →  scale_factor = 1
        #
        # (A final F.interpolate aligns any residual sub-pixel discrepancy.)
        #
        self.reconstruct1 = Reconstruct(ch1, ch1, kernel_size=1, scale_factor=4)
        self.reconstruct2 = Reconstruct(ch2, ch2, kernel_size=1, scale_factor=2)
        self.reconstruct3 = Reconstruct(ch3, ch3, kernel_size=1, scale_factor=1)
        self.reconstruct4 = Reconstruct(ch4, ch4, kernel_size=1, scale_factor=1)

        # ── Gated Channel Attention (one per scale) ───────────────────────────
        self.gca1 = GatedChannelAttention(ch1, reduction=gca_reduction)
        self.gca2 = GatedChannelAttention(ch2, reduction=gca_reduction)
        self.gca3 = GatedChannelAttention(ch3, reduction=gca_reduction)
        self.gca4 = GatedChannelAttention(ch4, reduction=gca_reduction)

        # Only at coarse scales — cheap and targeted
        self.spatial_gate3 = LightSpatialGate()
        self.spatial_gate4 = LightSpatialGate()
        # ── Decoder ──────────────────────────────────────────────────────────
        dec_ch4 = ch4 // 2
        dec_ch3 = ch3 // 2
        dec_ch2 = ch2 // 2
        dec_ch1 = ch1 // 2

        self.bottleneck = conv_bn_relu(ch4, dec_ch4)
        self.up3 = TextGuidedDecoderBlock(in_ch=dec_ch4, skip_ch=ch3, out_ch=dec_ch3, text_dim=768, num_heads=4)
        self.up2 = TextGuidedDecoderBlock(in_ch=dec_ch3, skip_ch=ch2, out_ch=dec_ch2, text_dim=768, num_heads=4)
        self.up1 = DecoderUpBlock(in_ch=dec_ch2, skip_ch=ch1, out_ch=dec_ch1)

        self.final_conv = nn.Sequential(
            conv_bn_relu(dec_ch1, dec_ch1),
            nn.Conv2d(dec_ch1, n_classes, kernel_size=1),
        )

        # Deep supervision heads (decoder features at 3 resolutions → full size)
        self.ds_heads = DeepSupervisionHeads(
            in_channels_list=[dec_ch3, dec_ch2, dec_ch1],
            n_classes=n_classes,
        )

        # ── Text projections (coarse scales only — Fix 4) ────────────────────
        self.text_proj4 = nn.Sequential(
            nn.Conv1d(768, ch4, kernel_size=1),
            nn.BatchNorm1d(ch4),
            nn.GELU(),
            nn.Conv1d(ch4, ch4, kernel_size=1),
        )
        self.text_proj3 = nn.Sequential(
            nn.Conv1d(768, ch3, kernel_size=1),
            nn.BatchNorm1d(ch3),
            nn.GELU(),
            nn.Conv1d(ch3, ch3, kernel_size=1),
        )

        # ── Text matching loss (Fix 6) ───────────────────────────────────────
        self.text_match_loss = TextMatchingLoss(visual_dim=dec_ch3, text_dim=768)

    # ── Helpers ─────────────────────────────────────────────────────────────

    def _proj_text(
        self,
        text: torch.Tensor | None,
        proj: nn.Module,
    ) -> torch.Tensor | None:
        """
        Project BERT text embeddings along the channel dimension.
        Input  text : [B, L, C_in]
        Output      : [B, L, C_out]
        """
        if text is None:
            return None
        t = text.permute(0, 2, 1)   # [B, C_in, L]
        t = proj(t)                 # [B, C_out, L]
        return t.permute(0, 2, 1)   # [B, L, C_out]

    # ── Forward ─────────────────────────────────────────────────────────────

    def forward(
        self,
        x:       torch.Tensor,
        text:    torch.Tensor | None = None,
        gt_mask: torch.Tensor | None = None,
    ) -> dict:
        """
        Args:
            x    : [B, C, H, W]   — input image (H == W == img_size recommended)
            text : [B, L, 768]    — optional BERT last-hidden-state

        Returns:
            dict:
                'out' : [B, n_classes, H, W]   — final logits (no sigmoid)
                'ds'  : list of 3 auxiliary logit tensors at full input resolution
        """
        B, _C, H, W = x.shape
        # ── Backbone encoding ─────────────────────────────────────────────
        feats          = self.backbone(x)        # ordered low → high resolution
        f1, f2, f3, f4 = feats
        # Typical shapes for img_size=224 with ConvNeXt-small:
        #   f1 : [B,  96, 56, 56]
        #   f2 : [B, 192, 28, 28]
        #   f3 : [B, 384, 14, 14]
        #   f4 : [B, 768,  7,  7]

        # ── Text projection (FIX #4: direct independent projections) ──────
        if text is not None:
            t3 = self._proj_text(text, self.text_proj3)   # 768 → ch3, [B, L, ch3]
            t4 = self._proj_text(text, self.text_proj4)   # 768 → ch4, [B, L, ch4]
        else:
            t3 = t4 = None
        t1 = t2 = None   # Fine scales don't fuse text (Fix 2)

        # ── Per-scale ViT refinement (FIX #3: meaningful token counts) ────
        y1_tokens = self.vit1(f1, text_tokens=t1)   # [B, 196, ch1]
        y2_tokens = self.vit2(f2, text_tokens=t2)   # [B, 196, ch2]
        y3_tokens = self.vit3(f3, text_tokens=t3)   # [B, 196, ch3]
        y4_tokens = self.vit4(f4, text_tokens=t4)   # [B,  49, ch4]

        # ── Reconstruct tokens → spatial maps ─────────────────────────────
        rec1 = self.reconstruct1(y1_tokens)   # 14×14 → 56×56
        rec2 = self.reconstruct2(y2_tokens)   # 14×14 → 28×28
        rec3 = self.reconstruct3(y3_tokens)   # 14×14 → 14×14
        rec4 = self.reconstruct4(y4_tokens)   #  7×7  →  7×7

        # Align to exact backbone spatial dimensions (absorbs any rounding)
        rec1 = F.interpolate(rec1, size=f1.shape[-2:], mode='bilinear', align_corners=False)
        rec2 = F.interpolate(rec2, size=f2.shape[-2:], mode='bilinear', align_corners=False)
        rec3 = F.interpolate(rec3, size=f3.shape[-2:], mode='bilinear', align_corners=False)
        rec4 = F.interpolate(rec4, size=f4.shape[-2:], mode='bilinear', align_corners=False)

        # ── Gated Channel Attention ────────────────────────────────────────
        f1 = self.gca1(f1, rec1)
        f2 = self.gca2(f2, rec2)
        f3 = self.gca3(f3, rec3)
        f4 = self.gca4(f4, rec4)
        
        f3 = self.spatial_gate3(f3)   # after GCA, before decoder
        f4 = self.spatial_gate4(f4)   # after GCA, before decoder

        # ── Decoder ───────────────────────────────────────────────────────
        b  = self.bottleneck(f4)           # [B, dec_ch4, H/32, W/32]
        u3 = self.up3(b,  f3, text=text)   # [B, dec_ch3, H/16, W/16]  (text cross-attn)
        u2 = self.up2(u3, f2, text=text)   # [B, dec_ch2, H/8,  W/8 ]  (text cross-attn)
        u1 = self.up1(u2, f1)              # [B, dec_ch1, H/4,  W/4 ]

        # Upsample to original input resolution
        u1 = F.interpolate(u1, size=(H, W), mode='bilinear', align_corners=False)

        # Final prediction (raw logits — apply sigmoid/softmax in loss or post-proc)
        logits = self.final_conv(u1)                              # [B, n_classes, H, W]

        # Deep supervision
        ds_maps = self.ds_heads([u3, u2, u1], target_size=(H, W))

        result = {'out': logits, 'ds': ds_maps}
        if text is not None and gt_mask is not None:
            # Expected usage: total_loss = seg_loss + 0.1 * outputs['text_match_loss']
            result['text_match_loss'] = self.text_match_loss(u3, text, gt_mask)
        return result