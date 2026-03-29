import torch
import torch.nn as nn
import numpy as np
import cv2
import os
from PIL import Image
import ml_collections
from nets.LViTN import LViTN
from transformers import AutoTokenizer, AutoModel

_tokenizer = None
_bert_model = None

def _load_bert():
    global _tokenizer, _bert_model
    if _bert_model is not None:
        return _tokenizer, _bert_model
    model_name='microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext'
    _tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
    _bert_model = AutoModel.from_pretrained(model_name, trust_remote_code=True).cuda().eval()
    return _tokenizer, _bert_model

def text_to_tensor(text):
    """Convert a text string to BERT embeddings [1, L, 768]."""
    tokenizer, bert = _load_bert()
    inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
    inputs = {k: v.cuda() for k, v in inputs.items()}
    with torch.no_grad():
        outputs = bert(**inputs)
    return outputs.last_hidden_state  # [1, L, 768]
def get_CTranS_config():
    cfg = ml_collections.ConfigDict()
    cfg.transformer = ml_collections.ConfigDict()

    cfg.KV_size = 960 # Dimension of K and V in Multi-Head Attention
    cfg.transformer.num_heads = 4
    cfg.transformer.num_layers = 4
    cfg.transformer.embeddings_dropout_rate = 0.1
    cfg.transformer.attention_dropout_rate = 0.1
    cfg.transformer.dropout_rate = 0

    cfg.base_channel = 64      # base U-Net channel
    cfg.n_classes = 1
    cfg.expand_ratio = 4
    cfg.patch_sizes = [16, 8, 4, 2]

    return cfg
_model = None
def _load_model(model_path="./models/best_model-LViT.pth.tar"):
    global _model
    if _model is not None:
        return _model

    os.environ["CUDA_VISIBLE_DEVICES"] = "0"
    checkpoint = torch.load(model_path, map_location="cuda")
    cfg = get_CTranS_config()
    model = LViTN(cfg,
                  n_channels=3,
                  n_classes=1,
                  img_size=224,
                  backbone_name='convnext_tiny.in12k_ft_in1k',
                  backbone_pretrained=False)

    model = model.cuda()
    if torch.cuda.device_count() > 1:
        model = nn.DataParallel(model)

    model.load_state_dict(checkpoint["state_dict"])
    model.eval()
    print("Model loaded.")
    _model = model
    return _model

def test_model(input_image, text_tensor=None):
    """
    input_image  : PIL Image (RGB)
    text_tensor  : torch tensor [1, L, D] or None
    Returns      : PIL Image (grayscale mask, 0 or 255)
    """
    model = _load_model()

    # Preprocess: ensure RGB, resize, normalize
    img_rgb = input_image.convert("RGB")
    img_resized = img_rgb.resize((224, 224), Image.BILINEAR)
    img_np = np.array(img_resized, dtype=np.float32) / 255.0
    img_np = img_np.transpose(2, 0, 1)              # [3, H, W]
    img_np = img_np[np.newaxis, :, :, :]             # [1, 3, H, W]

    img_t = torch.from_numpy(img_np).float().cuda()

    with torch.no_grad():
        if text_tensor is None:
            text = "Bilateral pulmonary infection, two infected areas, lower left lung and lower right lung."
            text_tensor = text_to_tensor(text)
        out = model(img_t, text_tensor.cuda())

    logits = out["out"]
    probs = torch.sigmoid(logits)
    preds = (probs > 0.5).float()
    pred_np = preds[0, 0].cpu().numpy()

    # Resize prediction back to config size
    pred_up = cv2.resize(
        pred_np,
        (224, 224),
        interpolation=cv2.INTER_NEAREST
    )

    mask_uint8 = (pred_up * 255).astype(np.uint8)
    mask_img = Image.fromarray(mask_uint8, mode="L")
    return mask_img