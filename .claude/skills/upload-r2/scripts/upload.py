#!/usr/bin/env python3
"""Upload a local file to Cloudflare R2 and return a public URL."""

import sys
import os
import yaml
import boto3
from datetime import datetime

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
    config_path = os.path.expanduser('~/.r2.yaml')
    if not os.path.exists(config_path):
        print(f"❌ 凭证文件不存在: {config_path}")
        print("请按 SKILL.md 说明创建 ~/.r2.yaml")
        sys.exit(1)
    with open(config_path) as f:
        cfg = yaml.safe_load(f)
    r2 = cfg.get('r2', {})
    if not r2.get('account_id') or not r2.get('access_key_id') or not r2.get('secret_access_key'):
        print("❌ ~/.r2.yaml 缺少必要字段 (account_id, access_key_id, secret_access_key)")
        sys.exit(1)
    return r2

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

    endpoint_url = f"https://{cfg['account_id']}.r2.cloudflarestorage.com"
    bucket = cfg.get('bucket', 'xiaowangzi-files')
    public_url = cfg.get('public_url', '')

    s3 = boto3.client(
        's3',
        endpoint_url=endpoint_url,
        aws_access_key_id=cfg['access_key_id'],
        aws_secret_access_key=cfg['secret_access_key'],
        region_name='auto',
    )

    
    filename = os.path.basename(file_path)
    content_type = get_content_type(filename)
    file_size = os.path.getsize(file_path)

    if not object_key:
        now = datetime.now()
        object_key = f"{now.strftime('%Y/%m/%d')}/{filename}"

    # Build public URL
    if public_url:
        url = f"{public_url.rstrip('/')}/{object_key}"
    else:
        url = f"https://{bucket}.{cfg['account_id']}.r2.cloudflarestorage.com/{object_key}"

    print(f"⬆ 上传中: {filename} ({human_size(file_size)}) → {bucket}/{object_key}")

    try:
        s3.head_object(Bucket=bucket, Key=object_key)
        print(f"⚠ 目标已存在，将覆盖")
    except Exception:
        pass

    extra_args = {'ContentType': content_type}

    # HTML files: ensure inline display
    if content_type.startswith('text/html'):
        extra_args['ContentDisposition'] = 'inline'

    try:
        s3.upload_file(file_path, bucket, object_key, ExtraArgs=extra_args)

        print(f"✅ 上传成功")
        print(f"🔗 URL: {url}")
        print(f"📋 Markdown: [{filename}]({url})")
        print(f"📦 Size: {human_size(file_size)} | Type: {content_type}")

    except Exception as e:
        print(f"❌ 上传失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()