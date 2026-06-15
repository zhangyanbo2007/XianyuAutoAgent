---
title: "Dynamic Role-Graph Reinforcement Learning for Multi-Agent Collaborative Coding Systems"
authors: [Chen Qi]
year: 2025
venue: "Submitted to ICLR 2026"
tags: []
ingested: "2026-06-11"
---

# 🔬 Dynamic Role-Graph Reinforcement Learning for Multi-Agent Collaborative Coding Systems

- **Authors**: Chen Qi
- **Date**: 2025-09-20
- **Source**: [openreview](https://openreview.net/forum?id=95bwpkVPuR)
- **Category**: Submitted to ICLR 2026

## Abstract

We propose \textbf{Dynamic Role-Graph Reinforcement Learning (DRGRL)}, a novel framework for multi-agent collaborative coding systems that addresses the challenges of evolving team dynamics and role-based coordination. Traditional multi-agent reinforcement learning (MARL) approaches are often ineffective for static representations of agent interactions, which don't correlate to the fluid nature of real world software development teams. The proposed method combines dynamic graph neural networks (GNNs) with role-aware attention mechanisms to model time-varying collaboration patterns in which agents (i.e., developers, corresponding to nodes in a graph) are represented as nodes of a graph with an adaptively changing topology reflecting changing teams. A transformer-based gnn encoder uses the SK severing information across the graph, and a collaboration complexity divider estimates coordination complexity to serve as a decision-making leader. The framework uses a centralized critic with decentralized actors (CCDA) to encourage a maximized team level rewards (e.g., reduced merge conflicts or test coverage) and individual autonomy. Moreover, the system is interfaced with traditional development tools, such as version control systems, IDEs, and conflict resolvers to simplify the integration of learned policies into traditional workflows. The key novelty lies in the \textbf{role-graph duality}, where roles are both learned from data and emergent from graph dynamics, enabling hierarchical coordination strategies. For instance, high collaboration complexity could lead to the distribution of the mediator roles to stabilize such a system. Experiments on man-made and real-world coding data sets show that simulations using the proposed method show significant gains in the efficiency of teamwork and code-quality over baseline methods for MARL. The Framework's flexibility with Dynamic Teams and the general nature of the collaboration scenario, the Framework can be a potential conten

## Notes

<!-- Claude 在此添加中文解读 -->
