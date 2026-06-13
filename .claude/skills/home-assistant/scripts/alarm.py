#!/usr/bin/env python3
"""起床闹钟脚本
用法: python3 alarm.py "提醒内容" [音乐关键词]
功能: 主卧音箱播报 + 播放音乐 + 播完自动停止 + 飞书通知
"""
import os, sys, json, time, urllib.request, ssl
from datetime import datetime, timezone, timedelta

SKILL_DIR = "/home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/.claude/skills/home-assistant"
ENV_FILE = os.path.join(SKILL_DIR, ".cache", "connection.env")
FEISHU_ENV = "/home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/.env"
LOG_FILE = os.path.join(SKILL_DIR, ".cache", "remind.log")
BEDROOM_SPEAKER = "media_player.xiaomi_lx06_46d3_play_control"

def load_env(filepath):
    if os.path.exists(filepath):
        with open(filepath) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    k, v = line.split('=', 1)
                    os.environ[k] = v

load_env(ENV_FILE)
load_env(FEISHU_ENV)

HA_TOKEN = os.environ.get('HA_TOKEN', '')
HA_URL_LOCAL = os.environ.get('HA_URL_LOCAL', '')
HA_URL_REMOTE = os.environ.get('HA_URL_REMOTE', '')
FEISHU_APP_ID = os.environ.get('FEISHU_APP_ID', '')
FEISHU_APP_SECRET = os.environ.get('FEISHU_APP_SECRET', '')
FEISHU_USER_OPEN_ID = os.environ.get('FEISHU_USER_OPEN_ID', '')

# 自动检测 URL
def check_url(url):
    try:
        req = urllib.request.Request(f"{url}/api/", method='HEAD')
        urllib.request.urlopen(req, timeout=2, context=ssl.create_default_context())
        return True
    except:
        return False

HA_URL = HA_URL_LOCAL if HA_URL_LOCAL and check_url(HA_URL_LOCAL) else HA_URL_REMOTE

def log(msg):
    bj = datetime.now(timezone(timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S')
    line = f"[{bj}] {msg}"
    print(line)
    with open(LOG_FILE, 'a') as f:
        f.write(line + '\n')

def ha_api(method, path, data=None):
    url = f"{HA_URL}{path}"
    headers = {"Authorization": f"Bearer {HA_TOKEN}", "Content-Type": "application/json"}
    req_data = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=req_data, headers=headers, method=method)
    try:
        resp = urllib.request.urlopen(req, timeout=10, context=ssl.create_default_context())
        return json.loads(resp.read())
    except:
        return None

def get_state(entity_id):
    result = ha_api("GET", f"/api/states/{entity_id}")
    if result:
        return result.get('state', ''), result.get('attributes', {})
    return '', {}

def intelligent_speaker(entity_id, text):
    """通过 intelligent_speaker 发送指令"""
    return ha_api("POST", "/api/services/xiaomi_miot/intelligent_speaker", {
        "entity_id": entity_id, "text": text, "execute": True
    })

def send_tts(entity_id, text):
    """TTS 播报"""
    return ha_api("POST", "/api/services/xiaomi_miot/intelligent_speaker", {
        "entity_id": entity_id, "text": text, "execute": False
    })

def volume_set(entity_id, vol):
    """设音量（触发 HA 刷新）"""
    return ha_api("POST", "/api/services/media_player/volume_set", {
        "entity_id": entity_id, "volume_level": vol
    })

def feishu_notify(msg):
    try:
        data = json.dumps({"app_id": FEISHU_APP_ID, "app_secret": FEISHU_APP_SECRET}).encode()
        req = urllib.request.Request(
            "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal",
            data=data, headers={"Content-Type": "application/json"}
        )
        token = json.loads(urllib.request.urlopen(req, timeout=5, context=ssl.create_default_context()).read()).get('tenant_access_token', '')
        msg_data = json.dumps({
            "receive_id": FEISHU_USER_OPEN_ID, "msg_type": "text",
            "content": json.dumps({"text": f"⏰ {msg}"})
        }).encode()
        req = urllib.request.Request(
            "https://open.feishu.cn/open-apis/im/v1/messages?receive_id_type=open_id",
            data=msg_data, headers={"Authorization": f"Bearer {token}", "Content-Type": "application/json"}
        )
        urllib.request.urlopen(req, timeout=5, context=ssl.create_default_context())
    except:
        pass

# 李健歌曲列表
ALL_SONGS = [
    "李健 传奇", "李健 贝加尔湖畔", "李健 风吹麦浪", "李健 当有天老去",
    "李健 一念一生", "李健 为你而来", "李健 异乡人", "李健 假如爱有天意",
    "李健 一生有你", "李健 爱你"
]

def get_song(alarm_num=1):
    """根据日期+闹钟序号选歌。alarm_num: 1=7:00, 2=7:10, 3=7:20, 4=7:30"""
    bj = datetime.now(timezone(timedelta(hours=8)))
    doy = bj.timetuple().tm_yday
    idx = (alarm_num - 1) % len(ALL_SONGS)
    offset = doy % len(ALL_SONGS)
    return ALL_SONGS[(offset + idx) % len(ALL_SONGS)]

def main():
    msg = sys.argv[1] if len(sys.argv) > 1 else "该起床了"
    alarm_num = int(sys.argv[2]) if len(sys.argv) > 2 else 1
    music = get_song(alarm_num)
    log(f"{msg} 播放{music}")

    # 1. TTS 播报
    send_tts(BEDROOM_SPEAKER, msg)
    time.sleep(3)

    # 2. 播放音乐
    intelligent_speaker(BEDROOM_SPEAKER, f"播放{music}")
    log("发送播放指令")

    # 3. 等待 playing + 监控进度
    play_start = None
    duration = 0
    for i in range(120):
        time.sleep(2)
        # volume_set 触发 HA 刷新
        vol, attrs = get_state(BEDROOM_SPEAKER)
        cur_vol = attrs.get('volume_level', 0.5)
        volume_set(BEDROOM_SPEAKER, cur_vol)
        time.sleep(1)
        # 读最新状态
        state, attrs = get_state(BEDROOM_SPEAKER)
        dur = attrs.get('media_duration', 0)
        pos = attrs.get('media_position', 0)

        if state == 'playing' and play_start is None:
            play_start = time.time()
            duration = dur
            log(f"音乐开始播放, duration={dur}")

        if play_start and dur > 0:
            elapsed = int(time.time() - play_start)
            log(f"播放{elapsed}s: state={state} pos={pos}/{dur}")
            # 到 duration-6 就停
            if pos >= dur - 6 or elapsed >= dur - 3:
                log(f"到停止点, 连续4次发停止")
                for _ in range(4):
                    intelligent_speaker(BEDROOM_SPEAKER, "停止播放")
                    time.sleep(1)
                time.sleep(2)
                state, _ = get_state(BEDROOM_SPEAKER)
                log(f"停止后: {state}")
                break

    # 4. 飞书通知
    feishu_notify(f"{msg} 正在播放{music}")

if __name__ == "__main__":
    main()
