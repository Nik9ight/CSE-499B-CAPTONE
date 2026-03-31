"""
Model registry — maps image_type keys to segmentation functions.

To add a new modality:
  1. Create a new module (e.g. my_model.py) with a function:
         def my_model(img: PIL.Image) -> PIL.Image
     that returns a grayscale mask (white pixels > 128 = segmented region).
  2. Import it here and add an entry to MODELS.
  3. Add a matching <option value="my_key"> in the CONFIG drawer of radiology_explainer.html.
"""

from test_model import test_model

# ---------------------------------------------------------------------------
# Add new entries here:  "frontend_key": model_function
# ---------------------------------------------------------------------------
MODELS = {
    "chest_xray": test_model,
    # "brain_mri":   brain_mri_model,
    # "abdominal_ct": abdominal_ct_model,
}


def get_model(image_type: str):
    """Return the segmentation function for the given image_type key."""
    fn = MODELS.get(image_type)
    if fn is None:
        available = list(MODELS.keys())
        raise KeyError(f"Unknown image type '{image_type}'. Available: {available}")
    return fn
