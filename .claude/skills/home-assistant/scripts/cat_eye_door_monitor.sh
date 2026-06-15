#!/bin/bash
# 猫眼门磁监控：轮询检测PIR + 门磁 → 判断进门/出门 → 人脸识别
# 用法: nohup bash cat_eye_door_monitor.sh &
#
# 逻辑：
#   每3秒拉HA代理图，比对MD5 → 检测PIR触发时间
#   门打开时 → PIR时间差 < 10s = 进门，> 15s = 出门
#   进门 → 连续抓拍5张 + 缓存 → Qwen-VL人脸识别

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
DETECT_SCRIPT="$(dirname "$0")/cat_eye_person_detect.sh"
LOG="$SKILL_DIR/.cache/logs/cat_eye_door_monitor.log"
EVENT_LOG="$SKILL_DIR/.cache/logs/door_events.log"

source "$SKILL_DIR/.cache/connection.env"
source /home/zhangyanbo/owner/xiaowangzi/.env
export BAILIAN_BASE_URL BAILIAN_API_KEY

curl -s --connect-timeout 2 -o /dev/null "$HA_URL_LOCAL/api/" 2>/dev/null \
  && HA_URL="$HA_URL_LOCAL" || HA_URL="$HA_URL_REMOTE"
export HA_URL HA_TOKEN

# EZVIZ API 配置
EZVIZ_TOKEN="$EZVIZ_ACCESS_TOKEN"
EZVIZ_SERIAL="F66074055"
EZVIZ_BASE="https://open.ys7.com"

ts() { TZ=Asia/Shanghai date '+%Y-%m-%d %H:%M:%S'; }
log() { echo "[$(ts)] $*" >> "$LOG"; }
event() { echo "[$(ts)] $*" >> "$EVENT_LOG"; echo "[$(ts)] $*"; }

DOOR_SENSOR="binary_sensor.lumi_cn_719859620_acn001_contact_state_p_2_1"
CAMERA="camera.ezviz_cat_eye"
POLL_INTERVAL=2      # 轮询间隔（秒）
PIR_WINDOW=10         # PIR触发后10秒内开门=进门
EXIT_THRESHOLD=15     # PIR触发超过15秒开门=出门
RAPID_COUNT=5         # 进门时连续抓拍次数
RAPID_DELAY=0.2       # 抓拍间隔（秒）

log "监控启动（轮询${POLL_INTERVAL}s，进门窗口${PIR_WINDOW}s）"
event "监控启动"

# 初始化
LAST_MD5=""
LAST_PIR_TIME=$(date +%s)  # 启动时设为当前时间，避免第一次开门误判
LAST_STATE=""

