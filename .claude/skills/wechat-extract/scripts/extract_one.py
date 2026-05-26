"""
微信单联系人数据提取 — 跨全部数据库合并去重，提取文本+图片+语音+视频
支持: 关键词搜索 / wxid精确匹配 / --contact 联系人备注/微信号/昵称搜索 / 自动回退

用法: python extract_one.py <搜索词|wxid> [输出目录] [--contact] [--keys=路径]
示例: python extract_one.py 子晨
      python extract_one.py 张三 C:\\wechat_export
      python extract_one.py wxid_abc123
      python extract_one.py --contact 兰周婵            ← 按备注名/微信号/昵称搜索
      python extract_one.py --contact lanzhouchan       ← 按拼音搜索
      python extract_one.py 兰周婵                      ← 关键词失败自动回退联系人搜索
      python extract_one.py --list                      ← 列出所有Msg表
      python extract_one.py --contact 兰周婵 --keys=C:\\...\\all_db_keys.json
"""
import hashlib, os, sqlite3, json, re, glob, shutil, sys, struct

# Ensure wx_decrypt_utils can be imported from same directory
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wx_decrypt_utils import (
    decrypt_db, load_keys, resolve_key, DB_ROOT, DB_DIR, ATTACH_DIR, VIDEO_DIR,
    IMAGE_AES, IMAGE_XOR, V1_KEY, V2_MAGIC, V1_MAGIC, PAGE_SZ, SQLITE_HDR,
)

# ─── Image/voice helpers (unchanged) ───
def aligned_aes_size(sz):
    return sz + (16 - sz % 16) if sz % 16 else sz + 16

def decrypt_dat(path):
    try:
        with open(path, 'rb') as f: data = f.read()
    except: return None, None, False
    if len(data) < 15: return None, None, False
    h6 = data[:6]
    if h6 == V2_MAGIC: ak, xk = IMAGE_AES, IMAGE_XOR
    elif h6 == V1_MAGIC: ak, xk = V1_KEY, IMAGE_XOR
    else: return None, None, False
    try:
        asz, xsz = struct.unpack_from('<LL', data, 6)
        al = aligned_aes_size(asz); ae = 15 + al
        from Crypto.Cipher import AES
        c = AES.new(ak, AES.MODE_ECB); dec = c.decrypt(data[15:ae])
        pad = dec[-1]
        if 0 < pad <= 16: dec = dec[:-pad]
        xs = ae; dec += bytes(b ^ xk for b in data[xs:xs + xsz]); dec += data[xs + xsz:]
        is_thumb = '_t.dat' in path
        return dec, detect_fmt(dec), is_thumb
    except: return None, None, False

def detect_fmt(h):
    if h[:3] == b'\xff\xd8\xff': return 'jpg'
    if h[:4] == b'\x89PNG': return 'png'
    if h[:3] == b'GIF': return 'gif'
    if h[:4] == b'RIFF' and len(h) >= 12 and h[8:12] == b'WEBP': return 'webp'
    if h[:4] == b'wxgf': return 'wxgf'
    if h[:4] == b'\x00\x00\x00' and len(h) > 8 and h[4:8] == b'ftyp': return 'mp4'
    return 'bin'

def extract_md5(packed):
    if not packed or not isinstance(packed, bytes): return []
    return [m.group(0).decode('ascii').lower() for m in re.finditer(rb'[0-9a-fA-F]{32}', packed)]

