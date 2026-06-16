#!/bin/bash
# HA 隧道守护：cron 每分钟调用，确保隧道始终在线

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
TUNNEL_SCRIPT="$SCRIPT_DIR/ha_tunnel.sh"
LOG="$SCRIPT_DIR/../.cache/logs/ha_tunnel_keeper.log"

ts() { TZ=Asia/Shanghai date '+%Y-%m-%d %H:%M:%S'; }

# 检查隧道状态
code=$(curl -s --max-time 5 -o /dev/null -w '%{http_code}' \
  "http://localhost:18123/api/" 2>/dev/null)

if [ "$code" = "200" ] || [ "$code" = "401" ]; then
  # 隧道正常，不输出任何内容（避免 cron 邮件）
  exit 0
fi

# 隧道断了，重建
echo "[$(ts)] 隧道断开(code=$code)，重建中..." >> "$LOG"
bash "$TUNNEL_SCRIPT" up >> "$LOG" 2>&1

# 验证
code2=$(curl -s --max-time 5 -o /dev/null -w '%{http_code}' \
  "http://localhost:18123/api/" 2>/dev/null)
echo "[$(ts)] 重建结果: HTTP $code2" >> "$LOG"
