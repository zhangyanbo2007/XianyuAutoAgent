#!/usr/bin/env python3
"""
自动化抓包: 注入Cookie → 打开闲鱼 → 探测发布接口 → 保存结果
无需人工操作，全自动运行
"""

import os
import json
import time
import asyncio
from dotenv import load_dotenv

load_dotenv()

from playwright.async_api import async_playwright


def parse_cookies(cookie_str: str) -> list:
    cookies = []
    for pair in cookie_str.split("; "):
        if "=" in pair:
            name, value = pair.split("=", 1)
            cookies.append({
                "name": name.strip(),
                "value": value.strip(),
                "domain": ".goofish.com",
                "path": "/",
            })
    return cookies


async def main():
    cookie_str = os.getenv("COOKIES_STR", "")
    if not cookie_str:
        print("❌ COOKIES_STR 未配置")
        return

    captured = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True, args=["--no-sandbox"])
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        )

        # 注入 Cookie
        cookies = parse_cookies(cookie_str)
        await context.add_cookies(cookies)
        print(f"✅ 注入 {len(cookies)} 个 Cookie")

        page = await context.new_page()

        # 监听网络请求
        def on_request(request):
            url = request.url
            if "h5api.m.goofish.com" in url or "mtop.taobao" in url:
                api_name = ""
                if "api=" in url:
                    api_name = url.split("api=")[1].split("&")[0]
                entry = {
                    "time": time.strftime("%H:%M:%S"),
                    "api": api_name,
                    "url": url.split("?")[0],
                    "method": request.method,
                    "post_data": (request.post_data or "")[:500],
                }
                captured.append(entry)
                print(f"  📡 {request.method} {api_name}")

        page.on("request", on_request)

        # ── 步骤1: 打开闲鱼首页 ──
        print("\n[1/4] 打开闲鱼首页...")
        await page.goto("https://www.goofish.com/", wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(2000)
        title = await page.title()
        print(f"  页面: {title}")

        # ── 步骤2: 检查登录状态 ──
        print("\n[2/4] 检查登录状态...")
        try:
            # 查找用户头像或用户名
            avatar = page.locator('.user-avatar, .avatar, [class*="avatar"], [class*="user"]').first
            if await avatar.is_visible(timeout=3000):
                print("  ✅ 已登录")
            else:
                print("  ⚠️ 未检测到登录状态（Cookie可能已过期）")
        except:
            print("  ⚠️ 无法确认登录状态")

        # ── 步骤3: 尝试各种发布入口 ──
        print("\n[3/4] 探测发布入口...")

        publish_entry_points = [
            # 直接URL
            ("URL", "https://www.goofish.com/publish"),
            ("URL", "https://post.goofish.com/publish"),
            ("URL", "https://www.goofish.com/sell"),
            ("URL", "https://www.goofish.com/post/publish"),
            ("URL", "https://www.goofish.com/idle/publish"),
        ]

        for method, url in publish_entry_points:
            try:
                resp = await page.goto(url, wait_until="domcontentloaded", timeout=8000)
                status = resp.status if resp else "no response"
                current = page.url
                print(f"  {method} {url[-40:]} → {status} → {current[-50:]}")
                if resp and resp.status == 200:
                    await page.wait_for_timeout(2000)
                    # 检查页面内容
                    body = await page.content()
                    if "发布" in body or "publish" in body.lower():
                        print(f"    ✅ 疑似发布页面!")
            except Exception as e:
                print(f"  {method} {url[-40:]} → {e}")

        # ── 步骤4: 尝试在页面上找发布入口 ──
        print("\n[4/4] 在页面上查找发布按钮...")
        await page.goto("https://www.goofish.com/", wait_until="domcontentloaded", timeout=15000)
        await page.wait_for_timeout(2000)

        # 查找所有包含"发布"的链接和按钮
        try:
            publish_links = await page.locator('a:has-text("发布"), button:has-text("发布"), [class*="publish"]').all()
            print(f"  找到 {len(publish_links)} 个发布相关元素")
            for i, link in enumerate(publish_links[:5]):
                text = await link.text_content()
                href = await link.get_attribute("href") or "no-href"
                print(f"    [{i}] {text.strip()[:30]} → {href[:60]}")
        except Exception as e:
            print(f"  查找失败: {e}")

        # ── 输出结果 ──
        print(f"\n{'='*60}")
        print(f"📡 共捕获 {len(captured)} 个 MTOP API 请求:")
        print(f"{'='*60}")
        seen = set()
        for c in captured:
            key = c["api"]
            if key and key not in seen:
                seen.add(key)
                print(f"  {c['method']} {key}")
                if c["post_data"]:
                    print(f"    data: {c['post_data'][:200]}")
        print(f"{'='*60}")

        # 保存完整结果
        with open("captured_api.json", "w", encoding="utf-8") as f:
            json.dump(captured, f, ensure_ascii=False, indent=2)
        print(f"\n💾 完整请求已保存到 captured_api.json")

        # 输出当前页面截图路径
        await page.screenshot(path="captured_screenshot.png")
        print(f"📸 页面截图已保存到 captured_screenshot.png")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
