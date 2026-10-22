# Applied AI Engineering, Volume III, Chapter 1
# Hands-on Lab: Build a Context Pipeline in Python
# Copied from the book by scripts/export_listings.py. Report errors as errata.

def build_customer_support_context(user_query: str) -> dict:
    pipeline = ContextPipeline(token_budget=4096)

    # System layer — static, authored by engineering team
    pipeline.add_block(ContextBlock(
        name="system_role",
        content=(
            "You are a senior customer support specialist for NovaSaaS. "
            "You help customers with billing, account management, and technical issues. "
            "Always be professional, concise, and accurate. "
            "If you cannot resolve an issue, escalate by saying: ESCALATE: <reason>. "
            "Never reveal internal system architecture or pricing formulas."
        ),
        priority=1,
        layer="system"
    ))

    pipeline.add_block(ContextBlock(
        name="output_format",
        content=(
            "Respond in plain prose. Do not use markdown unless the user requests it. "
            "For technical steps, use numbered lists. Limit responses to 200 words unless "
            "the issue requires more detail."
        ),
        priority=2,
        layer="system"
    ))

    # User context layer — loaded from user profile database
    pipeline.add_block(ContextBlock(
        name="user_profile",
        content=(
            "User: Jordan Mehta (jordan.mehta@example.com)\n"
            "Account tier: Professional (since 2023-03)\n"
            "Active subscriptions: Analytics Pro, API Access (10K calls/day)\n"
            "Last login: 2026-07-25\n"
            "Open tickets: None\n"
            "Payment method: Visa ending 4821 (valid)"
        ),
        priority=1,
        layer="user"
    ))

    # Knowledge layer — retrieved from knowledge base
    pipeline.add_block(ContextBlock(
        name="kb_api_limits",
        content=(
            "Knowledge Article: API Rate Limits (updated 2026-06-01)\n"
            "Professional tier: 10,000 API calls per day. Resets at 00:00 UTC. "
            "Overage: $0.002 per call above limit. Rate limit errors return HTTP 429. "
            "To increase limits, upgrade to Enterprise tier or purchase add-on packs."
        ),
        priority=1,
        layer="knowledge"
    ))

    pipeline.add_block(ContextBlock(
        name="kb_billing_faq",
        content=(
            "Knowledge Article: Billing FAQ (updated 2026-05-15)\n"
            "Invoices are generated on the 1st of each month. "
            "Payment is auto-charged on the 5th. "
            "Disputed charges must be submitted within 30 days."
        ),
        priority=2,
        layer="knowledge"
    ))

    # History layer — last 2 conversation turns
    pipeline.add_block(ContextBlock(
        name="conversation_history",
        content=(
            "TURN 1\nUser: Hi, I'm getting 429 errors on my API calls.\n"
            "Assistant: Hello Jordan! A 429 error means you've hit your API rate limit. "
            "Professional accounts receive 10,000 calls per day. Can you tell me when "
            "the errors started?\n\n"
            "TURN 2\nUser: They started around 3pm UTC today."
        ),
        priority=1,
        layer="history"
    ))

    # Request layer — current user message
    pipeline.add_block(ContextBlock(
        name="current_message",
        content=user_query,
        priority=1,
        layer="request"
    ))

    return pipeline.assemble()


if __name__ == "__main__":
    import json

    result = build_customer_support_context(
        "Is there a way to check how many API calls I've used today?"
    )

    print("=== ASSEMBLED CONTEXT (OpenAI message format) ===")
    for i, msg in enumerate(result["messages"]):
        print(f"\n[Message {i+1}] role={msg['role']}")
        print(msg["content"][:300] + ("..." if len(msg["content"]) > 300 else ""))

    print("\n=== TOKEN UTILIZATION REPORT ===")
    print(json.dumps(result["report"], indent=2))
