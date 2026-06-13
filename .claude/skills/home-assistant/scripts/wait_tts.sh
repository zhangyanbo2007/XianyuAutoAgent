#!/bin/bash
# 等待 TTS 播完（监控 speaker 状态）
# 用法: bash wait_tts.sh <entity_id> [max_wait_seconds]

EID="${1:-}"
MAX_WAIT="${2:-30}"

if [ -z "$EID" ]; then
  echo "用法: bash wait_tts.sh <entity_id> [max_wait_seconds]"
  exit 1
fi

# 加载环境
SKILL_DIR="/home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/.claude/skills/home-assistant"
source "$SKILL_DIR/.cache/connection.env"
curl -s --connect-timeout 2 -o /dev/null "$HA_URL_LOCAL/api/" 2>/dev/null \
  && HA_URL="$HA_URL_LOCAL" || HA_URL="$HA_URL_REMOTE"

# 等待状态从非 idle 变为 idle（TTS 播完）
PREV=""
for i in $(seq 1 "$MAX_WAIT"); do
  STATE=$(curl -s -H "Authorization: Bearer $HA_TOKEN" "$HA_URL/api/states/$EID" 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('state',''))" 2>/dev/null)

  # 如果状态从 playing/paused 变为 idle，说明 TTS 播完了
  if [ "$PREV" != "idle" ] && [ "$STATE" = "idle" ]; then
    sleep 2  # 额外等 2 秒确认
    FINAL=$(curl -s -H "Authorization: Bearer $HA_TOKEN" "$HA_URL/api/states/$EID" 2>/dev/null | python3 -c "import sys,json; print(json.load(sys.stdin).get('state',''))" 2>/dev/null)
    if [ "$FINAL" = "idle" ]; then
      echo "TTS 播完（${i}秒）"
      exit 0
    fi
  fi

  PREV="$STATE"
  sleep 1
done

echo "超时（${MAX_WAIT}秒），继续执行"
