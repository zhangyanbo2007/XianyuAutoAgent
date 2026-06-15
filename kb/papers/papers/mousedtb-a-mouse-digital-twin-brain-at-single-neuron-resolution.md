---
title: "MouseDTB: A Mouse Digital Twin Brain at Single-neuron Resolution"
authors: [Zhongyu Chen, Chong Li, Wenlian Lu, Xiangyang Xue, Jianfeng Feng]
year: 2025
venue: "Submitted to ICLR 2026"
tags: []
ingested: "2026-06-11"
---

# 🔬 MouseDTB: A Mouse Digital Twin Brain at Single-neuron Resolution

- **Authors**: Zhongyu Chen, Chong Li, Wenlian Lu, Xiangyang Xue, Jianfeng Feng
- **Date**: 2025-09-20
- **Source**: [openreview](https://openreview.net/forum?id=uajSG0jubM)
- **Category**: Submitted to ICLR 2026

## Abstract

Accurate whole-brain computational modeling grounded in single-neuron resolution connectivity is crucial for understanding how large-scale brain structures give rise to complex behaviors and cognition. Conventional mouse whole-brain models are typically constructed from coarse-grained regional or voxel-level connectivity, without considering single-neuron biological plausibility in the mouse brain connectome. In this study, we build a mouse digital twin brain (mouse DTB) at single-neuron resolution with large-scale spiking neural network, able to support complex behavioral tasks at whole-brain scale. We developed the mouse brain connectivity at single-neuron resolution through a data-driven pipeline that integrates high-resolution axonal projection data and spatial distributions of cells from the mouse brain cell atlas. The resulting neuronal connectivity is coupled with leaky integrate-and-fire (LIF) neurons and conductance-based synapses to form a large-scale spiking neural network of the mouse brain. The mouse DTB successfully reproduced blood-oxygen-level-dependent (BOLD) signals observed in both resting state and olfactory Go/No-Go discrimination task with high correlation, and exhibits correct behavioral responses aligned with perceptual odor inputs. This model leverages diffusion ensemble Kalman filtering (EnKF) and hierarchical Bayesian inference for parameter estimation. Our work provides a single-neuron resolution, whole-brain mouse DTB, offering a powerful tool for studying neural dynamics, behavior and cognition underlying mouse intelligence during complex tasks.

## Notes

<!-- Claude 在此添加中文解读 -->
