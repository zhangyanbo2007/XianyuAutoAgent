---
title: VPN备选渠道
date: 2026-05-18
last_updated: 2026-05-28
type: reference
tags: [VPN, 代理, 订阅]
sources:
  - 调研对比
related:
  - "[vpn-auto-check](vpn-auto-check.md)"
confidence: high
contested: false
---

## 当前订阅

| 项 | 值 |
|---|---|
| 服务商 | 零食铺集市 / 长风破浪 |
| 官网 | https://lspjs.com/ |
| 官网入口 | https://o1210d.555555001.xyz 或 https://o1211.555555001.xyz |
| 邮件通知 | no-reply@1314159.xyz 或 mail@lspjs.com（可发任意邮件获取最新地址） |
| 订阅 URL | https://o1210d.555555001.xyz/link/LxVvCYNAHsix9LoM?clash=1 |
| 协议类型 | anytls + IEPL vmess |
| 客户端 | mihomo (Clash Verge Rev) |
| 价格 | 基础版: 月¥12.99(60GB/25M), 季¥35.99(240GB/35M), 年¥114.99(1800GB/60M)；高级版: 月¥23.99(180GB/70M), 季¥68.99(1200GB/100M), 年¥219.99(4800GB/200M)；旗舰版: 季¥75(900GB不限速), 年¥275(4800GB不限速) |
| 状态 | 正常使用，anytls 节点稳定，IEPL 节点不通 |

## 备选渠道（待验证）

**Why:** 当前只有一个订阅源，一旦跑路或被封，代理完全中断。需要至少 1-2 个备选订阅随时可切换。

**How to apply:** 每周扫描一次备选渠道可用性。当前订阅失效时，从备选清单中选一个，更新订阅 URL + 刷新配置 + 重启 mihomo。

### 评估标准

| 维度 | 要求 |
|---|---|
| 运营年限 | >= 3 年（跑路风险低） |
| 协议支持 | mihomo/Clash 兼容，至少支持 Hysteria2 或 anytls |
| 专线线路 | 有 IPLC/专线选项 |
| 节点覆盖 | 有日/韩/美/新加坡（排除香港） |
| 试用 | 提供试用周期 |
| 价格 | 合理，不超过当前 2x |

### 备选服务商详情（2026-05-18 调研）

| # | 服务商 | 官网 | 价格(参考) | 线路 | mihomo | 特点 | 推荐度 |
|---|---|---|---|---|---|---|---|
| 1 | **TAG (Haka)** | tagssv2.com (需代理访问) | 待查官网(Cloudflare拦截) | IPLC专线+全专线架构 | ✅ | 运营多年、日本/美节点多、全专线、稳定性5星 | ⭐⭐⭐⭐⭐ |
| 2 | **Nexitally (钠云)** | nexitally.com (Cloudflare拦截) | 待查官网 | IPLC+IEPL纯专线 | ✅ | 纯专线不超卖、季付性价比高、稳定性5星 | ⭐⭐⭐⭐⭐ |
| 3 | **WgetCloud (速梯)** | wgetcloud.org | 入门月¥39-49(100GB), 标准月¥69-79(200GB全IPLC), 高级月¥99-119(500GB) | IPLC专线 | ✅ | 大厂线路低延迟、流媒体解锁、社区长期推荐 | ⭐⭐⭐⭐ |
| 4 | **DualNode** | dualnode.com (可直连跳转lv) | 入门$3-5/月(50-100GB), 标准$8-12/月(200-300GB) | IPLC专线 | ✅ | 双节点架构(入口+出口分离)、隐私性好、备线自动切换 | ⭐⭐⭐⭐ |
| 5 | **FlCloud (花云)** | 常变更域名,Telegram获取 | 月¥12起(入门),中档¥15-25 | 部分IPLC+普通混合 | ✅ | 月付12元与当前价格接近、性价比好、节点覆盖广(亚/美/欧) | ⭐⭐⭐⭐ |
| 6 | **Linkfox** | 常变更域名,Telegram获取 | 月¥15-30(入门),¥30-50(标准),¥50-100(高级不限) | IPLC专线 | ✅ | 支持SS/V2ray/Trojan多协议、节点覆盖好、界面简洁 | ⭐⭐⭐ |

**对比当前(零食铺集市):**
- 当前月付¥12.99起，价格最便宜
- 花云月付¥12起，价格与当前最接近，推荐作为首选备选
- WgetCloud/TAG/Nexitally 价格是当前 3-5x，但专线稳定性更好
- 如果当前跑路，优先选花云(价格接近)→TAG/Nexitally(纯专线最稳)→WgetCloud

### 技术备选方案（不换服务商）

如果不想换服务商，可以加强当前配置的韧性：

1. **mihomo fallback 组**：配置多协议自动回退
   ```yaml
   proxy-groups:
     - name: "Auto-Fallback"
       type: fallback
       proxies: [anytls-node, hysteria2-node, vless-reality-node]
       url: "https://www.gstatic.com/generate_204"
       interval: 300
   ```
2. **anytls 协议**：新兴抗探测协议，模拟正常 HTTPS 流量
3. **多订阅合并**：用 subconverter 合并多个订阅 URL

## 切换流程（当前订阅失效时）

1. 从备选清单选择一个服务商，购买/试用
2. 获取新的 Clash 订阅 URL
3. 更新 mihomo 配置：
   ```bash
   curl -s '<新订阅URL>' -o /tmp/new_sub.yaml
   cp /tmp/new_sub.yaml ~/.config/mihomo/config.yaml
   kill $(pgrep mihomo)
   nohup /usr/local/bin/mihomo -d ~/.config/mihomo -f ~/.config/mihomo/config.yaml > /tmp/mihomo.log 2>&1 &
   ```
4. 运行 `/proxy-switch` 测速选最优节点
5. 验证连通性