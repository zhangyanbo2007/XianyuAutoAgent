---
title: "Exploration Structure in LLM Agents for Multi-File Change Localization"
authors: [Akeela Darryl Fattha, Kia Ying Chua, Lingxiao Jiang, Laura Wynter]
year: 2026
venue: "cs.SE, cs.AI"
tags: []
arxiv_id: "2606.11976"
ingested: "2026-06-11"
---

# 🧠 Exploration Structure in LLM Agents for Multi-File Change Localization

- **Authors**: Akeela Darryl Fattha, Kia Ying Chua, Lingxiao Jiang, Laura Wynter
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.11976)
- **Category**: cs.SE, cs.AI

## Abstract

Software engineering tools increasingly rely on LLM based agents to localize files to change to resolve a software issue. Most AI agents explore repositories linearly, that is, visiting one directory or file per step. We postulate that this is a structural mismatch for changes that span several subsystems. We compare linear sequential exploration against non-linear, domain-scoped parallel agentic exploration. Using SWE Bench Pro as initial benchmark, we focus on ansible as an exemplar. We construct an approach for persistent-session evaluation of GitHub issues anchored at a single base commit. We compare our non-linear domain-agent file traversal system against a base LLM without direct repository access, a single agent Recursive Language Model (RLM) baseline with a persistent Python REPL and an external CLI baseline using Codex 5.5 High. Domain scoped parallel agent spawning with a small Haiku-class model achieves the highest micro F1 among Haiku class models by a large margin. Domain-agents is the second highest behind only the much larger Codex 5.5 High on our own expanded benchmark including over more recent PRs from 2025 and 2026. On the original, curated, 2020 SWE-bench Pro benchmark, a larger Sonnet plain LLM baseline attains higher micro F1 by predicting few files, leading to higher precision, but at significantly lower all gold recall. We also present three additional findings. First, documentation evolution is a latent dependency unresolved by any approach. Second, naive file system access can degrade localization driven by test-file over prediction. Lastly, forced multi-agent consultation does not measurably help and raises token cost substantially.

## Notes

<!-- Claude 在此添加中文解读 -->
