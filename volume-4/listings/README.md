# Volume IV — Code Listings

Every code example and prompt of 12 lines or more from *Applied AI Engineering, Volume
IV*, so you can copy it instead of typing it. Each file is named after the section it
comes from: `1.3-reliability.py` is from Section 1.3 of Chapter 1. Labs that have their
own folder in this volume are not repeated here; open the lab folder instead.

**Running a Python listing.** From the repository root, add the packages in its **Needs**
column. For example:

```bash
uv run python volume-4/listings/chapter-01/1.3-reliability.py
```

The **Runs** column says what else it needs:

- **on its own**: runs as it is.
- **after `x.py`**: builds on an earlier listing in the same chapter. Paste that listing
  above this one, or run them together in one file.
- **with the other files in `src/`**: one file of a small application; the chapter's lab
  shows how to run it.
- **sketch: see the text**: a fragment that shows one idea; the section explains what
  surrounds it.

Listings marked `OPENAI_API_KEY` call the OpenAI API and need a key in your environment.
Listings marked `CUDA GPU` need an NVIDIA graphics card.

## Chapter 1 — Production AI Architecture

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| 1.3 | [`1.3-reliability.py`](chapter-01/1.3-reliability.py) | 27 | — | on its own |
| 1.5 | [`1.5-observability.py`](chapter-01/1.5-observability.py) | 41 | — | on its own |

## Chapter 2 — AI System Design

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| 2.4 | [`2.4-interface-design.py`](chapter-02/2.4-interface-design.py) | 44 | `pydantic` | on its own |
| 2.6 | [`2.6-state-management.py`](chapter-02/2.6-state-management.py) | 53 | — | on its own |
| 2.9 | [`2.9-design-reviews.txt`](chapter-02/2.9-design-reviews.txt) | 14 | — | — |
| Lab | [`lab-system-design-document-for-an-ai.py`](chapter-02/lab-system-design-document-for-an-ai.py) | 74 | `fastapi`, `pydantic`, `python-multipart` | on its own |

## Chapter 3 — Enterprise Workflows

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| 3.3 | [`3.3-approval-workflows.py`](chapter-03/3.3-approval-workflows.py) | 60 | — | on its own |
| 3.4 | [`3.4-escalation-workflows.py`](chapter-03/3.4-escalation-workflows.py) | 59 | — | on its own |
| 3.5 | [`3.5-batch-processing.py`](chapter-03/3.5-batch-processing.py) | 33 | — | on its own |
| 3.6 | [`3.6-real-time-processing.py`](chapter-03/3.6-real-time-processing.py) | 20 | `openai` | on its own |
| 3.7 | [`3.7-workflow-state-management.py`](chapter-03/3.7-workflow-state-management.py) | 40 | `pydantic` | on its own |
| 3.9 | [`3.9-sla-management.py`](chapter-03/3.9-sla-management.py) | 30 | — | on its own |

## Chapter 4 — Automation

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| 4.3 | [`4.3-trigger-based-automation.py`](chapter-04/4.3-trigger-based-automation.py) | 56 | — | on its own |
| 4.4 | [`4.4-scheduled-automation.py`](chapter-04/4.4-scheduled-automation.py) | 47 | — | on its own |
| 4.5 | [`4.5-event-driven-automation.py`](chapter-04/4.5-event-driven-automation.py) | 33 | — | on its own |
| 4.6 | [`4.6-self-healing-systems.py`](chapter-04/4.6-self-healing-systems.py) | 52 | — | on its own |
| 4.7 | [`4.7-automation-testing.py`](chapter-04/4.7-automation-testing.py) | 76 | `pytest` | on its own |
| 4.8 | [`4.8-rollback-strategies.py`](chapter-04/4.8-rollback-strategies.py) | 38 | — | on its own |

## Chapter 5 — Model Deployment

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| 5.3 | [`5.3-the-production-dockerfile.Dockerfile`](chapter-05/5.3-the-production-dockerfile.Dockerfile) | 46 | — | — |
| 5.3 | [`5.3-dockerignore.txt`](chapter-05/5.3-dockerignore.txt) | 13 | — | — |
| 5.4 | [`5.4-kubernetes-for-ai.yaml`](chapter-05/5.4-kubernetes-for-ai.yaml) | 117 | — | — |
| 5.6 | [`5.6-api-gateway-patterns.py`](chapter-05/5.6-api-gateway-patterns.py) | 35 | `fastapi`, `pyjwt` | on its own |
| 5.9 | [`5.9-model-versioning.py`](chapter-05/5.9-model-versioning.py) | 39 | — | on its own |
| 5.10 | [`5.10-rollback-procedures.py`](chapter-05/5.10-rollback-procedures.py) | 56 | — | on its own |
| Lab | [`src/config.py`](chapter-05/src/config.py) | 24 | — | with the other files in `src/` |
| Lab | [`src/models.py`](chapter-05/src/models.py) | 23 | `pydantic` | with the other files in `src/` |
| Lab | [`src/main.py`](chapter-05/src/main.py) | 118 | `fastapi`, `openai` | with the other files in `src/` |
| Lab | [`lab-dockerfile.Dockerfile`](chapter-05/lab-dockerfile.Dockerfile) | 28 | — | — |
| Lab | [`lab-docker-compose-yml.yaml`](chapter-05/lab-docker-compose-yml.yaml) | 58 | — | — |
| Lab | [`scripts/smoke_test.sh`](chapter-05/scripts/smoke_test.sh) | 83 | — | — |
| Lab | [`lab-usage-instructions.sh`](chapter-05/lab-usage-instructions.sh) | 16 | — | — |

