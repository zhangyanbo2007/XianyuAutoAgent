---
title: VPN代理检查
date: 2026-05-21
last_updated: 2026-05-28
type: procedural
tags: [VPN, 代理, 网络]
sources:
  - 实践经验总结
related:
  - "[vpn-backup-channels](vpn-backup-channels.md)"
  - "[env-architecture](env-architecture.md)"
confidence: high
contested: false
---

## 先判断是否需要代理

访问任何网络目标前，自主判断走直连还是代理：

**直连（不走代理）：**
- 私有 IP：192.168.x.x、10.x.x.x、172.16-31.x.x、127.0.0.1、localhost
- 本机服务：同一台机器上的 API/端口
- 国内域名：.cn、baidu.com、aliyun.com、feishu.cn、qq.com、taobao.com、dashscope.aliyuncs.com 等
- LAN 内其他机器（如 walle 192.168.28.92）

**走代理（curl -x http://127.0.0.1:7897）：**
- 国际域名：github.com、google.com、arxiv.org、npmjs.com、pypi.org、stackoverflow.com 等
- WebSearch / WebFetch 工具（它们依赖外网）

## 外网访问前检查连通性

判断需要代理后，先检查：

```bash
curl -s -4 -o /dev/null -w '%{http_code}' --connect-timeout 5 -x http://127.0.0.1:7897 https://api.github.com
```

返回 `200` → 继续；返回 `000` 或超时 → 自动执行 `/proxy-switch` 测速切换最优非港节点，切换后再继续原任务。

**Why:** 内网不需要代理，浪费代理流量还可能更慢；外网不通时自动修复，避免空转。排除香港节点。

## 适用所有联网工具

本规则适用于一切网络访问，不限工具类型：

| 工具 | 联网方式 | 代理策略 |
|------|----------|----------|
| `curl` | `-x http://127.0.0.1:7897` | 外网加 `-x`，内网不加 |
| `wget` | `-e use_proxy=yes -e http_proxy=...` | 外网加代理参数，内网不加 |
| `WebSearch` | 系统内置 | 默认走外网，使用前先检查代理连通性 |
| `WebFetch` | 系统内置 | 默认走外网，使用前先检查代理连通性 |
| `pip install` | `--proxy http://127.0.0.1:7897` | pypi.org 外网加代理 |
| `npm install` | `--proxy http://127.0.0.1:7897` | npmjs.com 外网加代理 |
| `git clone/push/pull/fetch` | 必走外网（GitHub等） | 使用前先检查代理连通性，必走代理 |
| `ssh` | 直连 | 内网机器直连，不走代理 |
| MCP 工具（kb-search 等） | 本机服务 | 直连，不走代理 |

**How to apply:** 调用任何联网工具前，先看目标域名/IP判断内/外网。外网工具使用前先检查代理连通性，不通立刻跑 /proxy-switch 再继续。所有代理操作排除香港节点。