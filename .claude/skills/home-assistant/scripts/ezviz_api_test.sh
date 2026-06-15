#!/bin/bash
# EZVIZ 萤石云 API 可用性测试
# 用法: bash ezviz_api_test.sh [设备序列号]
# 默认序列号: F66074055（猫眼 DP2C）

source "$(dirname "$0")/../.cache/connection.env"
source /home/zhangyanbo/owner/xiaowangzi/.env

SERIAL="${1:-F66074055}"
TOKEN="$EZVIZ_ACCESS_TOKEN"
BASE="https://open.ys7.com"

echo "=========================================="
echo "  EZVIZ API 可用性测试"
echo "  设备: $SERIAL"
echo "  Token: ${TOKEN:0:20}..."
echo "=========================================="
echo ""

test_api() {
  local method=$1 path=$2 desc=$3 extra=$4
  local url="$BASE/$path"
  local data="accessToken=$TOKEN&deviceSerial=$SERIAL$extra"

  if [ "$method" = "POST" ]; then
    RESULT=$(curl -s -X POST "$url" -H "Content-Type: application/x-www-form-urlencoded" -d "$data" 2>/dev/null)
  else
    RESULT=$(curl -s "$url?$data" 2>/dev/null)
  fi

  CODE=$(echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('code', d.get('status','?')))" 2>/dev/null || echo "?")

  if [ "$CODE" = "200" ]; then
    echo "✅ $desc"
    echo "   $path"
    echo "$RESULT" | python3 -c "
import sys,json
d = json.load(sys.stdin)
data = d.get('data',{})
if isinstance(data, dict):
    for k,v in list(data.items())[:8]:
        val = str(v)[:80]
        print(f'   {k}: {val}')
elif isinstance(data, list) and data:
    print(f'   返回 {len(data)} 条记录')
" 2>/dev/null
  else
    echo "❌ $desc"
    echo "   $path → $CODE"
  fi
  echo ""
}

echo "【设备信息】"
test_api POST "api/lapp/device/list" "设备列表"
test_api POST "api/lapp/device/info" "设备详情"
test_api POST "api/lapp/device/status/get" "设备状态（电量/信号/PIR）"
test_api POST "api/lapp/device/capacity" "设备能力（支持功能）"
test_api POST "api/lapp/device/upgrade/status" "固件升级状态"

echo "【抓拍】"
test_api POST "api/lapp/device/capture" "实时抓拍（返回图片URL）"

echo "=========================================="
echo "  不可用接口（404）"
echo "=========================================="
echo "❌ device/defence/get    — 布防状态查询"
echo "❌ device/alarm/list     — 告警记录"
echo "❌ device/capture/list   — 抓拍列表"
echo "❌ device/snapshot       — 快照"
echo "❌ device/event/list     — 事件列表"
echo "❌ device/wifi           — WiFi 信息"
echo "❌ device/battery/info   — 电池详情"
echo "❌ device/storage/info   — 存储信息"
echo "❌ device/switch/status  — 开关状态"
echo "❌ device/ptz/control    — 云台控制"
echo ""
echo "=========================================="
echo "  有用的字段"
echo "=========================================="
echo "status/get:"
echo "  battryStatus  — 电量百分比"
echo "  signal        — WiFi 信号强度"
echo "  pirStatus     — PIR 状态（-2=不支持）"
echo "  cloudStatus   — 云存储状态"
echo "  diskNum       — 存储卡数量"
echo ""
echo "info:"
echo "  deviceName    — 设备名称"
echo "  model         — 型号"
echo "  signal        — 信号百分比"
echo "  netAddress    — 公网 IP"
echo ""
echo "capacity:"
echo "  support_smart_body_detect — 人形检测"
echo "  support_battery_manage    — 电池管理"
echo "  support_talk              — 对讲"
echo "  support_doorbell_talk     — 门铃对讲"
