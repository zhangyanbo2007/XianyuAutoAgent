---
title: "Learning Unions of Convex Sets via Invertible Latent Decomposition for Path Planning"
authors: [Taerim Yoon, Dongho Kang, Kisang Park, Junha Cha, Stelian Coros]
year: 2026
venue: "cs.RO"
tags: []
arxiv_id: "2606.12027"
ingested: "2026-06-11"
---

# 🧠 Learning Unions of Convex Sets via Invertible Latent Decomposition for Path Planning

- **Authors**: Taerim Yoon, Dongho Kang, Kisang Park, Junha Cha, Stelian Coros
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.12027)
- **Category**: cs.RO

## Abstract

Collision-free path planning in cluttered, real-world environments relies on a representation of the collision-free space, and existing representations broadly fall into two   categories. Explicit representations, such as unions of convex sets, can be plugged into optimization-based planners as hard collision-free constraints, but their parameters scale   poorly with configuration-space dimension. Implicit representations, by contrast, are flexible and scale well to complex geometries, yet typically lack such guarantees. We bridge this   gap with ILD (Invertible Latent Decomposition), a framework that jointly learns an invertible mapping and a union of explicit convex polytopes in the resulting latent space. Planning   is carried out over these latent convex sets, and the invertible mapping decodes the resulting paths back to the original configuration space while preserving feasibility with   respect to the refined explicit safe regions. We further propose Visibility-Guided Sampling (VGS) to keep the convex sets connected for path planning. Across 2D navigation, 6-DoF, and   14-DoF manipulation environments, ILD achieves broader coverage, better inter-set connectivity, and higher path-planning success rates than prior baselines, with zero observed false   positives after test-time refinement. On a 14-DoF bimanual manipulator, we further demonstrate real-time collision-free planning, with test-time refinement adapting to scene-geometry   changes during real-world deployment on a single 6-DoF arm.

## Notes

<!-- Claude 在此添加中文解读 -->