# ─── Contact.db lookup (NEW) ───
def lookup_in_contact_db(search_term, keys):
    """Search contact.db by remark/alias/nick_name/pinyin → return list of matches."""
    contact_db_path = os.path.join(DB_ROOT, "contact", "contact.db")
    if not os.path.exists(contact_db_path):
        print(f"  [SKIP] contact.db 不存在")
        return []
    try:
        contact_key = resolve_key("contact/contact.db", keys)
    except KeyError:
        print(f"  [SKIP] contact.db 密钥未找到（请先运行密钥提取）")
        return []

    print(f"联系人搜索 '{search_term}' ...")
    tmp = decrypt_db(contact_db_path, contact_key)
    conn = sqlite3.connect(tmp)
    c = conn.cursor()

    # Try exact matches first, then fuzzy
    c.execute("""
        SELECT username, alias, remark, nick_name FROM contact
        WHERE remark = ? OR alias = ? OR nick_name = ?
           OR remark LIKE ? OR nick_name LIKE ?
           OR remark_quan_pin LIKE ? OR quan_pin LIKE ?
           OR pin_yin_initial LIKE ?
    """, (search_term, search_term, search_term,
          f"%{search_term}%", f"%{search_term}%",
          f"%{search_term}%", f"%{search_term}%",
          f"%{search_term}%"))

    results = []
    for username, alias, remark, nick_name in c.fetchall():
        msg_hash = hashlib.md5(username.encode('utf-8')).hexdigest()
        results.append({
            'username': username, 'alias': alias, 'remark': remark,
            'nick_name': nick_name, 'msg_hash': msg_hash,
        })

    conn.close(); os.unlink(tmp)

    # Sort: prefer exact remark match, then exact alias, then exact nick, then fuzzy
    def match_score(r):
        if r['remark'] == search_term: return 0
        if r['alias'] and r['alias'].lower() == search_term.lower(): return 1
        if r['nick_name'] == search_term: return 2
        return 3
    results.sort(key=match_score)

    if results:
        best = results[0]
        display = best.get('remark') or best.get('nick_name') or best.get('alias') or search_term
        print(f"  找到: {display} (wxid: {best['username']})")
        if len(results) > 1:
            print(f"  其他匹配: {len(results)-1}个")
            for r in results[1:4]:
                d = r.get('remark') or r.get('nick_name') or r.get('alias')
                print(f"    {d} ({r['username']})")
    else:
        print(f"  contact.db 中未找到 '{search_term}'")

    return results

# ─── Search by keyword (unchanged logic, keys parameter) ───
def search_by_keyword(keyword, keys):
    print(f"关键词搜索 '{keyword}' ...")
    msg_dbs = [f for f in os.listdir(DB_DIR) if f.startswith("message_") and f.endswith(".db")]
    results = []
    for db_name in msg_dbs:
        try:
            db_key = resolve_key(db_name, keys)
        except KeyError: continue
        tmp = decrypt_db(os.path.join(DB_DIR, db_name), db_key)
        conn = sqlite3.connect(tmp)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'Msg_%'")
        for (tbl,) in c.fetchall():
            try:
                c.execute(f"SELECT COUNT(*) FROM [{tbl}] WHERE message_content LIKE ?", (f"%{keyword}%",))
                cnt = c.fetchone()[0]
                if cnt > 0: results.append((tbl[4:], db_name, cnt))
            except: pass
        conn.close(); os.unlink(tmp)
    results.sort(key=lambda x: -x[2])
    if results:
        best = results[0]
        print(f"  最佳匹配: Msg_{best[0][:16]}... ({best[1]}), {best[2]}条关键词匹配")
    return results

def search_by_wxid(wxid, keys):
    print(f"wxid 精确匹配 '{wxid}' ...")
    msg_hash = hashlib.md5(wxid.encode('utf-8')).hexdigest()
    msg_dbs = [f for f in os.listdir(DB_DIR) if f.startswith("message_") and f.endswith(".db")]
    found = False
    for db_name in msg_dbs:
        try:
            db_key = resolve_key(db_name, keys)
        except KeyError: continue
        tmp = decrypt_db(os.path.join(DB_DIR, db_name), db_key)
        conn = sqlite3.connect(tmp)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = [t[0] for t in c.fetchall()]
        target = f"Msg_{msg_hash}"
        if target in tables:
            c.execute(f"SELECT COUNT(*) FROM [{target}]")
            cnt = c.fetchone()[0]
            print(f"  找到: Msg_{msg_hash[:16]}... ({db_name}), {cnt}条消息")
            found = True
            conn.close(); os.unlink(tmp); break
        conn.close(); os.unlink(tmp)
    if not found:
        print(f"  ERROR: 未找到 wxid={wxid} 对应的 Msg 表")
    return msg_hash if found else None

