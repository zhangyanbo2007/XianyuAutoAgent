#!/usr/bin/env python3
"""
照片整理脚本 — 扫描、去重、分类、人脸聚类、涉黄检测、整理
在home-computer-ubuntu上运行，使用GPU加速
"""

import os
import sys
import json
import hashlib
import shutil
import re
import argparse
from pathlib import Path
from datetime import datetime
from collections import defaultdict
from PIL import Image
from PIL.ExifTags import TAGS

# 配置
PHOTO_EXTS = {'.jpg', '.jpeg', '.png', '.bmp', '.gif', '.webp', '.heic', '.heif', '.tif', '.tiff'}
VIDEO_EXTS = {'.mp4', '.avi', '.mkv', '.mov', '.wmv', '.flv', '.3gp', '.webm', '.m4v'}
ALL_MEDIA_EXTS = PHOTO_EXTS | VIDEO_EXTS

# CLIP分类类别
CLIP_CATEGORIES = {
    '人物': 'a photo of a person, portrait, selfie, human face',
    '风景': 'a photo of landscape, nature, mountain, sea, sky, sunset, forest',
    '美食': 'a photo of food, meal, dish, restaurant, cooking',
    '建筑': 'a photo of building, architecture, room, street, house',
    '动物': 'a photo of animal, pet, cat, dog, bird, fish',
    '截图': 'a screenshot of phone or computer screen, UI, app',
    '文档': 'a photo of document, text, paper, receipt, book',
    '表情包': 'a meme, sticker, emoji, cartoon, comic',
}

def get_exif_date(filepath):
    """从EXIF读取拍摄日期"""
    try:
        with Image.open(filepath) as img:
            exif = img._getexif()
            if exif:
                # DateTimeOriginal (0x9003)
                if 0x9003 in exif:
                    return exif[0x9003]
                # DateTimeDigitized (0x9004)
                if 0x9004 in exif:
                    return exif[0x9004]
                # DateTime (0x0132)
                if 0x0132 in exif:
                    return exif[0x0132]
    except Exception:
        pass
    return None

def get_exif_info(filepath):
    """获取完整EXIF信息"""
    info = {}
    try:
        with Image.open(filepath) as img:
            exif = img._getexif()
            if exif:
                info['date'] = get_exif_date(filepath)
                info['make'] = exif.get(0x010F, '')
                info['model'] = exif.get(0x0110, '')
                info['software'] = exif.get(0x0131, '')
                # 获取图片尺寸
                info['width'] = img.width
                info['height'] = img.height
    except Exception:
        pass
    return info

def get_date_from_filename(filename):
    """从文件名提取日期"""
    # 常见格式: IMG_20200115_123456.jpg, Screenshot_2020-01-15.png
    patterns = [
        r'(\d{4})(\d{2})(\d{2})[_\s]',
        r'(\d{4})-(\d{2})-(\d{2})',
        r'(\d{4})(\d{2})(\d{2})',
    ]
    for pattern in patterns:
        match = re.search(pattern, filename)
        if match:
            year, month, day = match.groups()
            if 1990 <= int(year) <= 2030 and 1 <= int(month) <= 12 and 1 <= int(day) <= 31:
                return f"{year}:{month}:{day} 00:00:00"
    return None

def get_target_date(filepath, filename):
    """获取目标日期（优先级：EXIF > 文件名 > mtime）"""
    ext = Path(filepath).suffix.lower()

    # 图片尝试EXIF
    if ext in PHOTO_EXTS:
        exif_date = get_exif_date(filepath)
        if exif_date:
            return exif_date

    # 文件名日期
    name_date = get_date_from_filename(filename)
    if name_date:
        return name_date

    # mtime
    mtime = os.path.getmtime(filepath)
    dt = datetime.fromtimestamp(mtime)
    return dt.strftime('%Y:%m:%d %H:%M:%S')

