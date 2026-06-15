---
title: "MedCTA: A Benchmark for Clinical Tool Agents"
authors: [Tajamul Ashraf, Hyewon Jeong, Fida Mohammad Thoker, Bernard Ghanem]
year: 2026
venue: "cs.CV, cs.AI, cs.CL"
tags: []
arxiv_id: "2606.11702"
ingested: "2026-06-11"
---

# 🧠 MedCTA: A Benchmark for Clinical Tool Agents

- **Authors**: Tajamul Ashraf, Hyewon Jeong, Fida Mohammad Thoker, Bernard Ghanem
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.11702)
- **Category**: cs.CV, cs.AI, cs.CL

## Abstract

To make clinically grounded decisions, medical AI agents are expected to go beyond simple recognition and be capable of tool retrieval, evidence acquisition, and integration. Existing benchmarks largely evaluate isolated perception or single-turn question answering, and therefore provide limited visibility into failures of planning, tool recruitment, and rollout reliability. We introduce MedCTA, a benchmark for evaluating medical tool agents on clinician-validated, step-implicit tasks grounded in realistic multimodal clinical inputs, including radiology images, pathology slides, and reports. MedCTA comprises 107 real-world clinical tasks with clinician-verified executable trajectories over 5 deployed tools, and supports process-aware evaluation of tool selection, argument validity, execution stability, trajectory fidelity, and outcome quality. We benchmark 18 open- and closed-source multimodal models and find that even frontier systems remain brittle in multi-step clinical tool use: autonomous rollouts are dominated by protocol failures, premature stopping, and incorrect tool recruitment, while gold-standard tool routing yields large but still incomplete gains. These results show that strong backbone perception does not translate into reliable agentic behavior in clinical settings. MedCTA provides a rigorous testbed for auditing, diagnosing, and advancing trustworthy medical AI agents. The dataset and evaluation suite are available at https://ivul-kaust.github.io/MedCTA/

## Notes

<!-- Claude 在此添加中文解读 -->
