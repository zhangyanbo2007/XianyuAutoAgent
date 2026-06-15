---
title: "Riemannian Geometry: Speech Detection from MEG Brain Signals Towards Non-Invasive BCI"
authors: [Aryan Mangla, Priyanshu Vij]
year: 2025
venue: "ICLR 2026 Conference Withdrawn Submission"
tags: []
ingested: "2026-06-11"
---

# 🔬 Riemannian Geometry: Speech Detection from MEG Brain Signals Towards Non-Invasive BCI

- **Authors**: Aryan Mangla, Priyanshu Vij
- **Date**: 2025-09-20
- **Source**: [openreview](https://openreview.net/forum?id=bkhsrCOZTu)
- **Category**: ICLR 2026 Conference Withdrawn Submission

## Abstract

Non-invasive brain--computer interfaces (BCIs) need fast, reliable speech vs.\ non-speech detection from neural time series. We propose a hybrid MEG decoder that fuses a compact temporal CNN with a geometry-aware covariance branch operating on symmetric positive-definite (SPD) sensor--sensor matrices. The CNN is stabilized by three pragmatic choices: a temporal-lobe sensor subset (auditory cortex) to improve signal-to-noise and efficiency, silence-aware sampling to mitigate class imbalance, and smoothed BCE with positive-class weighting for calibrated decisions. In parallel, each $1$-s window yields a shrinkage covariance projected to a Riemannian tangent space and classified by a linear model; we late-fuse CNN and covariance probabilities and select the operating threshold to maximize $F_1$-macro. This design is motivated by (i) the neurobiology of speech processing in superior temporal gyrus (onset/sustained responses; envelope entrainment in delta--theta bands) and (ii) extensive evidence that Riemannian treatment of SPD covariances improves neural decoding robustness and transfer. On a large within-subject MEG corpus (250~Hz; $\sim$1~s windows), the baseline scores 0.4985 $F_1$-macro; our CNN (+3 stabilizers) reaches 0.88773; the full hybrid attains 0.91023, adding accuracy with negligible training cost and low-latency inference. These results align with MEG's strengths for millisecond-scale cognitive dynamics and with best practices in representation learning targeted by ICLR.

## Notes

<!-- Claude 在此添加中文解读 -->
