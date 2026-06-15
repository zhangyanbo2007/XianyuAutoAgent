---
title: "Grammar-Constrained Decoding Can Jailbreak LLMs into Generating Malicious Code"
authors: [Yitong Zhang, Shiteng Lu, Jia Li]
year: 2026
venue: "cs.CR, cs.AI, cs.CL"
tags: []
arxiv_id: "2606.11817"
ingested: "2026-06-11"
---

# 🤖 Grammar-Constrained Decoding Can Jailbreak LLMs into Generating Malicious Code

- **Authors**: Yitong Zhang, Shiteng Lu, Jia Li
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.11817)
- **Category**: cs.CR, cs.AI, cs.CL

## Abstract

Large Language Models (LLMs) are increasingly used for code generation, raising concerns that they may be misused to produce malicious code. Meanwhile, Grammar-Constrained Decoding (GCD) has been widely adopted to improve the reliability of LLM-generated code by enforcing syntactic validity. In this paper, we reveal a counterintuitive risk: this reliability-oriented technique can itself become an attack surface. We uncover a new jailbreak attack, termed CodeSpear, that exploits GCD to induce LLMs into generating malicious code. Our experiments show that simply applying a benign code grammar constraint can effectively jailbreak LLMs.   To address this vulnerability, we propose CodeShield, a safety alignment approach that robustly preserves safe behavior even under attacker-controlled grammar constraints. CodeShield aligns the model in the code modality by teaching it to generate honeypot code under GCD. Such code is semantically harmless, so it does not implement the malicious request, and structurally diverse, so it is difficult to suppress through grammar tightening. At the same time, CodeShield still preserves natural-language refusals when natural language is available. Experiments on 10 popular LLMs across 4 benchmarks show that CodeSpear outperforms representative jailbreak baselines and increases the attack success rate by more than 30 percentage points on average. CodeShield also restores safety under CodeSpear while preserving benign utility. Our findings reveal a fundamental risk of GCD and call for greater attention to its potential security implications.

## Notes

<!-- Claude 在此添加中文解读 -->
