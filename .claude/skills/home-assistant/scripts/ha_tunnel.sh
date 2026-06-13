#!/usr/bin/env bash
# HA SSH 透传隧道管理
# 在本机起一条 SSH local-forward：localhost:18123 -> 家里HA(192.168.3.172:8123)
# 经由 home-computer(蒲公英VPN 172.16.1.183) 中转。
#
# 用法:
#   bash ha_tunnel.sh up       # 建立/确保隧道（已通则跳过）
#   bash ha_tunnel.sh status   # 查隧道状态
#   bash ha_tunnel.sh down     # 关闭隧道
#   bash ha_tunnel.sh restart  # 重建

set -uo pipefail

LOCAL_PORT=18123
HA_HOST=192.168.3.172
HA_PORT=8123
JUMP_USER=xiaowangzi
JUMP_HOST=172.16.1.183       # home-computer 蒲公英VPN
JUMP_PASS=zyb123456

probe() {  # 隧道是否可用
  curl -s --max-time 5 -o /dev/null -w '%{http_code}' \
    "http://localhost:${LOCAL_PORT}/api/" 2>/dev/null
}

find_pid() {
  pgrep -f "ssh.*-L ${LOCAL_PORT}:${HA_HOST}:${HA_PORT}" 2>/dev/null
}

up() {
  code=$(probe)
  if [ "$code" = "200" ] || [ "$code" = "401" ]; then
    echo "隧道已通 (localhost:${LOCAL_PORT} -> HA, HTTP ${code})"
    return 0
  fi
  # 清掉残留
  down >/dev/null 2>&1
  echo "建立隧道 localhost:${LOCAL_PORT} -> ${HA_HOST}:${HA_PORT} via ${JUMP_HOST} ..."
  sshpass -p "${JUMP_PASS}" ssh -fN \
    -o StrictHostKeyChecking=no \
    -o ExitOnForwardFailure=yes \
    -o ServerAliveInterval=30 \
    -o ServerAliveCountMax=3 \
    -L "${LOCAL_PORT}:${HA_HOST}:${HA_PORT}" \
    "${JUMP_USER}@${JUMP_HOST}"
  # 等隧道就绪（HA 偶有重启抖动，多试几次）
  for i in $(seq 1 15); do
    code=$(probe)
    if [ "$code" = "200" ] || [ "$code" = "401" ]; then
      echo "隧道已就绪 (HTTP ${code}) pid=$(find_pid)"
      return 0
    fi
    sleep 1
  done
  # SSH 转发进程在且端口在监听 = 隧道本身OK，多半是 HA 在抖
  if [ -n "$(find_pid)" ] && (ss -tln 2>/dev/null | grep -q ":${LOCAL_PORT} "); then
    echo "隧道进程已建立(pid=$(find_pid))，但 HA 探测为 ${code:-000}——多半 HA 正在重启，稍后重试即可" >&2
    return 0
  fi
  echo "隧道建立失败：localhost:${LOCAL_PORT} 仍无响应 (最后 code=${code})" >&2
  return 1
}

down() {
  pid=$(find_pid)
  if [ -n "${pid}" ]; then
    kill ${pid} 2>/dev/null && echo "已关闭隧道 pid=${pid}"
  else
    echo "无运行中的隧道进程"
  fi
}

status() {
  pid=$(find_pid)
  code=$(probe)
  echo "进程: ${pid:-无}"
  echo "探测: localhost:${LOCAL_PORT}/api/ -> HTTP ${code:-000}"
}

case "${1:-up}" in
  up)      up ;;
  down)    down ;;
  status)  status ;;
  restart) down; sleep 1; up ;;
  *) echo "用法: bash ha_tunnel.sh {up|down|status|restart}" >&2; exit 2 ;;
esac
