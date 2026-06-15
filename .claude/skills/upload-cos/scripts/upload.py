#!/usr/bin/env python3
"""Upload a local file to Tencent Cloud COS and return a public URL."""

import sys
import os
import yaml
from datetime import datetime

try:
    from qcloud_cos import CosConfig, CosS3Client
except ImportError:
    print("❌ cos_python_sdk_v5 not installed. Run: pip3 install cos_python_sdk_v5")
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
    '.m4a': 'audio/mp4',
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
    config_path = os.path.expanduser('~/.cos.yaml')
    with open(config_path) as f:
        cfg = yaml.safe_load(f)
    base = cfg.get('base', {})
    bucket = base.get('bucket', '')
    appid = bucket.split('-')[-1]
    return {
        'secretid': base.get('secretid', ''),
        'secretkey': base.get('secretkey', ''),
        'bucket': bucket,
        'region': base.get('region', 'ap-guangzhou'),
        'appid': appid,
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
    config = CosConfig(Region=cfg['region'], SecretId=cfg['secretid'], SecretKey=cfg['secretkey'])
    client = CosS3Client(config)

    filename = os.path.basename(file_path)
    content_type = get_content_type(filename)
    file_size = os.path.getsize(file_path)
    is_html = content_type.startswith('text/html')

    bucket = f"webpages-{cfg['appid']}" if is_html else cfg['bucket']

    if not object_key:
        now = datetime.now()
        object_key = f"{now.strftime('%Y/%m/%d')}/{filename}"

    cos_url = f"https://{bucket}.cos.{cfg['region']}.myqcloud.com/{object_key}"
    website_url = f"https://{bucket}.cos-website.{cfg['region']}.myqcloud.com/{object_key}"
    display_url = website_url if is_html else cos_url

    print(f"⬆ 上传中: {filename} ({human_size(file_size)}) → {bucket}/{object_key}")

    try:
        head = client.head_object(Bucket=bucket, Key=object_key)
        existing_size = head.get('Content-Length', 'unknown')
        print(f"⚠ 目标已存在 ({human_size(int(existing_size)) if existing_size != 'unknown' else existing_size})，将覆盖")
    except Exception:
        pass

    with open(file_path, 'rb') as f:
        content = f.read()

    try:
        response = client.put_object(
            Bucket=bucket,
            Body=content,
            Key=object_key,
            ACL='public-read',
            ContentType=content_type,
            EnableMD5=False
        )

        print(f"✅ 上传成功")
        print(f"🔗 URL: {display_url}")
        if is_html:
            print(f"🌐 浏览: {website_url}")
            print(f"💾 下载: {cos_url}")
        else:
            print(f"💾 直链: {cos_url}")
        print(f"📋 Markdown: [{filename}]({display_url})")
        print(f"📦 Size: {human_size(file_size)} | Type: {content_type}")

    except Exception as e:
        print(f"❌ 上传失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
