# Applied AI Engineering, Volume II, Chapter 1
# Hands-on Lab: Establishing Your Prompt Engineering Baseline
# Copied from the book by scripts/export_listings.py. Report errors as errata.

import os
import json
from openai import OpenAI

client = OpenAI(api_key=os.environ["OPENAI_API_KEY"])

# --- TASK: Summarize a product for an e-commerce listing ---

product_description = """
The ThermoBreeze X7 is a portable personal cooling device powered by thermoelectric
technology. It uses a Peltier module to actively cool air by up to 10 degrees Celsius
below ambient temperature. The device weighs 340 grams, operates on USB-C power,
and includes three fan speed settings. Battery life on the internal 5000mAh pack
is approximately 6 hours at medium setting.
"""

# --- UNDERSPECIFIED PROMPT ---
underspecified_prompt = f"Summarize this product:\n\n{product_description}"

# --- ENGINEERED PROMPT ---
engineered_prompt = f"""You are a professional e-commerce copywriter specializing in \
consumer electronics.

Your task: Write a concise product summary for an Amazon listing.

Requirements:
- Exactly 2 sentences
- First sentence: Lead with the primary benefit for the customer
- Second sentence: Include 3 specific technical features
- Tone: Confident, clear, consumer-friendly
- Do NOT use superlatives (best, amazing, incredible)

Product details:
{product_description}

Write only the 2-sentence summary. No preamble."""

def run_prompt(prompt: str, label: str, n_runs: int = 5) -> list[str]:
    outputs = []
    print(f"\n{'='*60}")
    print(f"PROMPT TYPE: {label}")
    print(f"{'='*60}")
    for i in range(n_runs):
        response = client.chat.completions.create(
            model="gpt-6-luna",
            messages=[{"role": "user", "content": prompt}],
            temperature=0.9,
            max_tokens=200
        )
        text = response.choices[0].message.content.strip()
        outputs.append(text)
        print(f"\nRun {i+1}:\n{text}")
    return outputs

def measure_variability(outputs: list[str]) -> dict:
    lengths = [len(o.split()) for o in outputs]
    return {
        "min_words": min(lengths),
        "max_words": max(lengths),
        "avg_words": sum(lengths) / len(lengths),
        "range": max(lengths) - min(lengths)
    }

# Run both prompts
underspec_outputs = run_prompt(underspecified_prompt, "UNDERSPECIFIED", n_runs=5)
engineered_outputs = run_prompt(engineered_prompt, "ENGINEERED", n_runs=5)

# Report variability
print("\n\n" + "="*60)
print("VARIABILITY REPORT")
print("="*60)

uv = measure_variability(underspec_outputs)
ev = measure_variability(engineered_outputs)

print(f"\nUnderspecified Prompt:")
print(f"  Word count range: {uv['min_words']}–{uv['max_words']} words")
print(f"  Average: {uv['avg_words']:.1f} words")
print(f"  Variability (range): {uv['range']} words")

print(f"\nEngineered Prompt:")
print(f"  Word count range: {ev['min_words']}–{ev['max_words']} words")
print(f"  Average: {ev['avg_words']:.1f} words")
print(f"  Variability (range): {ev['range']} words")
