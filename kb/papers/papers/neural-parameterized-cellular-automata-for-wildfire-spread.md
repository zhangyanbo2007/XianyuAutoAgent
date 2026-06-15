---
title: "Neural-Parameterized Cellular Automata for Wildfire Spread"
authors: [Maksym Zhenirovskyy, Ion Matei, Rohit Vuppala, Takuya Kurihana, Hon Yung Wonga]
year: 2026
venue: "cs.CE, cs.LG, physics.comp-ph"
tags: []
arxiv_id: "2606.11676"
ingested: "2026-06-11"
---

# 🤖 Neural-Parameterized Cellular Automata for Wildfire Spread

- **Authors**: Maksym Zhenirovskyy, Ion Matei, Rohit Vuppala, Takuya Kurihana, Hon Yung Wonga
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.11676)
- **Category**: cs.CE, cs.LG, physics.comp-ph

## Abstract

Traditional wildfire models rely on rigid, low-dimensional parameters and static fuel maps, frequently underpredicting fire spread. To address this weakness, we introduce a hybrid deep-learning parameterized Probabilistic Cellular Automata (CA) framework implemented in JAX. Our approach employs a Multi-Scale Convolutional Neural Network to dynamically generate spatially varying parameters that govern fire-spread probability, wind alignment, and slope influence. This hybrid design captures complex, nonlinear environmental interactions while preserving the physical interpretability of the underlying three-state CA. The JAX implementation enables hardware acceleration and gradient-based parameter calibration. Evaluated on six large-scale wildfires in the western United States, the model maintains IoU > 0.6 over 72-hour forecast horizons after a 10-day data assimilation window during which the model is fitted incrementally to observed perimeters; the resulting forecast is a conditional projection of fire growth under the suppression regime already ncoded in those observations.

## Notes

<!-- Claude 在此添加中文解读 -->
