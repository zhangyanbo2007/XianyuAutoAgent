#!/usr/bin/env python3
"""
Linux 端后处理：WXGF→JPG + SILK→WAV + OSS→ASR→voice2txt + 清理 + 更新 chat.json
用法: .venv/bin/python3.11 scripts/post_process.py <contact_dir>
"""
import os, sys, json, time, tempfile, subprocess, urllib.request, struct

FFMPEG = "/home/zhangyanbo/owner/xiaowangzi/.venv/lib/python3.11/site-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"

# 加载配置（同目录 wechat-config.json）
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
with open(os.path.join(_SCRIPT_DIR, "wechat-config.json")) as _f:
    _CFG = json.load(_f)
API_KEY = _CFG["api_key"]
ASR_URL = _CFG["asr_url"]
OSS_CFG = _CFG["oss"]

def upload_oss(local_path):
    import oss2
    auth = oss2.Auth(OSS_CFG['access_key_id'], OSS_CFG['access_key_secret'])
    bucket = oss2.Bucket(auth, OSS_CFG['endpoint'], OSS_CFG['bucket'])
    from datetime import datetime
    key = f"voice/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.path.basename(local_path)}"
    bucket.put_object_from_file(key, local_path,
        headers={'Content-Type': 'audio/wav', 'x-oss-object-acl': 'public-read'})
    return f"https://{OSS_CFG['bucket']}.{OSS_CFG['endpoint']}/{key}"

def transcribe(wav_path):
    oss_url = upload_oss(wav_path)
    payload = json.dumps({
        "model": "qwen3-asr-flash",
        "messages": [{"role": "user", "content": [
            {"type": "input_audio", "input_audio": {"data": oss_url, "format": "wav"}}
        ]}]
    }).encode()
    req = urllib.request.Request(ASR_URL, data=payload, headers={
        "Authorization": f"Bearer {API_KEY}", "Content-Type": "application/json"})
    resp = urllib.request.urlopen(req, timeout=60)
    result = json.loads(resp.read())
    return result.get("choices", [{}])[0].get("message", {}).get("content", "").strip() or "[silence]"

# ─── WXGF → JPG ───
def convert_wxgf(image_dir):
    """Convert all .wxgf files to .jpg, delete originals."""
    print("Converting WXGF → JPG...")
    converted = 0
    for fn in sorted(os.listdir(image_dir)):
        if not fn.endswith('.wxgf'): continue
        fp = os.path.join(image_dir, fn)
        data = open(fp, 'rb').read()
        # Find H.265 VPS NAL (type 32)
        hevc_start = None
        for i in range(len(data) - 4):
            if data[i:i+4] == b'\x00\x00\x00\x01' and ((data[i+4] >> 1) & 0x3f) == 32:
                hevc_start = i
                break
        if hevc_start is None:
            print(f"  SKIP {fn}: no HEVC data")
            continue
        hevc_tmp = tempfile.mktemp(suffix='.hevc')
        jpg_path = fp.replace('.wxgf', '.jpg')
        with open(hevc_tmp, 'wb') as f: f.write(data[hevc_start:])
        try:
            subprocess.run([FFMPEG, '-y', '-f', 'hevc', '-i', hevc_tmp,
                          '-q:v', '2', jpg_path], capture_output=True, timeout=30)
            if os.path.exists(jpg_path) and os.path.getsize(jpg_path) > 0:
                os.remove(fp)
                converted += 1
                print(f"  [{converted}] {fn} → {os.path.basename(jpg_path)} ({os.path.getsize(jpg_path)/1024:.0f}KB)")
        except Exception as e:
            print(f"  FAIL {fn}: {e}")
        finally:
            if os.path.exists(hevc_tmp): os.remove(hevc_tmp)
    print(f"  Converted: {converted}")
    return converted

