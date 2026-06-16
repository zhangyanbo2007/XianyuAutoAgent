#!/bin/bash
# HA 全量摄入脚本
# 用法: bash ingest.sh [HA_URL] [HA_TOKEN]
# 从 .env 读取默认值，自动检测本地/远程

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
INSTANCE_DIR="$SCRIPT_DIR/../.cache"
REGISTRY="$INSTANCE_DIR/entities_registry.json"
AUTOMATIONS_YAML="$INSTANCE_DIR/automations.yaml"
METHODS_REGISTRY="$INSTANCE_DIR/methods_registry.json"

# 加载连接信息
if [ -f "$SCRIPT_DIR/../.env" ]; then
  source "$SCRIPT_DIR/../.env"
fi

# 自动检测：能直连用 LOCAL，否则用 REMOTE
if [ -z "$1" ]; then
  curl -s --connect-timeout 2 -o /dev/null "${HA_URL_LOCAL}/api/" 2>/dev/null && HA_URL="$HA_URL_LOCAL" || HA_URL="$HA_URL_REMOTE"
  echo "Auto-detected: $HA_URL"
else
  HA_URL="$1"
fi

HA_TOKEN="${2:-$HA_TOKEN}"

if [ -z "$HA_URL" ] || [ -z "$HA_TOKEN" ]; then
  echo "ERROR: HA_URL and HA_TOKEN required"
  echo "Usage: bash ingest.sh [HA_URL] [HA_TOKEN]"
  echo "Or set them in .env"
  exit 1
fi

echo "=== HA 全量摄入 ==="
echo "HA: $HA_URL"

# 生成 Python 脚本并执行
python3 << PYEOF
import json, asyncio, urllib.request, ssl, sys

URL = "${HA_URL}"
TOKEN = "${HA_TOKEN}"
OUTPUT = "${REGISTRY}"

try:
    import websockets
except ImportError:
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "websockets", "-q"])
    import websockets

async def ingest():
    # 先用 REST API 验证连接
    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE
    req = urllib.request.Request(f"{URL}/api/config", headers={"Authorization": f"Bearer {TOKEN}"})
    config = json.loads(urllib.request.urlopen(req, context=ctx).read())
    print(f"HA Version: {config.get('version', '?')}")

    async with websockets.connect(f"ws://{URL.replace('http://','').replace('https://','')}/api/websocket", max_size=2**24) as ws:
        msg = json.loads(await ws.recv())
        await ws.send(json.dumps({"type": "auth", "access_token": TOKEN}))
        msg = json.loads(await ws.recv())
        if msg.get("type") != "auth_ok":
            print("AUTH FAILED")
            return

        # areas
        await ws.send(json.dumps({"id": 1, "type": "config/area_registry/list"}))
        msg = json.loads(await ws.recv())
        areas_raw = msg.get("result", [])
        areas = {a["area_id"]: a["name"] for a in areas_raw}
        print(f"Areas: {len(areas)}")

        # devices
        await ws.send(json.dumps({"id": 2, "type": "config/device_registry/list"}))
        msg = json.loads(await ws.recv())
        devices = msg.get("result", [])
        print(f"Devices: {len(devices)}")

        # entities
        await ws.send(json.dumps({"id": 3, "type": "config/entity_registry/list"}))
        msg = json.loads(await ws.recv())
        entities = msg.get("result", [])
        print(f"Entities: {len(entities)}")

    # build registry
    device_map = {d["id"]: d for d in devices}
    registry = {
        "last_scan": __import__("datetime").datetime.now().strftime("%Y-%m-%dT%H:%M:%S"),
        "ha_version": config.get("version", ""),
        "areas": {},
        "unassigned": {"devices": {}},
        "entity_index": {}
    }

    for e in entities:
        eid = e.get("entity_id", "")
        did = e.get("device_id")
        if not did or did not in device_map:
            continue
        device = device_map[did]
        area_id = device.get("area_id")
        area_name = areas.get(area_id, "未分配") if area_id else "未分配"
        area_key = area_id if area_id else "unassigned"
        device_name = device.get("name_by_user") or device.get("name", "未知设备")
        device_model = device.get("model", "")
        domain = eid.split(".")[0] if "." in eid else ""
        friendly = e.get("original_name") or e.get("name") or eid

        if area_key not in registry["areas"] and area_key != "unassigned":
            registry["areas"][area_key] = {"name": area_name, "devices": {}}
        target = registry["areas"].get(area_key, registry["unassigned"])
        if did not in target["devices"]:
            target["devices"][did] = {"name": device_name, "model": device_model, "entities": {}}
        target["devices"][did]["entities"][eid] = {"domain": domain, "name": friendly}

        registry["entity_index"][eid] = {"area": area_key, "device": did, "domain": domain}

    # 统计
    total_devices = sum(len(a["devices"]) for a in registry["areas"].values()) + len(registry["unassigned"]["devices"])
    total_entities = len(registry["entity_index"])
    print(f"Registry: {len(registry['areas'])} areas, {total_devices} devices, {total_entities} entities")

    with open(OUTPUT, "w") as f:
        json.dump(registry, f, ensure_ascii=False, indent=2)
    print(f"Saved: {OUTPUT}")

