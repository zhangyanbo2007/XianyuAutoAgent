#!/bin/bash
# 通用序列：无论当前状态 → 播指定TTS → 播指定音乐(去引导词) → 本曲放完自动停(不续下一首)
# 用法: play_tts_music_stop.sh <speaker_entity> "<TTS文本>" "<音乐关键词>" [音量0-1]
# 设计依据(记忆 xiaomi-speaker-guide-word-suppression)：
#   - silent:true 静默加载点名歌曲(压引导词)，只加载不起播 → 再 media_play 起播
#   - oh2 切歌慢，silent 后等更久再 media_play
#   - 顺序：volume_set → unmute → media_pause(清残留) → TTS → silent加载 → media_play
#   - media_position 才是"真在放"的可靠依据；到 duration-buffer 或检测到换曲就 pause
set -u
SKILL_DIR="/home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/.claude/skills/home-assistant"
source "$SKILL_DIR/.env"
curl -s --connect-timeout 2 -o /dev/null "$HA_URL_LOCAL/api/" 2>/dev/null \
  && HA_URL="$HA_URL_LOCAL" || HA_URL="$HA_URL_REMOTE"

SPK="$1"; TTS="$2"; MUSIC="$3"; VOL="${4:-0.5}"
case "$SPK" in *oh2*) LOAD_WAIT=10 ;; *) LOAD_WAIT=5 ;; esac

ts() { TZ=Asia/Shanghai date '+%H:%M:%S'; }
log() { echo "[$(ts)] $*"; }

