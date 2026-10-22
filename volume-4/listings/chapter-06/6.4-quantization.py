# Applied AI Engineering, Volume IV, Chapter 6
# Section 6.4, Quantization
# Copied from the book by scripts/export_listings.py. Report errors as errata.

# Example: Loading a GPTQ-quantized model using HuggingFace transformers
# Requires a CUDA GPU and: pip install transformers accelerate optimum
#   then: pip install gptqmodel --no-build-isolation
# (AutoGPTQ, which this used to need, was archived in 2025.)

from transformers import AutoTokenizer, AutoModelForCausalLM
import torch

MODEL_ID = "TheBloke/Mistral-7B-v0.1-GPTQ"  # 4-bit quantized

tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForCausalLM.from_pretrained(
    MODEL_ID,
    device_map="auto",
    torch_dtype=torch.float16,
)

prompt = "Explain quantization in one paragraph:"
inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

with torch.no_grad():
    outputs = model.generate(
        **inputs,
        max_new_tokens=150,
        do_sample=False,
        temperature=1.0,
    )

response = tokenizer.decode(outputs[0][inputs["input_ids"].shape[1]:], skip_special_tokens=True)
print(response)
