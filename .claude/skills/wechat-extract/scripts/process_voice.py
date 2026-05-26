#!/usr/bin/env python3
"""
语音后处理：SILK → WAV → OSS → Qwen ASR → txt + 更新 chat.json
支持：.silk 转码后 ASR，已有 .wav 直接 ASR
用法: python3 process_voice.py <contact_dir> [--force]
示例: python3 process_voice.py refs/people/黄子晨
"""
import os, sys, json, time, tempfile, subprocess, urllib.request

FFMPEG = "/home/zhangyanbo/owner/xiaowangzi/.venv/lib/python3.11/site-packages/imageio_ffmpeg/binaries/ffmpeg-linux-x86_64-v7.0.2"
API_KEY = "sk-a2675c4123764e46880426a87bff42de"
ASR_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1/chat/completions"

OSS_CONFIG = {
    'access_key_id': 'LTAI5tA6wxrUe1gahbSaeC5M',
    'access_key_secret': 'kNmxEpHRFLLZAoOuJ4WIaNTNlJcPII',
    'bucket': 'b612xiaowangzi',
    'endpoint': 'oss-cn-hangzhou.aliyuncs.com',
}

# ─── OSS Upload ───
def upload_oss(local_path, object_key=None):
    """Upload to OSS, return public URL."""
    import oss2
    auth = oss2.Auth(OSS_CONFIG['access_key_id'], OSS_CONFIG['access_key_secret'])
    bucket = oss2.Bucket(auth, OSS_CONFIG['endpoint'], OSS_CONFIG['bucket'])
    if not object_key:
        from datetime import datetime
        object_key = f"voice/{datetime.now().strftime('%Y%m%d_%H%M%S')}_{os.path.basename(local_path)}"

    bucket.put_object_from_file(object_key, local_path,
        headers={'Content-Type': 'audio/wav', 'x-oss-object-acl': 'public-read'})
    return f"https://{OSS_CONFIG['bucket']}.{OSS_CONFIG['endpoint']}/{object_key}"

# ─── SILK → WAV ───
def silk_to_wav(silk_path, wav_path):
    """Decode SILK_V3 to WAV using pilk + ffmpeg."""
    with open(silk_path, 'rb') as f:
        data = f.read()

    if data[:1] == b'\x02':
        data = data[1:]

    if not data.startswith(b'#!SILK_V3'):
        print(f"  SKIP {os.path.basename(silk_path)}: not SILK_V3")
        return None

    if not data.endswith(b'\xff\xff'):
        data += b'\xff\xff'

    silk_tmp = tempfile.mktemp(suffix='.silk')
    pcm_tmp = tempfile.mktemp(suffix='.pcm')

    try:
        with open(silk_tmp, 'wb') as f:
            f.write(data)

        import pilk
        pilk.decode(silk_tmp, pcm_tmp)

        subprocess.run([FFMPEG, '-y', '-f', 's16le', '-ar', '24000', '-ac', '1',
                       '-i', pcm_tmp, wav_path], capture_output=True)

        if os.path.exists(wav_path) and os.path.getsize(wav_path) > 0:
            return wav_path
    finally:
        if os.path.exists(silk_tmp): os.remove(silk_tmp)
        if os.path.exists(pcm_tmp): os.remove(pcm_tmp)

    return None

# ─── ASR ───
def transcribe(wav_path):
    """Transcribe WAV via Qwen ASR (input_audio format)."""
    oss_url = upload_oss(wav_path)

    payload = json.dumps({
        "model": "qwen3-asr-flash",
        "messages": [{
            "role": "user",
            "content": [
                {"type": "input_audio", "input_audio": {"data": oss_url, "format": "wav"}}
            ]
        }]
    }).encode()

    req = urllib.request.Request(ASR_URL, data=payload, headers={
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    })

    try:
        resp = urllib.request.urlopen(req, timeout=60)
        result = json.loads(resp.read())
        text = result.get("choices", [{}])[0].get("message", {}).get("content", "")
        return text.strip() if text else "[silence]"
    except Exception as e:
        return f"[error: {e}]"

# ─── Collect voice files needing ASR ───
def collect_voice_files(voice_dir, txt_dir, force=False):
    """Collect all voice files (.silk and .wav) that need ASR transcription."""
    tasks = []
    asr_done = {}

    for fn in sorted(os.listdir(voice_dir)):
        base = fn.rsplit('.', 1)[0]
        txt_fn = base + '.txt'
        txt_path = os.path.join(txt_dir, txt_fn)

        if fn.endswith('.silk'):
            wav_fn = base + '.wav'
            wav_path = os.path.join(voice_dir, wav_fn)
            silk_path = os.path.join(voice_dir, fn)

            # Check if already transcribed
            if not force and os.path.exists(txt_path):
                with open(txt_path) as f:
                    text = f.read().strip()
                if text and text not in ('[silence]', '[error]', '[error:', ''):
                    asr_done[fn] = {'wav_fn': wav_fn, 'txt_fn': txt_fn, 'text': text, 'had_silk': True}
                    # Still need to convert silk→wav and delete silk if wav doesn't exist
                    if not os.path.exists(wav_path):
                        tasks.append(('silk_to_wav', fn, silk_path, wav_path, txt_path, txt_fn, wav_fn))
                    continue

            tasks.append(('full', fn, silk_path, wav_path, txt_path, txt_fn, wav_fn))

        elif fn.endswith('.wav'):
            txt_fn = base + '.txt'
            txt_path = os.path.join(txt_dir, txt_fn)

            if not force and os.path.exists(txt_path):
                with open(txt_path) as f:
                    text = f.read().strip()
                if text and text not in ('[silence]', '[error]', '[error:', ''):
                    asr_done[fn] = {'wav_fn': fn, 'txt_fn': txt_fn, 'text': text, 'had_silk': False}
                    continue

            tasks.append(('asr_only', fn, os.path.join(voice_dir, fn),
                          os.path.join(voice_dir, fn), txt_path, txt_fn, fn))

    return tasks, asr_done

