"""
微信联系人查询 — 从 contact.db 搜索备注名/微信号/昵称，返回 wxid 和 Msg 映射
独立脚本，也可被 extract_one.py 调用

用法: python lookup_contact.py <搜索词> [--keys=路径]
示例: python lookup_contact.py 兰周婵
      python lookup_contact.py Izcchanxi
      python lookup_contact.py 地球观察员
      python lookup_contact.py lanzhouchan    ← 拼音搜索
      python lookup_contact.py wxid_1ui10kq11sp322  ← wxid查询
"""
import hashlib, os, sqlite3, json, sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from wx_decrypt_utils import decrypt_db, load_keys, resolve_key, DB_ROOT

def lookup_contact(search_term, keys):
    """Search contact.db by remark/alias/nick_name/pinyin → return list of matches."""
    contact_db_path = os.path.join(DB_ROOT, "contact", "contact.db")
    if not os.path.exists(contact_db_path):
        print(f"ERROR: contact.db 不存在: {contact_db_path}")
        return []

    try:
        contact_key = resolve_key("contact/contact.db", keys)
    except KeyError:
        print(f"ERROR: contact.db 密钥未找到")
        print(f"  请先运行密钥提取: find_all_keys_windows.py")
        print(f"  确保配置 db_dir 指向 db_storage 根目录（不是 message 子目录）")
        return []

    print(f"搜索联系人 '{search_term}' ...")
    tmp = decrypt_db(contact_db_path, contact_key)
    conn = sqlite3.connect(tmp)
    c = conn.cursor()

    if search_term.startswith("wxid_"):
        # Direct wxid lookup
        c.execute("""
            SELECT username, alias, remark, nick_name,
                   remark_quan_pin, pin_yin_initial, quan_pin
            FROM contact WHERE username = ?
        """, (search_term,))
    else:
        # Search by remark, alias, nick_name, pinyin
        c.execute("""
            SELECT username, alias, remark, nick_name,
                   remark_quan_pin, pin_yin_initial, quan_pin
            FROM contact
            WHERE remark = ? OR alias = ? OR nick_name = ?
               OR remark LIKE ? OR nick_name LIKE ?
               OR remark_quan_pin LIKE ? OR quan_pin LIKE ?
               OR pin_yin_initial LIKE ?
        """, (search_term, search_term, search_term,
              f"%{search_term}%", f"%{search_term}%",
              f"%{search_term}%", f"%{search_term}%",
              f"%{search_term}%"))

    results = []
    cols = ['username', 'alias', 'remark', 'nick_name',
            'remark_quan_pin', 'pin_yin_initial', 'quan_pin']

    for row in c.fetchall():
        info = dict(zip(cols, row))
        info['msg_hash'] = hashlib.md5(info['username'].encode('utf-8')).hexdigest()
        results.append(info)

    conn.close(); os.unlink(tmp)

    # Sort: exact remark > exact alias > exact nick > fuzzy
    def match_score(r):
        if r['remark'] == search_term: return 0
        if r['alias'] and r['alias'].lower() == search_term.lower(): return 1
        if r['nick_name'] == search_term: return 2
        if r['username'] == search_term: return 3
        return 4
    results.sort(key=match_score)

    if not results:
        print(f"  未找到 '{search_term}'")
        return []

    print(f"  找到 {len(results)} 个匹配:")
    for r in results:
        display = r.get('remark') or r.get('nick_name') or r.get('alias') or r['username']
        alias = r.get('alias') or ''
        nick = r.get('nick_name') or ''
        remark = r.get('remark') or ''
        print(f"    {display}")
        print(f"      wxid:    {r['username']}")
        print(f"      微信号:  {alias}")
        print(f"      昵称:    {nick}")
        print(f"      备注:    {remark}")
        print(f"      Msg表:   Msg_{r['msg_hash'][:16]}...")

    return results

def main():
    keys_path = None
    filtered_args = []

    for i, a in enumerate(sys.argv[1:]):
        if a.startswith('--keys='):
            keys_path = a.split('=', 1)[1]
        elif a == '--keys' and i + 1 < len(sys.argv[1:]):
            keys_path = sys.argv[i + 2]
        else:
            filtered_args.append(a)

    if not filtered_args:
        print("用法: python lookup_contact.py <搜索词> [--keys=路径]")
        print("搜索: 备注名、微信号、昵称、拼音缩写、wxid")
        print("示例:")
        print("  python lookup_contact.py 兰周婵")
        print("  python lookup_contact.py Izcchanxi")
        print("  python lookup_contact.py 地球观察员")
        print("  python lookup_contact.py lanzhouchan")
        print("  python lookup_contact.py wxid_1ui10kq11sp322")
        sys.exit(1)

    search_term = filtered_args[0]
    keys = load_keys(keys_path)
    results = lookup_contact(search_term, keys)

    # Output JSON for programmatic use
    if len(filtered_args) > 1 and filtered_args[1] == '--json':
        print(json.dumps(results, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()