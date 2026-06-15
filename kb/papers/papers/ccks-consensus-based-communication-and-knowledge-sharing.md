---
title: "CCKS: Consensus-based Communication and Knowledge Sharing"
authors: [Jinyuan Zu, Xiaowei Lv, Yongcai Wang, Deying Li, Yunjun Han]
year: 2026
venue: "cs.MA, cs.AI, cs.LG"
tags: []
arxiv_id: "2606.12281"
ingested: "2026-06-11"
---

# 🧠 CCKS: Consensus-based Communication and Knowledge Sharing

- **Authors**: Jinyuan Zu, Xiaowei Lv, Yongcai Wang, Deying Li, Yunjun Han
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.12281)
- **Category**: cs.MA, cs.AI, cs.LG

## Abstract

In Decentralized Training and Decentralized Execution (DTDE) for cooperative Multi-Agent Reinforcement Learning (MARL), action-advising-based knowledge sharing promotes interpretable and scalable cooperation among agents. However, current action advising approaches often adhere too much to the teacher's guidance without evaluating teacher-student compatibility, which causes excessive advising, suboptimal stability, and degraded performance. To overcome these challenges, this paper presents a Consensus-based Communication and Knowledge Sharing (CCKS) framework, which allows agents to adopt recommendations based on consensus-derived constraints and to follow the teacher's instructions more smartly. This mechanism enables agents to balance exploration and learning from experienced teachers, improving overall performance. The key is the consensus model construction, for which we propose to employ contrastive learning to construct consensus models based on local observations in the agents' training phase. In action selection, agents score and choose actions based on consensus and shared knowledge. Designed as a plug-and-play solution, CCKS integrates seamlessly with existing DTDE algorithms. Experiments conducted in the Google Research Football environment and the complex StarCraft II Multi-Agent Challenge demonstrate that the integration with CCKS significantly improves cooperation efficiency, learning speed, and overall performance compared with current DTDE baselines. The code is available at https://github.com/yuanxpy/CCKS.

## Notes

<!-- Claude 在此添加中文解读 -->