# ─── Main ───
def process_contact(contact_dir, force=False):
    voice_dir = os.path.join(contact_dir, 'voice')
    txt_dir = os.path.join(contact_dir, 'voice2txt')
    chat_json = os.path.join(contact_dir, 'chat.json')

    if not os.path.exists(voice_dir):
        print("No voice directory")
        return

    voice_files = [f for f in os.listdir(voice_dir) if f.endswith('.silk') or f.endswith('.wav')]
    if not voice_files:
        print("No voice files")
        return

    os.makedirs(txt_dir, exist_ok=True)

    tasks, asr_done = collect_voice_files(voice_dir, txt_dir, force)
    print(f"Voice files: {len(voice_files)} total, {len(asr_done)} already transcribed, {len(tasks)} to process")

    if not tasks and not asr_done:
        print("Nothing to do")
        return

    # Process tasks
    results = {}  # silk_fn or wav_fn → {wav_fn, txt_fn, text, had_silk}
    # Merge already done
    for fn, info in asr_done.items():
        results[fn] = info

    for i, (task_type, fn, src_path, wav_path, txt_path, txt_fn, wav_fn) in enumerate(tasks):
        print(f"  [{i+1}/{len(tasks)}] {fn}...", end=' ', flush=True)

        if task_type == 'silk_to_wav':
            # Only convert, don't transcribe (already have txt)
            result = silk_to_wav(src_path, wav_path)
            if result:
                os.remove(src_path)  # Delete .silk after successful conversion
                print(f"converted → {wav_fn}")
                # Find the silk entry in asr_done and update wav_fn
                for k, v in asr_done.items():
                    if k == fn:
                        results[fn] = v
                        break
            else:
                print("FAIL convert")
            continue

        if task_type == 'full':
            # SILK → WAV → ASR → txt, delete silk
            result = silk_to_wav(src_path, wav_path)
            if not result:
                print("FAIL decode")
                continue
            text = transcribe(wav_path)
            print(f'"{text[:60]}"')
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(text)
            os.remove(src_path)  # Delete .silk
            results[fn] = {'wav_fn': wav_fn, 'txt_fn': txt_fn, 'text': text, 'had_silk': True}

        elif task_type == 'asr_only':
            # WAV already exists, just ASR
            text = transcribe(src_path)
            print(f'"{text[:60]}"')
            with open(txt_path, 'w', encoding='utf-8') as f:
                f.write(text)
            results[fn] = {'wav_fn': wav_fn, 'txt_fn': txt_fn, 'text': text, 'had_silk': False}

        time.sleep(0.2)  # rate limit

    # Update chat.json
    with open(chat_json) as f:
        msgs = json.load(f)

    updated = 0
    for msg in msgs:
        media = msg.get('media_file', '')
        if not media or not media.startswith('voice/'):
            continue

        orig_fn = os.path.basename(media)
        base = orig_fn.rsplit('.', 1)[0]  # strip .silk/.wav extension

        # Find matching result by original filename or base name
        matched = None
        for fn, info in results.items():
            result_base = fn.rsplit('.', 1)[0]
            if result_base == base or fn == orig_fn:
                matched = info
                break

        if matched:
            wav_fn = matched['wav_fn']
            txt_fn = matched['txt_fn']
            text = matched['text']
            msg['content'] = f"[voice: voice/{wav_fn}]"
            msg['media_file'] = f"voice/{wav_fn}"
            msg['media_format'] = 'wav'
            msg['voice_text'] = text
            msg['voice_wav'] = f"voice/{wav_fn}"
            msg['voice_txt'] = f"voice2txt/{txt_fn}"
            if msg.get('thumbnail'):
                del msg['thumbnail']
            updated += 1

    with open(chat_json, 'w', encoding='utf-8') as f:
        json.dump(msgs, f, ensure_ascii=False, indent=2)

    print(f"\nUpdated {updated} voice messages in chat.json")
    print(f"Text files: {txt_dir}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python3 process_voice.py <contact_dir> [--force]")
        sys.exit(1)
    process_contact(sys.argv[1], '--force' in sys.argv)