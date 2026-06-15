---
title: "Data Passports: Confidentially Provable Provenance for Onboarding Verifiable ML"
authors: [Ali Shahin Shamsabadi, Yuxin Myles Liu, Olive Franzese, Gefei Tan, Hamed Haddadi]
year: 2025
venue: "Submitted to ICLR 2026"
tags: []
ingested: "2026-06-11"
---

# 🔬 Data Passports: Confidentially Provable Provenance for Onboarding Verifiable ML

- **Authors**: Ali Shahin Shamsabadi, Yuxin Myles Liu, Olive Franzese, Gefei Tan, Hamed Haddadi
- **Date**: 2025-09-20
- **Source**: [openreview](https://openreview.net/forum?id=CrGxvyppMS)
- **Category**: Submitted to ICLR 2026

## Abstract

Recent advances in ML have leveraged Zero Knowledge Proof protocols to enable institutions to cryptographically commit to a dataset and subsequently prove, to external auditors, the integrity of training and the trustworthiness of the resulting model on the committed data, all while protecting model confidentiality. Such approaches guarantee that the training algorithm which produced a model was computed correctly, but remain vulnerable to pre-commitment data tampering. This is because even if the training algorithm is executed faithfully, an institution can bypass the audit by manipulating the training data. Likewise, data generators may degrade a model’s utility via data poisoning. 

To address this, we introduce tamper-proof Data Passports that bind data to verifiable and confidential proofs of authenticity. We leverage Trusted Execution Environments to issue a certificate of authenticity or ‘passport’ for each data point produced by a generating process. The generating process passes the data and passport to the institution. Then, the institution uses a zero-knowledge proof to verify the validity of the passports to an auditor, as an onboarding step for downstream proofs of training integrity and model trustworthiness. This unlocks cryptographic verification of data provenance throughout the ML pipeline. 

Our experiments demonstrate that we can create tamper-proof passports for images taken by users on their smartphones with a very negligible overhead. Agnostic to data size, a passport can be created at capture time in only 230 ms and consumes just 4.8 KB; thus, it has minimal impact on compute, storage and network usage.

## Notes

<!-- Claude 在此添加中文解读 -->
