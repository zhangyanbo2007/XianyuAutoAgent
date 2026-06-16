#!/usr/bin/env python3
"""
闲鱼商品发布 CLI

用法:
  python publish_cmd.py list              列出所有商品模板
  python publish_cmd.py preview 0         预览第0个商品
  python publish_cmd.py draft             所有商品创建草稿
  python publish_cmd.py draft 0 1 3       指定索引创建草稿
  python publish_cmd.py categories        查看闲鱼分类ID
  python publish_cmd.py test              测试 Cookie 有效性
"""

import os
import sys
import json
import argparse
from dotenv import load_dotenv
from loguru import logger

# 加载环境变量
if os.path.exists(".env"):
    load_dotenv()

from XianyuApis import XianyuApis
from XianyuPublish import XianyuPublish
from product_manager import ProductManager
from utils.xianyu_utils import trans_cookies, generate_device_id


def get_publish_api() -> XianyuPublish:
    """初始化发布API"""
    cookies_str = os.getenv("COOKIES_STR", "")
    if not cookies_str:
        logger.error("COOKIES_STR 未配置，请在 .env 中设置")
        sys.exit(1)

    xianyu = XianyuApis()
    cookies = trans_cookies(cookies_str)
    xianyu.session.cookies.update(cookies)

    # 验证登录
    user_id = cookies.get("unb", "")
    if not user_id:
        logger.error("Cookie 中缺少 unb 字段，可能未登录")
        sys.exit(1)

    logger.info(f"已登录用户: {user_id}")
    return XianyuPublish(xianyu.session)


def cmd_list(args):
    """列出所有商品模板"""
    pm = ProductManager()
    products = pm.list_all()
    if not products:
        print("没有商品模板，请编辑 products.yaml")
        return

    print(f"\n📦 共 {len(products)} 个商品模板:\n")
    for i, p in enumerate(products):
        price = p.get("price", 0)
        skus = p.get("sku_list", [])
        sku_info = f" ({len(skus)}个SKU)" if skus else ""
        print(f"  [{i}] {p['title'][:35]}  ¥{price}{sku_info}")
    print()


def cmd_preview(args):
    """预览某个商品"""
    pm = ProductManager()
    product = pm.get(args.index)
    if not product:
        print(f"索引 {args.index} 不存在")
        return

    print(f"\n{'='*50}")
    print(f"标题: {product['title']}")
    print(f"价格: ¥{product.get('price', 0)}")
    print(f"品类: {product.get('category', '未设置')}")
    print(f"图片: {len(product.get('images', []))}张")
    print(f"\n描述:\n{product.get('desc', '无')}")
    if product.get("sku_list"):
        print(f"\nSKU:")
        for sku in product["sku_list"]:
            print(f"  - {sku['name']}: ¥{sku['price']}")
    print(f"{'='*50}\n")


def cmd_draft(args):
    """创建草稿"""
    pm = ProductManager()
    products = pm.list_all()

    if not products:
        print("没有商品模板")
        return

    # 确定要发布的商品
    if args.indices:
        indices = args.indices
        products = [pm.get(i) for i in indices if pm.get(i) is not None]
    else:
        products = pm.list_all()

    if not products:
        print("指定的商品不存在")
        return

    print(f"\n即将为 {len(products)} 个商品创建草稿:")
    for i, p in enumerate(products):
        print(f"  [{i+1}] {p['title'][:40]}  ¥{p.get('price', 0)}")

    confirm = input("\n确认发布？(y/N): ").strip().lower()
    if confirm != "y":
        print("已取消")
        return

    # 初始化发布API
    api = get_publish_api()
    publish_list = pm.to_publish_list()

    if args.indices:
        publish_list = [publish_list[i] for i in args.indices if i < len(publish_list)]

    # 创建草稿
    interval = args.interval
    results = api.batch_create_drafts(publish_list, interval=interval)

    # 输出结果
    print(f"\n{'='*50}")
    success = 0
    for r in results:
        status = "✓" if r["result"]["success"] else "✗"
        msg = r["result"]["message"]
        print(f"  {status} {r['title'][:30]}  →  {msg}")
        if r["result"]["success"]:
            success += 1
    print(f"\n结果: {success}/{len(results)} 成功")
    print(f"{'='*50}\n")


def cmd_categories(args):
    """查看闲鱼分类"""
    api = get_publish_api()
    result = api.get_publish_categories()
    if result:
        categories = result.get("categories", [])
        print(f"\n📋 闲鱼商品分类 (共 {len(categories)} 个):\n")
        for cat in categories:
            print(f"  ID: {cat.get('id', 'N/A')}")
            print(f"  名称: {cat.get('name', 'N/A')}")
            children = cat.get("children", [])
            if children:
                for child in children:
                    print(f"    └─ {child.get('id', 'N/A')}: {child.get('name', 'N/A')}")
            print()
    else:
        print("获取分类失败，可能 Cookie 已过期")


def cmd_test(args):
    """测试 Cookie 是否有效"""
    api = get_publish_api()
    # 尝试调用一个简单接口
    result = api._post_api("mtop.taobao.idle.publish.category.get", {"type": "1"})
    ret = result.get("ret", [])
    if any("SUCCESS" in r for r in ret):
        print("✅ Cookie 有效，可以正常调用闲鱼 API")
    else:
        print(f"❌ Cookie 可能已过期: {ret}")


def cmd_add(args):
    """交互式添加商品"""
    pm = ProductManager()

    print("\n📦 添加新商品模板\n")
    title = input("商品标题: ").strip()
    if not title:
        print("标题不能为空")
        return

    desc = input("商品描述 (支持换行，输入空行结束):\n")
    lines = []
    while True:
        line = input()
        if line == "":
            break
        lines.append(line)
    desc = "\n".join(lines) if lines else desc

    price_str = input("价格 (元): ").strip()
    try:
        price = float(price_str)
    except ValueError:
        price = 0.0

    category = input("品类 (video_member/phone_topup/game_credit/music_member/software_key/coupon_deal): ").strip()

    product = {
        "title": title,
        "desc": desc,
        "price": price,
        "category": category,
        "images": [],
        "sku_list": [],
    }

    idx = pm.add(product)
    print(f"\n✅ 已添加，索引: {idx}")


def main():
    parser = argparse.ArgumentParser(description="闲鱼商品发布工具")
    subparsers = parser.add_subparsers(dest="command", help="子命令")

    # list
    subparsers.add_parser("list", help="列出所有商品模板")

    # preview
    p_preview = subparsers.add_parser("preview", help="预览商品")
    p_preview.add_argument("index", type=int, help="商品索引")

    # draft
    p_draft = subparsers.add_parser("draft", help="创建草稿")
    p_draft.add_argument("indices", nargs="*", type=int, help="商品索引（不填则全部）")
    p_draft.add_argument("-i", "--interval", type=int, default=30, help="发布间隔秒数")

    # categories
    subparsers.add_parser("categories", help="查看闲鱼分类ID")

    # test
    subparsers.add_parser("test", help="测试 Cookie 有效性")

    # add
    subparsers.add_parser("add", help="交互式添加商品")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        return

    commands = {
        "list": cmd_list,
        "preview": cmd_preview,
        "draft": cmd_draft,
        "categories": cmd_categories,
        "test": cmd_test,
        "add": cmd_add,
    }
    commands[args.command](args)


if __name__ == "__main__":
    main()
