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
from model_registry import get_model

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


def _run_segment(image_type: str):
    """Shared logic for both routes."""
    data = request.get_json(force=True)
    if not data or "image_base64" not in data:
        return jsonify({"error": "Missing image_base64 field"}), 400

    try:
        model_fn = get_model(image_type)
    except KeyError as e:
        return jsonify({"error": str(e)}), 400

    try:
        img_bytes = base64.b64decode(data["image_base64"])
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    except Exception as e:
        return jsonify({"error": f"Could not decode image: {e}"}), 400

    mask_img = model_fn(img)

    buf = io.BytesIO()
    mask_img.save(buf, format="PNG")
    mask_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")
    return jsonify({"mask_base64": mask_b64})


@app.route("/segment/<image_type>", methods=["POST"])
def segment_typed(image_type):
    """Type-specific route — configure the frontend endpoint as /segment/chest_xray etc."""
    return _run_segment(image_type)


@app.route("/segment", methods=["POST"])
def segment():
    """Generic fallback route — defaults to chest_xray model."""
    return _run_segment("chest_xray")


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG)
