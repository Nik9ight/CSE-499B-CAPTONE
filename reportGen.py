import base64
import io
from PIL import Image
import torch

PROMPT = (
    "You are a radiology assistant. Analyze this medical image and generate "
    "a structured radiology report in JSON format with the following schema:\n"
    '{ "modality": "<modality>", "sections": [ { "title": "<section>", '
    '"sentences": [ { "text": "<finding>", "tag": "finding" } ] } ] }\n'
    "Include sections for Findings, Impressions, and Recommendations."
)
res = (f"""
    Raw model response: FINDINGS:
    The image is a chest X-ray. There is a consolidation in the left lower lobe. The right lung appears clear. The heart size is normal. The mediastinum is normal. There is no pleural effusion.

    IMPRESSIONS:
    Left lower lobe consolidation.

    RECOMMENDATIONS:
    Follow up as indicated.
    """
)
def reportGen(input_image, model, processor):
    """Generate a radiology report from a PIL Image."""

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image"},
                {"type": "text", "text": PROMPT},
            ],
        }
    ]

    # Step 1: format the chat prompt as a string (no tokenization)
    text = processor.apply_chat_template(
        messages, add_generation_prompt=True, tokenize=False
    )

    # Step 2: process text + image together
    inputs = processor(
        text=text,
        images=[input_image],
        return_tensors="pt",
    ).to(model.device, dtype=torch.bfloat16)

    input_len = inputs["input_ids"].shape[-1]

    with torch.inference_mode():
        generation = model.generate(**inputs, max_new_tokens=1024, do_sample=False)
        generation = generation[0][input_len:]

    decoded = processor.decode(generation, skip_special_tokens=True)

    print("Raw model response:", decoded)
    # print(res)
    return decoded

