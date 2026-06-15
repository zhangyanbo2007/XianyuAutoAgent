---
title: Walle Tailscale恢复
date: 2026-05-21
last_updated: 2026-05-28
type: procedural
tags: [Tailscale, 代理, 运维]
sources:
  - 实践经验总结
related:
  - "[devices_inventory](devices_inventory.md)"
  - "[vpn-auto-check](vpn-auto-check.md)"
confidence: high
contested: false
---

## walle (192.168.28.92) Tailscale 恢复方法

### 背景

本地网络（cuda124 所在 192.168.68.x）封禁了 Tailscale 控制平面 IP（192.200.0.x 网段），tailscaled 无法直连。walle 的 Clash Verge 代理是唯一出路，但代理经常出问题需要手动恢复。

### SSH 连接

```
sshpass -p 'zyb123456' ssh zhangyanbo@192.168.28.92
```

注意用户名是 **zhangyanbo**，不是 xiaowangzi。

### 恢复流程

#### 1. 启动 mihomo 核心

Clash Verge service 通常在跑，但核心进程经常不在。手动启动：

```bash
nohup /usr/bin/verge-mihomo -d ~/.local/share/io.github.clash-verge-rev.clash-verge-rev -f ~/.local/share/io.github.clash-verge-rev.clash-verge-rev/clash-verge.yaml > /tmp/mihomo.log 2>&1 &
```

验证：
```bash
ss -tlnp | grep 7897
```

#### 2. 刷新订阅（如节点过期）

```bash
curl -s 'https://o1210d.555555001.xyz/link/LxVvCYNAHsix9LoM?clash=1' -o /tmp/clash_sub1.yaml
```

替换配置文件后重启 mihomo：
```bash
cp /tmp/clash_sub1.yaml ~/.local/share/io.github.clash-verge-rev.clash-verge-rev/profiles/RJXDetWcpmLg.yaml
kill $(pgrep verge-mihomo)
# 重新执行步骤1的启动命令
```

#### 3. 测试节点连通性

TCP 测试代理节点服务器：
```bash
for host in cn2.mlinuu.top ocean.t.51guangtaobao.com obs.gateway.storagesvc.xyz ocean-gateway.obs.ap-kr.222220001.xyz; do
  echo -n "$host: "; timeout 3 bash -c "echo >/dev/tcp/$host/443" 2>/dev/null && echo 'OK' || echo 'FAIL'
done
```

#### 4. 切换可用节点

通过 Clash API 切换代理选择组（默认 SELECT 组当前选中节点可能不通）：

```bash
# API 地址和密钥
API=http://127.0.0.1:9099
SECRET='Dfsddf898902!./3dfasd0-0234-[]'

# 用 Python 切换（避免中文编码问题）
python3 -c "
import json, urllib.request
data = json.dumps({'name': '美国-a2'}).encode()
req = urllib.request.Request('http://127.0.0.1:9099/proxies/SELECT', data=data, method='PUT')
req.add_header('Content-Type', 'application/json')
req.add_header('Authorization', 'Bearer Dfsddf898902!./3dfasd0-0234-[]')
urllib.request.urlopen(req)
print('switched')
"
```

可用节点优先级（anytls 类型最稳定）：
- **韩国-a2-推荐**（obs.gateway.storagesvc.xyz:8443）— 延迟最低 ~1.2s
- **美国-a2**（ocean-gateway.obs.region-usw2.222220003.xyz:443）— ~1.5s，Tailscale 控制平面首选
- **日本1**（obs.gateway.storagesvc.xyz:8443）— ~1.9s
- **新加坡-a2**（ocean-gateway.obs.region-sgw2.222220003.xyz:443）— ~2.1s

不通的节点（IEPL vmess 节点走 ocean.t.51guangtaobao.com，全部不通）：
- 所有香港/韩国/美国/日本/新加坡的 IEPL-G1 节点
- 直连日本0/1、澳大利亚、台湾等

#### 5. 代理连通性验证

```bash
curl -s -4 -o /dev/null -w '%{http_code}' --connect-timeout 10 -x http://127.0.0.1:7897 https://www.google.com
curl -s -4 -o /dev/null -w '%{http_code}' --connect-timeout 10 -x http://127.0.0.1:7897 https://controlplane.tailscale.com/key?v=133
```

注意：韩国节点访问 Tailscale 控制平面会 EOF，**必须切换到美国-a2 节点**才能连通。

#### 6. 重启 tailscaled（带代理）

```bash
sudo systemctl restart tailscaled
# 代理配置已在 /etc/default/tailscaled 中设置（HTTP_PROXY/HTTPS_PROXY=http://127.0.0.1:7897）
sleep 10
tailscale status
```

#### 7. cuda124 侧恢复

如果 cuda124 的 tailscaled 也需要通过 walle 代理恢复：

```bash
sudo kill $(pgrep tailscaled)
sleep 2
sudo HTTP_PROXY=http://192.168.28.92:7897 HTTPS_PROXY=http://192.168.28.92:7897 nohup /usr/sbin/tailscaled \
  --state=/var/lib/tailscale/tailscaled.state \
  --socket=/var/run/tailscale/tailscaled.sock \
  > /tmp/tailscaled.log 2>&1 &
sleep 5
tailscale status
```

### 关键配置

| 项 | 值 |
|---|---|
| walle IP | 192.168.28.92 (局域网) / 100.123.160.126 (Tailscale) |
| SSH | zhangyanbo@192.168.28.92, 密码 zyb123456 |
| mihomo 端口 | 7897（统一端口，已在订阅配置和 /etc/default/tailscaled 中固定） |
| Clash API | 127.0.0.1:9099, secret 见配置文件 |
| 订阅 URL | https://o1210d.555555001.xyz/link/LxVvCYNAHsix9LoM?clash=1 |
| 活跃 profile | RJXDetWcpmLg.yaml |
| Tailscale 控制平面首选节点 | **美国-a2**（韩国节点会 EOF） |

### 注意事项

- tailscaled 代理配置写在 `/etc/default/tailscaled`（HTTP_PROXY/HTTPS_PROXY=http://127.0.0.1:7897），systemctl restart 会自动带上
- mihomo 的 cache.db 权限问题可以忽略（warning 级别）
- walle swap 使用率高(7/8GB)，内存紧张