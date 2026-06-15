---
title: "WorldReasoner: Evaluating Whether Language Model Agents Forecast Events with Valid Reasoning"
authors: [Yizhou Chi, Eric Chamoun, Zifeng Ding, Andreas Vlachos]
year: 2026
venue: "cs.CL, cs.AI"
tags: []
arxiv_id: "2606.11816"
ingested: "2026-06-11"
---

# 🧠 WorldReasoner: Evaluating Whether Language Model Agents Forecast Events with Valid Reasoning

- **Authors**: Yizhou Chi, Eric Chamoun, Zifeng Ding, Andreas Vlachos
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.11816)
- **Category**: cs.CL, cs.AI

## Abstract

Forecasting real-world events requires language-model agents to reason under uncertainty from incomplete, time-bounded information. Yet evaluating whether agents genuinely forecast requires more than final-answer accuracy: a model may be correct by recalling memorized training facts, citing fabricated evidence, or producing an unsupported causal story. We present WorldReasoner, an evaluation framework for temporally valid event forecasting. Each task gives an agent a resolved forecasting question, a simulated forecast date, and access only to evidence available before that date; after resolution, the framework scores the submitted probability, cited evidence, and optional causal event graph. WorldReasoner reports three complementary axes: outcome quality against resolved answers, evidence quality over cited sources, and reasoning quality against post-resolution hindsight graphs. The benchmark is built by an agentic construction pipeline that generates forecasting questions, collects time-stamped evidence, and builds hindsight reference graphs at scale, yielding 345 resolved tasks derived from 14,141 articles with graphs covering 8,087 extracted events. Across six controlled agent settings, temporally valid retrieval is the strongest driver of outcome accuracy; causal graph construction improves key-event recovery; and correct graph-enabled forecasts are more strongly grounded in key events and relevant sources, yet agents still struggle to convert grounded evidence into calibrated probabilities.

## Notes

<!-- Claude 在此添加中文解读 -->
