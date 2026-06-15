---
title: "Goal-Autopilot: A Verifiable Anti-Fabrication Firewall for Unattended Long-Horizon Agents"
authors: [Youwang Deng]
year: 2026
venue: "cs.CL, cs.AI"
tags: []
arxiv_id: "2606.11688"
ingested: "2026-06-11"
---

# 🧠 Goal-Autopilot: A Verifiable Anti-Fabrication Firewall for Unattended Long-Horizon Agents

- **Authors**: Youwang Deng
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.11688)
- **Category**: cs.CL, cs.AI

## Abstract

Long-horizon LLM agents are not trusted to run unattended: with no human watching, they confidently report success they never verified. We treat honesty -- bounding what an agent may claim at termination -- as a first-class metric for unattended autonomy, distinct from capability. We present Autopilot, an execution model that makes silent fabricated success structurally impossible rather than merely rarer. Autopilot externalizes all working state into a durable, gated finite-state machine that a scheduler advances one stateless tick at a time; a hard floor forbids any terminal "done" claim whose falsifiable gate did not actually execute and pass. We prove a No-False-Success theorem -- under gate soundness, floor enforcement, and plan coverage, termination implies the goal holds -- whose only trust points are empirically measurable, and show the worst case degrades to an honest stall, never a fabricated success. Because each tick rehydrates only the state machine, per-step context cost is constant in the horizon. Across a 3,150-cell paired corpus (70 tasks $\times$ 3 systems $\times$ 3 models $\times$ 5 seeds, including 50 SWE-bench Lite tasks across 11 OSS repos), Autopilot fabricates on 0.95% of cells [95% CI 0.38--1.62] while Reflexion and StateFlow baselines fabricate on 8.10% [6.48--9.81] and 25.05% [22.48--27.62] respectively. The headline contrast lives in the hard regime: on SWE-bench Lite, the firewall reduces fabrication from 33.7% (StateFlow) to 0.67%, a paired difference of $-33.07$ pp [95% CI $-36.53, -29.73$]. The mechanism is the gate, not the model: all ten Autopilot fabrications come from the strongest model, while two weaker mid-tier models never fabricate across 700 paired cells. The firewall trades coverage for honesty by design -- an honest stall is recoverable; a confident wrong output shipped downstream is not.

## Notes

<!-- Claude 在此添加中文解读 -->
