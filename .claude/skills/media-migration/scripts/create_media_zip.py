#!/usr/bin/env python3
"""
create_media_zip.py - 创建媒体文件ZIP包（用于跨平台传输）
用法: python3 create_media_zip.py <source_dir> <output_zip> [photo|video|all]
"""
import zipfile
import os
import sys

PHOTO_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.heic', '.tif', '.tiff'}
VIDEO_EXTS = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.3gp', '.webm', '.m4v'}

def create_zip(source_dir, output_zip, media_type='all'):
    if media_type == 'photo':
        allowed_exts = PHOTO_EXTS
    elif media_type == 'video':
        allowed_exts = VIDEO_EXTS
    else:
        allowed_exts = PHOTO_EXTS | VIDEO_EXTS

    count = 0
    total_size = 0
    skipped = 0

    with zipfile.ZipFile(output_zip, 'w', zipfile.ZIP_STORED) as zf:
        for root, dirs, files in os.walk(source_dir):
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in allowed_exts:
                    full_path = os.path.join(root, f)
                    # 跳过含冒号的文件（Windows不支持）
                    if ':' in f:
                        skipped += 1
                        continue
                    rel_path = os.path.relpath(full_path, os.path.dirname(source_dir))
                    try:
                        zf.write(full_path, rel_path)
                        count += 1
                        total_size += os.path.getsize(full_path)
                        if count % 500 == 0:
                            print(f'  Added {count} files ({total_size/1024/1024/1024:.2f} GB)...')
                    except Exception as e:
                        print(f'  SKIP: {full_path}: {e}')

    print(f'Done! {count} files, {total_size/1024/1024/1024:.2f} GB')
    if skipped > 0:
        print(f'Skipped {skipped} files with colon in name')
    print(f'ZIP saved to: {output_zip}')

if __name__ == '__main__':
    if len(sys.argv) < 3:
        print('Usage: python3 create_media_zip.py <source_dir> <output_zip> [photo|video|all]')
        sys.exit(1)

    source_dir = sys.argv[1]
    output_zip = sys.argv[2]
    media_type = sys.argv[3] if len(sys.argv) > 3 else 'all'

    if not os.path.exists(source_dir):
        print(f'Error: {source_dir} does not exist')
        sys.exit(1)

    create_zip(source_dir, output_zip, media_type)
