---
title: "ObjexMT: Objective Extraction and Metacognitive Calibration for LLM-as-a-Judge under Multi-Turn Jailbreaks"
authors: [Hyunjun Kim, Junwoo Ha, Haon Park, Sangyoon Yu]
year: 2025
venue: "Submitted to ICLR 2026"
tags: []
ingested: "2026-06-11"
---

# 🔬 ObjexMT: Objective Extraction and Metacognitive Calibration for LLM-as-a-Judge under Multi-Turn Jailbreaks

- **Authors**: Hyunjun Kim, Junwoo Ha, Haon Park, Sangyoon Yu
- **Date**: 2025-09-20
- **Source**: [openreview](https://openreview.net/forum?id=pKKtSi88fH)
- **Category**: Submitted to ICLR 2026

## Abstract

LLM-as-a-Judge (LLMaaJ) now underpins scalable evaluation, yet we lack a decisive test of a judge's qualification: can it recover a conversation's latent objective and know when that inference is trustworthy? LLMs degrade under irrelevant or long context; multi-turn jailbreaks further hide goals across turns. We introduce **ObjexMT**, a benchmark for objective extraction and metacognition. Given a multi-turn transcript, a model must return a one-sentence base objective and a self-reported confidence. Accuracy is computed via LLM-judge semantic similarity to gold objectives, converted to binary correctness by a single human-aligned threshold calibrated once on **N=300** items ($\tau^\star = 0.66$; $F_1@\tau^\star = 0.891$). Metacognition is evaluated with ECE, Brier, *Wrong@High-Confidence* (0.80/0.90/0.95), and risk--coverage. Across six models (`gpt-4.1`, `claude-sonnet-4`, `Qwen3-235B-A22B-FP8`, `kimi-k2`, `deepseek-v3.1`, `gemini-2.5-flash`) on *SafeMTData_Attack600*, *SafeMTData_1K*, and *MHJ*, `kimi-k2` attains the highest objective-extraction accuracy (**0.612**; 95% CI [0.594, 0.630]), with `claude-sonnet-4` (**0.603**) and `deepseek-v3.1` (**0.599**) not statistically distinguishable from it by paired tests. `claude-sonnet-4` yields the best selective risk and calibration (AURC **0.242**; ECE **0.206**; Brier **0.254**). 
**Striking dataset heterogeneity (16--82% accuracy variance) reveals that automated obfuscation poses fundamental challenges beyond model choice.**
Despite improvements, high-confidence errors remain: Wrong@0.90 ranges from **14.9%** (`claude-sonnet-4`) to **47.7%** (`Qwen3-235B-A22B-FP8`). ObjexMT thus supplies an actionable test for LLM judges: when objectives are not explicit, judges often misinfer them; we recommend exposing objectives when feasible and gating decisions by confidence otherwise. **All experimental data are provided in the Supplementary Material and at [https://anonymous.4open.science/r/ObjexMT_dataset_Anonymous_ICLR-F658

## Notes

<!-- Claude 在此添加中文解读 -->
