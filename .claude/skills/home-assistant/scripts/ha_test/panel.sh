#!/bin/bash
# 智能家居控制面板管理脚本
# 用法: bash panel.sh [port]
# 默认端口: 9124

PORT="${1:-9124}"
PANEL_DIR="$(cd "$(dirname "$0")" && pwd)"

# 停止已有面板
pkill -f "python3 -m http.server $PORT" 2>/dev/null && sleep 1

echo "🏠 启动智能家居控制面板"
echo "   地址: http://localhost:$PORT/panel.html"
echo "   按 Ctrl+C 停止"
echo ""

cd "$PANEL_DIR"
python3 -m http.server "$PORT" --bind 0.0.0.0
