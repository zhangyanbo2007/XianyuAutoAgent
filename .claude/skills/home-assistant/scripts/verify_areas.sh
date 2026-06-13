#!/bin/bash
# 验证设备区域分配
# 用法: bash scripts/verify_areas.sh [domain]
# 示例: bash scripts/verify_areas.sh media_player

SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
CACHE_DIR="$SCRIPT_DIR/../.cache"
REGISTRY="$CACHE_DIR/entities_registry.json"
DOMAIN="${1:-media_player}"

python3 -c "
import json, sys
domain = sys.argv[1]
with open('$REGISTRY') as f:
    r = json.load(f)
found = False
for a in r['areas'].values():
    for d in a['devices'].values():
        for e in d['entities'].values():
            if e['domain'] == domain:
                print(f'{a[\"name\"]:6s} | {d[\"name\"]}')
                found = True
if not found:
    print(f'未找到 domain={domain} 的实体')
" "$DOMAIN"