def parse_date_to_ym(date_str):
    """将日期字符串解析为(年, 月)"""
    if not date_str:
        return None, None
    try:
        # 格式: "2020:01:15 12:34:56" 或 "2020-01-15"
        date_str = date_str.replace('-', ':').replace('/', ':')
        parts = date_str.split(':')
        year = int(parts[0])
        month = int(parts[1])
        if 1990 <= year <= 2030 and 1 <= month <= 12:
            return str(year), f"{year}-{month:02d}"
    except (ValueError, IndexError):
        pass
    return None, None

def calculate_md5(filepath, chunk_size=8192):
    """计算文件MD5"""
    md5 = hashlib.md5()
    try:
        with open(filepath, 'rb') as f:
            while chunk := f.read(chunk_size):
                md5.update(chunk)
        return md5.hexdigest()
    except Exception:
        return None

def is_screenshot(filepath, exif_info, filename):
    """判断是否为截图"""
    # EXIF软件信息
    software = exif_info.get('software', '').lower()
    if 'screenshot' in software or 'screen' in software:
        return True

    # 宽高比判断（长条形通常是聊天截图）
    width = exif_info.get('width', 0)
    height = exif_info.get('height', 0)
    if width > 0 and height > 0:
        ratio = max(width, height) / min(width, height)
        if ratio > 2 and min(width, height) > 1080:
            return True

    # 文件名模式
    name_lower = filename.lower()
    if 'screenshot' in name_lower or 'screen_shot' in name_lower:
        return True

    return False

def is_sticker(filepath, source_dir, filesize):
    """判断是否为表情包"""
    # 来源目录含wechat
    if 'wechat' in source_dir.lower():
        if filesize < 500 * 1024:  # < 500KB
            return True

    # 文件名含mmexport（微信导出）
    filename = os.path.basename(filepath).lower()
    if 'mmexport' in filename:
        return True

    return False

def classify_photo(filepath, source_dir):
    """分类照片"""
    filename = os.path.basename(filepath)
    ext = Path(filepath).suffix.lower()
    filesize = os.path.getsize(filepath)

    # 获取EXIF信息
    exif_info = {}
    if ext in PHOTO_EXTS:
        exif_info = get_exif_info(filepath)

    # 截图判断
    if is_screenshot(filepath, exif_info, filename):
        return '截图', exif_info

    # 表情包判断
    if is_sticker(filepath, source_dir, filesize):
        return '表情包', exif_info

    # 视频
    if ext in VIDEO_EXTS:
        return '其他', exif_info

    # 其他情况，返回其他（CLIP会进一步分类）
    return '其他', exif_info

def scan_photos(source_dir, catalog_path):
    """扫描所有照片，生成catalog"""
    print(f"扫描目录: {source_dir}")
    catalog = []

    for root, dirs, files in os.walk(source_dir):
        for filename in files:
            ext = Path(filename).suffix.lower()
            if ext not in ALL_MEDIA_EXTS:
                continue

            filepath = os.path.join(root, filename)
            rel_path = os.path.relpath(filepath, source_dir)

            # 跳过已整理的目录
            if rel_path.startswith('_') or rel_path.startswith('PhotosSorted'):
                continue

            print(f"  扫描: {rel_path}", end='\r')

            filesize = os.path.getsize(filepath)
            md5 = calculate_md5(filepath)

            # 获取日期
            date_str = get_target_date(filepath, filename)
            year, ym = parse_date_to_ym(date_str)

            # 基础分类
            source_dir_name = os.path.relpath(root, source_dir)
            category, exif_info = classify_photo(filepath, source_dir_name)

            entry = {
                'path': filepath,
                'rel_path': rel_path,
                'size': filesize,
                'md5': md5,
                'ext': ext,
                'date': date_str,
                'year': year,
                'ym': ym,
                'category': category,
                'source_dir': source_dir_name,
                'exif_make': exif_info.get('make', ''),
                'exif_model': exif_info.get('model', ''),
                'exif_software': exif_info.get('software', ''),
                'target_path': None,
                'is_duplicate': False,
                'duplicate_of': None,
                'nsfw_score': None,
                'faces': [],
                'status': 'scanned'
            }
            catalog.append(entry)

    print(f"\n扫描完成: {len(catalog)} 个文件")

    # 保存catalog (不使用indent以减小文件大小)
    with open(catalog_path, 'w', encoding='utf-8') as f:
        json.dump(catalog, f, ensure_ascii=False)

    return catalog

