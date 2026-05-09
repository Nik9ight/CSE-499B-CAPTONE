# import torch
# import torch.nn as nn
# import numpy as np
# import cv2
# import os
# from PIL import Image
# import ml_collections
# from nets.LViTNT import LViTN
# from transformers import AutoTokenizer, AutoModel

# _tokenizer = None
# _bert_model = None

# def _load_bert():
#     global _tokenizer, _bert_model
#     if _bert_model is not None:
#         return _tokenizer, _bert_model
#     model_name='microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext'
#     _tokenizer = AutoTokenizer.from_pretrained(model_name, trust_remote_code=True)
#     _bert_model = AutoModel.from_pretrained(model_name, trust_remote_code=True).cuda().eval()
#     return _tokenizer, _bert_model

# def text_to_tensor(text):
#     """Convert a text string to BERT embeddings [1, L, 768]."""
#     tokenizer, bert = _load_bert()
#     inputs = tokenizer(text, return_tensors="pt", padding=True, truncation=True, max_length=512)
#     inputs = {k: v.cuda() for k, v in inputs.items()}
#     with torch.no_grad():
#         outputs = bert(**inputs)
#     return outputs.last_hidden_state  # [1, L, 768]
# def get_CTranS_config():
#     cfg = ml_collections.ConfigDict()
#     cfg.transformer = ml_collections.ConfigDict()

#     cfg.KV_size = 960 # Dimension of K and V in Multi-Head Attention
#     cfg.transformer.num_heads = 4
#     cfg.transformer.num_layers = 4
#     cfg.transformer.embeddings_dropout_rate = 0.1
#     cfg.transformer.attention_dropout_rate = 0.1
#     cfg.transformer.dropout_rate = 0

#     cfg.base_channel = 64      # base U-Net channel
#     cfg.n_classes = 1
#     cfg.expand_ratio = 4
#     cfg.patch_sizes = [16, 8, 4, 2]

#     return cfg
# _model = None
# def _load_model(modality):
#     global _model
#     if _model is not None:
#         return _model
#     model_path = f"./models/{modality}/best_model-LViT.pth.tar"
#     os.environ["CUDA_VISIBLE_DEVICES"] = "0"
#     checkpoint = torch.load(model_path, map_location="cuda")
#     cfg = get_CTranS_config()
#     model = LViTN(cfg,
#                   n_channels=3,
#                   n_classes=1,
#                   img_size=224,
#                   backbone_name='convnext_tiny.in12k_ft_in1k',
#                   backbone_pretrained=False)

#     model = model.cuda()
#     if torch.cuda.device_count() > 1:
#         model = nn.DataParallel(model)

#     model.load_state_dict(checkpoint["state_dict"], strict=True)
#     model.eval()
#     print(f"Model loaded. "f" Path: {model_path}")
#     _model = model
#     return _model

# def test_model(input_image, text=None, modality="chest_xray"):
#     """
#     input_image  : PIL Image (RGB)
#     text_tensor  : torch tensor [1, L, D] or None
#     Returns      : PIL Image (grayscale mask, 0 or 255)
#     """
#     model = _load_model(modality=modality)
#     # Preprocess: ensure RGB, resize, normalize
#     img_rgb = input_image.convert("RGB")
#     img_resized = img_rgb.resize((224, 224), Image.BILINEAR)
#     img_np = np.array(img_resized, dtype=np.float32) / 255.0
#     img_np = img_np.transpose(2, 0, 1)              # [3, H, W]
#     img_np = img_np[np.newaxis, :, :, :]             # [1, 3, H, W]

#     img_t = torch.from_numpy(img_np).float().cuda()

#     with torch.no_grad():
#         if text is None:
#             text = "Large lesion in the right hemisphere."
#             text_tensor = text_to_tensor(text)
#         else:
#             text_tensor = text_to_tensor(text)
#         out = model(img_t, text_tensor.cuda())
#         # out = model(img_t)

#     logits = out["out"]
#     probs = torch.sigmoid(logits)
#     preds = (probs > 0.5).float()
#     pred_np = preds[0, 0].cpu().numpy()

#     # Resize prediction back to config size
#     pred_up = cv2.resize(
#         pred_np,
#         (224, 224),
#         interpolation=cv2.INTER_NEAREST
#     )

#     mask_uint8 = (pred_up * 255).astype(np.uint8)
#     mask_img = Image.fromarray(mask_uint8, mode="L")
#     return mask_img


import torch
import torch.nn as nn
import numpy as np
import cv2
import os
from PIL import Image
import ml_collections

from nets.LViTNT import LViTN  # match the architecture used in your working test script
from Load_Dataset import ValGenerator, correct_dims
from bertem import BertEmbeddingWrapper

# -------------------------------
# Config
# -------------------------------
def get_CTranS_config():
    cfg = ml_collections.ConfigDict()
    cfg.transformer = ml_collections.ConfigDict()
    cfg.KV_size = 960
    cfg.transformer.num_heads = 4
    cfg.transformer.num_layers = 4
    cfg.transformer.embeddings_dropout_rate = 0.1
    cfg.transformer.attention_dropout_rate = 0.1
    cfg.transformer.dropout_rate = 0
    cfg.base_channel = 64
    cfg.n_classes = 1
    cfg.expand_ratio = 4
    cfg.patch_sizes = [16, 8, 4, 2]
    return cfg