asyncio.run(ingest())
PYEOF

echo "=== 设备扫描完成 ==="
echo ""

# === 自动化 YAML 扫描 ===
echo "=== HA 自动化扫描 ==="
python3 -c "
import json, urllib.request, ssl, datetime, sys

ha_url = sys.argv[1]
ha_token = sys.argv[2]
output = sys.argv[3]

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

# 获取所有自动化状态
req = urllib.request.Request(f'{ha_url}/api/states', headers={'Authorization': f'Bearer {ha_token}'})
data = json.loads(urllib.request.urlopen(req, context=ctx).read())
automations = [e for e in data if e['entity_id'].startswith('automation.')]

lines = []
lines.append('# ============================================================')
lines.append(f'# 全部自动化配置（共{len(automations)}个）')
lines.append(f'# 生成时间: {datetime.datetime.now().strftime(\"%Y-%m-%dT%H:%M:%S\")}')
lines.append('# 由 ingest.sh 从 HA API 自动生成')
lines.append('# 注意：HA 的 event 实体触发事件类型是 state_changed，不是情景触发N')
lines.append('# ============================================================')
lines.append('')
lines.append('automation:')

def write_trigger(lines, trigger, indent=6):
    prefix = ' ' * indent
    platform = trigger.get('platform', trigger.get('trigger', 'event'))
    if platform == 'time' or trigger.get('trigger') == 'time':
        lines.append(f'{prefix}- platform: time')
        lines.append(f'{prefix}  at: \"{trigger.get(\"at\", \"\")}\"')
    elif platform == 'state':
        lines.append(f'{prefix}- platform: state')
        lines.append(f'{prefix}  entity_id: {trigger.get(\"entity_id\", \"\")}')
        if trigger.get('to'):
            lines.append(f'{prefix}  to: \"{trigger[\"to\"]}\"')
        if trigger.get('from'):
            lines.append(f'{prefix}  from: \"{trigger[\"from\"]}\"')
    elif platform == 'event':
        lines.append(f'{prefix}- platform: event')
        lines.append(f'{prefix}  event_type: {trigger.get(\"event_type\", \"\")}')
        ed = trigger.get('event_data', {})
        if ed:
            lines.append(f'{prefix}  event_data:')
            for k, v in ed.items():
                lines.append(f'{prefix}    {k}: \"{v}\"')
    else:
        lines.append(f'{prefix}- platform: {platform}')
        for k, v in trigger.items():
            if k not in ('platform', 'trigger'):
                lines.append(f'{prefix}  {k}: \"{v}\"')

