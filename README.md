# RadVision — Radiology Segmentation & Report Explainer

A standalone web application for medical image analysis. Upload a radiology image, segment it with a local Python backend, generate an AI-powered diagnostic report via MedGemma, and get plain-language explanations of each finding on hover.

---

## Features

- **Image segmentation** — sends the image to a local Flask server and overlays the predicted mask
- **AI report generation** — calls the HuggingFace Inference API (MedGemma) to produce a structured radiology report
- **Hover-to-explain** — click any sentence in the report to get a plain-language explanation from MedGemma
- **Three canvas views** — Original, Mask, and Overlay with adjustable opacity
- **No build step** — the entire frontend is a single HTML file

---

## Project Structure

```
.
├── radiology_explainer.html   # Full frontend (CSS + HTML + JS, no frameworks)
├── server.py                  # Flask segmentation backend
├── requirements.txt           # Python dependencies
├── .env.example               # Secret config template — copy to .env
└── .gitignore
```

---

## Quick Start

### 1. Clone and configure secrets

```bash
git clone <repo-url>
cd <repo-folder>
cp .env.example .env
# Open .env and fill in your HF_TOKEN
```

### 2. Start the segmentation backend

```bash
pip install -r requirements.txt
python server.py        # listens on http://localhost:5000
```

### 3. Open the frontend

Open `radiology_explainer.html` directly in a browser — no server needed for the frontend.

### 4. Configure the app

Click **CONFIG** (top-right) and enter:

| Setting | Value |
|---------|-------|
| Segmentation API endpoint | `http://localhost:5000/segment` |
| HuggingFace token | your `hf_…` token |
| Model | `google/medgemma-4b-it` (fast) or `google/medgemma-27b-it` (quality) |
| Mask label / overlay color | optional |

Config is saved to `localStorage` — you only need to set it once.

---

## HuggingFace Access

MedGemma is a gated model. Before using it:

1. Request access at `huggingface.co/google/medgemma-4b-it`
2. Generate a token at `huggingface.co/settings/tokens`
3. Add it to `.env` as `HF_TOKEN=hf_…` (for local reference) and/or paste it into the CONFIG drawer

---

## Plugging in a Real Segmentation Model

Edit the `segment_image()` function in [server.py](server.py):

```python
def segment_image(img: Image.Image) -> Image.Image:
    # img  — PIL Image (RGB)
    # return a grayscale PIL Image; white pixels (>128) = segmented region
    ...
```

Drop-in replacements: PyTorch U-Net, MedSAM, or any HuggingFace segmentation model. The demo uses Otsu thresholding as a placeholder.

---

## API Reference

### `POST /segment`

**Request body**

```json
{ "image_base64": "<base64-encoded PNG/JPEG>" }
```

**Response**

```json
{ "mask_base64": "<base64-encoded grayscale PNG>" }
```

White pixels in the mask (`> 128`) mark the segmented region.

---

## Environment Variables

See [.env.example](.env.example) for all options.

| Variable | Default | Description |
|----------|---------|-------------|
| `HF_TOKEN` | — | HuggingFace token (required for report generation) |
| `FLASK_HOST` | `0.0.0.0` | Host the backend binds to |
| `FLASK_PORT` | `5000` | Port the backend listens on |
| `FLASK_DEBUG` | `false` | Enable Flask debug mode |

> `.env` is gitignored — never commit it.

---

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Frontend | Vanilla HTML/CSS/JS, HTML5 Canvas |
| Backend | Python, Flask, Flask-CORS |
| Segmentation (demo) | scikit-image (Otsu threshold) |
| AI / LLM | HuggingFace Inference API — MedGemma |
| Fonts | IBM Plex Sans, IBM Plex Mono |
