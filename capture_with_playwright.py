#!/usr/bin/env python3
"""
用 Playwright 打开闲鱼，自动注入 Cookie，捕获发布接口

流程:
  1. 启动浏览器（有界面）
  2. 注入 .env 中的 Cookie
  3. 打开发布页面
  4. 监听所有网络请求，过滤出 mtop.taobao.idle.*
  5. 输出捕获到的接口信息
"""

import os
import json
import time
import asyncio
from dotenv import load_dotenv

load_dotenv()

from playwright.async_api import async_playwright


def parse_cookies(cookie_str: str, domain: str = ".goofish.com") -> list:
    """将 Cookie 字符串转为 Playwright 格式"""
    cookies = []
    for pair in cookie_str.split("; "):
        if "=" in pair:
            name, value = pair.split("=", 1)
            cookies.append({
                "name": name.strip(),
                "value": value.strip(),
                "domain": domain,
                "path": "/",
            })
    return cookies


async def main():
    cookie_str = os.getenv("COOKIES_STR", "")
    if not cookie_str:
        print("❌ COOKIES_STR 未配置")
        return

    captured_requests = []

    async with async_playwright() as p:
        # 启动有界面的浏览器
        browser = await p.chromium.launch(headless=False, args=["--no-sandbox"])
        context = await browser.new_context(
            viewport={"width": 1280, "height": 800},
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
        )

        # 注入 Cookie
        cookies = parse_cookies(cookie_str)
        await context.add_cookies(cookies)
        print(f"✅ 已注入 {len(cookies)} 个 Cookie")

        page = await context.new_page()

        # 监听所有请求
        def on_request(request):
            url = request.url
            if "h5api.m.goofish.com" in url or "mtop.taobao.idle" in url:
                entry = {
                    "timestamp": time.strftime("%H:%M:%S"),
                    "url": url,
                    "method": request.method,
                    "post_data": request.post_data[:1000] if request.post_data else "",
                    "headers": dict(request.headers) if request.headers else {},
                }
                captured_requests.append(entry)
                # 简化输出
                api_name = ""
                if "api=" in url:
                    api_name = url.split("api=")[1].split("&")[0]
                elif "/h5/" in url:
                    parts = url.split("/h5/")[1].split("/")
                    api_name = parts[0] if parts else ""
                print(f"  📡 [{entry['method']}] {api_name or url[-50:]}")

        page.on("request", on_request)

        # 打开闲鱼
        print("\n🌐 正在打开闲鱼...")
        await page.goto("https://www.goofish.com/", wait_until="domcontentloaded")
        await page.wait_for_timeout(3000)

        # 检查是否登录
        title = await page.title()
        print(f"页面标题: {title}")

        # 尝试打开发布页面
        print("\n📝 正在打开发布页面...")

        # 方法1: 直接访问发布URL
        publish_urls = [
            "https://www.goofish.com/publish",
            "https://www.goofish.com/sell",
            "https://post.goofish.com/publish",
        ]

        for url in publish_urls:
            try:
                resp = await page.goto(url, wait_until="domcontentloaded", timeout=10000)
                if resp and resp.status == 200:
                    print(f"✅ 打开: {url}")
                    await page.wait_for_timeout(3000)
                    break
                else:
                    print(f"  ✗ {url} → {resp.status if resp else 'no response'}")
            except Exception as e:
                print(f"  ✗ {url} → {e}")

        # 方法2: 在页面上找发布按钮
        try:
            publish_btn = page.locator('text=发布').first
            if await publish_btn.is_visible(timeout=3000):
                print("找到发布按钮，点击...")
                await publish_btn.click()
                await page.wait_for_timeout(3000)
        except:
            pass

        print(f"\n📡 当前已捕获 {len(captured_requests)} 个 API 请求")
        print("👉 浏览器已打开，请手动操作发布流程")
        print("   操作完成后按 Enter 保存结果\n")

        # 等待用户操作
        input("按 Enter 继续...")

        # 保存结果
        output_file = "captured_api.json"
        with open(output_file, "w", encoding="utf-8") as f:
            json.dump(captured_requests, f, ensure_ascii=False, indent=2)
        print(f"\n💾 已保存 {len(captured_requests)} 条请求到 {output_file}")

        # 也输出当前页面URL
        current_url = page.url
        print(f"当前页面: {current_url}")

        await browser.close()


if __name__ == "__main__":
    asyncio.run(main())
