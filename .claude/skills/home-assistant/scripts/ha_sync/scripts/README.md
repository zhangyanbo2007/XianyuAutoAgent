# HA Script 本地备份

本地 JSON 文件 = HA 服务器上 script 配置的**权威副本**。

## 同步流程（每次改脚本必须走这个流程）

1. **读 HA** → 从 HA 拉取最新脚本配置，与本地比对
2. **改本地** → 在本地 JSON 文件中修改
3. **push 回 HA** → 通过 HA API 写入修改后的配置
4. **commit** → 把本地变更提交并 push 到 git

```bash
# 1. 拉取（读 HA，存本地）
source ../../.env
for sid in alarm_play_and_stop remind_tts rest_remind cat_eye_low_battery_remind; do
  curl -s "$HA_URL/api/config/script/config/$sid" \
    -H "Authorization: Bearer $HA_TOKEN" > "${sid}.json"
done

# 2. push 回 HA（改完本地后执行）
curl -s -X POST "$HA_URL/api/config/script/config/${sid}" \
  -H "Authorization: Bearer $HA_TOKEN" -H "Content-Type: application/json" \
  -d @${sid}.json
```

## 文件清单

| 文件 | 说明 |
|------|------|
| `alarm_play_and_stop.json` | 闹钟播放歌曲脚本 |
| `remind_tts.json` | 出门提醒 TTS 播报脚本 |
| `rest_remind.json` | 休息提醒 TTS+轻音乐脚本 |
| `cat_eye_low_battery_remind.json` | 猫眼低电量提醒（客厅音箱播报） |

## 已知限制

- `input_number` helper 只能通过 HA WebSocket API 或 UI 创建，REST API 不支持
- 自动化配置通过 `/api/config/automation/config/{id}` 读写
