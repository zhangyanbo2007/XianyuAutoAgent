---
title: 开发环境架构
date: 2026-05-21
last_updated: 2026-05-28
type: reference
tags: [Python, Node, 开发环境, 代理]
sources:
  - 服务器配置规范化
related:
  - "[devices_inventory](devices_inventory.md)"
confidence: high
contested: false
---

# 开发环境架构（2026-05-21 规范化）

## Python

| 层 | 工具 | 路径 | 说明 |
|---|---|---|---|
| 包管理 | uv | ~/.local/bin/uv (v0.11.7) | 全局唯一，替代 conda/pip |
| 解释器 | uv managed | ~/.local/share/uv/python/ | cpython-3.11.15 |
| 项目环境 | 项目级 .venv | projects/<name>/.venv | 每个项目独立，uv 创建 |
| 系统Python | /usr/bin/python3 | 3.10.12 | 仅备用，无 pip |

**规则：新项目一律 `uv venv .venv && uv pip install -e .`，不再用 conda 或 pip 全局安装。**

## Node

| 层 | 工具 | 路径 |
|---|---|---|
| 版本管理 | NVM | ~/.nvm/ (v22.22.2) |
| npm | PNPM_HOME 管理 | ~/.local/share/pnpm/bin/ (v10.9.7) |
| pnpm | PNPM_HOME 管理 | ~/.local/share/pnpm/bin/ (v11.0.8) |

**规则：全局 npm 包只装 CLI 工具（claude-code, cc-connect, clawhub 等），项目依赖用 pnpm install。**

## 代理

| 工具 | 代理地址 | 代理来源 |
|---|---|---|
| npm | 127.0.0.1:7897 | ~/.npmrc |
| pnpm | 127.0.0.1:7897 | pnpm config |
| 本地 mihomo | 127.0.0.1:7897 | 进程监听 |

**统一指向本地 mihomo (127.0.0.1:7897)，不再用 192.168.28.92。**

## bashrc 关键配置

- uv/uvx via ~/.local/bin/env
- Hermes CLI via HERMES_VENV 变量
- NVM 标准 init
- PNPM_HOME + PATH
- OpenClaw completion via $HOME/.openclaw/
- NVIDIA LD_LIBRARY_PATH

## 已删除（不再存在）

- miniconda3 (39G) — 全部删除，conda 不再使用
- ~/.local/venvs/ — 全部删除，venv 只放项目级
- ~/.npm-global/ — 删除，NVM/PNPM_HOME 替代
- 散落 pip 全局脚本 (~/.local/bin) — 清理，只保留 uv/uvx/gh/code/mihomo/feishu/env

## 项目 venv 状态

| 项目 | .venv | 状态 |
|---|---|---|
| hermes_agent | 3.11.15 / uv | 完整安装，v0.14.0 |
| kb-search-mcp | 3.11.15 / uv | 完整安装 |
| openviking | 3.10.12 / uv | 仅基础包，需 Rust 工具链才能完整安装 |
| lerobot_project | 无 | 需要时 uv 重建 |
| OpenClaw-RL | 无 | 需要时 uv 重建 |