---
name: home-assistant
description: >
  Control Home Assistant smart home devices. Scan devices, clarify intent,
  operate lights/AC/vacuum/speakers, query sensors and states.
  When: "打开/关闭/查询/控制/调节 + 设备", "温度/湿度/电量多少",
  "房间好热/好冷/太暗", "扫地机去XX打扫", "全屋XX"
metadata: {"version": "8.0.0", "requires": {"env": ["HA_URL", "HA_TOKEN"], "bins": ["curl"]}}
---

# Home Assistant 智能家居技能

## 快速开始

```bash
# 1. 加载连接
source .env
curl -s --connect-timeout 2 -o /dev/null "$HA_URL_LOCAL/api/" 2>/dev/null \
  && HA_URL="$HA_URL_LOCAL" || HA_URL="$HA_URL_REMOTE"

# 2. 首次使用：扫描全屋设备
bash scripts/ingest.sh
```

## 架构

```
.cache/
├── .env                    ← 双URL + HA_TOKEN
├── entities_registry.json    ← 实体注册表（区域/设备/实体映射）
├── automations.yaml        ← 全部自动化配置（HA YAML格式，ingest.sh 生成）
└── methods_registry.json    ← HA 服务方法注册表
scripts/
└── ingest.sh               ← 全量扫描（设备 + 自动化 + 服务方法）
```

---

# 1. 扫描（数据基础）

```bash
bash scripts/ingest.sh
```

扫描 HA 三个注册表（区域、设备、实体）+ 自动化状态 + 服务方法 → 写入 `entities_registry.json` + `automations.yaml` + `methods_registry.json`。

**需要重新扫描：** 新增/删除设备、设备区域变更、大面积 unavailable。

**扫描后验证：** entities_registry.json 继承 HA 设备注册表的区域分配。如果 HA 里区域分错了（比如音箱反了），entities_registry.json 会错。扫描后检查关键设备：

```bash
bash scripts/verify_areas.sh           # 默认查 media_player
bash scripts/verify_areas.sh light     # 查灯
bash scripts/verify_areas.sh climate   # 查空调
```

区域有误则在 HA 网页修正后重新扫描。

---

# 2. 意图澄清（通用能力）

意图不明确时，先检索 registry，再澄清。

**两类澄清：**

| 类型 | 用户说 | 处理 |
|------|--------|------|
| **实体不明确** | "打开灯" | 检索 registry → 26个灯 → 澄清房间 |
| **意图不明确** | "房间好热" | 查传感器 → 28°C → 推断 → 开空调 |

**推断模式（无需澄清）：**

| 用户说 | 查传感器 | 推断 | 自动执行 |
|--------|----------|------|----------|
| "房间好热" | 温度>28°C | 夏天高温 | 开空调 26°C |
| "好冷" | 温度<16°C | 冬天低温 | 开空调制热 24°C |
| "太暗了" | 光照<100lux | 光线不足 | 开灯 |
| "打扫卫生" | — | 只有一台扫地机 | 直接启动 |

**决策流程：**
```
用户意图 → 检索 entities_registry.json
  ├─ 唯一匹配 → 直接执行
  ├─ 多个匹配 → 列出选项 → 用户选择 → 执行
  └─ 隐式意图 → 查传感器 → 推断 → 执行
```

---

# 3. 操作（核心能力）

## 3.1 选择调用方式

**操作前必查 `.cache/` 注册表**：
- 找到实体 → REST API 精准控制（带 entity_id）
- 找不到实体 → Conversation API 自然语言控制（不带 entity_id，让 HA 解析）

```bash
# 精准控制（.cache/ 有实体时优先用）
curl -s -X POST "$HA_URL/api/services/{domain}/{service}" \
  -H "Authorization: Bearer $HA_TOKEN" -H "Content-Type: application/json" \
  -d '{"entity_id": "light.xxx"}'

# 自然语言控制（找不到实体时兜底）
curl -s -X POST "$HA_URL/api/conversation/process" \
  -H "Authorization: Bearer $HA_TOKEN" -H "Content-Type: application/json" \
  -d '{"text": "打开书房灯"}'
```

