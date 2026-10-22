# cost_tracker.py
from __future__ import annotations

import random
from dataclasses import dataclass, field


@dataclass
class ModelPricing:
    model_id: str
    input_price_per_million: float  # USD per 1M input tokens
    output_price_per_million: float  # USD per 1M output tokens

    def cost(self, tokens_in: int, tokens_out: int) -> float:
        return (
            tokens_in * self.input_price_per_million / 1_000_000
            + tokens_out * self.output_price_per_million / 1_000_000
        )


# Published list prices in USD per million tokens, standard tier, from the
# providers' pricing pages in October 2026 (Gemini at its rate from January
# 2027). Prices change often: check each provider's pricing page before using
# these figures.
PRICING = {
    "gpt-6.1-sol": ModelPricing("gpt-6.1-sol", 2.00, 10.00),
    "gpt-6-luna": ModelPricing("gpt-6-luna", 0.10, 0.50),
    "claude-sonnet-5-5": ModelPricing("claude-sonnet-5-5", 2.00, 10.00),
    "claude-haiku-5-5": ModelPricing("claude-haiku-5-5", 0.10, 0.50),
    "gemini-3.8-flash": ModelPricing("gemini-3.8-flash", 1.50, 7.50),
}


@dataclass
class RequestRecord:
    request_id: str
    model_id: str
    tokens_in: int
    tokens_out: int
    feature: str
    user_id: str
    cached: bool = False
    cost_usd: float = field(init=False)

    def __post_init__(self):
        # TODO 1: A request served from cache makes no model call: its cost is 0.0.
        pricing = PRICING.get(self.model_id, PRICING["gpt-6.1-sol"])
        self.cost_usd = pricing.cost(self.tokens_in, self.tokens_out)


def generate_sample_requests(n: int = 1000) -> list[RequestRecord]:
    """Generate realistic sample request data."""
    features = ["customer_support", "document_summary", "code_review", "email_draft", "faq_lookup"]
    feature_weights = [0.40, 0.20, 0.15, 0.15, 0.10]
    models = ["gpt-6.1-sol", "gpt-6.1-sol", "gpt-6.1-sol", "gpt-6-luna"]  # 75% Sol, 25% Luna

    records = []
    for i in range(n):
        feature = random.choices(features, weights=feature_weights)[0]
        model = random.choice(models)

        # Token distributions vary by feature
        if feature == "document_summary":
            tokens_in = random.randint(800, 3000)
            tokens_out = random.randint(150, 500)
        elif feature == "code_review":
            tokens_in = random.randint(400, 1500)
            tokens_out = random.randint(200, 800)
        elif feature == "faq_lookup":
            tokens_in = random.randint(100, 300)
            tokens_out = random.randint(50, 200)
        else:
            tokens_in = random.randint(200, 800)
            tokens_out = random.randint(100, 400)

        records.append(
            RequestRecord(
                request_id=f"req_{i:05d}",
                model_id=model,
                tokens_in=tokens_in,
                tokens_out=tokens_out,
                feature=feature,
                user_id=f"user_{random.randint(1, 200):04d}",
            )
        )
    return records
