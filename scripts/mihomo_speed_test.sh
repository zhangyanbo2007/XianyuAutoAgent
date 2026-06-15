#!/bin/bash
# mihomo 节点延迟测试脚本
# 不切换节点，通过 API 逐个测延迟

AUTH="Bearer Dfsddf898902!./3dfasd0-0234-[]"
API="http://127.0.0.1:9099"

PROXIES=$(curl -s -H "Authorization: $AUTH" "$API/proxies/SELECT" | python3 -c "import sys,json; [print(p) for p in json.load(sys.stdin)['all']]")

echo "开始测试 $(echo "$PROXIES" | wc -l) 个节点延迟..."
echo "-------------------------------------------"
echo "节点 | 延迟(ms) | 状态"
echo "-----|---------|------"

while IFS= read -r proxy; do
    RESULT=$(curl -s --max-time 8 -H "Authorization: $AUTH" "$API/proxies/$proxy/delay?timeout=5000&url=http://www.gstatic.com/generate_204")
    DELAY=$(echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('delay','超时'))" 2>/dev/null)
    if [ "$DELAY" = "超时" ] || [ -z "$DELAY" ]; then
        echo "$proxy | - | ❌ 超时/不可用"
    else
        echo "$proxy | ${DELAY}ms | ✅"
    fi
done <<< "$PROXIES"

echo "-------------------------------------------"
echo "测试完成"
