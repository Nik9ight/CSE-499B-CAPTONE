import base64
import io
from PIL import Image
import torch

PROMPT = (
    """
    You are a radiology assistant. Analyze this medical image and generate a one
    sentence radiology report including: Findings and Impressions. Explicitly
    mention the position of the lesion/tumor/cyst. Use the image's green overlay
    for hint and guidance. Do not add any medical advice.
    Findings and Impressions are in the same sentence.
    Do not say "Raw model response"/"FINDINGS"/"IMPRESSIONS".
    Example output:
      Bilateral pulmonary infection, two infected areas, lower left lung and middle lower right lung.
      Unilateral pulmonary infection, two infected areas, left lung and middle right lung.
      Large lesion in the right temporal lobe.
      Single cystic lesion in the upper right quadrant.

    DO NOT get bias on these examples. DO NOT mention the green overlay.
    """
)
# PROMPT = (
#     "You are a radiology assistant. Analyze this medical image and generate "
#     "a structured radiology report in JSON format with the following schema:\n"
#     '{ "modality": "<modality>", "sections": [ { "title": "<section>", '
#     '"sentences": [ { "text": "<finding>", "tag": "finding" } ] } ] }\n'
#     "The input image may be either: (1) the original raw image, or (2) an overlay "
#     "image where highlighted colored regions indicate model-segmented areas of interest. "
#     "If an overlay is present, treat the highlighted region as guidance and still evaluate "
#     "the full image context. Do not assume highlighted pixels are always pathology.\n"
#     "Include sections for Findings, Impressions, and Recommendations.\n"
#     "Return only valid JSON. Do not add markdown, code fences, or extra commentary."
# )
dummy_res = (f"""
    Raw model response: FINDINGS:
    The image is a chest X-ray. There is a consolidation in the left lower lobe. The right lung appears clear. The heart size is normal. The mediastinum is normal. There is no pleural effusion.

    IMPRESSIONS:
    Left lower lobe consolidation.

    RECOMMENDATIONS:
    Follow up as indicated.
    """
)
def get_medgemma_description(input_image, model, processor):
    """Generate a radiology report from a PIL Image."""
    decoded = None
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
        generation = model.generate(
                    **inputs,
                     max_new_tokens=32, 
                     do_sample=True, 
                     temperature=0.1, 
                     top_p=0.85)
        generation = generation[0][input_len:]

    decoded = processor.decode(generation, skip_special_tokens=True)
    print(decoded)
    # print(dummy_res)
    if decoded is None:
        return dummy_res
    return decoded