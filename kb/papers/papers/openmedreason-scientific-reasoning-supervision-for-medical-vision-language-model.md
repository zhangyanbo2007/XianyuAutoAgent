---
title: "OpenMedReason: Scientific Reasoning Supervision for Medical Vision-Language Models"
authors: [Negin Baghbanzadeh, Pritam Sarkar, Michael Colacci, Abeer Badawi, Adibvafa Fallahpour]
year: 2026
venue: "cs.CV, cs.AI, cs.CL"
tags: []
arxiv_id: "2606.12169"
ingested: "2026-06-11"
---

# 🤖 OpenMedReason: Scientific Reasoning Supervision for Medical Vision-Language Models

- **Authors**: Negin Baghbanzadeh, Pritam Sarkar, Michael Colacci, Abeer Badawi, Adibvafa Fallahpour
- **Date**: 2026-06-10
- **Source**: [arxiv](https://arxiv.org/abs/2606.12169)
- **Category**: cs.CV, cs.AI, cs.CL

## Abstract

High-stakes clinical use of large vision-language models (LVLMs) requires reasoning that is grounded in visual evidence and clinical knowledge, not just correct final answers. We introduce OpenMedReason, a large-scale, open multimodal medical reasoning corpus comprising approximately 450K image-question-answer instances whose reasoning traces are primarily derived from curated biomedical, human-authored scientific articles. OpenMedReason provides high-fidelity supervision beyond synthetic chains of thought, covering diverse medical domain vision modalities such as radiological scans, microscopic images, visible light photographs, charts, and others. We complement it with OpenMedReason-Bench, a held-out benchmark that allows fine-grained evaluation of LVLMs along three complementary axes of capability, including perception, medical knowledge, and rationale, enabling diagnostic evaluation beyond final-answer accuracy. OpenMedReason is a rich training resource that exhibits its effectiveness in both supervised fine-tuning (SFT) and reinforcement-based alignment. Training with OpenMedReason yields a 20% average improvement in VQA accuracy over the base model and achieves performance within 4.2% of the strongest comparable-scale medical LVLMs. Fine-grained performance analysis confirms that the gains are not concentrated in any single axis: OpenMedReason improves perception, medical knowledge, and rationale jointly, and its reasoning traces are preferred over those of the base model in 86.1% of pairwise comparisons. We release the code and dataset at huggingface.co/datasets/neginb/OpenMedReason.

## Notes

<!-- Claude 在此添加中文解读 -->