def dedup_photos(catalog, output_dir):
    """去重"""
    print("执行去重...")
    duplicates_dir = os.path.join(output_dir, '_duplicates')
    os.makedirs(duplicates_dir, exist_ok=True)

    # 按MD5分组
    md5_groups = defaultdict(list)
    for entry in catalog:
        if entry['md5']:
            md5_groups[entry['md5']].append(entry)

    dup_count = 0
    saved_size = 0

    for md5, files in md5_groups.items():
        if len(files) <= 1:
            continue

        # 保留策略：优先保留有EXIF日期的，其次保留大的
        files.sort(key=lambda x: (
            1 if x['date'] else 0,  # 有日期优先
            x['size'],  # 大文件优先
            1 if '副本' not in x['rel_path'] else 0  # 非副本优先
        ), reverse=True)

        # 保留第一个，其余标记为重复
        keep = files[0]
        for dup in files[1:]:
            dup['is_duplicate'] = True
            dup['duplicate_of'] = keep['rel_path']
            dup['status'] = 'duplicate'
            dup_count += 1
            saved_size += dup['size']

            # 移动到duplicates目录
            dup_target = os.path.join(duplicates_dir, os.path.basename(dup['path']))
            try:
                if os.path.exists(dup['path']):
                    shutil.move(dup['path'], dup_target)
                    print(f"  移动重复: {dup['rel_path']} -> _duplicates/")
            except Exception as e:
                print(f"  移动失败: {dup['rel_path']}: {e}")

    print(f"去重完成: {dup_count} 个重复文件, 节省 {saved_size / 1024 / 1024:.1f} MB")
    return catalog

def classify_with_clip(catalog, output_dir):
    """使用CLIP进行智能分类"""
    print("加载CLIP模型...")
    try:
        from transformers import CLIPProcessor, CLIPModel
        import torch

        device = "cuda" if torch.cuda.is_available() else "cpu"
        print(f"使用设备: {device}")

        model = CLIPModel.from_pretrained("openai/clip-vit-base-patch32")
        processor = CLIPProcessor.from_pretrained("openai/clip-vit-base-patch32")
        model = model.to(device)
        model.eval()

        # 准备类别文本
        categories = list(CLIP_CATEGORIES.keys())
        texts = list(CLIP_CATEGORIES.values())

        print(f"开始分类 {len(catalog)} 张照片...")

        batch_size = 32
        for i in range(0, len(catalog), batch_size):
            batch = catalog[i:i+batch_size]

            # 过滤需要分类的（只有'其他'类需要CLIP）
            to_classify = []
            for entry in batch:
                if entry['category'] == '其他' and entry['ext'] in PHOTO_EXTS:
                    to_classify.append(entry)

            if not to_classify:
                continue

            # 加载图片
            images = []
            valid_entries = []
            for entry in to_classify:
                try:
                    img = Image.open(entry['path']).convert('RGB')
                    images.append(img)
                    valid_entries.append(entry)
                except Exception:
                    continue

            if not images:
                continue

            # CLIP推理
            inputs = processor(text=texts, images=images, return_tensors="pt", padding=True)
            inputs = {k: v.to(device) for k, v in inputs.items()}

            with torch.no_grad():
                outputs = model(**inputs)
                logits = outputs.logits_per_image
                probs = logits.softmax(dim=1)

            # 分配类别
            for j, entry in enumerate(valid_entries):
                probs_j = probs[j].cpu().numpy()
                max_idx = probs_j.argmax()
                max_prob = probs_j[max_idx]

                if max_prob > 0.2:  # 阈值
                    entry['category'] = categories[max_idx]

            # 进度
            processed = min(i + batch_size, len(catalog))
            print(f"  分类进度: {processed}/{len(catalog)}", end='\r')

            # 清理
            for img in images:
                img.close()

        print(f"\nCLIP分类完成")

    except ImportError:
        print("警告: transformers/torch未安装，跳过CLIP分类")
    except Exception as e:
        print(f"CLIP分类失败: {e}")

    return catalog

