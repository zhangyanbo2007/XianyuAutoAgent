---
title: "AerialClaw: An Open-Source Framework for LLM-Driven Autonomous Aerial Agents"
authors: [Ke Li, Jianfei Yang, Luyao Zhang, Guo Yu, Chengwei Yan]
year: 2026
venue: "cs.RO, cs.CV"
tags: []
arxiv_id: "2606.12142"
ingested: "2026-06-11"
---

# 🧠 AerialClaw: An Open-Source Framework for LLM-Driven Autonomous Aerial Agents

- **Authors**: Ke Li, Jianfei Yang, Luyao Zhang, Guo Yu, Chengwei Yan
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.12142)
- **Category**: cs.RO, cs.CV

## Abstract

Unmanned aerial vehicles (UAVs) are increasingly used in inspection, search and rescue, environmental monitoring, and emergency response. However, most UAV applications still rely on pre-defined command sequences or task-specific pipelines, where developers manually connect perception, planning, flight control, simulation, logging, and safety modules. This limits the flexibility, reproducibility, and extensibility of autonomous aerial systems. This paper presents AerialClaw, an open-source software framework that enables UAVs to operate as decision-making aerial agents rather than merely command-following platforms. Given a natural-language mission, AerialClaw allows an LLM-based agent to understand the task, maintain context, invoke executable aerial skills, observe perception and runtime feedback, and iteratively update its decisions in a closed loop. The framework adopts a modular brain-skill-runtime architecture, combining hard skills for atomic UAV operations, Markdown-based soft skills for reusable task strategies, document-driven agent state and capability boundaries, memory-driven reflection, safety-oriented runtime validation, and platform-agnostic execution adapters. AerialClaw supports lightweight mock execution, PX4 SITL with Gazebo, and AirSim-based simulation, together with a web console, pluggable model backends, example missions, simulation assets, and staged deployment scripts. By combining standardized aerial skills, document-driven agent state, memory, and closed-loop LLM decision-making, AerialClaw provides a reproducible and extensible open-source framework for building UAV systems that can interpret missions, make decisions, execute skills, and adapt their behavior from feedback.

## Notes

<!-- Claude 在此添加中文解读 -->
