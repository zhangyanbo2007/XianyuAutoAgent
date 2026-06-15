#!/bin/bash
# mihomo 切换节点脚本
# 用法: ./mihomo_switch.sh "新加坡-IEPL-G1-2"
# 不带参数则显示当前节点和所有可用节点

AUTH="Bearer Dfsddf898902!./3dfasd0-0234-[]"
API="http://127.0.0.1:9099"

# 获取当前节点
CURRENT=$(curl -s -H "Authorization: $AUTH" "$API/proxies/SELECT" | python3 -c "import sys,json; print(json.load(sys.stdin)['now'])")

if [ -z "$1" ]; then
    echo "当前节点: $CURRENT"
    echo ""
    echo "可用节点:"
    curl -s -H "Authorization: $AUTH" "$API/proxies/SELECT" | python3 -c "
import sys,json
data = json.load(sys.stdin)
for p in data['all']:
    marker = ' ← 当前' if p == '$CURRENT' else ''
        print(f'  {p}{marker}')
"
    echo ""
    echo "用法: $0 \"节点名称\""
    exit 0
fi

TARGET="$1"

# 检查节点是否存在
EXISTS=$(curl -s -H "Authorization: $AUTH" "$API/proxies/SELECT" | python3 -c "
import sys,json
data = json.load(sys.stdin)
print('yes' if '$TARGET' in data['all'] else 'no')
")

if [ "$EXISTS" != "yes" ]; then
    echo "❌ 节点 '$TARGET' 不存在"
    echo ""
    echo "可用节点:"
    curl -s -H "Authorization: $AUTH" "$API/proxies/SELECT" | python3 -c "
import sys,json
for p in json.load(sys.stdin)['all']:
    print(f'  {p}')
"
    exit 1
fi

# 切换节点
curl -s -X PUT -H "Authorization: $AUTH" -H "Content-Type: application/json" \
    -d "{\"name\":\"$TARGET\"}" "$API/proxies/SELECT" > /dev/null

echo "✅ 已切换: $CURRENT → $TARGET"
