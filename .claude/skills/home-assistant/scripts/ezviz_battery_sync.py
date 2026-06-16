#!/usr/bin/env python3
"""
EZVIZ 猫眼电量同步脚本
- 调用 EZVIZ API 获取猫眼电池电量
- 更新 HA 中的 input_number.mao_yan_dian_liang
- 充电中（设备离线）自动跳过
"""

import requests
import json
import os
import sys
from pathlib import Path

# 配置
EZVIZ_API = "https://open.ys7.com/api/lapp/device/status/get"
EZVIZ_TOKEN = os.environ.get("EZVIZ_ACCESS_TOKEN", "")
EZVIZ_SERIAL = "F66074055"

# 从 .env 读取配置
ENV_FILE = Path(__file__).parent.parent / ".env"

def load_env():
    """从 .env 加载配置"""
    global EZVIZ_TOKEN, EZVIZ_SERIAL
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line.startswith("EZVIZ_ACCESS_TOKEN="):
                EZVIZ_TOKEN = line.split("=", 1)[1]
            elif line.startswith("EZVIZ_SERIAL="):
                EZVIZ_SERIAL = line.split("=", 1)[1]

def get_battery_level():
    """从 EZVIZ API 获取电池电量"""
    if not EZVIZ_TOKEN:
        print("错误: EZVIZ_ACCESS_TOKEN 未配置")
        return None

    try:
        resp = requests.post(
            EZVIZ_API,
            data={"accessToken": EZVIZ_TOKEN, "deviceSerial": EZVIZ_SERIAL},
            timeout=10
        )
        data = resp.json()

        if data.get("code") == "200":
            battery = data["data"].get("battryStatus")
            if battery is not None:
                return int(battery)
            print(f"警告: API 返回中无电量字段: {data['data'].keys()}")
            return None
        else:
            print(f"API 错误: code={data.get('code')}, msg={data.get('msg','')}")
            return None
    except Exception as e:
        print(f"请求失败: {type(e).__name__}: {e}")
        return None

def update_ha_battery(level):
    """更新 HA 中的 input_number"""
    # 从 .env 读取 HA 配置
    ha_url = ""
    ha_token = ""
    if ENV_FILE.exists():
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line.startswith("HA_URL_LOCAL="):
                ha_url = line.split("=", 1)[1]
            elif line.startswith("HA_TOKEN="):
                ha_token = line.split("=", 1)[1]

    if not ha_url or not ha_token:
        print("错误: HA 配置未找到")
        return False

    # 测试本地连接
    try:
        requests.get(f"{ha_url}/api/", timeout=2)
    except:
        # 用远程
        for line in ENV_FILE.read_text().splitlines():
            line = line.strip()
            if line.startswith("HA_URL_REMOTE="):
                ha_url = line.split("=", 1)[1]

    try:
        resp = requests.post(
            f"{ha_url}/api/services/input_number/set_value",
            headers={
                "Authorization": f"Bearer {ha_token}",
                "Content-Type": "application/json"
            },
            json={
                "entity_id": "input_number.mao_yan_dian_liang",
                "value": level
            },
            timeout=10
        )
        if resp.status_code == 200:
            print(f"✓ HA 电量已更新: {level}%")
            return True
        else:
            print(f"HA 更新失败: {resp.status_code} {resp.text[:200]}")
            return False
    except Exception as e:
        print(f"HA 更新失败: {type(e).__name__}: {e}")
        return False

def main():
    load_env()

    # 获取电量
    level = get_battery_level()
    if level is None:
        print("无法获取电量，跳过更新")
        sys.exit(1)

    print(f"猫眼电量: {level}%")

    # 更新 HA
    if update_ha_battery(level):
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
