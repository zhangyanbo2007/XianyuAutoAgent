---
title: VSCode Remote-SSH 连 node37 卡死恢复
date: 2026-06-13
last_updated: 2026-06-13
type: procedural
tags: [VSCode, Remote-SSH, node37, 代理, 运维]
sources:
  - 2026-06-13 实测排查
related:
  - "[devices_inventory](devices_inventory.md)"
  - "[walle-tailscale-recovery](walle-tailscale-recovery.md)"
confidence: high
contested: false
---

## VSCode Remote-SSH 连 node37 卡死/连不上 — 根因与恢复

### 症状

- VSCode Remote-SSH 连 node37（zhangyanbo@192.168.68.98:33）一直转圈连不上
- 但普通 SSH 终端**完全正常** → 不是网络层问题
- node37 负载异常升高（实测从 3.3 爬到 5.3）

### 根因（2026-06-13 实测确认）

**VSCode server 安装陷入并行重试死循环**，不是代理本身的锅：

1. 本地 VSCode 是某个 commit（如 6a44c352），该版本 server 在 node37 上**从未装成功**，
   cli/servers/ 下只有 `Stable-<hash>.staging`，永远没转正成最终 `Stable-<hash>/server`。
2. 客户端每隔 ~2.5 分钟超时重连，**各自启动一份 146MB 的 server 下载**。
   实测一瞬间 /tmp 里有 4 个 tarball 并行下载，全挤进同一个 .staging 目录互相覆盖
   → 产出残缺 server（缺 node_modules/@vscode/proxy-agent）
   → 扩展宿主一启动就崩（MODULE_NOT_FOUND）→ 再循环。
3. **代理 7897（mihomo）是帮凶**：VSCode CLI 下载走代理被绕到海外慢节点，仅 ~1MB/s，
   146MB 要下 ~2.5 分钟，几乎吃光整个连接超时窗口，来不及装完就被重试打断。
   注意 node37 其实可直连 update.code.visualstudio.com（直连更快）。
4. 附带：inotify max_user_watches 默认仅 8192（远低于 VSCode 推荐的 524288），
   server 跑起来后撞 `ENOSPC: file watchers reached`，文件监听失效。

### 永久修复（已实施，2026-06-13）

| 措施 | 内容 |
|---|---|
| **根治下载循环** | walle 的 `~/.config/Code/User/settings.json` 加 `"remote.SSH.localServerDownload": "always"` → 由 walle 本地下载 server 经 LAN 推送，绕开 node37 慢代理。**换其它机器连 node37 也要加这行。** |
| **inotify 上限** | node37 root 执行 `sysctl -w fs.inotify.max_user_watches=524288`，持久化在 `/etc/sysctl.d/99-vscode-inotify.conf` |
| **完整包备份** | 校验过的完整 server tarball 存于 `~/.vscode-server/_backup/`，应急可直接解压 |

### 快速诊断小抄（怀疑又犯时）

```bash
sshpass -p '333333' ssh -p 33 root@192.168.68.98   # 或 zyb123456 zhangyanbo
ls /tmp/.tmp*/ 2>/dev/null | wc -l                 # 一直涨 = 又在下载循环
ls ~/.vscode-server/cli/servers/                   # 只有 .staging 没转正 = 装不上
cat /proc/sys/fs/inotify/max_user_watches          # 应为 524288，若是 8192 说明 sysctl 没生效
```

### 应急恢复流程

```bash
# 1. 杀掉死循环进程（zhangyanbo 身份）
pkill -u zhangyanbo -f 'code-.*command-shell'
pkill -u zhangyanbo -f 'vscode-server.*bootstrap-fork'

# 2. 清理踩踏垃圾
rm -rf /tmp/.tmp*/
rm -rf ~/.vscode-server/cli/servers/*.staging

# 3.（可选）用备份包预置 server，跳过下载
HASH=<本地VSCode的commit hash>
DST=~/.vscode-server/cli/servers/Stable-$HASH/server
mkdir -p $DST
tar xzf ~/.vscode-server/_backup/vscode-server-*.tar.gz --strip-components=1 -C $DST
# 校验：
ls $DST/node_modules/@vscode/proxy-agent/out/index.js   # 必须存在
ls $DST/bin/code-server                                  # 必须存在

# 4. 若 inotify 被重置（容器重建后）
sudo sysctl -w fs.inotify.max_user_watches=524288 fs.inotify.max_user_instances=512

# 5. 重新发起 VSCode Remote-SSH 连接，连上后 Ctrl+Shift+P → Reload Window
```

### 关键路径

| 项 | 值 |
|---|---|
| node37 SSH | zhangyanbo@192.168.68.98:33（密码 zyb123456）/ root（333333） |
| server 安装目录 | ~/.vscode-server/cli/servers/Stable-<commit>/server |
| 活跃版本记录 | ~/.vscode-server/cli/servers/lru.json（最新在最前） |
| CLI 下载日志 | ~/.vscode-server/.cli.<commit>.log |
| 运行日志 | ~/.vscode-server/data/logs/<最新时间戳>/remoteagent.log |
| 完整包备份 | ~/.vscode-server/_backup/ |
| walle 设置 | /home/zhangyanbo/.config/Code/User/settings.json（已加 localServerDownload） |