def list_all_msg_tables(keys):
    print("列出所有 Msg 表...")
    msg_dbs = [f for f in os.listdir(DB_DIR) if f.startswith("message_") and f.endswith(".db")]
    tables = []
    for db_name in msg_dbs:
        try:
            db_key = resolve_key(db_name, keys)
        except KeyError: continue
        tmp = decrypt_db(os.path.join(DB_DIR, db_name), db_key)
        conn = sqlite3.connect(tmp)
        c = conn.cursor()
        c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'Msg_%'")
        for (tbl,) in c.fetchall():
            try:
                c.execute(f"SELECT COUNT(*) FROM [{tbl}]")
                cnt = c.fetchone()[0]
                tables.append((tbl[4:], db_name, cnt))
            except: pass
        conn.close(); os.unlink(tmp)
    tables.sort(key=lambda x: -x[2])
    print(f"  共 {len(tables)} 个 Msg 表:")
    for mh, db, cnt in tables[:20]:
        print(f"    Msg_{mh[:16]}... ({db}): {cnt}条")
    if len(tables) > 20:
        print(f"    ... 还有 {len(tables)-20} 个表")
    return tables

def resolve_username(msg_hash, keys):
    msg_dbs = [f for f in os.listdir(DB_DIR) if f.startswith("message_") and f.endswith(".db")]
    for db_name in msg_dbs:
        try:
            db_key = resolve_key(db_name, keys)
            tmp = decrypt_db(os.path.join(DB_DIR, db_name), db_key)
            conn = sqlite3.connect(tmp)
            c = conn.cursor()
            c.execute("SELECT user_name FROM Name2Id")
            for (uname,) in c.fetchall():
                if hashlib.md5(uname.encode('utf-8')).hexdigest() == msg_hash:
                    conn.close(); os.unlink(tmp)
                    return uname
            conn.close(); os.unlink(tmp)
        except: pass
    return f"unknown_{msg_hash[:8]}"

# ─── Image file search ───
def find_image_file(md5, date_str):
    for suffix in ['.dat', '_h.dat', '_t.dat']:
        pat = os.path.join(ATTACH_DIR, '*', date_str, 'Img', md5 + suffix)
        matches = glob.glob(pat)
        if matches: return matches[0], suffix == '_t.dat'
    return None, False

