---
title: "FingerTip 20K: A Benchmark for Proactive and Personalized Mobile LLM Agents"
authors: [Qinglong Yang, Haoming Li, Haotian Zhao, Xiaokai Yan, Jingtao Ding]
year: 2025
venue: "ICLR 2026 Poster"
tags: []
ingested: "2026-06-11"
---

# 🔬 FingerTip 20K: A Benchmark for Proactive and Personalized Mobile LLM Agents

- **Authors**: Qinglong Yang, Haoming Li, Haotian Zhao, Xiaokai Yan, Jingtao Ding
- **Date**: 2025-09-20
- **Source**: [openreview](https://openreview.net/forum?id=n3iFV0gLMc)
- **Category**: ICLR 2026 Poster

## Abstract

Mobile GUI agents are becoming critical tools to improve user experience on smart devices, with multimodal large language models (MLLMs) emerging as the dominant paradigms in this domain. Current agents, however, rely on explicit human instructions, overlooking the potential to leverage the contextual information (like location, time, user profile) and historical data for proactive task suggestions. Besides, previous works focus on optimizing the success rate during task execution, but pay less attention to the personalized execution trajectory, thereby neglecting potentially vast differences in user preferences. To address these challenges, we introduce the FingerTip 20K benchmark. We collected 20K unique human demonstrations of multi-step Android device interactions across a variety of everyday apps. These demonstrations are not isolated but are continuously acquired from the users' long-term usage in their real lives, and encompass essential user-related contextual information. The benchmark contains two new tracks: proactive task suggestions by analyzing environment observation and users' previous intents, and personalized task execution by catering to users' action preferences. Our experiments reveal that the tracks we propose pose significant challenges for leveraging user-related information in GUI tasks. We also performed a human study to show that there exists a huge gap between existing agents and humans. The model fine-tuned with the data we collected effectively utilized user information and achieved good results, highlighting the potential of our approach in building more user-oriented mobile LLM agents. Our code is open-source at \url{https://github.com/tsinghua-fib-lab/FingerTip-20K} for reproducibility.

## Notes

<!-- Claude 在此添加中文解读 -->