while true; do
  NOW=$(date +%s)

  # 1. 拉HA代理图，检测PIR触发
  TMP="/tmp/cat_eye_poll_$$.jpg"
  curl -s "$HA_URL/api/camera_proxy/$CAMERA" -H "Authorization: Bearer $HA_TOKEN" -o "$TMP" 2>/dev/null

  if [ -s "$TMP" ]; then
    CURRENT_MD5=$(md5sum "$TMP" | cut -d' ' -f1)
    # 保留最近一次扫描图
    cp "$TMP" "$SKILL_DIR/.cache/cat_eye_events/latest.jpg"
    if [ -n "$LAST_MD5" ] && [ "$CURRENT_MD5" != "$LAST_MD5" ]; then
      LAST_PIR_TIME=$NOW
      # 保存PIR触发图片到事件文件夹
      EVENT_TIME=$(TZ=Asia/Shanghai date '+%Y%m%d_%H%M%S')
      EVENT_FILE="$SKILL_DIR/.cache/cat_eye_events/${EVENT_TIME}_pir.jpg"
      cp "$TMP" "$EVENT_FILE"
      log "PIR触发（图片变化）→ $EVENT_FILE"
    fi
    LAST_MD5="$CURRENT_MD5"
  fi
  rm -f "$TMP"

  # 2. 检测门磁状态
  STATE=$(curl -s "$HA_URL/api/states/$DOOR_SENSOR" -H "Authorization: Bearer $HA_TOKEN" 2>/dev/null \
    | python3 -c "import sys,json; print(json.load(sys.stdin).get('state','unknown'))" 2>/dev/null)

  if [ "$STATE" = "on" ] && [ "$LAST_STATE" = "off" ]; then
    log "门打开"
    PIR_DIFF=$(( NOW - LAST_PIR_TIME ))
    EVENT_TIME=$(TZ=Asia/Shanghai date '+%Y%m%d_%H%M%S')
    EVENT_DIR="$SKILL_DIR/.cache/cat_eye_events/${EVENT_TIME}_open"
    mkdir -p "$EVENT_DIR"

    # 保存开门时的缓存图
    [ -f "$TMP" ] && cp "$TMP" "$EVENT_DIR/cache.jpg"
    echo "$EVENT_TIME 门打开 PIR差=${PIR_DIFF}s" > "$EVENT_DIR/info.txt"

    if [ "$LAST_PIR_TIME" -eq 0 ]; then
      log "无PIR记录，跳过"
      echo "结果: 无PIR记录" >> "$EVENT_DIR/info.txt"
      event "门开（无PIR记录）"
    elif [ "$PIR_DIFF" -lt "$PIR_WINDOW" ]; then
      # 进门：PIR触发在10秒内
      log "进门（PIR ${PIR_DIFF}s前，< ${PIR_WINDOW}s）→ 启动人脸识别"
      echo "结果: 进门（PIR ${PIR_DIFF}s前）" >> "$EVENT_DIR/info.txt"

      # 连续抓拍5张（EZVIZ API，每张间隔200ms）
      CAPTURES=""
      for i in $(seq 1 $RAPID_COUNT); do
        PIC_URL=$(curl -s -X POST "$EZVIZ_BASE/api/lapp/device/capture" \
          -H "Content-Type: application/x-www-form-urlencoded" \
          -d "accessToken=$EZVIZ_TOKEN&deviceSerial=$EZVIZ_SERIAL" 2>/dev/null \
          | python3 -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('picUrl',''))" 2>/dev/null)

        if [ -n "$PIC_URL" ]; then
          CAPTURE_FILE="$EVENT_DIR/capture_${i}.jpg"
          curl -s "$PIC_URL" -o "$CAPTURE_FILE" 2>/dev/null
          CAPTURES="$CAPTURES $CAPTURE_FILE"
          log "抓拍 $i: $(ls -la "$CAPTURE_FILE" 2>/dev/null | awk '{print $5}') bytes"
        fi
        [ "$i" -lt "$RAPID_COUNT" ] && sleep "$RAPID_DELAY"
      done

      # 加上缓存图
      CACHED="$SKILL_DIR/.cache/cat_eye_snapshots/last.jpg"
      [ -f "$CACHED" ] && CAPTURES="$CAPTURES $CACHED"

      # 送AI识别
      RESULT=$(bash "$DETECT_SCRIPT" $CAPTURES 2>/dev/null)
      log "识别结果: $RESULT"
      echo "识别结果: $RESULT" >> "$EVENT_DIR/info.txt"

      # 清理临时文件
      rm -f /tmp/cat_eye_capture_*_$$.jpg

      # 记录事件
      if [ "$RESULT" = "xiaowangzi" ] || [ "$RESULT" = "dad" ] || [ "$RESULT" = "mom" ] || [ "$RESULT" = "aunt" ]; then
        event "进门: $RESULT"
      elif [ "$RESULT" = "stranger" ]; then
        event "进门: 陌生人"
      else
        event "进门: $RESULT"
      fi

    elif [ "$PIR_DIFF" -gt "$EXIT_THRESHOLD" ]; then
      # 出门：PIR触发超过15秒
      log "出门（PIR ${PIR_DIFF}s前，> ${EXIT_THRESHOLD}s）"
      echo "结果: 出门（PIR ${PIR_DIFF}s前）" >> "$EVENT_DIR/info.txt"

      # 连续抓拍5张记录
      for i in $(seq 1 $RAPID_COUNT); do
        PIC_URL=$(curl -s -X POST "$EZVIZ_BASE/api/lapp/device/capture" \
          -H "Content-Type: application/x-www-form-urlencoded" \
          -d "accessToken=$EZVIZ_TOKEN&deviceSerial=$EZVIZ_SERIAL" 2>/dev/null \
          | python3 -c "import sys,json; print(json.load(sys.stdin).get('data',{}).get('picUrl',''))" 2>/dev/null)
        if [ -n "$PIC_URL" ]; then
          curl -s "$PIC_URL" -o "$EVENT_DIR/capture_${i}.jpg" 2>/dev/null
          log "出门抓拍 $i"
        fi
        [ "$i" -lt "$RAPID_COUNT" ] && sleep "$RAPID_DELAY"
      done

      event "出门"
    else
      # PIR在10-15秒之间，不确定
      log "不确定（PIR ${PIR_DIFF}s前）"
      event "门开（PIR ${PIR_DIFF}s前，不确定）"
    fi
  fi

  # 检测关门
  if [ "$STATE" = "off" ] && [ "$LAST_STATE" = "on" ]; then
    EVENT_TIME=$(TZ=Asia/Shanghai date '+%Y%m%d_%H%M%S')
    EVENT_DIR="$SKILL_DIR/.cache/cat_eye_events/${EVENT_TIME}_close"
    mkdir -p "$EVENT_DIR"
    echo "$EVENT_TIME 门关闭" > "$EVENT_DIR/info.txt"
    log "门关闭"
    event "门关闭"
  fi

  LAST_STATE="$STATE"
  sleep "$POLL_INTERVAL"
done
