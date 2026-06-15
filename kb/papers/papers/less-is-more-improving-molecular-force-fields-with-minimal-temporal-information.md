---
title: "Less is More: Improving Molecular Force Fields with Minimal Temporal Information"
authors: [Ali Mollahosseini, Mohammed Haroon Dupty, Wee Sun Lee]
year: 2025
venue: "Submitted to ICLR 2026"
tags: []
ingested: "2026-06-11"
---

# 🔬 Less is More: Improving Molecular Force Fields with Minimal Temporal Information

- **Authors**: Ali Mollahosseini, Mohammed Haroon Dupty, Wee Sun Lee
- **Date**: 2025-09-20
- **Source**: [openreview](https://openreview.net/forum?id=fjH9raahDC)
- **Category**: Submitted to ICLR 2026

## Abstract

Accurate prediction of energy and forces for 3D molecular systems is one of fundamental challenges at the core of AI for Science applications. Many powerful and data-efficient neural networks predict molecular energies and forces from single atomic configurations. However, one crucial aspect of the data generation process is rarely considered while learning these models i.e. Molecular Dynamics (MD) simulation.
Molecular Dynamics (MD) simulations generate time-ordered trajectories of atomic
positions that fluctuate in energy and explore regions of the potential energy surface
(e.g., under standard NVE/NVT ensembles), rather than being constructed to steadily lower
the potential energy toward a minimum as in geometry relaxations.
This work explores a novel way to leverage molecular dynamics (MD) data, when available, to improve the performance of such predictors. We introduce a novel training strategy called FRAMES, that use an auxiliary loss function for exploiting the temporal relationships within MD trajectories. 
Counter-intuitively, on two atomistic benchmarks and a synthetic system we
observe that minimal temporal information, captured by pairs of just two consecutive
frames, is often sufficient to obtain the best performance, while adding longer
trajectory sequences can introduce redundancy and degrade performance.
On the widely used MD17 and ISO17 benchmarks, FRAMES significantly outperforms its Equiformer baseline, achieving highly competitive results in both energy and force accuracy. Our work not only presents a novel training strategy which improves the accuracy of the model, but also provides evidence that for distilling physical priors of atomic systems, more temporal data is not always better.

## Notes

<!-- Claude 在此添加中文解读 -->
