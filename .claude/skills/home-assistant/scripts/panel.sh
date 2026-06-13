#!/bin/bash
# 智能家居控制面板管理脚本
# 用法:
#   bash panel.sh node37   — 在 node37 启动（公司局域网访问）
#   bash panel.sh home     — 在 home-computer 启动（家里局域网访问）
#   bash panel.sh deploy   — 同步文件到 home-computer
#   bash panel.sh stop     — 停止所有面板进程

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
CACHE_DIR="$SKILL_DIR/.cache"
PORT=9124

# home-computer 连接信息（PgyVPN，跨网优先）
HC_SSH="sshpass -p zyb123456 ssh xiaowangzi@172.16.1.183"
HC_SCP="sshpass -p zyb123456 scp"
HC_CACHE="~/ha-skill/.cache"
HC_LAN_IP="192.168.3.67"

# node37 局域网 IP
NODE37_LAN_IP="192.168.68.98"

# 同步文件到 home-computer
deploy() {
  echo "=== 同步文件到 home-computer ==="
  $HC_SSH "mkdir -p $HC_CACHE"
  $HC_SCP "$CACHE_DIR/serve.py" "$CACHE_DIR/ha-control.html" "xiaowangzi@172.16.1.183:$HC_CACHE/"
  # 同步最新 entities_registry.json（如果本地更新过）
  if [ -f "$CACHE_DIR/entities_registry.json" ]; then
    $HC_SCP "$CACHE_DIR/entities_registry.json" "xiaowangzi@172.16.1.183:$HC_CACHE/"
  fi
  echo "✓ 文件已同步"
}

# 在 node37 本机启动（公司局域网访问）
start_node37() {
  echo "=== 在 node37 启动控制面板 ==="
  # 停止已有进程
  pkill -f "python3 serve.py" 2>/dev/null && echo "已停止旧进程"
  sleep 1
  # 启动
  cd "$CACHE_DIR"
  nohup python3 serve.py --port "$PORT" > serve.log 2>&1 &
  sleep 2
  if curl -s --connect-timeout 3 "http://localhost:$PORT/" -o /dev/null; then
    echo "✓ 面板已启动"
    echo "🌐 公司局域网访问: http://${NODE37_LAN_IP}:${PORT}"
  else
    echo "❌ 启动失败，查看日志: $CACHE_DIR/serve.log"
    tail -5 "$CACHE_DIR/serve.log"
  fi
}

# 在 home-computer 启动（家里局域网访问）
start_home() {
  echo "=== 在 home-computer 启动控制面板 ==="
  # 先同步文件
  deploy
  # 停止已有进程并启动
  $HC_SSH "pkill -f 'python3 serve.py' 2>/dev/null; sleep 1; cd $HC_CACHE && nohup python3 serve.py --port $PORT > serve.log 2>&1 & sleep 2 && pgrep -f 'serve.py' > /dev/null && echo ok || echo fail"
  echo "✓ 面板已在 home-computer 启动"
  echo "🌐 家里局域网访问: http://${HC_LAN_IP}:${PORT}"
  echo "🌐 PgyVPN 跨网访问: http://172.16.1.183:${PORT}"
}

# 停止所有
stop_all() {
  echo "=== 停止所有面板进程 ==="
  pkill -f "python3 serve.py" 2>/dev/null && echo "✓ node37 已停止" || echo "node37 无运行中进程"
  $HC_SSH "pkill -f 'python3 serve.py' 2>/dev/null && echo '✓ home-computer 已停止' || echo 'home-computer 无运行中进程'" 2>/dev/null
}

case "${1:-}" in
  node37)  start_node37 ;;
  home)    start_home ;;
  deploy)  deploy ;;
  stop)    stop_all ;;
  *)
    echo "用法: bash panel.sh <命令>"
    echo ""
    echo "命令:"
    echo "  node37  — 在 node37 启动，公司局域网访问 http://${NODE37_LAN_IP}:${PORT}"
    echo "  home    — 在 home-computer 启动，家里局域网访问 http://${HC_LAN_IP}:${PORT}"
    echo "  deploy  — 同步 serve.py / ha-control.html 到 home-computer"
    echo "  stop    — 停止所有面板进程"
    ;;
esac