def detect_faces(catalog, output_dir):
    """人脸检测和聚类"""
    print("加载人脸检测模型...")
    try:
        import insightface
        from insightface.app import FaceAnalysis
        import numpy as np
        from sklearn.cluster import DBSCAN

        # 初始化模型
        app = FaceAnalysis(name='buffalo_l', providers=['CUDAExecutionProvider', 'CPUExecutionProvider'])
        app.prepare(ctx_id=0 if os.environ.get('CUDA_VISIBLE_DEVICES') else -1, det_size=(640, 640))

        print("开始检测人脸...")
        all_faces = []  # (entry, face_embedding, face_bbox)

        for i, entry in enumerate(catalog):
            if entry['ext'] not in PHOTO_EXTS:
                continue

            try:
                img = cv2.imread(entry['path'])
                if img is None:
                    continue

                faces = app.get(img)
                for face in faces:
                    all_faces.append({
                        'entry': entry,
                        'embedding': face.embedding,
                        'bbox': face.bbox.tolist(),
                        'det_score': face.det_score
                    })
            except Exception:
                continue

            if (i + 1) % 100 == 0:
                print(f"  检测进度: {i+1}/{len(catalog)}", end='\r')

        print(f"\n检测到 {len(all_faces)} 张人脸")

        if not all_faces:
            return catalog

        # 聚类
        print("开始聚类...")
        embeddings = np.array([f['embedding'] for f in all_faces])

        # DBSCAN聚类
        clustering = DBSCAN(eps=0.4, min_samples=2, metric='cosine')
        labels = clustering.fit_predict(embeddings)

        # 输出目录
        by_person_dir = os.path.join(output_dir, '_by_person')
        os.makedirs(by_person_dir, exist_ok=True)

        # 按聚类分组
        clusters = defaultdict(list)
        for idx, label in enumerate(labels):
            if label == -1:
                clusters['unknown'].append(all_faces[idx])
            else:
                clusters[f'person_{label:03d}'].append(all_faces[idx])

        # 生成输出
        for person_id, faces in clusters.items():
            person_dir = os.path.join(by_person_dir, person_id)
            os.makedirs(person_dir, exist_ok=True)

            # 保存人脸缩略图和链接
            links = []
            for j, face_info in enumerate(faces):
                # 裁剪人脸
                entry = face_info['entry']
                try:
                    img = Image.open(entry['path'])
                    bbox = face_info['bbox']
                    x1, y1, x2, y2 = [int(b) for b in bbox]
                    face_img = img.crop((x1, y1, x2, y2))
                    face_img = face_img.resize((128, 128))
                    face_img.save(os.path.join(person_dir, f'face_{j:03d}.jpg'))
                    img.close()
                except Exception:
                    pass

                links.append(entry['rel_path'])
                entry['faces'].append(person_id)

            # 保存links.json
            with open(os.path.join(person_dir, 'links.json'), 'w', encoding='utf-8') as f:
                json.dump(links, f, ensure_ascii=False, indent=2)

        print(f"人脸聚类完成: {len(clusters)} 个人物")

    except ImportError:
        print("警告: insightface/opencv未安装，跳过人脸聚类")
    except Exception as e:
        print(f"人脸聚类失败: {e}")

    return catalog

