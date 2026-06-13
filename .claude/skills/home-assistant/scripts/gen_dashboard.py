#!/usr/bin/env python3
# 生成智能家居设备表 HTML
import json

with open('.cache/registry.json') as f:
    r = json.load(f)

total_devices = sum(len(a['devices']) for a in r['areas'].values()) + len(r['unassigned']['devices'])
total_entities = len(r['entity_index'])

domain_colors = {
    'light': '#fbbf24', 'switch': '#10b981', 'climate': '#ef4444',
    'media_player': '#8b5cf6', 'sensor': '#06b6d4', 'cover': '#f97316',
    'vacuum': '#ec4899', 'fan': '#14b8a6', 'button': '#a78bfa',
    'select': '#f472b6', 'number': '#34d399', 'binary_sensor': '#f59e0b',
    'text': '#64748b', 'event': '#6366f1', 'remote': '#8b5cf6',
}

# domain 操作方法映射
domain_ops = {
    'light': 'turn_on / turn_off / toggle',
    'switch': 'turn_on / turn_off / toggle',
    'climate': 'set_temperature / set_hvac_mode',
    'media_player': 'play / pause / volume_set',
    'cover': 'open_cover / close_cover / set_cover_position',
    'vacuum': 'start / pause / return_to_base',
    'fan': 'turn_on / turn_off / set_speed',
    'sensor': '只读',
    'binary_sensor': '只读',
    'button': 'press',
    'select': 'select_option',
    'number': 'set_value',
    'text': 'set_value',
    'event': '只读',
    'remote': 'send_command',
}

areas_html = ''
for area_id, area in sorted(r['areas'].items(), key=lambda x: x[1]['name']):
    devices = area['devices']
    entity_count = sum(len(d['entities']) for d in devices.values())
    domains = set()
    for d in devices.values():
        for e in d['entities'].values():
            domains.add(e['domain'])
    domain_tags = ' '.join(f'<span class="domain-pill" style="background:{domain_colors.get(d,"#666")}20;color:{domain_colors.get(d,"#666")}">{d}</span>' for d in sorted(domains))

    areas_html += f'''
    <div class="area">
      <div class="area-header" onclick="this.parentElement.classList.toggle('collapsed')">
        <div>
          <span class="area-icon">📍</span>
          <span class="area-name">{area["name"]}</span>
          <span class="area-id">({area_id})</span>
        </div>
        <div class="area-right">
          {domain_tags}
          <span class="area-badge">{len(devices)} 设备 / {entity_count} 实体</span>
        </div>
      </div>
      <div class="area-body">'''

    for did, device in sorted(devices.items(), key=lambda x: x[1]['name']):
        areas_html += f'''
        <div class="device">
          <div class="device-header">
            <span class="device-name">{device["name"]}</span>
            <span class="device-model">{device.get("model", "")}</span>
          </div>
          <div class="entities">'''
        for eid, entity in sorted(device['entities'].items(), key=lambda x: x[1]['name']):
            color = domain_colors.get(entity['domain'], '#666')
            op = domain_ops.get(entity['domain'], '')
            areas_html += f'''
            <div class="entity" style="border-left-color:{color}" title="{eid}\n操作: {op}">
              <span class="domain-tag" style="color:{color}">{entity['domain']}</span>
              {entity['name']}
            </div>'''
        areas_html += '</div></div>'

    areas_html += '</div></div>'

