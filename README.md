# RadVision — Radiology Segmentation & Report Explainer

A web application for medical image analysis. Upload a radiology image, segment it with a local Python backend powered by LViTN (Language-Vision Transformer), generate an AI-powered diagnostic report via MedGemma, and get plain-language explanations of each finding by clicking sentences in the report.

---

## Features

- **Image segmentation** — language-guided LViTN model segments the uploaded image and overlays the predicted mask
- **AI report generation** — calls the HuggingFace Inference API (MedGemma) to produce a structured radiology report
- **Click-to-explain** — click any sentence in the report to get a plain-language explanation from MedGemma
- **Three canvas views** — Original, Mask, and Overlay with adjustable opacity

---

## Project Structure

```
.
├── server.py            # Flask API server (segmentation, report, explanation endpoints)
├── test_model.py        # LViTN inference pipeline
├── reportGen.py         # MedGemma report generation
├── explain.py           # Sentence explanation endpoint
├── model_registry.py    # Maps imaging modality → model config
├── nets/
│   ├── LViTN.py         # Language-Vision Transformer Network architecture
│   └── ViTN.py          # Vision Transformer backbone
├── models/              # Pretrained weights (not included — see below)
│   └── chest_xray/
│       └── best_model-LViT.pth.tar
├── requirements.txt
├── .env.example
└── frontEnd/            # React + Vite frontend
    ├── src/
    │   ├── App.jsx
    │   ├── context/AppContext.jsx   # Global state (config + runtime)
    │   ├── hooks/                   # useSegmentation, useReport, useExplanation
    │   └── components/              # ViewerPanel, ReportPanel, Header, etc.
    └── package.json
```

---

## Setup & Running

### Prerequisites

- Python 3.10+
- Node.js 18+
- CUDA-capable GPU (required for LViTN inference)
- HuggingFace account with MedGemma access (for report generation)

---

### 1. Clone and configure secrets

```bash
git clone <repo-url>
cd <repo-folder>
cp .env.example .env
# Open .env and set your HF_TOKEN
```

---

### 2. Download model weights

Pretrained LViTN weights are not included in the repository. Place the checkpoint at:

```text
models/chest_xray/best_model-LViT.pth.tar
```

---

### 3. Start the backend

```bash
pip install -r requirements.txt
python server.py        # listens on http://localhost:5000
```

---

### 4. Start the frontend

```bash
cd frontEnd/
npm install
npm run dev             # runs on http://localhost:5173
```

Open [http://localhost:5173](http://localhost:5173) in your browser.

---

### 5. Configure the app

Click **CONFIG** (top-right) and enter:

| Setting | Value |
|---------|-------|
| Segmentation API endpoint | `http://localhost:5000` |
| HuggingFace token | your `hf_…` token |
| Model | `google/medgemma-4b-it` (fast) or `google/medgemma-27b-it` (quality) |

Config is saved to `localStorage` — you only need to set it once.

---

## HuggingFace Access

MedGemma is a gated model. Before using report generation:

1. Request access at `huggingface.co/google/medgemma-4b-it`
2. Generate a token at `huggingface.co/settings/tokens`
3. Add it to `.env` as `HF_TOKEN=hf_…` and/or paste it into the CONFIG drawer

---

## API Reference

### `POST /segment?modality=<type>`

```json
// Request
{ "image_base64": "<base64-encoded PNG/JPEG>" }

// Response
{ "mask_base64": "<base64-encoded grayscale PNG>" }
```

White pixels (`> 128`) in the mask mark the segmented region.

### `POST /report`

```json
// Request
{ "image_base64": "<base64-encoded image>" }

// Response
{ "report": "<JSON string with Findings/Impressions/Recommendations>" }
```

### `POST /explain`

```json
// Request
{ "sentenceText": "<a sentence from the report>" }

// Response
{ "explanation": "<plain-language explanation>" }
```

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
| Frontend | React 19, Vite, HTML5 Canvas |
| Backend | Python, Flask 3, Flask-CORS |
| Segmentation | LViTN (Language-Vision Transformer Network) |
| Text encoder | BiomedBERT (`microsoft/BiomedNLP-BiomedBERT-base-uncased-abstract-fulltext`) |
| Vision backbone | ConvNeXt (`convnext_tiny.in12k_ft_in1k`) via timm |
| AI / LLM | HuggingFace Inference API — MedGemma 4b / 27b |
