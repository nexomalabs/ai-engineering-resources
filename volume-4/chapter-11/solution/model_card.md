---
model_name: "EnterpriseAssist-7B"
version: "2.1.0"
date: "2026-07-01"
organization: "Nexoma Labs LLC"
license: "Internal use only"
---

# Model Card: EnterpriseAssist-7B v2.1.0

## Model Details

- **Type:** Fine-tuned autoregressive language model (7B parameters)
- **Base model:** Mistral-7B-v0.3
- **Fine-tuning:** Supervised on internal IT support tickets (2022–2025)
- **Inference:** FP16, 4-bit GPTQ quantization available

## Intended Use

- **Primary:** IT help desk automation for employees
- **Secondary:** HR policy Q&A, IT troubleshooting

## Out of Scope

- Medical advice, legal counsel, financial guidance
- Any external-facing application

## Training Data

- Internal IT support tickets from 2022–2025, with names, email addresses and employee IDs removed before training

## Performance Metrics

| Benchmark                       | Score | Baseline       |
| ------------------------------- | ----- | -------------- |
| IT Ticket Resolution Rate       | 72%   | 58% (GPT-3.5)  |
| Hallucination Rate              | 3.1%  | 8.4% (GPT-3.5) |
| Response Relevance (human eval) | 4.2/5 | 3.8/5          |

## Evaluation

- Metrics measured on a held-out set of 2025 tickets not used in training
- Relevance rated by IT staff on a 1–5 scale

## Demographic Performance

| Language | Resolution Rate |
| -------- | --------------- |
| English  | 74%             |
| Spanish  | 68%             |
| French   | 61%             |

## Ethical Considerations

- Training data contains historical IT tickets; may reflect historical access patterns
- Not validated for users with disabilities (screen readers, voice input)

## Known Limitations

- Accuracy degrades on tickets older than the training cutoff (2025)
- Not suitable for security-sensitive requests (password resets, privileged access)
