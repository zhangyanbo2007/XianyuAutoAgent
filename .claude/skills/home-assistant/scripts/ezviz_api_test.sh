#!/bin/bash
# 摄像头 API 可用性测试（HA + 萤石云）
# 用法: bash ezviz_api_test.sh [设备序列号]
# 默认序列号: F66074055（猫眼 DP2C）

source "$(dirname "$0")/../.env"
source /home/zhangyanbo/owner/xiaowangzi/.env

SERIAL="${1:-F66074055}"
TOKEN="$EZVIZ_ACCESS_TOKEN"
EZVIZ_BASE="https://open.ys7.com"
HA_URL="${HA_URL_REMOTE:-http://localhost:18123}"
HA_TOKEN_VAL="$HA_TOKEN"
CAMERA_ENTITY="camera.ezviz_cat_eye"

echo "=========================================="
echo "  摄像头 API 可用性测试"
echo "  设备: $SERIAL"
echo "=========================================="
echo ""

# ==========================================
# 1. HA Camera（萤石云猫眼）
# ==========================================
echo "【1】HA Camera（萤石云猫眼）"
echo "------------------------------------------"

HA_OK=false
code=$(curl -s --max-time 3 -o /dev/null -w "%{http_code}" "$HA_URL/api/" \
  -H "Authorization: Bearer $HA_TOKEN_VAL" 2>/dev/null)

if [ "$code" = "200" ] || [ "$code" = "401" ]; then
  HA_OK=true
  echo "✅ HA 连接成功 ($HA_URL)"
  echo ""

  HA_STATE=$(curl -s --max-time 3 "$HA_URL/api/states/$CAMERA_ENTITY" \
    -H "Authorization: Bearer $HA_TOKEN_VAL" 2>/dev/null)

  if echo "$HA_STATE" | python3 -c "import sys,json; json.load(sys.stdin)" 2>/dev/null; then
    echo "  实体属性:"
    echo "$HA_STATE" | python3 -c "
import sys, json
d = json.load(sys.stdin)
attrs = d.get('attributes', {})
print(f'    entity_id:        {d.get(\"entity_id\")}')
print(f'    state:            {d.get(\"state\")}')
print(f'    friendly_name:    {attrs.get(\"friendly_name\")}')
print(f'    supported_features: {attrs.get(\"supported_features\")}')
print(f'    access_token:     {attrs.get(\"access_token\", \"\")[:20]}...')
" 2>/dev/null

    echo ""
    echo "  REST API（获取图片）:"
    echo "    GET /api/camera_proxy/<entity_id>         — 获取当前缓存图片"
    echo "    GET /api/camera_proxy/<entity_id>/<ts>    — 获取指定时间点图片"
    echo ""

    echo "  可用服务:"
    echo "    camera.snapshot                        — 保存快照到指定路径"
    echo "    camera.play_stream                     — 播放视频流"
    echo "    camera.record                          — 录像"
    echo "    camera.turn_on                         — 开启摄像头"
    echo "    camera.turn_off                        — 关闭摄像头"
    echo "    camera.enable_motion_detection         — 启用运动检测"
    echo "    camera.disable_motion_detection        — 禁用运动检测"
    echo ""

    echo "  用法示例:"
    echo "    # 获取缓存图片"
    echo "    curl \"$HA_URL/api/camera_proxy/$CAMERA_ENTITY\" \\"
    echo "      -H \"Authorization: Bearer $HA_TOKEN_VAL\" -o snapshot.jpg"
    echo ""
    echo "    # 保存快照"
    echo "    curl -X POST \"$HA_URL/api/services/camera/snapshot\" \\"
    echo "      -H \"Authorization: Bearer $HA_TOKEN_VAL\" \\"
    echo "      -H \"Content-Type: application/json\" \\"
    echo "      -d '{\"entity_id\": \"$CAMERA_ENTITY\", \"filename\": \"/tmp/snap.jpg\"}'"
  else
    echo "❌ 实体 $CAMERA_ENTITY 不存在"
  fi
else
  echo "❌ HA 连接失败 ($HA_URL) → HTTP $code"
  echo "   需要先建立隧道: bash ha_tunnel.sh up"
fi
echo ""

# ==========================================
# 2. 萤石云 API（设备控制）
# ==========================================
echo "【2】萤石云 API（设备控制）"
echo "------------------------------------------"
echo "  设备: $SERIAL"
echo "  Token: ${TOKEN:0:20}..."
echo ""

test_ezviz() {
  local method=$1 path=$2 desc=$3 extra=$4
  local url="$EZVIZ_BASE/$path"
  local data="accessToken=$TOKEN&deviceSerial=$SERIAL$extra"

  if [ "$method" = "POST" ]; then
    RESULT=$(curl -s -X POST "$url" -H "Content-Type: application/x-www-form-urlencoded" -d "$data" 2>/dev/null)
  else
    RESULT=$(curl -s "$url?$data" 2>/dev/null)
  fi

  CODE=$(echo "$RESULT" | python3 -c "import sys,json; d=json.load(sys.stdin); print(d.get('code', d.get('status','?')))" 2>/dev/null || echo "?")

  if [ "$CODE" = "200" ]; then
    echo "  ✅ $desc"
    echo "     $path"
    echo "$RESULT" | python3 -c "
import sys,json
d = json.load(sys.stdin)
data = d.get('data',{})
if isinstance(data, dict):
    for k,v in list(data.items())[:8]:
        val = str(v)[:80]
        print(f'     {k}: {val}')
elif isinstance(data, list) and data:
    print(f'     返回 {len(data)} 条记录')
" 2>/dev/null
  else
    echo "  ❌ $desc"
    echo "     $path → $CODE"
  fi
  echo ""
}

echo "  可用接口:"
test_ezviz POST "api/lapp/device/list" "设备列表"
test_ezviz POST "api/lapp/device/info" "设备详情"
test_ezviz POST "api/lapp/device/status/get" "设备状态（电量/信号/PIR）"
test_ezviz POST "api/lapp/device/capacity" "设备能力（支持功能）"
test_ezviz POST "api/lapp/device/upgrade/status" "固件升级状态"
test_ezviz POST "api/lapp/device/capture" "实时抓拍（返回图片URL）"

echo "  不可用接口（404）:"
echo "    device/defence/get    — 布防状态查询"
echo "    device/alarm/list     — 告警记录"
echo "    device/capture/list   — 抓拍列表"
echo "    device/snapshot       — 快照"
echo "    device/event/list     — 事件列表"
echo "    device/wifi           — WiFi 信息"
echo "    device/battery/info   — 电池详情"
echo "    device/storage/info   — 存储信息"
echo "    device/switch/status  — 开关状态"
echo "    device/ptz/control    — 云台控制"
echo ""

echo "  关键字段:"
echo "    status/get: battryStatus(电量) signal(WiFi) pirStatus(PIR) cloudStatus diskNum"
echo "    info:       deviceName model signal netAddress(公网IP)"
echo "    capacity:   support_smart_body_detect support_battery_manage support_talk"
