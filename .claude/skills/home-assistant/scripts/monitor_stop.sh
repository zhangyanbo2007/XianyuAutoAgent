#!/bin/bash
# 监控音箱播放状态，播完自动发停止指令
# 用法: bash monitor_stop.sh <entity_id>

SKILL_DIR="/home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/.claude/skills/home-assistant"
source "$SKILL_DIR/.cache/connection.env"

curl -s --connect-timeout 2 -o /dev/null "$HA_URL_LOCAL/api/" 2>/dev/null \
  && HA_URL="$HA_URL_LOCAL" || HA_URL="$HA_URL_REMOTE"

EID="${1:-}"
if [ -z "$EID" ]; then
  echo "用法: bash monitor_stop.sh <entity_id>"
  exit 1
fi

LOG="$SKILL_DIR/.cache/remind.log"
log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1" >> "$LOG"; }

# 等 15 秒让歌曲信息加载
sleep 15

# 读 duration
DUR=$(curl -s -H "Authorization: Bearer $HA_TOKEN" "$HA_URL/api/states/$EID" 2>/dev/null \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('attributes',{}).get('media_duration',300))" 2>/dev/null)
DUR=${DUR:-300}
log "$EID 监控启动, duration=${DUR}s"

# 轮询 media_position，到 duration-6 就停
for i in $(seq 1 $((DUR / 2))); do
  sleep 2
  # volume_set 触发 HA 刷新
  CUR_VOL=$(curl -s -H "Authorization: Bearer $HA_TOKEN" "$HA_URL/api/states/$EID" 2>/dev/null \
    | python3 -c "import sys,json; print(json.load(sys.stdin).get('attributes',{}).get('volume_level',0.5))" 2>/dev/null)
  curl -s -X POST "$HA_URL/api/services/media_player/volume_set" \
    -H "Authorization: Bearer $HA_TOKEN" -H "Content-Type: application/json" \
    -d "{\"entity_id\":\"$EID\",\"volume_level\":$CUR_VOL}" > /dev/null 2>&1
  sleep 1

  # 读最新状态
  STATE_JSON=$(curl -s -H "Authorization: Bearer $HA_TOKEN" "$HA_URL/api/states/$EID" 2>/dev/null)
  STATE=$(echo "$STATE_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin).get('state',''))" 2>/dev/null)
  POS=$(echo "$STATE_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin).get('attributes',{}).get('media_position',0))" 2>/dev/null)

  if [ "$STATE" != "playing" ]; then
    log "$EID 已停止"
    break
  fi

  log "$EID pos=$POS/$DUR"
  if [ "$POS" -ge "$((DUR - 6))" ] 2>/dev/null; then
    log "$EID 到停止点, 连续4次发停止"
    for j in 1 2 3 4; do
      curl -s -X POST "$HA_URL/api/services/xiaomi_miot/intelligent_speaker" \
        -H "Authorization: Bearer $HA_TOKEN" -H "Content-Type: application/json" \
        -d "{\"entity_id\":\"$EID\",\"text\":\"停止播放\",\"execute\":true}" > /dev/null 2>&1
      sleep 1
    done
    log "$EID 停止完成"
    break
  fi
done
