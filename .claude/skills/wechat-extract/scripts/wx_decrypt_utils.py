"""Shared utilities for WeChat database decryption and key loading.

Used by extract_one.py and lookup_contact.py on Windows.
All scripts must be in the same directory for imports to work.
"""
import hashlib, hmac as hm, struct, os, json, sys
from Crypto.Cipher import AES

# ─── Constants ───
PAGE_SZ = 4096; KEY_SZ = 32; SALT_SZ = 16; IV_SZ = 16; HMAC_SZ = 64; RESERVE_SZ = 80
SQLITE_HDR = b'SQLite format 3\x00'

IMAGE_AES = b'b999dcc3e32aa58e'; IMAGE_XOR = 0x6c; V1_KEY = b'cfcd208495d565ef'
V2_MAGIC = b'\x07\x08V2\x08\x07'; V1_MAGIC = b'\x07\x08V1\x08\x07'

# ─── Paths ───
DB_ROOT = r"E:\xwechat_files\zhangyanbo4815_77a1\db_storage"
DB_DIR = os.path.join(DB_ROOT, "message")
ATTACH_DIR = r"E:\xwechat_files\zhangyanbo4815_77a1\msg\attach"
VIDEO_DIR = r"E:\xwechat_files\zhangyanbo4815_77a1\msg\video"

# ─── Fallback hardcoded keys (for backward compatibility) ───
HARDCODED_KEYS = {
    "message_0.db": "4e00f60c3325e3e175687977e12f4c7e908f09fabe16f1927e4c08c8c87656e2",
    "message_1.db": "ae33f6b8e618bb97e787cce79c653e93517ddec60ef4429ac64c4b9cda86fe6e",
    "message_2.db": "f24b3c5ed7efece486a9b921b6dbc9d0f2d58350fc6d5bfc2532c3c2f15ed2f9",
    "media_0.db": "e7ab55fa4bf33b5872882c93d49ac3fc10a9276b95e3bf526f89876146627a9e",
}

# ─── Database decryption ───
def decrypt_db(db_path, enc_key_hex):
    enc_key = bytes.fromhex(enc_key_hex)
    with open(db_path, 'rb') as fin: page1 = fin.read(PAGE_SZ)
    salt = page1[:SALT_SZ]
    mk = hashlib.pbkdf2_hmac("sha512", enc_key, bytes(b ^ 0x3a for b in salt), 2, dklen=KEY_SZ)
    mac = hm.new(mk, page1[SALT_SZ:PAGE_SZ - RESERVE_SZ + IV_SZ], hashlib.sha512)
    mac.update(struct.pack('<I', 1))
    if mac.digest() != page1[PAGE_SZ - HMAC_SZ:PAGE_SZ]:
        raise ValueError(f"HMAC failed: {db_path}")
    total = os.path.getsize(db_path) // PAGE_SZ
    out = bytearray()
    with open(db_path, 'rb') as fin:
        for pg in range(1, total + 1):
            page = fin.read(PAGE_SZ)
            if len(page) < PAGE_SZ: break
            iv = page[PAGE_SZ - RESERVE_SZ:PAGE_SZ - RESERVE_SZ + IV_SZ]
            if pg == 1:
                c = AES.new(enc_key, AES.MODE_CBC, iv)
                out.extend(bytearray(SQLITE_HDR + c.decrypt(page[SALT_SZ:PAGE_SZ - RESERVE_SZ]) + b'\x00' * RESERVE_SZ))
            else:
                c = AES.new(enc_key, AES.MODE_CBC, iv)
                out.extend(c.decrypt(page[:PAGE_SZ - RESERVE_SZ]) + b'\x00' * RESERVE_SZ)
    tmp = os.path.join(os.environ["TEMP"], f"_wx_{os.path.basename(db_path)}")
    with open(tmp, 'wb') as f: f.write(bytes(out))
    return tmp

# ─── Key loading ───
def load_keys(keys_path=None):
    """Load database keys from JSON. Falls back to hardcoded keys if file missing."""
    # Try explicit path
    if keys_path and os.path.exists(keys_path):
        with open(keys_path, encoding='utf-8') as f:
            data = json.load(f)
        keys = {}
        for k, v in data.items():
            if k == "_db_dir": continue
            if isinstance(v, dict) and "enc_key" in v:
                keys[k] = v["enc_key"]
            elif isinstance(v, str):
                keys[k] = v
        return keys

    # Try default locations on Windows
    default_paths = [
        r"C:\Users\zhangyanbo\wechat-env\all_db_keys.json",
        r"E:\xwechat_files\export\all_db_keys.json",
    ]
    for p in default_paths:
        if os.path.exists(p):
            with open(p, encoding='utf-8') as f:
                data = json.load(f)
            keys = {}
            for k, v in data.items():
                if k == "_db_dir": continue
                if isinstance(v, dict) and "enc_key" in v:
                    keys[k] = v["enc_key"]
                elif isinstance(v, str):
                    keys[k] = v
            return keys

    # Last resort: hardcoded keys
    print("  [WARN] 未找到密钥文件，使用硬编码密钥（不含 contact.db）")
    return dict(HARDCODED_KEYS)

def resolve_key(db_rel_path, keys):
    """Resolve a database key by trying multiple path formats."""
    # Try exact match
    if db_rel_path in keys:
        return keys[db_rel_path]
    # Try bare filename
    bare = os.path.basename(db_rel_path)
    if bare in keys:
        return keys[bare]
    # Try with subdirectory prefix variations
    for key_path, key_val in keys.items():
        if os.path.basename(key_path) == bare:
            return key_val
    raise KeyError(f"No key found for {db_rel_path} (checked bare name '{bare}')")