# ─── Cross-database extraction + dedup ───
def extract_from_all_dbs(msg_hash, keyword, output_dir, keys):
    safe_name = keyword.replace('/', '_').replace('\\', '_').replace(':', '_')[:60]
    out = os.path.join(output_dir, safe_name)
    for sub in ['image', 'voice', 'video']:
        os.makedirs(os.path.join(out, sub), exist_ok=True)

    # Load voice map
    voice_map = {}
    try:
        media_key = resolve_key("media_0.db", keys)
        vtmp = decrypt_db(os.path.join(DB_DIR, "media_0.db"), media_key)
        vconn = sqlite3.connect(vtmp)
        vc = vconn.cursor()
        vc.execute("SELECT create_time, local_id, voice_data FROM VoiceInfo")
        for vts, vlid, vdata in vc.fetchall():
            if vdata and len(vdata) > 10: voice_map[(vts, vlid)] = vdata
        vconn.close(); os.unlink(vtmp)
        print(f"  语音库: {len(voice_map)} 条")
    except Exception as e:
        print(f"  语音库加载失败: {e}")

    # Extract from all databases
    all_rows = []; sender_status = {}; db_sources = []
    table_name = f"Msg_{msg_hash}"
    msg_dbs = [f for f in os.listdir(DB_DIR) if f.startswith("message_") and f.endswith(".db")]

    for db_name in msg_dbs:
        db_path = os.path.join(DB_DIR, db_name)
        try:
            db_key = resolve_key(db_name, keys)
        except KeyError: continue
        try:
            tmp = decrypt_db(db_path, db_key)
            conn = sqlite3.connect(tmp)
            c = conn.cursor()
            c.execute(f"SELECT name FROM sqlite_master WHERE type='table' AND name='{table_name}'")
            if not c.fetchone():
                conn.close(); os.unlink(tmp); continue
            c.execute(f"SELECT local_id, create_time, local_type, real_sender_id, status, message_content, packed_info_data FROM [{table_name}] ORDER BY create_time ASC")
            rows = c.fetchall()
            if rows:
                print(f"  {db_name}: {len(rows)} 条消息")
                db_sources.append(db_name)
                all_rows.extend(rows)
                for lid, ts, mtype, sender_id, status, content, packed in rows:
                    if sender_id not in sender_status: sender_status[sender_id] = set()
                    sender_status[sender_id].add(status)
            conn.close(); os.unlink(tmp)
        except Exception as e:
            print(f"  {db_name}: 跳过 ({e})")

    if not all_rows:
        print("ERROR: 未提取到任何消息")
        return False

    # Dedup by local_id
    seen_ids = set(); unique_rows = []
    for row in all_rows:
        if row[0] not in seen_ids:
            seen_ids.add(row[0])
            unique_rows.append(row)
    unique_rows.sort(key=lambda r: r[1])
    print(f"  合计: {len(all_rows)} → 去重后 {len(unique_rows)} 条")

    # Sender mapping — build sender_id→name map from status patterns across all messages
    # Key insight: any sender_id with status=2 is the user (小王子),
    # any sender_id with status=4 (but NOT status=2) is the contact.
    # This handles cross-database sender_id inconsistency (e.g. 小王子=id=4 in old db, id=2 in new db).
    sender_id_map = {}
    for sid, statuses in sender_status.items():
        if 2 in statuses:
            sender_id_map[sid] = "小王子"
        elif 4 in statuses:
            sender_id_map[sid] = keyword

    my_sender_ids = [sid for sid, name in sender_id_map.items() if name == "小王子"]
    contact_sender_ids = [sid for sid, name in sender_id_map.items() if name == keyword]
    print(f"  发送方映射: 小王子={my_sender_ids}, {keyword}={contact_sender_ids}")

    username = resolve_username(msg_hash, keys)
    print(f"  wxid: {username}")

    # Process messages
    from datetime import datetime
    messages = []
    stats = {'text': 0, 'image': 0, 'image_thumb': 0, 'voice': 0, 'video': 0, 'other': 0}

    for lid, ts, mtype, sender_id, status, content, packed in unique_rows:
        dt = datetime.fromtimestamp(ts) if ts else None
        time_str = dt.isoformat() if dt else None
        # Determine sender: status is definitive for 2/4,
        # sender_id_map resolves ambiguous status (e.g. status=3="delivered" applies to both sides)
        if status == 2:
            sender = "小王子"
        elif status == 4:
            sender = keyword
        elif sender_id in sender_id_map:
            sender = sender_id_map[sender_id]
        elif mtype == 10000:
            sender = "system"
        else:
            sender = str(sender_id)
        msg = {"id": lid, "time": time_str, "type": mtype, "sender": sender}

        if mtype == 1:
            if isinstance(content, str): msg["content"] = content
            elif isinstance(content, bytes):
                try: msg["content"] = content.decode('utf-8')
                except: msg["content"] = f"[binary {len(content)}B]"
            else: msg["content"] = str(content) if content else ""
            stats['text'] += 1

        elif mtype == 3:
            found = False
            for md5_img in extract_md5(packed) if packed else []:
                date_str = dt.strftime('%Y-%m') if dt else '*'
                dat_path, is_thumb = find_image_file(md5_img, date_str)
                if dat_path:
                    dec_data, fmt, _ = decrypt_dat(dat_path)
                    if dec_data:
                        fmt = fmt or 'jpg'
                        time_tag = dt.strftime('%Y%m%d_%H%M%S') if dt else f"img_{lid}"
                        suffix = '_thumb' if is_thumb else ''
                        fn = f"{time_tag}_{md5_img[:8]}{suffix}.{fmt}"
                        fpath = os.path.join(out, 'image', fn)
                        if not os.path.exists(fpath):
                            with open(fpath, 'wb') as f: f.write(dec_data)
                            if is_thumb: stats['image_thumb'] += 1
                            else: stats['image'] += 1
                        msg["content"] = f"[image: image/{fn}]"
                        msg["media_file"] = f"image/{fn}"
                        msg["media_format"] = fmt
                        if is_thumb: msg["thumbnail"] = True
                        found = True; break
            if not found: msg["content"] = "[image: not found]"

        elif mtype == 34:
            vdata = voice_map.get((ts, lid))
            if vdata:
                time_tag = dt.strftime('%Y%m%d_%H%M%S') if dt else f"voice_{lid}"
                fn = f"{time_tag}_voice_{lid}.silk"
                fpath = os.path.join(out, 'voice', fn)
                if not os.path.exists(fpath):
                    with open(fpath, 'wb') as f: f.write(vdata)
                    stats['voice'] += 1
                msg["content"] = f"[voice: voice/{fn}]"
                msg["media_file"] = f"voice/{fn}"
                msg["media_format"] = "silk"
            else: msg["content"] = "[voice: not found]"

        elif mtype == 43:
            found = False
            for md5_vid in extract_md5(packed) if packed else []:
                pat = os.path.join(VIDEO_DIR, '*', md5_vid + '.mp4')
                matches = glob.glob(pat)
                if matches:
                    time_tag = dt.strftime('%Y%m%d_%H%M%S') if dt else f"video_{lid}"
                    fn = f"{time_tag}_video_{md5_vid[:8]}.mp4"
                    fpath = os.path.join(out, 'video', fn)
                    if not os.path.exists(fpath):
                        shutil.copy2(matches[0], fpath)
                        stats['video'] += 1
                    msg["content"] = f"[video: video/{fn}]"
                    msg["media_file"] = f"video/{fn}"
                    msg["media_format"] = "mp4"
                    found = True; break
            if not found: msg["content"] = "[video: not found]"

        elif mtype == 10000:
            msg["content"] = str(content) if content else "[system]"
            stats['other'] += 1
        elif mtype in (47, 48):
            msg["content"] = "[sticker]"
            stats['other'] += 1
        else:
            msg["content"] = f"[type{mtype}]"
            stats['other'] += 1

        messages.append(msg)

    # Save JSON
    dates = [m.get('time','')[:10] for m in messages if m.get('time')]
    dates = [d for d in dates if d]
    json_name = f"chat_{dates[0]}_{dates[-1]}.json" if dates else "chat.json"
    json_path = os.path.join(out, json_name)
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(messages, f, ensure_ascii=False, indent=2)

    # Summary
    print(f"\n{'='*50}")
    print(f"提取完成: {username}")
    print(f"  数据库: {', '.join(db_sources)}")
    print(f"  文本: {stats['text']}")
    print(f"  图片: {stats['image']} (原图) + {stats['image_thumb']} (缩略)")
    print(f"  语音: {stats['voice']} (SILK)")
    print(f"  视频: {stats['video']} (MP4)")
    print(f"  其他: {stats['other']}")
    print(f"  总计: {len(messages)}")
    print(f"  输出: {out}")

    with open(os.path.join(out, '_stats.json'), 'w', encoding='utf-8') as f:
        json.dump({
            'username': username, 'msg_hash': msg_hash, 'dbs': db_sources,
            **stats, 'total': len(messages),
            'date_range': f"{dates[0]}_{dates[-1]}" if dates else None,
        }, f, ensure_ascii=False, indent=2)
    return True

