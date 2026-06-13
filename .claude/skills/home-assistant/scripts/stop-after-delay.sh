#!/bin/bash
# 延时停止音箱播放脚本
# 用法: bash stop-after-delay.sh <秒数>
# 功能: 等待指定秒数后通过 HA API 暂停音箱

SKILL_DIR="/home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/.claude/skills/home-assistant"
source "$SKILL_DIR/.cache/connection.env"

# 北京时间函数（系统TZ=Asia/Shanghai不生效，用Python偏移）
bj_time() { python3 -c "from datetime import datetime,timezone,timedelta; print((datetime.now(timezone.utc)+timedelta(hours=8)).strftime('$1'))"; }

# 自动检测 URL
curl -s --connect-timeout 2 -o /dev/null "$HA_URL_LOCAL/api/" 2>/dev/null \
  && HA_URL="$HA_URL_LOCAL" || HA_URL="$HA_URL_REMOTE"
export HA_URL HA_TOKEN

BEDROOM_SPEAKER="media_player.xiaomi_lx06_46d3_play_control"
DELAY="${1:-20}"

# 等待音乐开始播放
PLAY_START=""
for i in $(seq 1 30); do
  sleep 1
  STATE=$(curl -s -H "Authorization: Bearer $HA_TOKEN" "$HA_URL/api/states/$BEDROOM_SPEAKER" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('state',''))" 2>/dev/null)
  if [ "$STATE" = "playing" ] && [ -z "$PLAY_START" ]; then
    PLAY_START=$(date +%s)
    echo "[$(bj_time '%H:%M:%S')] 音乐开始播放" >> "$SKILL_DIR/.cache/remind.log"
  fi
  if [ -n "$PLAY_START" ]; then
    ELAPSED=$(( $(date +%s) - PLAY_START ))
    echo "[$(bj_time '%H:%M:%S')] 播放${ELAPSED}秒: $STATE" >> "$SKILL_DIR/.cache/remind.log"
    if [ "$ELAPSED" -ge "$DELAY" ]; then
      echo "[$(bj_time '%H:%M:%S')] ${DELAY}秒到，通过 HA API 停止播放" >> "$SKILL_DIR/.cache/remind.log"
      curl -s -X POST "$HA_URL/api/services/media_player/media_pause" \
        -H "Authorization: Bearer $HA_TOKEN" \
        -H "Content-Type: application/json" \
        -d "{\"entity_id\": \"${BEDROOM_SPEAKER}\"}" > /dev/null 2>&1
      sleep 3
      STATE=$(curl -s -H "Authorization: Bearer $HA_TOKEN" "$HA_URL/api/states/$BEDROOM_SPEAKER" 2>/dev/null | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('state','?'))" 2>/dev/null)
      echo "[$(bj_time '%H:%M:%S')] 停止后: $STATE" >> "$SKILL_DIR/.cache/remind.log"
      break
    fi
  fi
done