"""
Segmentation API for RadVision
POST /segment
  Body:    { "image_base64": "<base64 string>" }
  Returns: { "mask_base64": "<base64 binary PNG>" }

White pixels (brightness > 128) = segmented region
Black pixels = background

Replace the body of `segment_image()` with your real model.
"""

import base64
import io
import os
import numpy as np
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
from skimage.filters import threshold_otsu
from skimage.morphology import remove_small_objects, binary_closing, disk

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


def segment_image(img: Image.Image) -> Image.Image:
    """
    Replace this function body with your real segmentation model.

    Input:  PIL Image (RGB)
    Output: PIL Image (grayscale, white = mask, black = background)

    Example drop-in replacements:
      - Load a PyTorch U-Net: model(tensor) -> binary mask
      - Call an external model API
      - Use MedSAM or another HuggingFace segmentation model

    The demo below uses Otsu thresholding on grayscale as a stand-in.
    """
    gray = np.array(img.convert("L"), dtype=np.float32)

    # --- REPLACE BELOW WITH YOUR MODEL ---
    thresh = threshold_otsu(gray)
    binary = gray > thresh
    # Clean up small noise and smooth edges
    binary = remove_small_objects(binary, min_size=500)
    binary = binary_closing(binary, disk(4))
    # --- END OF DEMO SEGMENTATION ---

    mask = (binary.astype(np.uint8)) * 255
    return Image.fromarray(mask, mode="L")


@app.route("/segment", methods=["POST"])
def segment():
    data = request.get_json(force=True)
    if not data or "image_base64" not in data:
        return jsonify({"error": "Missing image_base64 field"}), 400

    try:
        img_bytes = base64.b64decode(data["image_base64"])
        img = Image.open(io.BytesIO(img_bytes)).convert("RGB")
    except Exception as e:
        return jsonify({"error": f"Could not decode image: {e}"}), 400

    mask_img = segment_image(img)

    buf = io.BytesIO()
    mask_img.save(buf, format="PNG")
    mask_b64 = base64.b64encode(buf.getvalue()).decode("utf-8")

    return jsonify({"mask_base64": mask_b64})


if __name__ == "__main__":
    app.run(host=HOST, port=PORT, debug=DEBUG)
