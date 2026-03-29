"""
ViT.py  —  Fixed Version
=========================
Bugs fixed vs original:
  1. MLP activation bug  : GELU was incorrectly applied *after* fc2 (output projection).
                           Standard transformer MLP applies activation only between fc1 and fc2.
                           Applying GELU post-fc2 changes the function class and pollutes the
                           residual stream before the skip-add.
  2. Positional-embedding interpolation: the original code contained shape-math errors
                           (using pos_emb.size(1) ** 0.5 as both grid dimension AND channel
                           dimension, causing a silent misinterpretation).  Replaced with a
                           clean 2-D bicubic interpolation that correctly separates H_old, W_old
                           from embed_dim.
"""

import math
import warnings
import torch
import torch.nn as nn
import torch.nn.functional as F
from torch.nn import Dropout, Conv2d
from torch.nn.modules.utils import _pair

try:
    import timm
    _HAS_TIMM = True
except Exception:
    _HAS_TIMM = False


def _pair(x):
    return (x, x) if not isinstance(x, (tuple, list)) else x


# ---------------------------------------------------------------------------
# Reconstruct
# ---------------------------------------------------------------------------
class Reconstruct(nn.Module):
    """Tokens [B, n_patches, C] → spatial map [B, C_out, H, W]."""

    def __init__(self, in_channels, out_channels, kernel_size=1, scale_factor=1, mode='bilinear'):
        super().__init__()
        padding = 1 if kernel_size == 3 else 0
        self.conv = nn.Conv2d(in_channels, out_channels, kernel_size=kernel_size, padding=padding)
        self.norm = nn.BatchNorm2d(out_channels)
        self.act = nn.ReLU(inplace=True)
        self.scale_factor = scale_factor
        self.mode = mode

    def forward(self, x):
        if x is None:
            return None
        B, n_patch, C = x.size()
        side = int(math.sqrt(n_patch))
        assert side * side == n_patch, (
            f"n_patches ({n_patch}) is not a perfect square – check patch_size / img_size config."
        )
        x = x.permute(0, 2, 1).view(B, C, side, side)
        if self.scale_factor != 1:
            if isinstance(self.scale_factor, (tuple, list)):
                size = (side * self.scale_factor[0], side * self.scale_factor[1])
            else:
                size = (side * self.scale_factor, side * self.scale_factor)
            x = F.interpolate(
                x, size=size, mode=self.mode,
                align_corners=False if self.mode == 'bilinear' else None
            )
        x = self.conv(x)
        x = self.norm(x)
        x = self.act(x)
        return x