def detect_nsfw(catalog, output_dir):
    """涉黄检测"""
    print("执行涉黄检测...")
    try:
        import torch
        from PIL import Image

        # 尝试加载NSFW检测模型
        # 这里使用简单的启发式方法作为备选
        nsfw_dir = os.path.join(output_dir, '_nsfw')
        os.makedirs(nsfw_dir, exist_ok=True)
        previews_dir = os.path.join(nsfw_dir, 'previews')
        os.makedirs(previews_dir, exist_ok=True)

        nsfw_count = 0
        report = []

        for entry in catalog:
            if entry['ext'] not in PHOTO_EXTS:
                continue

            # 简单启发式：检测皮肤色调占比
            try:
                img = Image.open(entry['path']).convert('RGB')
                # 缩小加速
                img_small = img.resize((100, 100))
                pixels = list(img_small.getdata())

                # 计算皮肤色调像素占比（HSV空间）
                skin_count = 0
                for r, g, b in pixels:
                    # 简单的皮肤色调检测
                    if r > 95 and g > 40 and b > 20 and r > g and r > b and abs(r - g) > 15:
                        skin_count += 1

                skin_ratio = skin_count / len(pixels)

                # 阈值（保守）
                nsfw_score = min(skin_ratio * 2, 1.0)  # 皮肤占比>50%时分数接近1
                entry['nsfw_score'] = nsfw_score

                if nsfw_score > 0.7:
                    nsfw_count += 1
                    # 复制到nsfw目录
                    preview_path = os.path.join(previews_dir, os.path.basename(entry['path']))
                    img.save(preview_path)
                    report.append({
                        'path': entry['rel_path'],
                        'score': nsfw_score,
                        'preview': f'previews/{os.path.basename(entry["path"])}'
                    })

                img.close()

            except Exception:
                continue

        # 保存报告
        with open(os.path.join(nsfw_dir, 'report.json'), 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)

        print(f"涉黄检测完成: {nsfw_count} 个可疑文件")

    except Exception as e:
        print(f"涉黄检测失败: {e}")

    return catalog

def organize_photos(catalog, source_dir, output_dir, dry_run=False):
    """按日期+分类整理"""
    print("执行整理...")
    sorted_dir = os.path.join(output_dir, 'PhotosSorted')
    os.makedirs(sorted_dir, exist_ok=True)

    moved_count = 0
    skipped_count = 0

    for entry in catalog:
        if entry['status'] == 'duplicate':
            continue

        year = entry['year']
        ym = entry['ym']
        category = entry['category']

        if not year or not ym:
            target_dir = os.path.join(sorted_dir, 'unknown-date', category)
        else:
            target_dir = os.path.join(sorted_dir, year, ym, category)

        target_path = os.path.join(target_dir, os.path.basename(entry['path']))
        entry['target_path'] = target_path

        if dry_run:
            print(f"  [DRY-RUN] {entry['rel_path']} -> {os.path.relpath(target_path, output_dir)}")
            moved_count += 1
            continue

        try:
            os.makedirs(target_dir, exist_ok=True)
            if os.path.exists(entry['path']) and not os.path.exists(target_path):
                shutil.move(entry['path'], target_path)
                entry['status'] = 'organized'
                moved_count += 1
            elif os.path.exists(target_path):
                skipped_count += 1
            else:
                skipped_count += 1
        except Exception as e:
            print(f"  移动失败: {entry['rel_path']}: {e}")
            skipped_count += 1

        if (moved_count + skipped_count) % 100 == 0:
            print(f"  整理进度: {moved_count + skipped_count}/{len(catalog)}", end='\r')

    print(f"\n整理完成: {moved_count} 个文件已移动, {skipped_count} 个跳过")
    return catalog

