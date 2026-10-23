import sys
from pathlib import Path

# Find the volume's shared/ folder, which holds the recording client.
sys.path.insert(
    0,
    str(
        next(
            p / "shared"
            for p in Path(__file__).resolve().parents
            if (p / "shared" / "nexoma_labs").is_dir()
        )
    ),
)

import os

from jinja2 import BaseLoader, Environment
from nexoma_labs import OpenAI  # records and replays responses; see shared/

client = OpenAI(api_key=os.environ.get("OPENAI_API_KEY"))

# ============================================================
# PART 1: RISEN Framework Template
# ============================================================

RISEN_TEMPLATE = """ROLE:
{{ role }}

INSTRUCTIONS:
{{ instructions }}

STEPS:
{% for step in steps %}
{{ loop.index }}. {{ step }}
{% endfor %}

END GOAL:
{{ end_goal }}

NARROWING:
{% for constraint in constraints %}
- {{ constraint }}
{% endfor %}"""

# Template variables
risen_vars = {
    "role": "You are a senior technical writer specializing in developer documentation for REST APIs",
    "instructions": "Write the documentation for the authentication endpoint described below",
    "steps": [
        "Start with a one-sentence description of what the endpoint does",
        "Document all required and optional parameters with types and descriptions",
        "Show an example request using curl",
        "Show the success response structure",
        "List the common error codes and their meanings",
    ],
    "end_goal": "A complete, developer-friendly endpoint documentation section that a developer with no prior knowledge of this API can use to successfully authenticate",
    "constraints": [
        "Use Markdown formatting",
        "All code examples must be complete and runnable",
        "Parameter table must include: Name, Type, Required, Description",
        "Maximum length: 400 words",
    ],
}

# Endpoint data to document
endpoint_data = """
POST /api/v2/auth/token

Description: Exchange credentials for an access token

Required parameters:
- client_id (string): Your application's client identifier
- client_secret (string): Your application's secret key
- grant_type (string): Must be "client_credentials"

Optional parameters:
- scope (string): Space-separated list of requested permissions. Default: "read"
- expires_in (integer): Token TTL in seconds. Default: 3600. Max: 86400

Success response (200):
{
  "access_token": "eyJhbGc...",
  "token_type": "Bearer",
  "expires_in": 3600,
  "scope": "read"
}

Error codes: 400 (invalid request), 401 (invalid credentials), 429 (rate limit exceeded)
"""

env = Environment(loader=BaseLoader())
template = env.from_string(RISEN_TEMPLATE)
risen_prompt = template.render(**risen_vars)

print("RISEN-STRUCTURED PROMPT:")
print("=" * 60)
print(risen_prompt[:500] + "...")  # Print preview

# Run with endpoint data
full_user_message = risen_prompt + f"\n\nEndpoint to document:\n{endpoint_data}"

response = client.chat.completions.create(
    model="gpt-6-sol",
    reasoning_effort="none",
    messages=[{"role": "user", "content": full_user_message}],
    temperature=0.1,
    max_completion_tokens=600,
)

print("\nGENERATED DOCUMENTATION:")
print("=" * 60)
print(response.choices[0].message.content)

# ============================================================
# PART 2: JSON Prompt Store with Variable Substitution
# ============================================================

PROMPT_STORE = {
    "sentiment-classifier-v1.2": {
        "version": "1.2.0",
        "system": "You are a sentiment analysis specialist. Classify text sentiment with high precision. Return ONLY the label: POSITIVE, NEGATIVE, or NEUTRAL.",
        "user_template": 'Classify the sentiment of the following {{content_type}}:\n\n"{{content}}"\n\nSentiment:',
        "variables": {
            "content_type": {"type": "string", "default": "customer review"},
            "content": {"type": "string", "required": True},
        },
    }
}


def load_and_run_prompt(prompt_id: str, variables: dict) -> str:
    if prompt_id not in PROMPT_STORE:
        raise ValueError(f"Prompt '{prompt_id}' not found in store")

    prompt_def = PROMPT_STORE[prompt_id]

    # Fill defaults
    for var_name, var_spec in prompt_def["variables"].items():
        if var_name not in variables and "default" in var_spec:
            variables[var_name] = var_spec["default"]
        elif var_name not in variables and var_spec.get("required"):
            raise ValueError(f"Required variable '{var_name}' not provided")

    # Render template
    tmpl = env.from_string(prompt_def["user_template"])
    user_msg = tmpl.render(**variables)

    response = client.chat.completions.create(
        model="gpt-6-luna",
        reasoning_effort="none",
        messages=[
            {"role": "system", "content": prompt_def["system"]},
            {"role": "user", "content": user_msg},
        ],
        temperature=0,
        max_completion_tokens=20,
    )
    return response.choices[0].message.content.strip()


print("\n\nJSON PROMPT STORE TEST:")
print("=" * 60)

test_inputs = [
    {"content": "The service was excellent and exceeded all expectations!"},
    {"content": "Product arrived damaged. Completely unacceptable."},
    {"content": "Order was delivered on time. Nothing special.", "content_type": "order note"},
]

for inp in test_inputs:
    result = load_and_run_prompt("sentiment-classifier-v1.2", inp)
    print(f"Input: '{inp['content'][:50]}...' → {result}")