html = f'''<!DOCTYPE html>
<html lang="zh-CN">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>智能家居设备表</title>
<style>
@import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@300;400;500;600;700&display=swap');
* {{ margin: 0; padding: 0; box-sizing: border-box; }}
body {{ font-family: 'Noto Sans SC', sans-serif; background: #0f1419; color: #e7e9ea; min-height: 100vh; }}
.header {{ background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%); padding: 40px 32px; border-bottom: 1px solid #2f3336; position: relative; overflow: hidden; }}
.header::before {{ content: ''; position: absolute; top: -50%; left: -50%; width: 200%; height: 200%; background: radial-gradient(circle, rgba(29,155,240,0.1) 0%, transparent 70%); animation: pulse 8s infinite; }}
@keyframes pulse {{ 0%, 100% {{ opacity: 0.5; }} 50% {{ opacity: 1; }} }}
.header h1 {{ font-size: 32px; font-weight: 700; margin-bottom: 12px; position: relative; }}
.header .subtitle {{ color: #71767b; font-size: 14px; margin-bottom: 16px; position: relative; }}
.stats {{ display: flex; gap: 24px; position: relative; flex-wrap: wrap; }}
.stat {{ background: rgba(255,255,255,0.05); padding: 12px 20px; border-radius: 12px; border: 1px solid #2f3336; }}
.stat .label {{ font-size: 12px; color: #71767b; margin-bottom: 4px; }}
.stat .num {{ font-size: 24px; font-weight: 700; color: #1d9bf0; }}
.container {{ max-width: 1400px; margin: 0 auto; padding: 24px; }}
.area {{ margin-bottom: 20px; background: #16181c; border-radius: 16px; overflow: hidden; border: 1px solid #2f3336; transition: all 0.3s; }}
.area:hover {{ border-color: #1d9bf033; }}
.area-header {{ padding: 16px 20px; background: #1d1f23; cursor: pointer; display: flex; justify-content: space-between; align-items: center; transition: background 0.2s; }}
.area-header:hover {{ background: #25272b; }}
.area-icon {{ margin-right: 8px; }}
.area-name {{ font-size: 18px; font-weight: 600; }}
.area-id {{ color: #71767b; font-size: 13px; margin-left: 8px; }}
.area-right {{ display: flex; align-items: center; gap: 8px; flex-wrap: wrap; }}
.domain-pill {{ padding: 2px 8px; border-radius: 8px; font-size: 11px; font-weight: 500; }}
.area-badge {{ background: #1d9bf0; color: white; padding: 4px 12px; border-radius: 12px; font-size: 12px; font-weight: 500; white-space: nowrap; }}
.area-body {{ padding: 16px 20px; }}
.area.collapsed .area-body {{ display: none; }}
.device {{ margin-bottom: 10px; background: #1d1f23; border-radius: 12px; padding: 12px 16px; border: 1px solid #2f3336; transition: all 0.2s; }}
.device:hover {{ border-color: #1d9bf0; transform: translateX(2px); }}
.device-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px; }}
.device-name {{ font-weight: 600; font-size: 14px; }}
.device-model {{ color: #71767b; font-size: 11px; }}
.entities {{ display: flex; flex-wrap: wrap; gap: 6px; }}
.entity {{ background: #25272b; padding: 4px 10px; border-radius: 8px; font-size: 12px; cursor: default; transition: all 0.2s; border-left: 3px solid; white-space: nowrap; }}
.entity:hover {{ background: #2f3336; transform: translateY(-1px); box-shadow: 0 2px 8px rgba(0,0,0,0.3); }}
.domain-tag {{ font-size: 10px; font-weight: 500; margin-right: 4px; }}
</style>
</head>
<body>
<div class="header">
  <h1>🏠 智能家居设备表</h1>
  <div class="subtitle">小王子的家 · 广州南沙</div>
  <div class="stats">
    <div class="stat"><div class="label">扫描时间</div><div class="num" style="font-size:14px">{r['last_scan'][:16].replace('T',' ')}</div></div>
    <div class="stat"><div class="label">区域</div><div class="num">{len(r['areas'])}</div></div>
    <div class="stat"><div class="label">设备</div><div class="num">{total_devices}</div></div>
    <div class="stat"><div class="label">实体</div><div class="num">{total_entities}</div></div>
  </div>
</div>
<div class="container">
{areas_html}
</div>
<script>
// 点击实体显示 entity_id 和操作方法
document.querySelectorAll('.entity').forEach(el => {{
  el.addEventListener('click', function() {{
    const title = this.getAttribute('title');
    if (title) {{
      const [eid, op] = title.split('\\n');
      navigator.clipboard.writeText(eid).then(() => {{
        const orig = this.innerHTML;
        this.innerHTML = '<span style="color:#1d9bf0">✓ 已复制</span> ' + eid;
        setTimeout(() => this.innerHTML = orig, 1500);
      }});
    }}
  }});
}});
</script>
</body>
</html>'''

with open('/home/zhangyanbo/owner/xiaowangzi/projects/privacy-engineering/kb/smart-home-devices.html', 'w') as f:
    f.write(html)

print(f'已生成: kb/smart-home-devices.html')
print(f'区域: {len(r["areas"])}')
print(f'设备: {total_devices}')
print(f'实体: {total_entities}')