def write_action(lines, action, indent=6):
    prefix = ' ' * indent
    if 'choose' in action:
        lines.append(f'{prefix}- choose:')
        for choice in action['choose']:
            conds = choice.get('conditions', [])
            seq = choice.get('sequence', [])
            lines.append(f'{prefix}    - conditions:')
            for c in conds:
                lines.append(f'{prefix}        - condition: {c.get(\"condition\",\"\")}')
                if 'entity_id' in c:
                    lines.append(f'{prefix}          entity_id: {c[\"entity_id\"]}')
                if 'state' in c:
                    lines.append(f'{prefix}          state: \"{c[\"state\"]}\"')
                if 'from' in c:
                    lines.append(f'{prefix}          from: \"{c[\"from\"]}\"')
            lines.append(f'{prefix}      sequence:')
            for s in seq:
                write_action(lines, s, indent+10)
        lines.append(f'{prefix}    default: []')
    elif 'wait_for_trigger' in action:
        lines.append(f'{prefix}- wait_for_trigger:')
        for wt in action['wait_for_trigger']:
            write_trigger(lines, wt, indent+4)
        timeout = action.get('timeout', {})
        if timeout:
            lines.append(f'{prefix}  timeout:')
            lines.append(f'{prefix}    seconds: {timeout.get(\"seconds\",30)}')
        lines.append(f'{prefix}  continue_on_timeout: {str(action.get(\"continue_on_timeout\",False)).lower()}')
    elif 'delay' in action:
        delay = action['delay']
        if isinstance(delay, dict):
            lines.append(f'{prefix}- delay:')
            for k, v in delay.items():
                lines.append(f'{prefix}    {k}: {v}')
        else:
            lines.append(f'{prefix}- delay: {delay}')
    elif 'service' in action or 'action' in action:
        svc = action.get('service', action.get('action', ''))
        target = action.get('target', {})
        lines.append(f'{prefix}- service: {svc}')
        if target:
            lines.append(f'{prefix}  target:')
            for k, v in target.items():
                lines.append(f'{prefix}    {k}: \"{v}\"')
    else:
        lines.append(f'{prefix}# {json.dumps(action, ensure_ascii=False)[:200]}')

for a in sorted(automations, key=lambda x: x['entity_id']):
    eid = a['entity_id']
    auto_id = a['attributes'].get('id', '')
    name = a['attributes'].get('friendly_name', eid)

    config = {}
    try:
        req2 = urllib.request.Request(
            f'{ha_url}/api/config/automation/config/{auto_id}',
            headers={'Authorization': f'Bearer {ha_token}'}
        )
        resp = urllib.request.urlopen(req2, context=ctx)
        config = json.loads(resp.read())
    except:
        pass

    lines.append(f'  - alias: \"{name}\"')
    lines.append(f'    id: \"{auto_id}\"')

    lines.append('    trigger:')
    for t in config.get('triggers', []):
        write_trigger(lines, t, indent=6)

    lines.append('    condition: []')

    lines.append('    action:')
    for action in config.get('actions', []):
        write_action(lines, action, indent=6)

    lines.append('    mode: single')
    lines.append('')

with open(output, 'w') as f:
    f.write('\n'.join(lines))
print(f'Automations: {len(automations)} saved to {output}')
" "$HA_URL" "$HA_TOKEN" "$AUTOMATIONS_YAML"

echo "=== 自动化 YAML 生成完成 ==="
echo ""

# === 方法注册表扫描 ===
echo "=== HA 服务方法扫描 ==="
python3 -c "
import json, urllib.request, ssl, sys

ha_url = sys.argv[1]
ha_token = sys.argv[2]
output = sys.argv[3]

ctx = ssl.create_default_context()
ctx.check_hostname = False
ctx.verify_mode = ssl.CERT_NONE

req = urllib.request.Request(f'{ha_url}/api/services', headers={'Authorization': f'Bearer {ha_token}'})
services_data = json.loads(urllib.request.urlopen(req, context=ctx).read())

ACTIONABLE_DOMAINS = {
    'light', 'media_player', 'climate', 'vacuum', 'fan', 'cover',
    'switch', 'text', 'button', 'tts', 'lock', 'alarm_control_panel',
    'humidifier', 'remote', 'select', 'number', 'scene', 'script'
}

def extract_param_info(field_def):
    selector = field_def.get('selector', {})
    info = {
        'type': 'string',
        'required': field_def.get('required', False),
        'description': field_def.get('description', '')
    }
    if 'number' in selector:
        ns = selector['number']
        info['type'] = 'number'
        info['range'] = [ns.get('min'), ns.get('max')]
        info['unit'] = ns.get('unit_of_measurement', '')
    elif 'boolean' in selector:
        info['type'] = 'boolean'
    elif 'color_rgb' in selector:
        info['type'] = '[int,int,int]'
    elif 'color_temp' in selector:
        ct = selector['color_temp']
        info['type'] = 'integer'
        info['range'] = [ct.get('min'), ct.get('max')]
        info['unit'] = ct.get('unit', 'mired')
    elif 'entity' in selector:
        info['type'] = 'entity_id'
    elif 'select' in selector:
        info['type'] = 'string'
        info['options'] = selector['select'].get('options', [])
    return info

