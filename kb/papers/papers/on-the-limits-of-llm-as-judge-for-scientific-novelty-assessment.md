---
title: "On the Limits of LLM-as-Judge for Scientific Novelty Assessment"
authors: [Soumitra Sinhahajari, Navonil Majumder, Soujanya Poria]
year: 2026
venue: "cs.DL, cs.AI"
tags: []
arxiv_id: "2606.12071"
ingested: "2026-06-11"
---

# 🤖 On the Limits of LLM-as-Judge for Scientific Novelty Assessment

- **Authors**: Soumitra Sinhahajari, Navonil Majumder, Soujanya Poria
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.12071)
- **Category**: cs.DL, cs.AI

## Abstract

LLMs are increasingly used to generate and judge scientific ideas. This makes novelty evaluation a central problem. Full idea evaluation is difficult because it often requires judging a method, its feasibility, and its empirical promise. We therefore study a cleaner upstream object: the research question (RQ). RQ generation is a prerequisite for scientific ideation, and RQs can be compared against questions pursued in real papers. We introduce RQ-Bench, a benchmark built from recent arXiv papers. For each paper, we reconstruct author-anchored RQs from its cited background, gaps, and contributions. These RQs are not the only valid questions for the same background. They are author-anchored reference points for testing novelty judgments. We evaluate model-generated RQs with standalone LLM judging, comparative LLM judging, and human expert evaluation. LLM judges consistently rate model-generated RQs as highly novel, producing a novelty mirage; in comparative evaluations, this preference becomes even stronger. Domain experts, however, reach the opposite conclusion and prefer the author-anchored reference questions. We further find that many generated RQs are narrow or source-bound, a dimension that LLM judges often miss unless explicitly tested. Overall, the contradictory novelty evaluations between LLM judges and human experts raise a serious concern about the reliability of using LLMs to assess the scientific novelty of research questions.

## Notes

<!-- Claude 在此添加中文解读 -->
