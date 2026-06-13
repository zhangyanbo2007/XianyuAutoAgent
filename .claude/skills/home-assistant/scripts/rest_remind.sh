#!/bin/bash
# 休息提醒脚本（node37 总控）
# 用法: bash rest_remind.sh "提醒内容"
# 功能: 主卧+书房音箱播报 + 轻音乐 + 飞书通知

SKILL_DIR="/home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/.claude/skills/home-assistant"
source "$SKILL_DIR/.cache/connection.env"
source /home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/.env

# 自动检测 URL
curl -s --connect-timeout 2 -o /dev/null "$HA_URL_LOCAL/api/" 2>/dev/null \
  && HA_URL="$HA_URL_LOCAL" || HA_URL="$HA_URL_REMOTE"
export HA_URL HA_TOKEN

MSG="${1:-该休息了}"

# 主卧+书房音箱 entity
BEDROOM="media_player.xiaomi_lx06_46d3_play_control"
STUDY="media_player.xiaomi_oh2_5da4_play_control"

# 1. 无需取消静音

# 2. 先停止所有音乐（用 intelligent_speaker）
curl -s -X POST "$HA_URL/api/services/xiaomi_miot/intelligent_speaker" \
  -H "Authorization: Bearer $HA_TOKEN" -H "Content-Type: application/json" \
  -d "{\"entity_id\":\"$BEDROOM\",\"text\":\"停止播放\",\"execute\":true}" > /dev/null 2>&1
curl -s -X POST "$HA_URL/api/services/xiaomi_miot/intelligent_speaker" \
  -H "Authorization: Bearer $HA_TOKEN" -H "Content-Type: application/json" \
  -d "{\"entity_id\":\"$STUDY\",\"text\":\"停止播放\",\"execute\":true}" > /dev/null 2>&1
sleep 3

# 3. 播报提醒（顺序，间隔1秒）
TTS_MSG=$(echo "$MSG" | head -c 120)
for SPK in "$BEDROOM" "$STUDY"; do
  curl -s -X POST "$HA_URL/api/services/xiaomi_miot/intelligent_speaker" \
    -H "Authorization: Bearer $HA_TOKEN" -H "Content-Type: application/json" \
    -d "{\"entity_id\":\"$SPK\",\"text\":\"$TTS_MSG\",\"execute\":false}" > /dev/null 2>&1
  sleep 1
done

# 4. 等待 TTS 播完（固定 30 秒）
sleep 30

# 5. 播放轻音乐（用 intelligent_speaker）
curl -s -X POST "$HA_URL/api/services/xiaomi_miot/intelligent_speaker" \
  -H "Authorization: Bearer $HA_TOKEN" -H "Content-Type: application/json" \
  -d "{\"entity_id\":\"$BEDROOM\",\"text\":\"播放轻音乐\",\"execute\":true}" > /dev/null 2>&1
curl -s -X POST "$HA_URL/api/services/xiaomi_miot/intelligent_speaker" \
  -H "Authorization: Bearer $HA_TOKEN" -H "Content-Type: application/json" \
  -d "{\"entity_id\":\"$STUDY\",\"text\":\"播放轻音乐\",\"execute\":true}" > /dev/null 2>&1

# 6. 监控播放状态，播完自动停止（后台执行）
bash "$SKILL_DIR/scripts/monitor_stop.sh" "$BEDROOM" &
bash "$SKILL_DIR/scripts/monitor_stop.sh" "$STUDY" &

# 7. 飞书通知
FEISHU_TOKEN=$(curl -s -X POST "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal" \
  -H "Content-Type: application/json" \
  -d "{\"app_id\":\"$FEISHU_APP_ID\",\"app_secret\":\"$FEISHU_APP_SECRET\"}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tenant_access_token',''))")

curl -s -X POST "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id" \
  -H "Authorization: Bearer $FEISHU_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"receive_id\":\"$FEISHU_USER_OPEN_ID\",\"msg_type\":\"text\",\"content\":\"{\\\"text\\\":\\\"🌙 ${MSG}\\\"}\"}" > /dev/null 2>&1

# 记录日志
echo "[$(date '+%Y-%m-%d %H:%M:%S')] $MSG" >> "$SKILL_DIR/.cache/remind.log"