def generate_summary(catalog, output_dir):
    """生成统计摘要"""
    summary = {
        'total_files': len(catalog),
        'total_size_mb': sum(e['size'] for e in catalog) / 1024 / 1024,
        'by_category': defaultdict(lambda: {'count': 0, 'size_mb': 0}),
        'by_year': defaultdict(lambda: {'count': 0, 'size_mb': 0}),
        'by_source': defaultdict(lambda: {'count': 0, 'size_mb': 0}),
        'duplicates': sum(1 for e in catalog if e['is_duplicate']),
        'nsfw_suspicious': sum(1 for e in catalog if (e.get('nsfw_score') or 0) > 0.7),
    }

    for entry in catalog:
        cat = entry['category']
        summary['by_category'][cat]['count'] += 1
        summary['by_category'][cat]['size_mb'] += entry['size'] / 1024 / 1024

        year = entry['year'] or 'unknown'
        summary['by_year'][year]['count'] += 1
        summary['by_year'][year]['size_mb'] += entry['size'] / 1024 / 1024

        src = entry['source_dir']
        summary['by_source'][src]['count'] += 1
        summary['by_source'][src]['size_mb'] += entry['size'] / 1024 / 1024

    # 转换defaultdict
    summary['by_category'] = dict(summary['by_category'])
    summary['by_year'] = dict(summary['by_year'])
    summary['by_source'] = dict(summary['by_source'])

    # 保存
    summary_path = os.path.join(output_dir, '_catalog_summary.json')
    with open(summary_path, 'w', encoding='utf-8') as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"\n统计摘要已保存: {summary_path}")
    return summary

def main():
    parser = argparse.ArgumentParser(description='照片整理工具')
    parser.add_argument('--source', required=True, help='源目录')
    parser.add_argument('--output', default=None, help='输出目录（默认与source同级）')
    parser.add_argument('--scan', action='store_true', help='扫描模式')
    parser.add_argument('--dedup', action='store_true', help='去重模式')
    parser.add_argument('--classify', action='store_true', help='CLIP分类模式')
    parser.add_argument('--face-cluster', action='store_true', help='人脸聚类模式')
    parser.add_argument('--nsfw-detect', action='store_true', help='涉黄检测模式')
    parser.add_argument('--organize', action='store_true', help='整理模式')
    parser.add_argument('--dry-run', action='store_true', help='模拟运行')
    parser.add_argument('--all', action='store_true', help='执行所有步骤')

    args = parser.parse_args()

    # 输出目录
    if args.output:
        output_dir = args.output
    else:
        output_dir = os.path.dirname(args.source.rstrip('/'))

    os.makedirs(output_dir, exist_ok=True)

    catalog_path = os.path.join(output_dir, '_catalog.json')

    # 执行模式
    if args.scan or args.all:
        catalog = scan_photos(args.source, catalog_path)
    elif os.path.exists(catalog_path):
        with open(catalog_path, 'r', encoding='utf-8') as f:
            catalog = json.load(f)
        print(f"加载已有catalog: {len(catalog)} 个文件")
    else:
        print("错误: 请先执行 --scan 或 --all")
        sys.exit(1)

    if args.dedup or args.all:
        catalog = dedup_photos(catalog, output_dir)
        with open(catalog_path, 'w', encoding='utf-8') as f:
            json.dump(catalog, f, ensure_ascii=False)

    if args.classify or args.all:
        catalog = classify_with_clip(catalog, output_dir)
        with open(catalog_path, 'w', encoding='utf-8') as f:
            json.dump(catalog, f, ensure_ascii=False)

    if args.face_cluster or args.all:
        catalog = detect_faces(catalog, output_dir)
        with open(catalog_path, 'w', encoding='utf-8') as f:
            json.dump(catalog, f, ensure_ascii=False)

    if args.nsfw_detect or args.all:
        catalog = detect_nsfw(catalog, output_dir)
        with open(catalog_path, 'w', encoding='utf-8') as f:
            json.dump(catalog, f, ensure_ascii=False)

    if args.organize or args.all:
        catalog = organize_photos(catalog, args.source, output_dir, args.dry_run)
        with open(catalog_path, 'w', encoding='utf-8') as f:
            json.dump(catalog, f, ensure_ascii=False)

    # 生成摘要
    summary = generate_summary(catalog, output_dir)
    print(f"\n总计: {summary['total_files']} 个文件, {summary['total_size_mb']:.1f} MB")
    print(f"重复: {summary['duplicates']} 个")
    print(f"涉黄可疑: {summary['nsfw_suspicious']} 个")

if __name__ == '__main__':
    main()