# ─── SILK → WAV + ASR ───
def process_voice(contact_dir):
    """Convert SILK→WAV, upload OSS, ASR, update chat.json, delete .silk"""
    voice_dir = os.path.join(contact_dir, 'voice')
    txt_dir = os.path.join(contact_dir, 'voice2txt')
    chat_json = get_chat_json(contact_dir)
    if not os.path.exists(voice_dir): return 0

    silk_files = sorted([f for f in os.listdir(voice_dir) if f.endswith('.silk')])
    if not silk_files:
        print("No SILK files to process")
        return 0

    os.makedirs(txt_dir, exist_ok=True)
    print(f"\nProcessing {len(silk_files)} voice files...")

    with open(chat_json) as f: msgs = json.load(f)
    updated = 0

    for i, silk_fn in enumerate(silk_files):
        txt_fn = silk_fn.replace('.silk', '.txt')
        txt_path = os.path.join(txt_dir, txt_fn)
        wav_fn = silk_fn.replace('.silk', '.wav')
        wav_path = os.path.join(voice_dir, wav_fn)
        silk_path = os.path.join(voice_dir, silk_fn)

        # Skip if already done
        if os.path.exists(txt_path) and os.path.exists(wav_path):
            with open(txt_path) as f: text = f.read().strip()
            if text and text not in ('[silence]', '[error]'):
                # Update chat.json references anyway
                for msg in msgs:
                    if msg.get('media_file') == f"voice/{silk_fn}":
                        msg['content'] = f"[voice: voice/{wav_fn}]"
                        msg['voice_wav'] = f"voice/{wav_fn}"
                        msg['voice_txt'] = f"voice2txt/{txt_fn}"
                        msg.pop('media_file', None)
                        msg.pop('media_format', None)
                # Still need to delete silk
                if os.path.exists(silk_path): os.remove(silk_path)
                continue

        # Step 1: SILK → WAV
        with open(silk_path, 'rb') as f: data = f.read()
        if data[:1] == b'\x02': data = data[1:]
        if not data.startswith(b'#!SILK_V3'):
            print(f"  [{i+1}] SKIP {silk_fn}: not SILK_V3")
            continue
        if not data.endswith(b'\xff\xff'): data += b'\xff\xff'

        silk_tmp = tempfile.mktemp(suffix='.silk')
        pcm_tmp = tempfile.mktemp(suffix='.pcm')
        try:
            with open(silk_tmp, 'wb') as f: f.write(data)
            import pilk
            pilk.decode(silk_tmp, pcm_tmp)
            subprocess.run([FFMPEG, '-y', '-f', 's16le', '-ar', '24000', '-ac', '1',
                          '-i', pcm_tmp, wav_path], capture_output=True)
        finally:
            if os.path.exists(silk_tmp): os.remove(silk_tmp)
            if os.path.exists(pcm_tmp): os.remove(pcm_tmp)

        if not os.path.exists(wav_path):
            print(f"  [{i+1}] FAIL decode {silk_fn}")
            continue

        # Step 2: ASR
        print(f"  [{i+1}/{len(silk_files)}] {silk_fn} ({os.path.getsize(wav_path)/1024:.0f}KB)...", end=' ', flush=True)
        try:
            text = transcribe(wav_path)
            print(f'"{text[:60]}"')
        except Exception as e:
            text = f"[error: {e}]"
            print(f'ERROR: {e}')

        with open(txt_path, 'w', encoding='utf-8') as f: f.write(text)

        # Step 3: Update chat.json
        for msg in msgs:
            if msg.get('media_file') == f"voice/{silk_fn}":
                msg['content'] = text
                msg['voice_wav'] = f"voice/{wav_fn}"
                msg['voice_txt'] = f"voice2txt/{txt_fn}"
                msg.pop('media_file', None)
                msg.pop('media_format', None)
                updated += 1

        # Step 4: Delete .silk
        os.remove(silk_path)
        time.sleep(0.2)

    with open(chat_json, 'w', encoding='utf-8') as f:
        json.dump(msgs, f, ensure_ascii=False, indent=2)

    print(f"  Updated {updated} messages")
    return updated

# ─── Update image references ───
def find_chat_json(contact_dir):
    """Find chat JSON file (chat.json or chat_YYYY-MM-DD_YYYY-MM-DD.json)"""
    for fn in sorted(os.listdir(contact_dir)):
        if fn.startswith('chat') and fn.endswith('.json'):
            return os.path.join(contact_dir, fn)
    return os.path.join(contact_dir, 'chat.json')

def get_chat_json(contact_dir):
    return find_chat_json(contact_dir)

def fix_image_refs(contact_dir):
    """Update chat.json to replace .wxgf with .jpg, .silk with voice_wav/voice_txt."""
    chat_json = get_chat_json(contact_dir)
    with open(chat_json) as f: msgs = json.load(f)
    updated = 0
    for msg in msgs:
        if msg.get('media_file', '').endswith('.wxgf'):
            msg['content'] = msg['content'].replace('.wxgf', '.jpg')
            msg['media_file'] = msg['media_file'].replace('.wxgf', '.jpg')
            msg['media_format'] = 'jpg'
            updated += 1
        if msg.get('media_file', '').endswith('.silk'):
            wav = msg['media_file'].replace('.silk', '.wav')
            if os.path.exists(os.path.join(contact_dir, wav)):
                msg['content'] = msg['content'].replace('.silk', '.wav')
                msg['voice_wav'] = wav
                msg.pop('media_file', None)
                msg.pop('media_format', None)
                updated += 1
    with open(chat_json, 'w', encoding='utf-8') as f:
        json.dump(msgs, f, ensure_ascii=False, indent=2)
    print(f"Fixed {updated} media references in chat.json")

# ─── Main ───
if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 post_process.py <contact_dir>")
        sys.exit(1)

    contact_dir = sys.argv[1]
    img_dir = os.path.join(contact_dir, 'image')

    # 1. WXGF → JPG
    if os.path.exists(img_dir):
        convert_wxgf(img_dir)

    # 2. SILK → WAV + ASR + cleanup
    process_voice(contact_dir)

    # 3. Fix references
    fix_image_refs(contact_dir)

    print("\nDone!")