```
用户意图 → .cache/entities_registry.json 查实体 domain + 设备 model
  → .cache/methods_registry.json 查 domain.services[xxx]
  → 检查 model_overrides（如 oh2 不能 turn_on/turn_off）
  → 有覆盖则用替代方案，无覆盖则用标准方法
```

| 方式 | 适用场景 | 命令 |
|------|----------|------|
| **REST API** | 所有设备，精准控制 | `POST /api/services/{domain}/{service}` |
| **Conversation API** | 找不到实体时，自然语言兜底 | `POST /api/conversation/process` |
| **xiaomi_miot** | 小米专属功能（TTS、智能音箱） | `POST /api/services/xiaomi_miot/{service}` |

> 小米设备的 light 实体可能 unavailable，但 Conversation API 能正常控制。
> 如果标准 API 返回成功但设备没反应，改用 Conversation API。

## 3.2 调用示例

```bash
# REST API — 开灯
curl -s -X POST "$HA_URL/api/services/light/turn_on" \
  -H "Authorization: Bearer $HA_TOKEN" -H "Content-Type: application/json" \
  -d '{"entity_id": "light.xxx"}'

# Conversation API — 自然语言控制
curl -s -X POST "$HA_URL/api/conversation/process" \
  -H "Authorization: Bearer $HA_TOKEN" -H "Content-Type: application/json" \
  -d '{"text": "打开书房灯"}'

# xiaomi_miot — 小爱音箱 TTS
curl -s -X POST "$HA_URL/api/services/xiaomi_miot/intelligent_speaker" \
  -H "Authorization: Bearer $HA_TOKEN" -H "Content-Type: application/json" \
  -d '{"entity_id": "media_player.xxx", "text": "播报内容", "execute": false}'
```

## 3.3 多步骤任务

一句话包含多个操作/查询时，拆解为子任务编排执行。

**示例：** "扫地机去厨房打扫，打扫完告诉我厨房温度"

```
1. 拆解 → 操作（扫地机去厨房）+ 查询（厨房温度）
2. 检索 registry → 找到 entity
3. 执行：先操作，等待完成后查询
```

**编排原则：**
- 识别连接词（"然后"、"同时"、"完成后"）拆分意图
- 有依赖按顺序，无依赖可并行
- 操作+查询自然交替

**⚠️ 多音箱播报注意：** 并行触发会导致播放不完整，必须顺序播报（间隔1秒）。

---

# 4. 查询（核心能力）

**查询前先读 `.cache/`**：
- 找到实体 → REST API 精准查询（带 entity_id）
- 找不到实体 → Conversation API 自然语言查询（不带 entity_id，让 HA 解析）

## 4.1 单次查询

```bash
# 精准查询（.cache/ 有实体时优先用）
curl -s "$HA_URL/api/states/ENTITY_ID" -H "Authorization: Bearer $HA_TOKEN"

# 自然语言查询（找不到实体时兜底）
curl -s -X POST "$HA_URL/api/conversation/process" \
  -H "Authorization: Bearer $HA_TOKEN" -H "Content-Type: application/json" \
  -d '{"text": "书房温度多少"}'

# 按名称搜索（遍历所有实体）
curl -s "$HA_URL/api/states" -H "Authorization: Bearer $HA_TOKEN" \
  | jq -r --arg kw "关键词" '.[] | select(.attributes.friendly_name // "" | contains($kw)) | "\(.entity_id): \(.state)"'
```

## 4.2 批量查询