# ─── Main flow ───
def main():
    # Parse arguments
    args = sys.argv[1:]
    keys_path = None
    contact_mode = False
    filtered_args = []

    i = 0
    while i < len(args):
        a = args[i]
        if a == '--contact':
            contact_mode = True
        elif a.startswith('--keys='):
            keys_path = a.split('=', 1)[1]
        elif a == '--keys' and i + 1 < len(args):
            keys_path = args[i + 1]
            i += 1
        else:
            filtered_args.append(a)
        i += 1

    if not filtered_args:
        print("用法: python extract_one.py <搜索词|wxid> [输出目录] [--contact] [--keys=路径]")
        print("搜索模式:")
        print("  关键词:   搜索 message_content（如 '子晨'）")
        print("  wxid:    精确匹配（如 'wxid_wzd2l8rcya1621'）")
        print("  --contact: 搜索联系人备注名/微信号/昵称（如 '--contact 兰周婵'）")
        print("  自动回退: 关键词搜索失败 → 自动搜索联系人数据库")
        print("  --list:  列出所有 Msg 表（排查用）")
        print("示例:")
        print("  python extract_one.py 子晨")
        print("  python extract_one.py wxid_wzd2l8rcya1621")
        print("  python extract_one.py --contact 兰周婵")
        print("  python extract_one.py --contact lanzhouchan  ← 拼音搜索")
        print("  python extract_one.py 兰周婵  ← 关键词失败自动回退联系人")
        print("  python extract_one.py --list")
        sys.exit(1)

    arg = filtered_args[0]
    output_dir = filtered_args[1] if len(filtered_args) > 1 else r"E:\xwechat_files\export"
    keys = load_keys(keys_path)

    # --list mode
    if arg == "--list":
        list_all_msg_tables(keys)
        return

    # --contact mode: direct contact.db lookup
    if contact_mode:
        contact_results = lookup_in_contact_db(arg, keys)
        if not contact_results:
            print(f"ERROR: 联系人数据库中未找到 '{arg}'")
            return
        best = contact_results[0]
        msg_hash = best['msg_hash']
        keyword = best.get('remark') or best.get('nick_name') or best.get('alias') or arg
        print(f"  使用联系人: {keyword} ({best['username']})")
        extract_from_all_dbs(msg_hash, keyword, output_dir, keys)
        return

    # wxid mode
    if arg.startswith("wxid_") or arg.startswith("wxid"):
        msg_hash = search_by_wxid(arg, keys)
        if not msg_hash: return
        keyword = arg

    # keyword mode (with auto-fallback to contact.db)
    else:
        results = search_by_keyword(arg, keys)
        if not results:
            # Auto-fallback: try contact.db lookup
            print(f"  关键词搜索未找到，尝试联系人搜索...")
            contact_results = lookup_in_contact_db(arg, keys)
            if contact_results:
                best = contact_results[0]
                msg_hash = best['msg_hash']
                keyword = best.get('remark') or best.get('nick_name') or best.get('alias') or arg
                print(f"  使用联系人: {keyword} ({best['username']})")
            else:
                print(f"ERROR: 未找到 '{arg}' 的聊天记录")
                print(f"  提示: 尝试 --contact 搜索联系人备注名/微信号/昵称")
                print(f"  提示: 或用 wxid 精确匹配（如 'wxid_wzd2l8rcya1621'）")
                print(f"  提示: 或用 --list 查看所有 Msg 表")
                return
        else:
            msg_hash = results[0][0]
            keyword = arg

    extract_from_all_dbs(msg_hash, keyword, output_dir, keys)

if __name__ == '__main__':
    main()