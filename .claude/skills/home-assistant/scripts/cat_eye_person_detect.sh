#!/bin/bash
# 猫眼人脸识别：多张缓存图 → Qwen-VL 对比参考照片 → 识别是谁 → 更新 HA
# 用法: bash cat_eye_person_detect.sh [图片1] [图片2] ...
#       不传参数则现场抓图
# 依赖: curl, python3, base64
# 照片存放: .cache/faces/*.jpg（文件名即人名）

SKILL_DIR="$(cd "$(dirname "$0")/.." && pwd)"
FACES_DIR="$SKILL_DIR/.cache/faces"
source "$SKILL_DIR/.cache/connection.env"
source /home/zhangyanbo/owner/xiaowangzi/.env
export BAILIAN_BASE_URL BAILIAN_API_KEY

curl -s --connect-timeout 2 -o /dev/null "$HA_URL_LOCAL/api/" 2>/dev/null \
  && HA_URL="$HA_URL_LOCAL" || HA_URL="$HA_URL_REMOTE"

PERSON_TEXT="input_text.mao_yan_shi_bie_jie_guo"
PERSON_BOOL="input_boolean.mao_yan_ren_xing_jian_ce"

# 1. 获取监控画面（参数 > 现场抓）
SNAPSHOTS=()
if [ $# -gt 0 ]; then
  # 使用传入的缓存图片
  for f in "$@"; do
    [ -s "$f" ] && SNAPSHOTS+=("$f")
  done
fi

if [ ${#SNAPSHOTS[@]} -eq 0 ]; then
  # 无参数，现场抓一张
  TMP="$SKILL_DIR/.cache/cat_eye_tmp.jpg"
  curl -s "$HA_URL/api/camera_proxy/camera.ezviz_cat_eye" \
    -H "Authorization: Bearer $HA_TOKEN" -o "$TMP" 2>/dev/null
  [ -s "$TMP" ] && SNAPSHOTS+=("$TMP")
fi

if [ ${#SNAPSHOTS[@]} -eq 0 ]; then
  echo "抓图失败"
  curl -s -X POST "$HA_URL/api/services/input_text/set_value" \
    -H "Authorization: Bearer $HA_TOKEN" -H "Content-Type: application/json" \
    -d "{\"entity_id\": \"$PERSON_TEXT\", \"value\": \"unknown\"}" > /dev/null
  exit 1
fi

# 2. 读取参考照片
PHOTOS=()
NAMES=()
for f in "$FACES_DIR"/*.jpg "$FACES_DIR"/*.png; do
  [ -f "$f" ] || continue
  name=$(basename "$f" | sed 's/\.[^.]*$//')
  PHOTOS+=("$f")
  NAMES+=("$name")
done

if [ ${#PHOTOS[@]} -eq 0 ]; then
  echo "无参考照片"
  exit 1
fi

# 3. Qwen-VL 人脸识别（逐张检查，找到人就返回）
RESULT=$(python3 - <<PY
import os, base64, json, urllib.request, glob, sys

snapshots = """${SNAPSHOTS[*]}""".strip().split()
faces_dir = "$FACES_DIR"
face_photos = sorted(glob.glob(os.path.join(faces_dir, "*.jpg")) + glob.glob(os.path.join(faces_dir, "*.png")))
face_names = [os.path.splitext(os.path.basename(f))[0] for f in face_photos]

# 读取参考照片
ref_images = []
for path, name in zip(face_photos, face_names):
    with open(path, "rb") as f:
        ref_images.append((name, base64.b64encode(f.read()).decode()))

names_str = "、".join(face_names)

# 逐张检查监控画面
for snap_path in snapshots:
    if not os.path.exists(snap_path) or os.path.getsize(snap_path) == 0:
        continue

    with open(snap_path, "rb") as f:
        snap_b64 = base64.b64encode(f.read()).decode()

    content = [{"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{snap_b64}"}}]
    for i, (name, b64) in enumerate(ref_images):
        content.append({"type": "text", "text": f"参考照片{i+1}（{name}）："})
        content.append({"type": "image_url", "image_url": {"url": f"data:image/jpeg;base64,{b64}"}})

    content.append({"type": "text", "text": f"第一张是监控抓拍，后面是参考照片。判断：1. 画面里没有人→回答：无人 2. 有人→看和哪张参考照片是同一人，只回答名字（{names_str}）3. 有人但不认识→回答：陌生人"})

    url = f"{os.environ['BAILIAN_BASE_URL']}/chat/completions"
    data = json.dumps({"model": "qwen-vl-max", "messages": [{"role": "user", "content": content}]}).encode()
    req = urllib.request.Request(url, data=data, headers={
        "Authorization": f"Bearer {os.environ['BAILIAN_API_KEY']}",
        "Content-Type": "application/json"
    })

    try:
        resp = json.load(urllib.request.urlopen(req, timeout=15))
        answer = resp["choices"][0]["message"]["content"].strip()

        if "无人" in answer or "没有" in answer or "没人" in answer:
            continue  # 这张没人，检查下一张

        # 有人，匹配名字
        for name in face_names:
            if name in answer:
                print(name)
                sys.exit(0)

        print("stranger")
        sys.exit(0)
    except:
        continue

# 所有图片都没检测到人
print("nobody")
PY
)

# 4. 更新 HA
echo "识别结果: $RESULT"

curl -s -X POST "$HA_URL/api/services/input_text/set_value" \
  -H "Authorization: Bearer $HA_TOKEN" -H "Content-Type: application/json" \
  -d "{\"entity_id\": \"$PERSON_TEXT\", \"value\": \"$RESULT\"}" > /dev/null

if [ "$RESULT" = "nobody" ] || [ "$RESULT" = "stranger" ] || [ "$RESULT" = "unknown" ]; then
  curl -s -X POST "$HA_URL/api/services/input_boolean/turn_off" \
    -H "Authorization: Bearer $HA_TOKEN" -H "Content-Type: application/json" \
    -d "{\"entity_id\": \"$PERSON_BOOL\"}" > /dev/null
else
  curl -s -X POST "$HA_URL/api/services/input_boolean/turn_on" \
    -H "Authorization: Bearer $HA_TOKEN" -H "Content-Type: application/json" \
    -d "{\"entity_id\": \"$PERSON_BOOL\"}" > /dev/null
fi
