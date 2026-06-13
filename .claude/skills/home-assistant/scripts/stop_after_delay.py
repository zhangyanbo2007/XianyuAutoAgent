#!/usr/bin/env python3
"""延时停止音箱播放脚本
用法: python3 stop_after_delay.py <秒数>
功能: 等待音乐开始播放后，指定秒数后通过 HA API 暂停音箱，日志输出北京时间
只用标准库，不依赖 requests
"""

import sys
import time
import json
import urllib.request
from datetime import datetime, timezone, timedelta

BJ_OFFSET = timedelta(hours=8)
SKILL_DIR = "/home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/.claude/skills/home-assistant"
LOG_FILE = f"{SKILL_DIR}/.cache/remind.log"

def bj_now(fmt="%H:%M:%S"):
    """返回北京时间格式化字符串"""
    return (datetime.now(timezone.utc) + BJ_OFFSET).strftime(fmt)

def log(msg):
    """写入日志（北京时间）"""
    with open(LOG_FILE, "a") as f:
        f.write(f"[{bj_now()}] {msg}\n")

def load_ha_config():
    """从 connection.env 加载 HA 配置"""
    config = {}
    with open(f"{SKILL_DIR}/.cache/connection.env") as f:
        for line in f:
            line = line.strip()
            if "=" in line and not line.startswith("#"):
                key, val = line.split("=", 1)
                config[key.strip()] = val.strip()
    return config

def detect_ha_url(config):
    """自动检测本地/远程 HA URL"""
    local = config.get("HA_URL_LOCAL", "")
    try:
        urllib.request.urlopen(f"{local}/api/", timeout=2)
        return local
    except Exception:
        return config.get("HA_URL_REMOTE", "")

def ha_api_get(ha_url, ha_token, path):
    """HA API GET 请求"""
    url = f"{ha_url}{path}"
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {ha_token}"})
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return json.loads(resp.read().decode())
    except Exception:
        return {}

def ha_api_post(ha_url, ha_token, path, data):
    """HA API POST 请求"""
    url = f"{ha_url}{path}"
    body = json.dumps(data).encode()
    req = urllib.request.Request(url, data=body, headers={
        "Authorization": f"Bearer {ha_token}",
        "Content-Type": "application/json"
    })
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            return resp.status == 200
    except Exception:
        return False

def main():
    delay = int(sys.argv[1]) if len(sys.argv) > 1 else 20
    config = load_ha_config()
    ha_url = detect_ha_url(config)
    ha_token = config.get("HA_TOKEN", "")
    entity = "media_player.xiaomi_lx06_46d3_play_control"

    # 等待音乐开始播放
    play_start = None
    for i in range(30):
        time.sleep(1)
        d = ha_api_get(ha_url, ha_token, f"/api/states/{entity}")
        state = d.get("state", "")
        if state == "playing" and play_start is None:
            play_start = time.time()
            log("音乐开始播放")
        if play_start is not None:
            elapsed = int(time.time() - play_start)
            log(f"播放{elapsed}秒: {state}")
            if elapsed >= delay:
                log(f"{delay}秒到，通过 HA API 停止播放")
                ha_api_post(ha_url, ha_token, "/api/services/media_player/media_pause", {"entity_id": entity})
                time.sleep(3)
                d = ha_api_get(ha_url, ha_token, f"/api/states/{entity}")
                log(f"停止后: {d.get('state', '?')}")
                break

if __name__ == "__main__":
    main()