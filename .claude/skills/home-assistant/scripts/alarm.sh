#!/bin/bash
# 起床闹钟脚本
# 用法: bash alarm.sh "提醒内容" "音乐关键词"
# 功能: 主卧音箱播报 + 播放音乐 + 播完自动停止 + 飞书通知

SKILL_DIR="/home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/.claude/skills/home-assistant"
source "$SKILL_DIR/.cache/connection.env"
source /home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/.env

# 自动检测 URL
curl -s --connect-timeout 2 -o /dev/null "$HA_URL_LOCAL/api/" 2>/dev/null \
  && HA_URL="$HA_URL_LOCAL" || HA_URL="$HA_URL_REMOTE"

bj_time() { TZ=Asia/Shanghai date '+%Y-%m-%d %H:%M:%S'; }

MSG="${1:-该起床了}"
ALARM_NUM="${2:-1}"

# 李健歌曲列表（按闹钟序号轮换：1=7:00, 2=7:10, 3=7:20, 4=7:30）
DAY_OF_YEAR=$(TZ=Asia/Shanghai date +%j)
ALL_SONGS=("李健 传奇" "李健 贝加尔湖畔" "李健 风吹麦浪" "李健 当有天老去"
  "李健 一念一生" "李健 为你而来" "李健 异乡人" "李健 假如爱有天意"
  "李健 一生有你" "李健 爱你")
OFFSET=$(( DAY_OF_YEAR % ${#ALL_SONGS[@]} ))
SONG_INDEX=$(( (ALARM_NUM - 1) % ${#ALL_SONGS[@]} ))
MUSIC="${ALL_SONGS[$(( (OFFSET + SONG_INDEX) % ${#ALL_SONGS[@]} ))]}"

BEDROOM="media_player.xiaomi_lx06_46d3_play_control"
LOG="$SKILL_DIR/.cache/remind.log"

log() { echo "[$(bj_time)] $1" >> "$LOG"; echo "[$(bj_time)] $1"; }

# 1. TTS 播报
curl -s -X POST "$HA_URL/api/services/xiaomi_miot/intelligent_speaker" \
  -H "Authorization: Bearer $HA_TOKEN" -H "Content-Type: application/json" \
  -d "{\"entity_id\":\"$BEDROOM\",\"text\":\"$MSG\",\"execute\":false}" > /dev/null 2>&1
sleep 3

# 2. 播放音乐
curl -s -X POST "$HA_URL/api/services/xiaomi_miot/intelligent_speaker" \
  -H "Authorization: Bearer $HA_TOKEN" -H "Content-Type: application/json" \
  -d "{\"entity_id\":\"$BEDROOM\",\"text\":\"播放$MUSIC\",\"execute\":true}" > /dev/null 2>&1
log "发送播放: $MUSIC"

# 3. 监控进度，duration-6 秒停止
PLAY_START=""
DURATION=0
for i in $(seq 1 60); do
  sleep 3
  # volume_set 触发 HA 刷新
  CUR_VOL=$(curl -s -H "Authorization: Bearer $HA_TOKEN" "$HA_URL/api/states/$BEDROOM" 2>/dev/null \
    | python3 -c "import sys,json; print(json.load(sys.stdin).get('attributes',{}).get('volume_level',0.5))" 2>/dev/null)
  curl -s -X POST "$HA_URL/api/services/media_player/volume_set" \
    -H "Authorization: Bearer $HA_TOKEN" -H "Content-Type: application/json" \
    -d "{\"entity_id\":\"$BEDROOM\",\"volume_level\":$CUR_VOL}" > /dev/null 2>&1
  sleep 1
  # 读最新状态
  STATE_JSON=$(curl -s -H "Authorization: Bearer $HA_TOKEN" "$HA_URL/api/states/$BEDROOM" 2>/dev/null)
  STATE=$(echo "$STATE_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin).get('state',''))" 2>/dev/null)
  POS=$(echo "$STATE_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin).get('attributes',{}).get('media_position',0))" 2>/dev/null)
  DUR=$(echo "$STATE_JSON" | python3 -c "import sys,json; print(json.load(sys.stdin).get('attributes',{}).get('media_duration',0))" 2>/dev/null)

  if [ "$STATE" = "playing" ] && [ -z "$PLAY_START" ]; then
    PLAY_START=$(date +%s)
    DURATION=$DUR
    log "音乐开始, duration=$DUR"
  fi

  if [ -n "$PLAY_START" ] && [ "$DUR" -gt 0 ]; then
    ELAPSED=$(( $(date +%s) - PLAY_START ))
    log "播放${ELAPSED}s: state=$STATE pos=$POS/$DUR"
    # 到 duration-6 就停
    if [ "$POS" -ge "$((DUR - 6))" ] 2>/dev/null || [ "$ELAPSED" -ge "$((DUR - 3))" ] 2>/dev/null; then
      log "到停止点, 连续4次发停止"
      for j in 1 2 3 4; do
        curl -s -X POST "$HA_URL/api/services/xiaomi_miot/intelligent_speaker" \
          -H "Authorization: Bearer $HA_TOKEN" -H "Content-Type: application/json" \
          -d "{\"entity_id\":\"$BEDROOM\",\"text\":\"停止播放\",\"execute\":true}" > /dev/null 2>&1
        sleep 1
      done
      sleep 2
      FINAL=$(curl -s -H "Authorization: Bearer $HA_TOKEN" "$HA_URL/api/states/$BEDROOM" 2>/dev/null \
        | python3 -c "import sys,json; print(json.load(sys.stdin).get('state',''))" 2>/dev/null)
      log "停止后: $FINAL"
      break
    fi
  fi
done

# 4. 飞书通知
FEISHU_TOKEN=$(curl -s -X POST "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal" \
  -H "Content-Type: application/json" \
  -d "{\"app_id\":\"$FEISHU_APP_ID\",\"app_secret\":\"$FEISHU_APP_SECRET\"}" \
  | python3 -c "import sys,json; print(json.load(sys.stdin).get('tenant_access_token',''))" 2>/dev/null)
curl -s -X POST "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id" \
  -H "Authorization: Bearer $FEISHU_TOKEN" -H "Content-Type: application/json" \
  -d "{\"receive_id\":\"$FEISHU_USER_OPEN_ID\",\"msg_type\":\"text\",\"content\":\"{\\\"text\\\":\\\"⏰ $MSG 正在播放$MUSIC\\\"}\"}" > /dev/null 2>&1

log "$MSG 播放$MUSIC 完成"
