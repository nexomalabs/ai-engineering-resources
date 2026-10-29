---
system_name: "EnterpriseAssist Help Desk"
version: "1.0.0"
date: "2026-07-01"
organization: "Quillmark Software"
---

# System Card: EnterpriseAssist Help Desk v1.0.0

This is a reference example for a hypothetical system. Every figure in it is illustrative.

## System Overview

- **Purpose:** Answers employees' IT and HR policy questions, and drafts help desk tickets
- **Model:** EnterpriseAssist-7B v2.1.0 (see `model_card.md`)
- **Tools and data:** Read-only access to the IT knowledge base and the ticketing system
- **Users:** Employees, signed in through single sign-on; no external users

## Safety Evaluations

- Red-team exercise before launch: prompt injection, data extraction and policy evasion
- Findings: two injection paths through pasted ticket text, both closed by input filtering
- Residual risk: confident but wrong answers about rarely used systems

## Safeguards

- Input filter for injection patterns, and an output filter for credentials and personal data
- Rate limit of 30 requests per user per minute
- Password resets and privileged-access requests are refused and routed to a person

## Usage Policy

- Permitted: IT troubleshooting, HR policy questions, drafting tickets
- Prohibited: security-sensitive requests, processing data the user is not authorized to see
- Enforcement: violations are logged and reviewed; repeated violations suspend access

## Monitoring

- Tracked weekly: resolution rate, escalation rate, user ratings and filter triggers
- A quality review samples 50 conversations a week

## Known Limitations

- Answers degrade for systems introduced after the model's training cutoff
- Resolution rate is lower in French and Spanish than in English (see the model card)

## Escalation

- A harmful or incorrect answer reported by a user reaches the on-call AI engineer within one business hour
- A safety-filter spike of more than ten triggers in an hour pages the on-call engineer
- Incidents are reviewed by the AI governance lead within five business days
