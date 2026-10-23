# Volume II — Code Listings

Every code example and prompt of 12 lines or more from *Applied AI Engineering, Volume
II*, so you can copy it instead of typing it. Each file is named after the section it
comes from: `2.2-the-system-prompt.txt` is from Section 2.2 of Chapter 2. Labs that have
their own folder in this volume are not repeated here; open the lab folder instead.

**Running a Python listing.** From the repository root, add the packages in its **Needs**
column. For example:

```bash
uv run --with openai python volume-2/listings/chapter-09/9.3-json-mode-and-structured-output.py
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

## Chapter 2 — Prompt Anatomy: Dissecting Every Component

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| 2.2 | [`2.2-the-system-prompt.txt`](chapter-02/2.2-the-system-prompt.txt) | 17 | — | — |

## Chapter 4 — Context Design: What to Include and How to Position It

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| 4.4 | [`4.4-context-ordering-strategies.xml`](chapter-04/4.4-context-ordering-strategies.xml) | 20 | — | — |
| 4.5 | [`4.5-context-labeling-and-structure.xml`](chapter-04/4.5-context-labeling-and-structure.xml) | 13 | — | — |

## Chapter 5 — Role Prompting: Personas, Expert Roles, and Author Voice

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| 5.2 | [`5.2-types-of-role-prompts.txt`](chapter-05/5.2-types-of-role-prompts.txt) | 16 | — | — |
| 5.4 | [`5.4-author-voice-prompting.txt`](chapter-05/5.4-author-voice-prompting.txt) | 12 | — | — |

## Chapter 7 — Chain-of-Thought Prompting: Engineering Reasoning

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| 7.3 | [`7.3-zero-shot-chain-of-thought.txt`](chapter-07/7.3-zero-shot-chain-of-thought.txt) | 12 | — | — |
| 7.4 | [`7.4-few-shot-chain-of-thought.txt`](chapter-07/7.4-few-shot-chain-of-thought.txt) | 13 | — | — |

## Chapter 8 — Structured Prompting: Templates, Frameworks, and XML Architectures

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| 8.2 | [`8.2-the-risen-framework.txt`](chapter-08/8.2-the-risen-framework.txt) | 26 | — | — |
| 8.4 | [`8.4-xml-prompt-architecture.xml`](chapter-08/8.4-xml-prompt-architecture.xml) | 36 | — | — |
| 8.5 | [`8.5-json-prompt-structure.json`](chapter-08/8.5-json-prompt-structure.json) | 31 | — | — |
| 8.6 | [`8.6-prompt-templates-with-variable-slots.j2`](chapter-08/8.6-prompt-templates-with-variable-slots.j2) | 21 | — | — |

## Chapter 9 — Output Control: Format, Structure, and Length Engineering

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| 9.3 | [`9.3-json-mode-and-structured-output.py`](chapter-09/9.3-json-mode-and-structured-output.py) | 46 | `openai`, `OPENAI_API_KEY` | on its own |
| 9.7 | [`9.7-output-validation-pipeline.py`](chapter-09/9.7-output-validation-pipeline.py) | 26 | `pydantic` | on its own |

## Chapter 10 — Reasoning Strategies: Advanced Multi-Step Inference Techniques

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| 10.2 | [`10.2-least-to-most-prompting.txt`](chapter-10/10.2-least-to-most-prompting.txt) | 16 | — | — |
| 10.4 | [`10.4-tree-of-thoughts.py`](chapter-10/10.4-tree-of-thoughts.py) | 50 | `openai`, `OPENAI_API_KEY` | on its own |
| 10.5 | [`10.5-the-analogical-reasoning-prompt-pattern.txt`](chapter-10/10.5-the-analogical-reasoning-prompt-pattern.txt) | 12 | — | — |
| 10.5 | [`10.5-analogical-reasoning-example.txt`](chapter-10/10.5-analogical-reasoning-example.txt) | 16 | — | — |

## Chapter 11 — Prompt Evaluation: Measuring What Matters

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| 11.3 | [`11.3-reference-free-evaluation.py`](chapter-11/11.3-reference-free-evaluation.py) | 26 | `openai`, `OPENAI_API_KEY` | on its own |
| 11.5 | [`11.5-llm-as-judge.py`](chapter-11/11.5-llm-as-judge.py) | 38 | `openai`, `OPENAI_API_KEY` | on its own |
| 11.6 | [`11.6-g-eval.txt`](chapter-11/11.6-g-eval.txt) | 13 | — | — |

## Chapter 13 — Prompt Testing: Regression, Edge Cases, and A/B Testing

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| 13.4 | [`13.4-regression-testing.txt`](chapter-13/13.4-regression-testing.txt) | 18 | — | — |

## Chapter 14 — Prompt Debugging: Systematic Failure Diagnosis

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| 14.3 | [`14.3-contrastive-pair-design.py`](chapter-14/14.3-contrastive-pair-design.py) | 19 | — | on its own |
| 14.3 | [`14.3-contrastive-prompting-for-hallucination.py`](chapter-14/14.3-contrastive-prompting-for-hallucination.py) | 24 | — | on its own |
| 14.4 | [`14.4-prompt-logging-for-production-debugging.py`](chapter-14/14.4-prompt-logging-for-production-debugging.py) | 21 | — | on its own |

## Chapter 15 — Prompt Patterns: A Catalog of Proven Approaches

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| 15.3 | [`15.3-the-template-pattern.txt`](chapter-15/15.3-the-template-pattern.txt) | 20 | — | — |
| 15.4 | [`15.4-the-context-manager-pattern.txt`](chapter-15/15.4-the-context-manager-pattern.txt) | 16 | — | — |
| 15.4 | [`15.4-the-context-manager-pattern-2.txt`](chapter-15/15.4-the-context-manager-pattern-2.txt) | 19 | — | — |
| 15.5 | [`15.5-the-few-shot-selector-pattern.py`](chapter-15/15.5-the-few-shot-selector-pattern.py) | 13 | — | on its own |
| 15.6 | [`15.6-the-cognitive-verifier-pattern.txt`](chapter-15/15.6-the-cognitive-verifier-pattern.txt) | 15 | — | — |

## Chapter 17 — Reusable Prompt Frameworks

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| 17.5 | [`17.5-structure.txt`](chapter-17/17.5-structure.txt) | 12 | — | — |
| 17.5 | [`17.5-python-implementation.py`](chapter-17/17.5-python-implementation.py) | 90 | `jinja2` | on its own |
| 17.7 | [`17.7-the-pipeline-pattern.py`](chapter-17/17.7-the-pipeline-pattern.py) | 49 | — | after `17.5-python-implementation.py` |
| 17.8 | [`17.8-the-evaluation-pattern.py`](chapter-17/17.8-the-evaluation-pattern.py) | 67 | — | after `17.5-python-implementation.py` |
| 17.9 | [`17.9-building-a-framework-library.py`](chapter-17/17.9-building-a-framework-library.py) | 60 | — | on its own |

## Chapter 18 — Professional Prompt Libraries

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| 18.3 | [`18.3-cataloging-and-tagging-prompts.json`](chapter-18/18.3-cataloging-and-tagging-prompts.json) | 26 | — | — |
| 18.5 | [`18.5-testing-prompt-libraries.py`](chapter-18/18.5-testing-prompt-libraries.py) | 12 | — | on its own |
| 18.9 | [`18.9-prompt-library-apis.py`](chapter-18/18.9-prompt-library-apis.py) | 33 | — | on its own |

## Chapter 20 — Volume II Capstone Project: Prompt Engineering Workflow

| Section | File | Lines | Needs | Runs |
|:-------:|------|------:|-------|------|
| 20.5 | [`shopcore_support_pipeline.py`](chapter-20/shopcore_support_pipeline.py) | 203 | — | on its own |
| 20.6 | [`baseline_test.py`](chapter-20/baseline_test.py) | 112 | — | after `shopcore_support_pipeline.py` |
| 20.7 | [`ab_test.py`](chapter-20/ab_test.py) | 81 | — | after `shopcore_support_pipeline.py` |
