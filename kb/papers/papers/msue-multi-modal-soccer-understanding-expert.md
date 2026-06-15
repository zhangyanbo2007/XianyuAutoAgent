---
title: "MSUE: Multi-Modal Soccer Understanding Expert"
authors: [Litao Li, Yibo Yu, Yufeng Hu, Zhuo Yang, Jiali Wen]
year: 2026
venue: "cs.CV, cs.AI"
tags: []
arxiv_id: "2606.12106"
ingested: "2026-06-11"
---

# 🤖 MSUE: Multi-Modal Soccer Understanding Expert

- **Authors**: Litao Li, Yibo Yu, Yufeng Hu, Zhuo Yang, Jiali Wen
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.12106)
- **Category**: cs.CV, cs.AI

## Abstract

This paper presents our solution to the 2026 SoccerNet VQA Challenge. We first develop a cost-effective data synthesis pipeline driven by a Vision-Language Model (VLM), which systematically restructures raw domain data into diverse VQA samples, including concise answers and long-form responses. Second, we propose MSUE, a multi-expert question answering architecture that employs a Large Language Model (LLM) to dynamically dispatch questions to text, image, and video experts. These experts are instantiated as a strong text baseline Gemini3-Flash, a fine-tuned Qwen3-VL, and an external knowledge base, respectively, working collaboratively to enhance VQA performance. MSUE achieves an accuracy of \textbf{0.95} on the challenge benchmark, securing third place in the leaderboard.

## Notes

<!-- Claude 在此添加中文解读 -->