registry = {
    '\$schema_version': '1.0.0',
    '_description': 'API 控制方法注册表。由 ingest.sh 从 HA services API 自动生成。特殊操作备注见 SKILL.md。',
    'domains': {},
    'cross_domain': {
        'conversation_process': {
            'description': '自然语言兜底 — 向 HA 对话代理发送中文指令',
            'http_method': 'POST',
            'url': '/api/conversation/process',
            'required_params': {
                'text': {'type': 'string', 'description': '中文自然语言指令'}
            },
            'notes': ['小米设备首选控制方式', '标准 API 返回成功但设备无响应时用此方法重试'],
            'curl_template': 'curl -s -X POST \"\$HA_URL/api/conversation/process\" -H \"Authorization: Bearer \$HA_TOKEN\" -H \"Content-Type: application/json\" -d \\'\\'{\"text\": \"{指令}\"}\\'\\''
        },
        'xiaomi_miot_intelligent_speaker': {
            'description': '小米 MIoT 智能音箱 TTS 和语音指令',
            'http_method': 'POST',
            'url': '/api/services/xiaomi_miot/intelligent_speaker',
            'required_params': {
                'entity_id': {'type': 'entity_id', 'description': '小米音箱 media_player 实体 ID'},
                'text': {'type': 'string', 'description': 'TTS 文本或指令'}
            },
            'optional_params': {
                'execute': {'type': 'boolean', 'default': False, 'description': 'true=执行指令，false=TTS 播报'}
            },
            'notes': ['前置: 先取消静音 volume_mute: false', '多音箱必须顺序执行间隔1秒'],
            'curl_template': 'curl -s -X POST \"\$HA_URL/api/services/xiaomi_miot/intelligent_speaker\" -H \"Authorization: Bearer \$HA_TOKEN\" -H \"Content-Type: application/json\" -d \\'\\'{\"entity_id\": \"{id}\", \"text\": \"{text}\", \"execute\": false}\\'\\''
        }
    }
}

for domain_data in services_data:
    domain = domain_data['domain']
    if domain not in ACTIONABLE_DOMAINS:
        continue

    services = domain_data['services']
    domain_entry = {
        '_description': f'{domain} 控制',
        'entity_pattern': f\"entity_id 以 '{domain}.' 开头\",
        'services': {}
    }

    for svc_name, svc_def in services.items():
        target = svc_def.get('target', {})
        fields = svc_def.get('fields', {})

        required_params = {}
        optional_params = {}
        for fname, fdef in fields.items():
            if fname == 'advanced_fields':
                continue
            param_info = extract_param_info(fdef)
            if fdef.get('required', False):
                required_params[fname] = param_info
            else:
                optional_params[fname] = param_info

        if target.get('entity'):
            required_params['entity_id'] = {
                'type': 'entity_id',
                'description': f'{domain} 实体 ID'
            }

        curl_body = '{\"entity_id\": \"{entity_id}\"'
        for pname in optional_params:
            curl_body += f', \"{pname}\": {{{pname}}}'
        curl_body += '}'

        curl_template = (
            f'curl -s -X POST \"\$HA_URL/api/services/{domain}/{svc_name}\" '
            f'-H \"Authorization: Bearer \$HA_TOKEN\" -H \"Content-Type: application/json\" '
            f'-d \'{curl_body}\''
        )

        domain_entry['services'][svc_name] = {
            'description': svc_def.get('description', ''),
            'http_method': 'POST',
            'url': f'/api/services/{domain}/{svc_name}',
            'required_params': required_params,
            'optional_params': optional_params,
            'notes': [],
            'curl_template': curl_template
        }

    registry['domains'][domain] = domain_entry

print(f'Auto-generated: {len(registry[\"domains\"])} domains')

with open(output, 'w') as f:
    json.dump(registry, f, ensure_ascii=False, indent=2)
print(f'Saved: {output}')
" "$HA_URL" "$HA_TOKEN" "$METHODS_REGISTRY"

echo "=== 方法注册表扫描完成 ==="

# === 验证：检查音箱区域分配 ===
echo ""
echo "=== 音箱区域验证 ==="
python3 -c "
import json
with open('$REGISTRY') as f:
    r = json.load(f)
for a in r['areas'].values():
    for d in a['devices'].values():
        for e in d['entities'].values():
            if e['domain'] == 'media_player':
                print(f'{a[\"name\"]:6s} | {d[\"name\"]}')"
