---
title: "DrivingAgent: Design and Scheduling Agents for Autonomous Driving Systems"
authors: [Zhongyu Xia, Wenhao Chen, Yongtao Wang, Ming-Hsuan Yang]
year: 2026
venue: "cs.RO, cs.CV"
tags: []
arxiv_id: "2606.12236"
ingested: "2026-06-11"
---

# 🧠 DrivingAgent: Design and Scheduling Agents for Autonomous Driving Systems

- **Authors**: Zhongyu Xia, Wenhao Chen, Yongtao Wang, Ming-Hsuan Yang
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.12236)
- **Category**: cs.RO, cs.CV

## Abstract

Many autonomous driving systems are increasingly incorporating foundation models to improve generalization and handle long-tail scenarios. However, this trend introduces two key challenges: (i) the manual and labor-intensive process of designing and integrating new models, and (ii) the lack of intelligent, dynamic scheduling mechanisms to meet strict real-time constraints. While Large Language Model (LLM)-based agents offer a promising avenue for automation, existing frameworks are ill-suited for autonomous driving. Specifically, they fail to distinguish between the fundamentally different requirements of system design and real-time scheduling, treat modules as opaque black boxes, and are not designed for continuous operation. To address these limitations, we propose DrivingAgent, a novel agent framework tailored to the dual challenges of autonomous driving system design and scheduling. In the design phase, DrivingAgent automates module development by interpreting system architecture, generating code, and validating modules via super-network training. In the scheduling phase, it employs a lightweight LLM trained with reinforcement learning to dynamically orchestrate system modules in real time, supported by a structured memory that integrates long-term storage with timestamped short-term context. Experimental results demonstrate that DrivingAgent achieves a superior speed--accuracy trade-off on both the nuScenes and Bench2Drive benchmarks.

## Notes

<!-- Claude 在此添加中文解读 -->