# ---------------------------------------------------------------------------
# Embeddings
# ---------------------------------------------------------------------------
class Embeddings(nn.Module):
    """Patch embedding: conv projection → flatten tokens → add positional embeddings."""

    def __init__(self, in_channels, embed_dim, patch_size, img_size, dropout=0.1):
        super().__init__()
        img_size   = _pair(img_size)
        patch_size = _pair(patch_size)
        assert img_size[0] % patch_size[0] == 0 and img_size[1] % patch_size[1] == 0, (
            f"img_size {img_size} must be divisible by patch_size {patch_size}"
        )
        self.patch_size = patch_size
        self.n_patches  = (img_size[0] // patch_size[0]) * (img_size[1] // patch_size[1])
        self.grid_h     = img_size[0] // patch_size[0]   # stored for interpolation reference
        self.grid_w     = img_size[1] // patch_size[1]

        self.proj    = Conv2d(in_channels, embed_dim, kernel_size=patch_size, stride=patch_size)
        self.pos_emb = nn.Parameter(torch.zeros(1, self.n_patches, embed_dim))
        self.dropout = Dropout(dropout)

    def _interpolate_pos_emb(self, n_tokens: int, embed_dim: int) -> torch.Tensor:
        """
        Bicubic 2-D resize of pos_emb when the runtime token count differs from
        the count baked in at construction time.

        FIX (vs original): the original code re-used pos_emb.size(1) as BOTH the
        grid dimension AND the channel dimension, which gave wrong shapes.  Here we
        keep embed_dim as its own axis and only resize the spatial (H, W) grid.
        """
        H_new = int(math.sqrt(n_tokens))
        W_new = n_tokens // H_new  # handles non-square grids gracefully
        # pos_emb: [1, N_old, C]  →  [1, C, H_old, W_old]
        pos = self.pos_emb.permute(0, 2, 1).view(1, embed_dim, self.grid_h, self.grid_w)
        # bicubic resize to new spatial grid
        pos = F.interpolate(pos, size=(H_new, W_new), mode='bicubic', align_corners=False)
        # [1, C, H_new, W_new]  →  [1, H_new*W_new, C]
        pos = pos.flatten(2).permute(0, 2, 1)
        return pos  # [1, n_tokens, C]

    def forward(self, x):
        B, _C, _H, _W = x.shape
        x = self.proj(x)                          # [B, embed_dim, H', W']
        x = x.flatten(2).transpose(1, 2)          # [B, n_tokens, embed_dim]

        n_tokens, embed_dim = x.size(1), x.size(2)
        if n_tokens != self.n_patches:
            pos = self._interpolate_pos_emb(n_tokens, embed_dim)
        else:
            pos = self.pos_emb

        x = x + pos
        return self.dropout(x)


# ---------------------------------------------------------------------------
# CrossAttention
# ---------------------------------------------------------------------------
# class CrossAttention(nn.Module):
#     """Cross-attention: Q from image tokens, K/V from text tokens."""

#     def __init__(self, dim, num_heads=8, qkv_bias=True, dropout=0.0):
#         super().__init__()
#         self.num_heads = num_heads
#         head_dim       = dim // num_heads
#         self.scale     = head_dim ** -0.5

#         self.q         = nn.Linear(dim, dim, bias=qkv_bias)
#         self.k         = nn.Linear(dim, dim, bias=qkv_bias)
#         self.v         = nn.Linear(dim, dim, bias=qkv_bias)
#         self.proj      = nn.Linear(dim, dim)
#         self.attn_drop = nn.Dropout(dropout)
#         self.proj_drop = nn.Dropout(dropout)

#     def forward(self, x_img, x_txt):
#         B, N1, C = x_img.shape
#         _,  N2, _ = x_txt.shape
#         q = self.q(x_img).view(B, N1, self.num_heads, C // self.num_heads).permute(0, 2, 1, 3)
#         k = self.k(x_txt).view(B, N2, self.num_heads, C // self.num_heads).permute(0, 2, 1, 3)
#         v = self.v(x_txt).view(B, N2, self.num_heads, C // self.num_heads).permute(0, 2, 1, 3)

#         attn = (q @ k.transpose(-2, -1)) * self.scale
#         attn = attn.softmax(dim=-1)
#         attn = self.attn_drop(attn)

#         out = (attn @ v).permute(0, 2, 1, 3).reshape(B, N1, C)
#         out = self.proj(out)
#         out = self.proj_drop(out)
#         return out
class GatedCrossAttention(nn.Module):
    """
    Cross-attention with a learned gate that controls text influence.
    The gate is conditioned on BOTH the image token and the 
    cross-attention output — so it can shut off text when irrelevant.
    """
    def __init__(self, dim, num_heads=8, dropout=0.0):
        super().__init__()
        self.norm_img  = nn.LayerNorm(dim)
        self.norm_txt  = nn.LayerNorm(dim)
        self.cross_attn = nn.MultiheadAttention(
            embed_dim=dim, num_heads=num_heads,
            dropout=dropout, batch_first=True
        )
        # Gate: takes [img_token || cross_output] → scalar per token
        self.gate_mlp = nn.Sequential(
            nn.Linear(dim * 2, dim // 2),
            nn.ReLU(inplace=True),
            nn.Linear(dim // 2, 1),
            nn.Sigmoid()
        )
        self.proj_drop = nn.Dropout(dropout)

    def forward(self, img_tokens, txt_tokens):
        """
        img_tokens: [B, N, C]
        txt_tokens: [B, L, C]
        """
        img_norm = self.norm_img(img_tokens)
        txt_norm = self.norm_txt(txt_tokens)

        # Cross-attention: image queries, text keys/values
        cross_out, _ = self.cross_attn(
            img_norm, txt_norm, txt_norm, need_weights=False
        )
        cross_out = self.proj_drop(cross_out)

        # Gate: per-token scalar in [0, 1]
        gate_input = torch.cat([img_norm, cross_out], dim=-1)  # [B, N, 2C]
        gate = self.gate_mlp(gate_input)                        # [B, N, 1]

        # Gated residual fusion
        return img_tokens + gate * cross_out

# ---------------------------------------------------------------------------
# MLP  (FIX #1: no GELU after fc2)
# ---------------------------------------------------------------------------
class _MLP(nn.Module):
    """
    Standard transformer FFN / MLP block.

    FIX (vs original): the original applied self.act(x) a second time *after* fc2
    (the output projection).  This is non-standard: activating the output projection
    (a) changes the function class of the MLP, (b) clips negative outputs before the
    residual add, and (c) can slow convergence.  Correct behaviour is activation only
    between fc1 and fc2.
    """

    def __init__(self, dim, mlp_ratio=4.0, dropout=0.0):
        super().__init__()
        hidden = int(dim * mlp_ratio)
        self.fc1  = nn.Linear(dim, hidden)
        self.act  = nn.GELU()
        self.fc2  = nn.Linear(hidden, dim)
        self.drop = nn.Dropout(dropout)

        nn.init.xavier_uniform_(self.fc1.weight)
        nn.init.xavier_uniform_(self.fc2.weight)
        nn.init.normal_(self.fc1.bias, std=1e-6)
        nn.init.normal_(self.fc2.bias, std=1e-6)

    def forward(self, x):
        x = self.fc1(x)
        x = self.act(x)   # activation only here — between fc1 and fc2
        x = self.drop(x)
        x = self.fc2(x)   # NO activation after fc2  ← bug fixed
        x = self.drop(x)
        return x


# ---------------------------------------------------------------------------
# Block
# ---------------------------------------------------------------------------
class Block(nn.Module):
    """Transformer encoder block (pre-LN)."""

    def __init__(self, dim, num_heads=8, mlp_ratio=4.0, dropout=0.0, attn_dropout=0.0):
        super().__init__()
        self.norm1 = nn.LayerNorm(dim)
        self.attn  = nn.MultiheadAttention(
            embed_dim=dim, num_heads=num_heads, dropout=attn_dropout, batch_first=True
        )
        self.norm2 = nn.LayerNorm(dim)
        self.mlp   = _MLP(dim, mlp_ratio=mlp_ratio, dropout=dropout)

    def forward(self, x):
        residual  = x
        x_norm    = self.norm1(x)
        x_attn, _ = self.attn(x_norm, x_norm, x_norm, need_weights=False)
        x         = residual + x_attn

        residual = x
        x_norm   = self.norm2(x)
        x        = residual + self.mlp(x_norm)
        return x


# ---------------------------------------------------------------------------
# VisionTransformer
# ---------------------------------------------------------------------------
class VisionTransformer(nn.Module):
    def __init__(
        self,
        img_size=224, patch_size=16, in_channels=3, embed_dim=64, depth=1, heads=8,
        mlp_ratio=4.0, attn_dropout=0.0, dropout=0.0,
        text_fuse=False,
        pretrained_timm_name=None, pretrained=False,
    ):
        super().__init__()
        self.embed = Embeddings(
            in_channels=in_channels, embed_dim=embed_dim,
            patch_size=patch_size, img_size=img_size, dropout=dropout,
        )
        self.n_patches = self.embed.n_patches
        self.blocks    = nn.Sequential(*[
            Block(embed_dim, num_heads=heads, mlp_ratio=mlp_ratio,
                  dropout=dropout, attn_dropout=attn_dropout)
            for _ in range(depth)
        ])
        self.norm      = nn.LayerNorm(embed_dim)
        self.text_fuse = text_fuse
        if text_fuse:
            # self.cross = CrossAttention(embed_dim, num_heads=heads, qkv_bias=True, dropout=attn_dropout)
            self.cross = GatedCrossAttention(embed_dim, num_heads=heads, dropout=attn_dropout)
        self._timm_model = None
        if pretrained_timm_name is not None:
            self.load_pretrained_from_timm(pretrained_timm_name, pretrained=pretrained)

        nn.init.trunc_normal_(self.embed.pos_emb, std=0.02)

    # ------------------------------------------------------------------
    def load_pretrained_from_timm(self, model_name, pretrained=True, use_forward_features=True):
        if not _HAS_TIMM:
            raise ImportError("timm is required. Install via `pip install timm`.")
        tm = timm.create_model(model_name, pretrained=pretrained, num_classes=0, global_pool='')
        if use_forward_features and hasattr(tm, 'forward_features'):
            self._timm_model = tm
            warnings.warn(
                f"Using timm model {model_name} forward_features as feature extractor. "
                "Ensure returned shape matches token expectations."
            )
            return
        tm_state = tm.state_dict()
        my_state = self.state_dict()
        copied = 0
        for k_tm, v_tm in tm_state.items():
            if k_tm in my_state and my_state[k_tm].shape == v_tm.shape:
                my_state[k_tm].copy_(v_tm); copied += 1
            else:
                for k_my in my_state:
                    if k_my.endswith(k_tm) and my_state[k_my].shape == v_tm.shape:
                        my_state[k_my].copy_(v_tm); copied += 1; break
        self.load_state_dict(my_state)
        warnings.warn(
            f"Copied pretrained weights from {model_name}: {copied}/{len(my_state)} params matched."
        )

    # ------------------------------------------------------------------
    def forward(self, x, text_tokens=None):
        """
        x           : [B, in_channels, H, W]
        text_tokens : [B, L, embed_dim]  (optional)
        returns     : tokens [B, n_patches, embed_dim]
        """
        if self._timm_model is not None and hasattr(self._timm_model, 'forward_features'):
            feat = self._timm_model.forward_features(x)
            if feat.ndim == 4:
                B, C, Hf, Wf = feat.shape
                tokens = feat.flatten(2).transpose(1, 2)
            elif feat.ndim == 2:
                raise RuntimeError(
                    "timm forward_features returned pooled features, not tokens."
                )
            else:
                tokens = feat
            if self.text_fuse and text_tokens is not None:
                if text_tokens.size(-1) != tokens.size(-1):
                    raise ValueError(
                        f"text_tokens dim {text_tokens.size(-1)} != feature dim {tokens.size(-1)}"
                    )
                tokens = tokens + self.cross(tokens, text_tokens)
            if tokens.size(-1) == self.norm.normalized_shape[0]:
                tokens = self.blocks(tokens)
                tokens = self.norm(tokens)
            return tokens

        # ── Normal path ────────────────────────────────────────────────
        tokens = self.embed(x)                                            # [B, n_patches, embed_dim]
        if self.text_fuse and text_tokens is not None:
            if text_tokens.size(-1) != tokens.size(-1):
                raise ValueError(
                    f"text_tokens last dim {text_tokens.size(-1)} != embed_dim {tokens.size(-1)}"
                )
            # tokens = tokens + self.cross(tokens, text_tokens)
            tokens = self.cross(tokens, text_tokens)
        tokens = self.blocks(tokens)
        tokens = self.norm(tokens)
        return tokens