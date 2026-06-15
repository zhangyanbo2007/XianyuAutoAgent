---
title: "The Impossibility of Eliciting Latent Knowledge"
authors: [Korbinian Friedl, Francis Rhys Ward, Paul Yushin Rapoport, Tom Everitt, Jonathan Richens]
year: 2026
venue: "cs.AI"
tags: []
arxiv_id: "2606.12268"
ingested: "2026-06-11"
---

# 🧠 The Impossibility of Eliciting Latent Knowledge

- **Authors**: Korbinian Friedl, Francis Rhys Ward, Paul Yushin Rapoport, Tom Everitt, Jonathan Richens
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.12268)
- **Category**: cs.AI

## Abstract

Advanced AI systems have extensive knowledge of their environments; in fact, their knowledge may (far) exceed that of their developers or users. Consequently, a desirable property for an AI system is that it is honest -- that it accurately reports its beliefs about the world. Designing an AI system to be honest may be difficult, especially if we want to ask it questions about latent variables in the environment -- variables which are hidden from the human interacting with it. This gives rise to the problem of eliciting latent knowledge (ELK): the problem of training an AI agent to honestly report its beliefs. In this paper, we make ELK formally precise using Causal Influence Diagrams (CIDs). CIDs can be used to describe the relationship between an agent's training environment and its subjective representation of the world. We use CIDs to formalise the distinction between observable and latent variables, to specify what exactly it means for an agent to be honest, and to formally define goal misgeneralisation. We show that, under certain circumstances, developers can incentivise an agent to honestly answer questions by providing correct feedback during training. However, a natural, but undesirable, way for an agent to generalise is to provide answers which humans would evaluate as true, rather than honest answers. We prove an impossibility theorem stating: There is no feedback-based training strategy that depends only on agent behaviour and with certainty produces an honest agent, even if feedback is perfect during training.

## Notes

<!-- Claude 在此添加中文解读 -->