```bash
# 所有温度传感器
curl -s "$HA_URL/api/states" -H "Authorization: Bearer $HA_TOKEN" \
  | jq -r '.[] | select(.attributes.device_class == "temperature") | "\(.attributes.friendly_name // .entity_id): \(.state)°C"'

# 低电量设备
curl -s "$HA_URL/api/states" -H "Authorization: Bearer $HA_TOKEN" \
  | jq -r '.[] | select(.attributes.battery_level != null and .attributes.battery_level < 20) | "\(.attributes.friendly_name // .entity_id): \(.attributes.battery_level)%"'
```

---

# 5. 配置文件写入（新增能力）

## 5.1 支持的配置文件

| 类型 | API 端点 | 读取 | 写入 |
|------|----------|------|------|
| **自动化** | `/api/config/automation/config/{id}` | GET | POST |
| **脚本** | `/api/config/script/config/{id}` | GET | POST |
| `.cache/automations.yaml` | 本地缓存 | 读写 | ingest.sh 生成 |
| `.cache/entities_registry.json` | 本地缓存 | 仅读 | ingest.sh 生成 |

## 5.2 自动化配置写入

**⚠️ automations.yaml 是只读缓存，不要手动编辑。** 通过 HA API 写入：

```bash
# 添加/修改自动化（通过 API）
curl -s -X POST "$HA_URL/api/config/automation/config/{id}" \
  -H "Authorization: Bearer $HA_TOKEN" -H "Content-Type: application/json" \
  -d '{ ...配置... }'

# 重新加载自动化
curl -s -X POST "$HA_URL/api/services/automation/reload" \
  -H "Authorization: Bearer $HA_TOKEN" -H "Content-Type: application/json"
```

## 5.2b 脚本配置写入

脚本（script）和自动化（automation）是 HA 中两种不同的实体类型，**脚本不能通过 automations.yaml 管理**，需用专用 API。

### 读取脚本配置

```bash
curl -s "$HA_URL/api/config/script/config/{脚本ID}" \
  -H "Authorization: Bearer $HA_TOKEN"
# 返回 JSON：alias, fields, sequence
```

### 写入/更新脚本配置

```bash
curl -s -X POST "$HA_URL/api/config/script/config/{脚本ID}" \
  -H "Authorization: Bearer $HA_TOKEN" -H "Content-Type: application/json" \
  -d '{
    "alias": "脚本别名",
    "fields": { ... },
    "sequence": [ ... ]
  }'
# 返回 {"result":"ok"}
```

### 脚本 JSON 格式

```json
{
  "alias": "闹钟播放歌曲完后停止",
  "fields": {
    "music": {
      "name": "音乐关键词",
      "description": "要播放的歌曲",
      "required": true
    }
  },
  "sequence": [
    {"alias": "1.取消静音", "action": "media_player.volume_mute", "data": {...}},
    {"alias": "2.等1秒", "delay": {"seconds": 1}},
    {"alias": "3.发送播放指令", "action": "text.set_value", "data": {...}},
    {"alias": "4.等待playing", "wait_for_trigger": [...], "timeout": {"seconds": 15}, "continue_on_timeout": true},
    {"alias": "5.等media_duration", "delay": {"seconds": "{{ template }}"}},
    {"alias": "6.停止播放", "action": "media_player.media_pause", "target": {...}}
  ]
}
```

> **⚠️ 给每步加 `alias`** — HA trace 会记录每步执行结果，alias 让日志可读。

### 标准操作流程

```bash
# 1. 读取当前配置
curl -s "$HA_URL/api/config/script/config/{id}" -H "Authorization: Bearer $HA_TOKEN"

# 2. 修改后写入
curl -s -X POST "$HA_URL/api/config/script/config/{id}" \
  -H "Authorization: Bearer $HA_TOKEN" -H "Content-Type: application/json" \
  -d '{ ...新配置... }'

# 3. 重新加载脚本
curl -s -X POST "$HA_URL/api/services/script/reload" \
  -H "Authorization: Bearer $HA_TOKEN" -H "Content-Type: application/json" -d '{}'
```

