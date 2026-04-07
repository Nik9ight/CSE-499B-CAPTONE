import torch

dummy_explanation = (f"""
    Raw model response: Explanation: There is a small area of increased density in the lower part of your right lung. This could be due to a few different things, such as lung tissue that has collapsed (atelectasis) or an area where there is inflammation or infection (consolidation). Further evaluation may be needed to determine the exact cause.
"""
)
def explain(sentence, model, processor):
    print(f"Received sentence for explanation: '{sentence}'")
    decoded = None
    PROMPT = (
    f"""
        You are a patient-friendly medical translator. You receive a single sentence from a radiology or pathology report.
        Your job is to explain what it means in plain language that a non-medical adult can understand.
        Follow the exact format shown in the examples.

        Example 1:
        Sentence: "No pneumothorax."
        Explanation: Your lungs are not collapsed. There is no air leaking into the space around them.

        Example 2:
        Sentence: "Normal heart size."
        Explanation: Your heart appears to be a normal size on the scan, which is a good sign.

        Example 3:
        Sentence: "Small to medium right pleural effusion with adjacent right basilar atelectasis."
        Explanation: There is a small to medium amount of fluid in the space between your lung and chest wall on the right side (pleural effusion). This fluid is causing some of your lung tissue near the bottom on the right side (basilar) to collapse or be less inflated (atelectasis).

        Now explain this sentence in the same style. Use 2-4 sentences. Replace medical terms with plain language in parentheses. Do not add any medical advice.

        Sentence: "{sentence}"
        Explanation:
        """
    )
    # print(f"Formatted prompt for model:\n{PROMPT}")
    messages = [
           {
               "role": "user",
               "content": [
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
           return_tensors="pt",
       ).to(model.device, dtype=torch.bfloat16)
    input_len = inputs["input_ids"].shape[-1]
    
    # Set hyperparameters here
    with torch.inference_mode():
           generation = model.generate(
               **inputs,
               max_new_tokens=256,
               do_sample=True,
               temperature=0.1,
               top_p=0.85
           )
           generation = generation[0][input_len:]
    decoded = processor.decode(generation, skip_special_tokens=True)
    # print("Raw model response:", decoded)
    if decoded is None:
        return dummy_explanation
    return decoded