#!/usr/bin/env python3
"""
照片分类客户端 — 在mobile-computer上运行，调用home-computer-ubuntu的GPU服务
"""

import os
import sys
import json
import requests
import argparse
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed

# 服务地址（蒲公英网络）
SERVER_URL = "http://172.16.1.183:8899"

PHOTO_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.heic', '.heif', '.tif', '.tiff'}

def check_server():
    """检查服务是否可用"""
    try:
        resp = requests.get(f"{SERVER_URL}/health", timeout=5)
        return resp.json()
    except Exception as e:
        return {"status": "error", "error": str(e)}

def classify_image(filepath):
    """分类单张图片"""
    try:
        with open(filepath, 'rb') as f:
            resp = requests.post(
                f"{SERVER_URL}/classify",
                files={"file": (os.path.basename(filepath), f, "image/jpeg")},
                timeout=30
            )
        if resp.status_code == 200:
            return resp.json()
        else:
            return {"error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def classify_batch(filepaths):
    """批量分类"""
    try:
        files = []
        for fp in filepaths:
            with open(fp, 'rb') as f:
                files.append(("files", (os.path.basename(fp), f.read(), "image/jpeg")))

        resp = requests.post(
            f"{SERVER_URL}/classify_batch",
            files=files,
            timeout=60
        )
        if resp.status_code == 200:
            return resp.json()
        else:
            return {"error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def detect_faces(filepath):
    """检测人脸"""
    try:
        with open(filepath, 'rb') as f:
            resp = requests.post(
                f"{SERVER_URL}/detect_faces",
                files={"file": (os.path.basename(filepath), f, "image/jpeg")},
                timeout=30
            )
        if resp.status_code == 200:
            return resp.json()
        else:
            return {"error": f"HTTP {resp.status_code}"}
    except Exception as e:
        return {"error": str(e)}

def load_catalog(catalog_path):
    """加载catalog"""
    with open(catalog_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_catalog(catalog, catalog_path):
    """保存catalog"""
    with open(catalog_path, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, ensure_ascii=False, indent=2)

def main():
    parser = argparse.ArgumentParser(description='照片分类客户端')
    parser.add_argument('--catalog', required=True, help='catalog文件路径')
    parser.add_argument('--check', action='store_true', help='检查服务状态')
    parser.add_argument('--classify', action='store_true', help='执行分类')
    parser.add_argument('--faces', action='store_true', help='执行人脸检测')
    parser.add_argument('--batch-size', type=int, default=8, help='批量大小')
    parser.add_argument('--workers', type=int, default=4, help='并发数')

    args = parser.parse_args()

    # 检查服务
    if args.check:
        print("检查服务状态...")
        status = check_server()
        print(json.dumps(status, indent=2, ensure_ascii=False))
        return

    # 加载catalog
    print(f"加载catalog: {args.catalog}")
    catalog = load_catalog(args.catalog)
    print(f"共 {len(catalog)} 个文件")

    # 筛选需要分类的文件（只有"其他"类的图片）
    to_classify = [e for e in catalog if e['category'] == '其他' and e['ext'] in PHOTO_EXTS]
    print(f"需要分类: {len(to_classify)} 个文件")

    if args.classify:
        print("开始分类...")
        batch_size = args.batch_size
        total = len(to_classify)
        processed = 0

        for i in range(0, total, batch_size):
            batch = to_classify[i:i+batch_size]
            filepaths = [e['path'] for e in batch]

            # 调用批量分类API
            result = classify_batch(filepaths)

            if 'results' in result:
                for j, res in enumerate(result['results']):
                    batch[j]['category'] = res['category']
                    processed += 1

            if processed % 100 == 0:
                print(f"  进度: {processed}/{total}")

                # 定期保存
                save_catalog(catalog, args.catalog)

        # 最后保存
        save_catalog(catalog, args.catalog)
        print(f"分类完成: {processed} 个文件")

    if args.faces:
        print("开始人脸检测...")
        to_detect = [e for e in catalog if e['ext'] in PHOTO_EXTS]
        total = len(to_detect)
        processed = 0
        faces_found = 0

        for e in to_detect:
            result = detect_faces(e['path'])
            if 'faces' in result and result['faces']:
                e['faces'] = [f"detected_{i}" for i in range(len(result['faces']))]
                faces_found += 1

            processed += 1
            if processed % 100 == 0:
                print(f"  进度: {processed}/{total}, 发现人脸: {faces_found}")
                save_catalog(catalog, args.catalog)

        save_catalog(catalog, args.catalog)
        print(f"人脸检测完成: {processed} 个文件, {faces_found} 个含人脸")

    # 输出统计
    print("\n分类统计:")
    from collections import Counter
    cat_counter = Counter(e['category'] for e in catalog)
    for cat, count in cat_counter.most_common():
        print(f"  {cat}: {count}")

if __name__ == '__main__':
    main()
