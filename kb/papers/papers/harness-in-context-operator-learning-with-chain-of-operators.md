---
title: "Harness In-Context Operator Learning with Chain of Operators"
authors: [Minghui Yang, Ling Guo, Liu Yang]
year: 2026
venue: "cs.LG, cs.AI"
tags: []
arxiv_id: "2606.12318"
ingested: "2026-06-11"
---

# 🤖 Harness In-Context Operator Learning with Chain of Operators

- **Authors**: Minghui Yang, Ling Guo, Liu Yang
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.12318)
- **Category**: cs.LG, cs.AI

## Abstract

Neural operators approximate mappings between function spaces, but often generalize poorly to other operators and usually require fine-tuning or retraining. In-Context Operator Networks (ICON) addresses this issue by prompting the model with numerical context so that the model learns specific operators from prompts and adapt to different operators without fine-tuning. However, ICON may still fail to generalize to out-of-distribution (OOD) operator tasks. Inpired by the success of harness engineering of Large Language models (LLMs), we introduce Chain of Operators (CHOP), a framework that harness a frozen ICON to OOD operator tasks without updating its parameters. Specifically, CHOP constructs a chain of operators consisting of explicit elementary transformations and the frozen ICON. Experiments on a scalar conservation law and a mean-field control problem show that CHOP reduces relative inference error over direct ICON evaluation, while each operator in the chain remains interpretable and in closed form. A chain constructed on one PDE family further generalizes to a different family, indicating shared mechanisms across harness systems.

## Notes

<!-- Claude 在此添加中文解读 -->