# -------------------------------
# Globals (cache heavy objects)
# -------------------------------
_model = None
_bert_wrapper = None
IMG_SIZE = 224
MAX_TEXT_TOKENS = 80
TEXT_EMBED_DIM = 768


def _load_model(modality):
    global _model
    if _model is not None:
        return _model

    os.environ["CUDA_VISIBLE_DEVICES"] = "0"
    model_path = f"./models/{modality}/best_model-LViT.pth.tar"
    checkpoint = torch.load(model_path, map_location="cuda")

    cfg = get_CTranS_config()
    model = LViTN(
        cfg,
        n_channels=3,
        n_classes=1,
        img_size=IMG_SIZE,
        backbone_name='convnext_tiny.in12k_ft_in1k',
        backbone_pretrained=False,
    )
    model = model.cuda()
    if torch.cuda.device_count() > 1:
        model = nn.DataParallel(model)

    # strict=True so missing/unexpected keys raise instead of silently
    # leaving layers randomly initialized
    model.load_state_dict(checkpoint["state_dict"], strict=True)
    model.eval()
    print(f"Model loaded from {model_path}")

    _model = model
    return _model


def _get_bert_wrapper():
    global _bert_wrapper
    if _bert_wrapper is None:
        _bert_wrapper = BertEmbeddingWrapper()
    return _bert_wrapper


# -------------------------------
# Text encoding (matches _load_and_process_text)
# -------------------------------
def encode_text(text_string):
    """
    Replicates ImageToImage2D._load_and_process_text but for an in-memory string.
    Returns numpy array [MAX_TEXT_TOKENS, TEXT_EMBED_DIM].
    """
    bert = _get_bert_wrapper()

    # Same split the dataset class uses
    text_lines = text_string.split('\n')

    text_tok = bert(text_lines)
    text_arr = np.array(text_tok[0][1])

    # Pad / truncate to MAX_TEXT_TOKENS
    if text_arr.shape[0] > MAX_TEXT_TOKENS:
        text_arr = text_arr[:MAX_TEXT_TOKENS, :]
    elif text_arr.shape[0] < MAX_TEXT_TOKENS:
        pad = np.zeros(
            (MAX_TEXT_TOKENS - text_arr.shape[0], TEXT_EMBED_DIM),
            dtype=text_arr.dtype,
        )
        text_arr = np.vstack([text_arr, pad])

    return text_arr


# -------------------------------
# Image preprocessing (matches __getitem__ + ValGenerator)
# -------------------------------
def preprocess_image(pil_image):
    """
    Replicates ImageToImage2D.__getitem__ image-loading branch:
      cv2-style BGR->RGB conversion, correct_dims, then ValGenerator transform.
    Returns torch tensor [1, 3, IMG_SIZE, IMG_SIZE] on CUDA.
    Also returns original (W, H) so the mask can be resized back if desired.
    """
    # PIL is already RGB, but the dataset uses cv2.imread (BGR) then cv2.cvtColor
    # to RGB. The end result is an RGB uint8 numpy array — so this is equivalent:
    image = np.array(pil_image.convert("RGB"))
    orig_size = (pil_image.width, pil_image.height)

    # Dummy mask + dummy text purely to satisfy ValGenerator's signature
    dummy_mask = np.zeros(image.shape[:2], dtype=np.uint8)
    dummy_text = np.zeros((MAX_TEXT_TOKENS, TEXT_EMBED_DIM), dtype=np.float32)

    image, dummy_mask = correct_dims(image, dummy_mask)

    sample = {"image": image, "label": dummy_mask, "text": dummy_text}

    tf = ValGenerator(output_size=(IMG_SIZE, IMG_SIZE))
    sample = tf(sample)

    img_t = sample["image"]                # [3, H, W], normalized
    img_t = img_t.unsqueeze(0).float().cuda()  # [1, 3, H, W]
    return img_t, orig_size


# -------------------------------
# Public inference function
# -------------------------------
def test_model(input_image, text=None, modality="chest_xray", resize_to_original=False):
    """
    Args:
        input_image : PIL.Image
        text        : str or None. If None, a generic placeholder is used —
                      but note that LViT is text-conditioned, so accuracy
                      depends heavily on a relevant description.
        modality    : which checkpoint folder to load
        resize_to_original : if True, the returned mask matches input image size

    Returns:
        PIL.Image (mode 'L'), values 0 or 255.
    """
    model = _load_model(modality)

    if text is None or text.strip() == "":
        text = "Bilateral pulmonary infection, two infected areas, lower left lung and middle lower right lung."

    img_t, orig_size = preprocess_image(input_image)

    print(text)  # Debug: print the text being encoded
    text_arr = encode_text(text)                              # [80, 768]
    text_t = torch.from_numpy(text_arr).float().unsqueeze(0)  # [1, 80, 768]
    text_t = text_t.cuda()

    with torch.no_grad():
        out = model(img_t, text_t)

    logits = out["out"]                          # [1, 1, h, w]
    probs = torch.sigmoid(logits)
    pred = (probs > 0.5).float()[0, 0].cpu().numpy()  # [h, w], 0/1

    mask_uint8 = (pred * 255).astype(np.uint8)

    if resize_to_original:
        mask_uint8 = cv2.resize(
            mask_uint8, orig_size, interpolation=cv2.INTER_NEAREST
        )

    return Image.fromarray(mask_uint8, mode="L")