## Chapter 6 — Inference Optimization

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| 6.4 | [`6.4-quantization.py`](chapter-06/6.4-quantization.py) | 30 | `torch`, `transformers`, `accelerate`, `optimum`, `gptqmodel`, `CUDA GPU` | on its own |
| 6.10 | [`6.10-benchmarking-inference.py`](chapter-06/6.10-benchmarking-inference.py) | 98 | `numpy`, `openai`, `OPENAI_API_KEY` | on its own |

## Chapter 7 — Performance Engineering

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| 7.3 | [`7.3-profiling-ai-applications.py`](chapter-07/7.3-profiling-ai-applications.py) | 19 | — | on its own |
| 7.3 | [`7.3-profiling-ai-applications-2.py`](chapter-07/7.3-profiling-ai-applications-2.py) | 15 | `line_profiler` | on its own |
| 7.8 | [`7.8-async-processing.py`](chapter-07/7.8-async-processing.py) | 82 | `openai`, `OPENAI_API_KEY` | on its own |

## Chapter 8 — Caching Strategies

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| 8.4 | [`8.4-semantic-similarity-cache.py`](chapter-08/8.4-semantic-similarity-cache.py) | 86 | `numpy`, `openai`, `OPENAI_API_KEY` | on its own |
| 8.7 | [`8.7-cache-warming.py`](chapter-08/8.7-cache-warming.py) | 16 | — | on its own |
| Lab | [`lab-two-level-cache-system.py`](chapter-08/lab-two-level-cache-system.py) | 16 | — | after `8.4-semantic-similarity-cache.py` |

## Chapter 9 — Security

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| 9.3 | [`9.3-prompt-injection-direct.py`](chapter-09/9.3-prompt-injection-direct.py) | 22 | — | on its own |
| 9.8 | [`9.8-authentication-and-authorization.py`](chapter-09/9.8-authentication-and-authorization.py) | 57 | `fastapi`, `python-jose` | on its own |
| 9.9 | [`9.9-rate-limiting.py`](chapter-09/9.9-rate-limiting.py) | 41 | — | on its own |
| Lab | [`lab-create-the-ai-endpoint.py`](chapter-09/lab-create-the-ai-endpoint.py) | 33 | `fastapi`, `pydantic`, `security_middleware.py` | on its own |
| Lab | [`lab-run-attack-simulations.py`](chapter-09/lab-run-attack-simulations.py) | 15 | `httpx`, `security_middleware.py` | on its own |

## Chapter 10 — Privacy

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| 10.3 | [`10.3-pii-detection-and-redaction.py`](chapter-10/10.3-pii-detection-and-redaction.py) | 94 | `presidio_analyzer`, `presidio_anonymizer`, `spaCy model en_core_web_lg` | on its own |
| 10.5 | [`10.5-data-retention.py`](chapter-10/10.5-data-retention.py) | 13 | — | on its own |
| Lab | [`lab-pii-detection-and-redaction-pipeline.py`](chapter-10/lab-pii-detection-and-redaction-pipeline.py) | 19 | — | after `10.3-pii-detection-and-redaction.py` |

## Chapter 11 — Governance

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| 11.5 | [`11.5-usage-policies.txt`](chapter-11/11.5-usage-policies.txt) | 22 | — | — |

## Chapter 13 — Monitoring

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| 13.8 | [`13.8-log-analysis.json`](chapter-13/13.8-log-analysis.json) | 17 | — | — |

## Chapter 14 — Evaluation

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| 14.5 | [`14.5-llm-as-judge.txt`](chapter-14/14.5-llm-as-judge.txt) | 22 | — | — |
| Lab | [`llm_judge.py`](chapter-14/llm_judge.py) | 58 | `pydantic` | on its own |
| Lab | [`evaluation_runner.py`](chapter-14/evaluation_runner.py) | 162 | `tabulate`, `llm_judge.py` | on its own |

## Chapter 18 — Final Capstone Project: Enterprise AI Platform

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| 18.5 | [`18.5-volume-ii-integration-prompt.py`](chapter-18/18.5-volume-ii-integration-prompt.py) | 82 | — | on its own |
| 18.10 | [`nexoai_platform.py`](chapter-18/nexoai_platform.py) | 215 | — | on its own |
| 18.11 | [`18.11-series-completion.txt`](chapter-18/18.11-series-completion.txt) | 38 | — | — |
