---
title: 知识库演化日志
last_updated: 2026-05-28
type: log
---

# 隐私工程知识库演化日志

## [2026-05-28] restructure | kb 目录规整

- 从父级目录迁移设备拓扑相关文件到 kb/
- 创建 INDEX.md 内容导航
- 创建 LOG.md 演化日志
- 更新文件 frontmatter 规范
- 迁移设备信息 HTML 可视化文件

### 迁移的文件

| 文件 | 来源 | 说明 |
|------|------|------|
| devices_inventory.md | kb/infra/ | 10台设备清单、SSH凭据、Tailscale网络 |
| devices_inventory.html | kb/infra/ | 设备信息汇总可视化 |
| docker-commands.md | kb/infra/ | Docker 启动命令备忘 |
| docker-cuda124-container.md | kb/infra/ | CUDA124 容器配置 |
| env-architecture.md | kb/infra/ | 开发环境架构 |
| walle-tailscale-recovery.md | kb/infra/ | Walle Tailscale 恢复流程 |
| vpn-auto-check.md | kb/infra/ | VPN 代理检查 |
| vpn-backup-channels.md | kb/infra/ | VPN 备选渠道 |
