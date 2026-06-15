---
title: "Fourier Features Let Agents Learn High Precision Policies with Imitation Learning"
authors: [Balázs Gyenes, Emiliyan Gospodinov, Jan Frieling, Enrico Krohmer, Nicolas Schreiber]
year: 2026
venue: "cs.LG, cs.RO"
tags: []
arxiv_id: "2606.12334"
ingested: "2026-06-11"
---

# 🤖 Fourier Features Let Agents Learn High Precision Policies with Imitation Learning

- **Authors**: Balázs Gyenes, Emiliyan Gospodinov, Jan Frieling, Enrico Krohmer, Nicolas Schreiber
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.12334)
- **Category**: cs.LG, cs.RO

## Abstract

High-precision robotic manipulation requires fine-grained spatial reasoning that is often difficult to achieve with RGB-only policies due to depth ambiguity and perspective scale issues. Policies that leverage 3D information directly, such as those based on point clouds, offer a stronger geometric prior over purely image-based ones, yet their performance remains highly task-dependent. We hypothesize that this discrepancy may be due to the spectral bias of neural networks towards learning low frequency functions, which especially affects architectures conditioned on slow-moving Cartesian features. We thus propose to map point clouds from Cartesian space into high-dimensional Fourier space, effectively equipping the point cloud encoder with direct access to high-frequency features. We experimentally validate the use of Fourier features on challenging manipulation tasks from the RoboCasa and ManiSkill3 benchmarks and on a real robot setup. Despite their simplicity, we find that Fourier features provide significant benefits across diverse encoder architectures and benchmarks and are robust across hyperparameters. Our results indicate that Fourier features let policies leverage geometric details more effectively than Cartesian features, showing their potential as a general-purpose tool for point cloud-based imitation learning. We provide source code and videos on our project page: https://fourier-il.github.io/fourier-il

## Notes

<!-- Claude 在此添加中文解读 -->
