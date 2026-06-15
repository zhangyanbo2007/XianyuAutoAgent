# 隐私工程

集中管理个人隐私敏感文件：保险理赔、个人档案、人物档案、医疗诊断、微信聊天记录等。

## 核心规则

1. **隐私文件不进 git** — 本目录所有内容不应提交到公开仓库

## 运行环境

- 项目 Python：`/home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/.venv/bin/python3.11`（通用工具、无外部依赖脚本）
- **Skill 独立 venv**：每个有外部依赖的 skill 在自身目录下维护 `.venv/`，通过 `requirements.txt` 管理依赖
- **projects 独立 venv**：每个有外部依赖的 projects 在自身目录下维护 `.venv/`，通过 `requirements.txt` 管理依赖
- 代理：外网操作前确认 `127.0.0.1:7897` 连通性
