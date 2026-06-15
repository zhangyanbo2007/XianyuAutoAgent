#!/usr/bin/env python3
"""Upload a local file to Alibaba Cloud OSS and return a public URL.

Mirrors the upload-cos skill structure. Reads config from ~/.oss.yaml.
"""

import sys
import os
import yaml
from datetime import datetime

try:
    import oss2
except ImportError:
    print("❌ oss2 not installed. Run: pip3 install oss2")
    sys.exit(1)

CONTENT_TYPES = {
    '.html': 'text/html; charset=utf-8',
    '.htm': 'text/html; charset=utf-8',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.png': 'image/png',
    '.gif': 'image/gif',
    '.webp': 'image/webp',
    '.bmp': 'image/bmp',
    '.svg': 'image/svg+xml',
    '.pdf': 'application/pdf',
    '.json': 'application/json',
    '.xml': 'application/xml',
    '.txt': 'text/plain; charset=utf-8',
    '.md': 'text/markdown; charset=utf-8',
    '.mp4': 'video/mp4',
    '.mov': 'video/quicktime',
    '.avi': 'video/x-msvideo',
    '.webm': 'video/webm',
    '.mp3': 'audio/mpeg',
    '.wav': 'audio/wav',
    '.ogg': 'audio/ogg',
    '.flac': 'audio/flac',
    '.m4a': 'audio/mp4',
    '.opus': 'audio/opus',
    '.pcm': 'audio/pcm',
    '.css': 'text/css; charset=utf-8',
    '.js': 'application/javascript',
}


def human_size(n):
    for unit in ['B', 'KB', 'MB', 'GB']:
        if n < 1024:
            return f"{n:.1f}{unit}" if unit != 'B' else f"{n}B"
        n /= 1024
    return f"{n:.1f}TB"


def get_content_type(filename):
    ext = os.path.splitext(filename)[1].lower()
    return CONTENT_TYPES.get(ext, 'application/octet-stream')


def load_config():
    config_path = os.path.expanduser('~/.oss.yaml')
    if not os.path.exists(config_path):
        print(f"❌ 配置文件不存在: {config_path}")
        print("请创建 ~/.oss.yaml 并填入阿里云OSS凭证，格式:")
        print("""
base:
  access_key_id: <your-access-key-id>
  access_key_secret: <your-access-key-secret>
  bucket: <your-bucket-name>
  endpoint: oss-cn-hangzhou.aliyuncs.com""")
        sys.exit(1)

    with open(config_path) as f:
        cfg = yaml.safe_load(f)

    base = cfg.get('base', {})
    access_key_id = base.get('access_key_id', '')
    access_key_secret = base.get('access_key_secret', '')
    bucket = base.get('bucket', '')
    endpoint = base.get('endpoint', 'oss-cn-hangzhou.aliyuncs.com')

    # 检查是否还是模板占位符
    if access_key_id.startswith('<') or access_key_secret.startswith('<') or bucket.startswith('<'):
        print("❌ ~/.oss.yaml 中的凭证还是模板占位符，请填入实际的 AccessKey 和 Bucket 名称")
        print("获取凭证步骤:")
        print("  1. 登录 https://www.aliyun.com 控制台")
        print("  2. 开通 OSS 服务 → 创建 Bucket（建议杭州节点）")
        print("  3. 设置 Bucket ACL 为 public-read")
        print("  4. 在 AccessKey 管理页面创建 AccessKey")
        sys.exit(1)

    return {
        'access_key_id': access_key_id,
        'access_key_secret': access_key_secret,
        'bucket': bucket,
        'endpoint': endpoint,
    }


def main():
    if len(sys.argv) < 2:
        print("用法: python3 upload.py <file_path> [object_key]")
        sys.exit(1)

    file_path = sys.argv[1]
    object_key = sys.argv[2] if len(sys.argv) > 2 else None

    if not os.path.isfile(file_path):
        print(f"❌ 文件不存在: {file_path}")
        sys.exit(1)

    cfg = load_config()

    # 创建 OSS 认证和 Bucket 对象
    auth = oss2.Auth(cfg['access_key_id'], cfg['access_key_secret'])
    bucket = oss2.Bucket(auth, cfg['endpoint'], cfg['bucket'])

    filename = os.path.basename(file_path)
    content_type = get_content_type(filename)
    file_size = os.path.getsize(file_path)

    if not object_key:
        now = datetime.now()
        object_key = f"{now.strftime('%Y/%m/%d')}/{filename}"

    oss_url = f"https://{cfg['bucket']}.{cfg['endpoint']}/{object_key}"

    print(f"⬆ 上传中: {filename} ({human_size(file_size)}) → {cfg['bucket']}/{object_key}")

    # 检查是否已存在
    try:
        if bucket.object_exists(object_key):
            print(f"⚠ 目标已存在，将覆盖")
    except Exception:
        pass

    try:
        bucket.put_object_from_file(
            object_key,
            file_path,
            headers={'Content-Type': content_type, 'x-oss-object-acl': 'public-read'},
        )

        print(f"✅ 上传成功")
        print(f"🔗 URL: {oss_url}")
        print(f"📋 Markdown: [{filename}]({oss_url})")
        print(f"📦 Size: {human_size(file_size)} | Type: {content_type}")

    except oss2.exceptions.OssError as e:
        print(f"❌ 上传失败: {e.status} {e.code} {e.message}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ 上传失败: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()