call() { # domain/service json
  curl -s -X POST "$HA_URL/api/services/$1" \
    -H "Authorization: Bearer $HA_TOKEN" -H "Content-Type: application/json" \
    -d "$2" >/dev/null 2>&1
}
# 读音箱属性: 返回 "state|position|duration|title"
read_spk() {
  curl -s "$HA_URL/api/states/$SPK" -H "Authorization: Bearer $HA_TOKEN" 2>/dev/null | python3 -c "
import sys,json
try:
    d=json.load(sys.stdin); a=d.get('attributes',{})
    print(f\"{d.get('state','')}|{a.get('media_position','')}|{a.get('media_duration','')}|{a.get('media_title','')}\")
except: print('|||')
"
}

log "===== 目标音箱: $SPK ====="
log "初始: $(read_spk)"

# 1. 停止播放(和用户手动控制一样) → mute+pause双保险 → 音量
call "xiaomi_miot/intelligent_speaker" "{\"entity_id\":\"$SPK\",\"text\":\"停止播放\",\"execute\":true}"
sleep 3
call "media_player/volume_mute" "{\"entity_id\":\"$SPK\",\"is_volume_muted\":true}"
call "media_player/media_pause" "{\"entity_id\":\"$SPK\"}"
sleep 1
call "media_player/volume_set" "{\"entity_id\":\"$SPK\",\"volume_level\":$VOL}"
log "清场后: $(read_spk)"

# 2. TTS 播报 (execute:false 不触发播放)
log "→ TTS: $TTS"
call "xiaomi_miot/intelligent_speaker" "{\"entity_id\":\"$SPK\",\"text\":\"$TTS\",\"execute\":false}"
sleep 8
log "TTS后: $(read_spk)"

# 3. 静默加载音乐 (去引导词) —— 必须说"播放X的歌"
log "→ 静默加载音乐: 播放${MUSIC}的歌 (silent)"
call "xiaomi_miot/intelligent_speaker" "{\"entity_id\":\"$SPK\",\"text\":\"播放${MUSIC}的歌\",\"execute\":true,\"silent\":true}"
sleep "$LOAD_WAIT"

# 4. 起播
call "media_player/media_play" "{\"entity_id\":\"$SPK\"}"
sleep 4
log "起播后: $(read_spk)"

# 5. 关 repeat 防循环 (best effort)
call "media_player/repeat_set" "{\"entity_id\":\"$SPK\",\"repeat\":\"off\"}"

# 6. 锁定阶段：等 position 真正在增长(真起播我们点的歌)再抓基线
#    —— 云端 title/state 滞后，media_play 后可能先顶着残留旧歌(pos不动)，
#       要等到 pos 连续增长才算锁定，避免把"残留→新歌"误判成"续下一首"
T0=""; D0=""; P_LOCK=0; LOCK_TIME=0; LOCKED=0
prevP=""
LOCK_MAX=20; [ "$SPK" = *"oh2"* ] && LOCK_MAX=35  # oh2 切歌慢，给更长锁定窗口
for i in $(seq 1 $LOCK_MAX); do
  IFS='|' read -r ST P D T <<< "$(read_spk)"
  printf '[%s] lock +%02ds state=%s pos=%s/%s title=%s\n' "$(ts)" "$((i*2))" "$ST" "$P" "$D" "$T"
  if [ -n "$P" ] && [ "$P" != "None" ] && [ -n "$prevP" ] && [ "$prevP" != "None" ] 2>/dev/null; then
    if [ "$P" -gt "$prevP" ] 2>/dev/null; then
      T0="$T"; D0="$D"; P_LOCK="$P"; LOCK_TIME=$(date +%s); LOCKED=1
      log "🔒 锁定本曲: title='$T0' duration=$D0 pos=$P"
      break
    fi
  fi
  prevP="$P"
  sleep 2
done
if [ "$LOCKED" = "0" ]; then
  IFS='|' read -r ST P D0 T0 <<< "$(read_spk)"
  P_LOCK="${P:-0}"; LOCK_TIME=$(date +%s)
  log "⚠️ 未能锁定(position未见增长)，用当前: title='$T0' dur=$D0"
fi
[ "$P_LOCK" = "None" ] && P_LOCK=0

# 7. 监控：云端 pos/title 滞后严重，主用【墙钟计时】，辅以 duration变化/pos回跳兜底
#    锁定时已知本曲 duration=D0、当时 pos=P_LOCK → 还剩 (D0-P_LOCK) 秒结束
#    到点(留 BUF 秒余量)直接 pause，赶在续下一首前停住
BUF=5                       # 距结束多少秒就 pause（云端 pos 滞后偏小→剩余估偏大→留足余量防溜进下一首）
DEFAULT_DUR="${5:-80}"      # 遥测不可信时的兜底播放时长(秒)
LAST_P="$P_LOCK"
HAVE_DUR=0
# 仅当"锁定成功(position 真在推进)且时长有效"才信任 duration，否则用默认时长兜底
if [ "$LOCKED" = "1" ] && [ -n "$D0" ] && [ "$D0" != "None" ] && [ "$D0" -gt 0 ] 2>/dev/null; then
  HAVE_DUR=1
  REMAIN=$(( D0 - P_LOCK - BUF )); [ "$REMAIN" -lt 0 ] && REMAIN=0
  log "✅ 遥测可信: 本曲约还剩 $((D0 - P_LOCK))s → 墙钟 ${REMAIN}s 后停止"
else
  REMAIN=$(( DEFAULT_DUR - BUF )); [ "$REMAIN" -lt 0 ] && REMAIN=0
  log "⚠️ 遥测不可信(position 未推进) → 用默认时长 ${DEFAULT_DUR}s，墙钟 ${REMAIN}s 后停止"
fi
MAXLOOP=$(( (REMAIN / 2) + 15 ))   # 监控轮数随 REMAIN 自适应，加点余量
for i in $(seq 1 $MAXLOOP); do
  sleep 2
  IFS='|' read -r ST P D T <<< "$(read_spk)"
  ELAPSED=$(( $(date +%s) - LOCK_TIME ))
  printf '[%s] +%02ds(墙钟%ss) state=%s pos=%s/%s title=%s\n' "$(ts)" "$((i*2))" "$ELAPSED" "$ST" "$P" "$D" "$T"
  # (主)墙钟到点：本曲该结束了（可信时长 或 默认兜底时长）
  if [ "$ELAPSED" -ge "$REMAIN" ] 2>/dev/null; then
    log "→ 墙钟到点 (已 ${ELAPSED}s ≥ ${REMAIN}s)，停止"; break
  fi
  # (辅)duration 变了 = 换曲了
  if [ "$HAVE_DUR" = "1" ] && [ -n "$D" ] && [ "$D" != "None" ] && [ "$D" -gt 0 ] 2>/dev/null && [ "$D" != "$D0" ]; then
    log "!! duration 变化 ($D0 → $D)，已换曲，停止"; break
  fi
  # (辅)pos 回跳 = 新曲从头
  if [ -n "$P" ] && [ "$P" != "None" ] && [ -n "$LAST_P" ] && [ "$LAST_P" != "None" ] 2>/dev/null; then
    if [ "$P" -lt "$((LAST_P - 5))" ] 2>/dev/null; then
      log "!! position 回跳 ($LAST_P → $P)，已换曲，停止"; break
    fi
  fi
  # (辅)title 变了（最滞后，兜底）
  if [ -n "$T" ] && [ -n "$T0" ] && [ "$T" != "$T0" ]; then
    log "!! title 变化 ($T0 → $T)，已换曲，停止"; break
  fi
  [ -n "$P" ] && [ "$P" != "None" ] && LAST_P="$P"
done

# 7. 停止 (×2 保险)
call "media_player/media_pause" "{\"entity_id\":\"$SPK\"}"
sleep 1
call "media_player/media_pause" "{\"entity_id\":\"$SPK\"}"
sleep 2

# 8. 验证：停止后 5 秒内 position 不再增长 = 真停
IFS='|' read -r ST1 PA D1 T1 <<< "$(read_spk)"
sleep 4
IFS='|' read -r ST2 PB D2 T2 <<< "$(read_spk)"
log "停止后: state=$ST2 pos=$PA→$PB title=$T2"
if [ "$PA" = "$PB" ] || [ "$ST2" != "playing" ]; then
  log "✅ 已停止 (position 不再增长)"
else
  log "⚠️ 可能仍在播放 (position $PA→$PB 仍增长)，需补停"
  call "media_player/media_pause" "{\"entity_id\":\"$SPK\"}"
fi
log "===== 完成: $SPK ====="
