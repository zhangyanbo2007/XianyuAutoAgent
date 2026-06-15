---
title: "DIRECT: When and Where Should You Allocate Test-Time Compute in Embodied Planners?"
authors: [Jadelynn Dao, Milan Ganai, Yasmina Abukhadra, Ajay Sridhar, Mozhgan Nasr Azadani]
year: 2026
venue: "cs.RO, cs.AI, cs.CV"
tags: []
arxiv_id: "2606.12402"
ingested: "2026-06-11"
---

# 🤖 DIRECT: When and Where Should You Allocate Test-Time Compute in Embodied Planners?

- **Authors**: Jadelynn Dao, Milan Ganai, Yasmina Abukhadra, Ajay Sridhar, Mozhgan Nasr Azadani
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.12402)
- **Category**: cs.RO, cs.AI, cs.CV

## Abstract

Vision-Language Models (VLMs) are increasingly deployed as high-level planners for embodied agents, with an emerging strategy of scaling test-time compute to improve capability. However, we observe that doing so increases latency, token usage, and FLOPs while yielding uneven, often diminishing gains in downstream success, limiting where embodied agents can be deployed. We argue that choosing when and where to spend test-time compute is central to bringing frontier performance to the real world. We introduce DIRECT, a routing framework that uses multimodal scene context to allocate compute per prompt, improving the success--cost Pareto frontier over fixed model selection. Across three dominant scaling axes, namely chain-of-thought depth, model size, and memory history, our experiments on VLABench and RoboMME show that test-time compute is not a uniform lever: different axes yield qualitatively distinct capability gains. We validate these insights on a physical Franka arm in a DROID setup spanning zero-shot manipulation and long-horizon chaining, where our router matches or exceeds a stronger model's success rate at up to 65% lower average latency. Ultimately, our results show that naively scaling test-time compute is wasteful, and that DIRECT can provide frontier-level embodied planning in robotic systems at a fraction of the cost. Project page can be found at jadee-dao.github.io/direct/.

## Notes

<!-- Claude 在此添加中文解读 -->
