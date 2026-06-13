#!/bin/bash
# 出门提醒脚本（node37 总控）
# 用法: bash remind.sh "提醒内容" [带天气(1/0)]
# 功能: 三音箱同时播报 + 飞书通知 + 天气判断

SKILL_DIR="/home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/.claude/skills/home-assistant"
source "$SKILL_DIR/.cache/connection.env"
source /home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/.env

# 自动检测 URL
curl -s --connect-timeout 2 -o /dev/null "$HA_URL_LOCAL/api/" 2>/dev/null \
  && HA_URL="$HA_URL_LOCAL" || HA_URL="$HA_URL_REMOTE"

MSG="${1:-该出门了}"
WITH_WEATHER="${2:-0}"

# 带天气判断
if [ "$WITH_WEATHER" = "1" ]; then
  # 获取天气描述和温度
  WEATHER_EN=$(curl -s "wttr.in/Guangzhou+Nansha?format=%C" 2>/dev/null)
  TEMP=$(curl -s "wttr.in/Guangzhou+Nansha?format=%t" 2>/dev/null)

  # 翻译天气为中文
  case "$WEATHER_EN" in
    *Rain*|*rain*|*Drizzle*|*drizzle*|*Shower*|*shower*) WEATHER_CN="有雨" ;;
    *Thunder*|*thunder*) WEATHER_CN="雷阵雨" ;;
    *Snow*|*snow*) WEATHER_CN="下雪" ;;
    *Cloud*|*cloud*|*Overcast*) WEATHER_CN="多云" ;;
    *Sunny*|*sunny*|*Clear*|*clear*) WEATHER_CN="晴天" ;;
    *Fog*|*fog*|*Mist*|*mist*) WEATHER_CN="有雾" ;;
    *) WEATHER_CN="$WEATHER_EN" ;;
  esac

  # 判断是否下雨
  IS_RAIN=0
  if echo "$WEATHER_EN" | grep -qiE "rain|drizzle|thunder|shower|snow"; then
    IS_RAIN=1
  fi

  if [ "$IS_RAIN" = "1" ]; then
    WEATHER_MSG="今天${WEATHER_CN}，${TEMP}，建议开车上班，出门别忘带雨伞"
  else
    WEATHER_MSG="今天${WEATHER_CN}，${TEMP}，不下雨，建议骑电瓶车上班"
  fi

  MSG="${MSG}。${WEATHER_MSG}"
fi

# 三音箱播报（oh2音箱TTS长度有限，单独截断80字）
# 其他音箱截断150字
SPEAKERS=(
  "media_player.xiaomi_lx06_81cc_play_control|150"
  "media_player.xiaomi_lx06_46d3_play_control|150"
  "media_player.xiaomi_oh2_5da4_play_control|80"
)

# 无需取消静音，直接播报

# 顺序播报
for item in "${SPEAKERS[@]}"; do
  IFS='|' read -r SPK LIMIT <<< "$item"
  TTS_MSG=$(echo "$MSG" | head -c "$LIMIT")
  curl -s -X POST "$HA_URL/api/services/xiaomi_miot/intelligent_speaker" \
    -H "Authorization: Bearer $HA_TOKEN" -H "Content-Type: application/json" \
    -d "{\"entity_id\":\"$SPK\",\"text\":\"$TTS_MSG\",\"execute\":false}" > /dev/null 2>&1
  sleep 1
done

# 飞书通知
FEISHU_TOKEN=$(curl -s -X POST "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal" \
  -H "Content-Type: application/json" \
  -d "{\"app_id\":\"$FEISHU_APP_ID\",\"app_secret\":\"$FEISHU_APP_SECRET\"}" | python3 -c "import sys,json; print(json.load(sys.stdin).get('tenant_access_token',''))")

curl -s -X POST "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id" \
  -H "Authorization: Bearer $FEISHU_TOKEN" \
  -H "Content-Type: application/json" \
  -d "{\"receive_id\":\"$FEISHU_USER_OPEN_ID\",\"msg_type\":\"text\",\"content\":\"{\\\"text\\\":\\\"📢 ${MSG}\\\"}\"}" > /dev/null 2>&1

# 记录日志
echo "[$(date '+%Y-%m-%d %H:%M:%S')] $MSG" >> "$SKILL_DIR/.cache/remind.log"
