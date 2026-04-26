"""
Segmentation API for RadVision

Two route styles — use whichever matches your frontend config:

  POST /segment/<image_type>   e.g. /segment/chest_xray  (type comes from URL)
  POST /segment                fallback; defaults to chest_xray

Request body:  { "image_base64": "<base64 string>" }
Response:      { "mask_base64": "<base64 binary PNG>" }

White pixels (brightness > 128) = segmented region
Black pixels = background

To add a new modality, edit model_registry.py.
"""

import base64
import io
import os
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
from explain import explain
from test_model import test_model
from reportGen import reportGen
from transformers import AutoProcessor, AutoModelForImageTextToText
from huggingface_hub import login
import torch
MODEL_ID = "google/medgemma-1.5-4b-it"

# Load .env if present (pip install python-dotenv, or set vars in your shell)
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass  # dotenv optional — set env vars in your shell instead

HOST  = os.environ.get("FLASK_HOST",  "0.0.0.0")
PORT  = int(os.environ.get("FLASK_PORT",  "5000"))
DEBUG = os.environ.get("FLASK_DEBUG", "false").lower() == "true"

app = Flask(__name__)
CORS(app)  # Required so the browser can call this from the HTML file

@app.route("/hello", methods=["GET"])
def hello():
    return "Hello from RadVision backend!"


@app.route("/segment", methods=["POST"])
def segment():
    """Route that reads modality from query param, e.g. ?modality=chest_xray"""
    modality = request.args.get("modality", "chest_xray")  # defaults to chest_xray if not provided
    image_filename = request.args.get("image_filename", "uploaded_image.png")  # optional filename for logging
    print(f"Received segmentation request for modality '{modality}' with image filename '{image_filename}'")
    data = request.get_json(force=True)
    if not data or "image_base64" not in data:
        return jsonify({"error": "Missing image_base64 field"}), 400
    try:
        img_bytes = base64.b64decode(data["image_base64"])
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    except Exception as e:
        return jsonify({"error": f"Could not decode image: {e}"}), 400
    mask_img = test_model(img, modality=modality)

    buf = io.BytesIO()
    mask_img.save(buf, format="PNG")
    mask_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return jsonify({"mask_base64": mask_b64})


model= "None"
processor = "None"
# def load_model():
#     """Load model and processor once."""
#     hf_token = os.environ.get("HF_TOKEN")
#     if not hf_token:
#         raise RuntimeError("HF_TOKEN is not set. Add it to .env or environment variables.")

#     login(token=hf_token)

#     dtype = torch.bfloat16 if torch.cuda.is_available() else torch.float32
#     device_map = "cuda" if torch.cuda.is_available() else "cpu"

#     model = AutoModelForImageTextToText.from_pretrained(
#         MODEL_ID,
#         dtype=dtype,
#         device_map=device_map,
#     )
#     processor = AutoProcessor.from_pretrained(MODEL_ID)
#     return model, processor
# model, processor = load_model()

@app.route("/report", methods=["POST"])
def generate_report():
    data = request.get_json(force=True)
    if not data or "image_base64" not in data:
        return jsonify({"error": "Missing image_base64 field"}), 400
    try:
        img_bytes = base64.b64decode(data["image_base64"])
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    except Exception as e:
        return jsonify({"error": f"Could not decode image: {e}"}), 400
    report = reportGen(img, model, processor)
    return jsonify({"report": report})

@app.route("/explain", methods=["POST"])
def explainSentence():
    data = request.get_json(force=True)
    sentence = data.get("sentenceText", "")
    response = explain(sentence, model, processor)
    return jsonify({"explanation": response})

if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG)
