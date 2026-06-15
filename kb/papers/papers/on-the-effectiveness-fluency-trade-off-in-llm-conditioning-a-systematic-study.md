---
title: "On The Effectiveness-Fluency Trade-Off In LLM Conditioning: A Systematic Study"
authors: [Iuri Macocco, Pau Rodríguez, Arno Blaas, Luca Zappella, Marco Baroni]
year: 2026
venue: "cs.CL"
tags: []
arxiv_id: "2606.12234"
ingested: "2026-06-11"
---

# 🤖 On The Effectiveness-Fluency Trade-Off In LLM Conditioning: A Systematic Study

- **Authors**: Iuri Macocco, Pau Rodríguez, Arno Blaas, Luca Zappella, Marco Baroni
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.12234)
- **Category**: cs.CL

## Abstract

Controlling the output of Large Language Models (LLMs) is a central challenge for their reliable deployment, yet a clear understanding of the involved trade-offs remains elusive. Current approaches to conditioning are often evaluated with a narrow focus on their effectiveness at injecting or removing a target concept, neglecting generation quality. We systematically investigate a range of conditioning methods in both injection and removal scenarios. We find that efficient steering methods frequently achieve conditioning at a steep cost to fluency. Furthermore, we identify a critical yet previously overlooked interaction with the training paradigm: activation steering methods are far less effective on instruction-tuned models than on their base counterparts. Simple prompting and full-fledged supervised fine-tuning, on the other hand, are viable options for concept injection, but are not as good at concept removal. Finally, cheaply computed textual metrics highly correlate to costly LLM-as-judge scores, and provide insights on the behavior of conditioning methods.

## Notes

<!-- Claude 在此添加中文解读 -->