## 5.3 同步配置到 HA

**自动化同步：**

```bash
# 验证 YAML 语法
python3 -c "import yaml; yaml.safe_load(open('.cache/automations.yaml'))"

# 重新加载自动化
curl -s -X POST "$HA_URL/api/services/automation/reload" \
  -H "Authorization: Bearer $HA_TOKEN" -H "Content-Type: application/json"
```

**脚本同步：**（写入 API 即时生效，无需额外 reload）

```bash
# 如需手动刷新
curl -s -X POST "$HA_URL/api/services/script/reload" \
  -H "Authorization: Bearer $HA_TOKEN" -H "Content-Type: application/json" -d '{}'
```

## 5.4 连接配置修改

```bash
# 编辑 .env
vim .env

# 格式：
# HA_URL_LOCAL=http://192.168.x.x:8123
# HA_URL_REMOTE=https://xxx.duckdns.org:8123
# HA_TOKEN=eyJxxx...
```

## 5.5 写入安全规则

**⚠️ 写入前必须遵守：**

1. **备份原则** — 修改任何配置文件前先备份
   ```bash
   cp .cache/xxx.yaml .cache/xxx.yaml.bak.$(date +%Y%m%d)
   ```

2. **验证原则** — 写入后验证格式
   ```bash
   # YAML 验证
   python3 -c "import yaml; yaml.safe_load(open('.cache/automations.yaml'))"
   
   # JSON 验证
   python3 -c "import json; json.load(open('.cache/xxx.json'))"
   ```

3. **测试原则** — 新增自动化先用单次触发测试，确认无误再改为定时

4. **回滚原则** — 出错立即恢复备份
   ```bash
   cp .cache/xxx.yaml.bak .cache/xxx.yaml
   ```

## 5.6 脚本执行追踪（调试/日志）

HA 自动记录每次脚本执行的 trace，包含每步的输入、输出和耗时。

### 查看脚本 trace

```bash
# 获取脚本最近的 trace 列表
curl -s "$HA_URL/api/config/script/trace/{脚本ID}" \
  -H "Authorization: Bearer $HA_TOKEN"
```

### trace 数据结构

```json
{
  "trace_id": "...",
  "state": "terminated",        // terminated / running / error
  "script_id": "script.xxx",
  "run_id": "...",
  "started": "2026-06-03T07:00:00",
  "finished": "2026-06-03T07:03:15",
  "execution_time_ms": 195000,
  "trace": {
    "step_0": [{"result": true, "state": "...", "...": "..."}],
    "step_1": [...],
    ...
  }
}
```

### 利用 alias 增强 trace 可读性

给每步加 `alias` 字段，trace 中会显示为 `seq/alias` 而不是 `seq/step_0`：

```json
"trace": {
  "seq/1.取消静音": [{"result": true}],
  "seq/3.发送播放指令": [{"result": true}],
  "seq/4.等待playing": [{"result": true, "waited_until": "..."}],
  "seq/6.停止播放": [{"result": true}]
}
```

### 调试流程

```bash
# 1. 触发脚本
curl -s -X POST "$HA_URL/api/services/script/{脚本ID}" \
  -H "Authorization: Bearer $HA_TOKEN" -H "Content-Type: application/json" \
  -d '{"参数名": "参数值"}'

# 2. 等待执行完成

# 3. 查看 trace 结果
curl -s "$HA_URL/api/config/script/trace/{脚本ID}" \
  -H "Authorization: Bearer $HA_TOKEN"
```

## 5.7 常见配置模板

### 定时提醒类自动化

```yaml
  - alias: "HH:MM 提醒事项"
    id: "remind_HH_MM"
    trigger:
      - platform: time
        at: "HH:MM:SS"
    condition: []
    action:
      - service: script.remind_tts
    mode: single
```

### 设备联动类自动化

