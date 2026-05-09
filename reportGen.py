import base64
import io
from PIL import Image
import torch

# PROMPT = (
#     """
#     You are a radiology assistant. Analyze this medical image and generate a radiology report including:
#     Findings, Impressions, Diagnoses and Recommendations.
#     """
# )
# # PROMPT = (
# #     "You are a radiology assistant. Analyze this medical image and generate "
# #     "a structured radiology report in JSON format with the following schema:\n"
# #     '{ "modality": "<modality>", "sections": [ { "title": "<section>", '
# #     '"sentences": [ { "text": "<finding>", "tag": "finding" } ] } ] }\n'
# #     "The input image may be either: (1) the original raw image, or (2) an overlay "
# #     "image where highlighted colored regions indicate model-segmented areas of interest. "
# #     "If an overlay is present, treat the highlighted region as guidance and still evaluate "
# #     "the full image context. Do not assume highlighted pixels are always pathology.\n"
# #     "Include sections for Findings, Impressions, and Recommendations.\n"
# #     "Return only valid JSON. Do not add markdown, code fences, or extra commentary."
# # )
# dummy_res = (f"""
#     Raw model response: FINDINGS:
#     The image is a chest X-ray. There is a consolidation in the left lower lobe. The right lung appears clear. The heart size is normal. The mediastinum is normal. There is no pleural effusion.

#     IMPRESSIONS:
#     Left lower lobe consolidation.

#     RECOMMENDATIONS:
#     Follow up as indicated.
#     """
# )
# def reportGen(input_image, model, processor):
#     """Generate a radiology report from a PIL Image."""
#     decoded = None
#     # messages = [
#     #     {
#     #         "role": "user",
#     #         "content": [
#     #             {"type": "image"},
#     #             {"type": "text", "text": PROMPT},
#     #         ],
#     #     }
#     # ]

#     # # Step 1: format the chat prompt as a string (no tokenization)
#     # text = processor.apply_chat_template(
#     #     messages, add_generation_prompt=True, tokenize=False
#     # )

#     # # Step 2: process text + image together
#     # inputs = processor(
#     #     text=text,
#     #     images=[input_image],
#     #     return_tensors="pt",
#     # ).to(model.device, dtype=torch.bfloat16)

#     # input_len = inputs["input_ids"].shape[-1]

#     # with torch.inference_mode():
#     #     generation = model.generate(**inputs, max_new_tokens=1024, do_sample=False)
#     #     generation = generation[0][input_len:]

#     # decoded = processor.decode(generation, skip_special_tokens=True)

#     # print("Raw model response:", decoded)
#     # print(dummy_res)
#     if decoded is None:
#         return dummy_res
#     return decoded

def reportGen(img, text_hint, model, processor):
    PROMPT = f"""
You are a radiology assistant. Analyze this medical image and generate a
detailed radiology report with the following sections:

1. Findings (detailed description of all abnormalities, their locations,
   sizes, margins, densities, and any effect on surrounding structures)
2. Impressions (summary of key findings with differential diagnoses if
   applicable)

Text hint from detection model: "{text_hint}"
Use this hint as the primary guide for your report. The hint tells you the
type of condition, the number of affected areas, and their locations.
Your report must be consistent with this hint. Expand and elaborate on the
hint with appropriate radiological language and detail, but do NOT
contradict the hint regarding condition type, count, or location of
affected areas.

Use the image's green overlay for additional visual guidance.
Do not add any medical advice or treatment recommendations.
Do not say "Raw model response".
Do not mention the green overlay or the text hint in the report.
"""

    messages = [
        {
            "role": "user",
            "content": [
                {"type": "image"},
                {"type": "text", "text": PROMPT},
            ],
        }
    ]

    text = processor.apply_chat_template(
        messages, add_generation_prompt=True, tokenize=False
    )
    inputs = processor(
        text=text,
        images=[img],
        return_tensors="pt",
    ).to(model.device, dtype=torch.bfloat16)
    input_len = inputs["input_ids"].shape[-1]

    with torch.inference_mode():
        generation = model.generate(
            **inputs,
            max_new_tokens=232,
            do_sample=True,
            temperature=0.2,
            top_p=0.95,
        )
        generation = generation[0][input_len:]

    decoded = processor.decode(generation, skip_special_tokens=True)
    return decoded