```yaml
  - alias: "XX触发-XX响应"
    id: "link_xxx"
    trigger:
      - platform: state
        entity_id: sensor.xxx
        to: "on"  # 或具体值
    condition: []
    action:
      - service: light.turn_on
        target:
          entity_id: light.xxx
    mode: single
```

### 条件自动化（带条件判断）

```yaml
  - alias: "条件自动化"
    id: "cond_xxx"
    trigger:
      - platform: time
        at: "08:00:00"
    condition:
      - condition: state
        entity_id: binary_sensor.home
        state: "on"
    action:
      - service: script.xxx
    mode: single
```

---

# 安全规则

**以下操作必须先确认用户：**
- 锁（lock）的上锁/解锁
- 报警器（alarm_control_panel）的布防/撤防
- 车库门（cover with device_class: garage）的开关

---

# 注意事项

## ⚠️ 定时音箱提醒：HA 内部自动化是唯一来源

每天的定时音箱提醒（起床闹钟 7:00-7:30、出门提醒 8:00-8:40 / 13:30-13:50、休息提醒 23:00-0:30）**只能由 HA 内部 Automation + Script 驱动**：

- 3 个 Script：`alarm_play_and_stop`（起床放歌）、`remind_tts`（出门播报，带天气）、`rest_remind`（休息播报+轻音乐）
- 16 条 Automation 定时触发（工作日类带 `{{ now().weekday() < 5 }}` 条件）

**绝对不要在任何机器（尤其 home-computer）上用 crontab/脚本另外 curl HA API 触发音箱。** 历史上 home-computer 的 `ha_remind.sh`/`ha_commute.sh` cron 在迁移到 HA 后没删，导致同一时刻 cron + HA **双重/三重触发**，TTS 互相打断、随机音乐乱放 —— 这是"定时播放很乱、响应不对"的根因。2026-06-13 已清除（备份在 home-computer `~/crontab.bak.*`）。

排查"音箱乱响"步骤：
1. 查 HA 自动化 `last_triggered` 是否与实际播放时刻吻合；若音箱在响但自动化没触发（如周末），说明有 HA 之外的源（cron/外部脚本）在跑
2. logbook 里有 `script.xxx started` 才是 HA 触发；只有 `media_player ... playing` 而无 script 记录 = 外部源
3. 检查 home-computer crontab：`sshpass -p zyb123456 ssh -p 6003 xiaowangzi@8.163.122.236 'crontab -l'`，只应保留 `@reboot frp/start.sh`

`remind_tts` 是纯播报（取消静音→TTS→静音），**不放音乐**；只有 `rest_remind`（理查德·克莱德曼）和 `alarm_play_and_stop`（李健）才放音乐。

> 备注：小米云端音箱的 `is_volume_muted` 标志滞后/半失效，命令返回成功但状态常不更新；`intelligent_speaker` 的 TTS 播报不受该 media mute 标志影响，照样出声。

## 特殊操作备注

### 小米音箱

- **oh2**: `media_player/turn_on`、`turn_off`、`toggle` 无效 → 用 Conversation API 或不管（常开）
- **oh2**: `media_stop` 不可靠 → 用 `text/set_value` → `execute_text_directive` "停止播放"
- **lx06/l05c**: `media_stop` 不可靠 → 用 `media_pause`
- **⚠️ 播放音乐必须用 `xiaomi_miot.intelligent_speaker`**，不能用 `text.set_value`！`text.set_value` 发送播放指令会导致音箱报 "播放失败，请检查网络"
- **所有型号**: TTS 播报前必须先 `volume_mute: false`（取消静音）
- **多音箱 TTS**: 必须顺序执行（间隔 1 秒），并行会导致播放不完整
- **TTS 文本限制**: oh2 约 80 字，其他约 150 字

### 小米灯

- 实体可能显示 `unavailable`，但 Conversation API 能正常控制
- 标准 REST API 返回成功但设备没反应时，改用 Conversation API
