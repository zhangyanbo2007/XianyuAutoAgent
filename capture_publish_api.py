#!/usr/bin/env python3
"""
闲鱼发布接口抓包工具

用途: 在浏览器中操作一次发布商品，脚本自动捕获发布相关的 API 请求

使用步骤:
  1. 以调试模式启动 Chrome:
     chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome_debug

  2. 在浏览器中登录闲鱼 (www.goofish.com)

  3. 运行本脚本:
     python capture_publish_api.py

  4. 在浏览器中手动发布一个商品（或保存草稿）

  5. 脚本会自动捕获并保存 API 请求参数到 captured_api.json

  6. 把 captured_api.json 发给 Claude，我来帮你对接
"""

import json
import time
import sys

try:
    import websocket
except ImportError:
    print("请先安装: pip install websocket-client")
    sys.exit(1)

try:
    import requests
except ImportError:
    pass


def get_chrome_ws_url(port=9222):
    """获取 Chrome DevTools WebSocket URL"""
    try:
        resp = requests.get(f"http://127.0.0.1:{port}/json")
        tabs = resp.json()
        for tab in tabs:
            if "goofish" in tab.get("url", "") or "xianyu" in tab.get("url", ""):
                return tab["webSocketDebuggerUrl"]
        # 如果没有闲鱼 tab，用第一个
        if tabs:
            return tabs[0]["webSocketDebuggerUrl"]
    except Exception as e:
        print(f"无法连接 Chrome (端口 {port}): {e}")
        print("\n请先启动 Chrome 调试模式:")
        print("  google-chrome --remote-debugging-port=9222 --user-data-dir=/tmp/chrome_debug")
        return None
    return None


class PublishApiCapture:
    """捕获闲鱼发布相关的 API 请求"""

    # 与发布相关的关键词
    PUBLISH_KEYWORDS = [
        "publish", "draft", "save", "submit", "upload",
        "category", "item", "post", "create",
    ]

    def __init__(self):
        self.captured = []
        self.ws = None

    def on_message(self, ws, message):
        try:
            data = json.loads(message)
            method = data.get("method", "")

            # 捕获网络请求
            if method == "Network.requestWillBeSent":
                request = data["params"]["request"]
                url = request.get("url", "")
                method_name = request.get("method", "")

                # 过滤 MTOP API 请求
                if "h5api.m.goofish.com" in url or "mtop.taobao.idle" in url:
                    post_data = request.get("postData", "")
                    entry = {
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "url": url,
                        "method": method_name,
                        "headers": dict(request.get("headers", {})),
                        "post_data": post_data[:2000] if post_data else "",
                    }
                    self.captured.append(entry)
                    print(f"  📡 捕获: {url.split('?')[0][-60:]}")

            # 捕获 WebSocket 消息（如果发布走 WS）
            elif method == "Network.webSocketFrameSent":
                payload = data["params"].get("response", {}).get("payloadData", "")
                if any(kw in payload.lower() for kw in self.PUBLISH_KEYWORDS):
                    entry = {
                        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
                        "type": "websocket",
                        "data": payload[:2000],
                    }
                    self.captured.append(entry)
                    print(f"  📡 WS 消息捕获 ({len(payload)} bytes)")

        except Exception as e:
            pass

    def on_error(self, ws, error):
        print(f"WebSocket 错误: {error}")

    def on_close(self, ws, close_status_code, close_msg):
        print("连接关闭")

    def on_open(self, ws):
        # 启用网络监听
        ws.send(json.dumps({"id": 1, "method": "Network.enable", "params": {}}))
        print("✅ 已连接 Chrome，开始监听网络请求...")
        print("👉 请在浏览器中操作发布商品，完成后按 Ctrl+C 停止\n")

    def start(self, port=9222):
        ws_url = get_chrome_ws_url(port)
        if not ws_url:
            return

        print(f"连接到: {ws_url[:60]}...")
        self.ws = websocket.WebSocketApp(
            ws_url,
            on_message=self.on_message,
            on_error=self.on_error,
            on_close=self.on_close,
            on_open=self.on_open,
        )
        self.ws.run_forever()

    def save(self, filename="captured_api.json"):
        with open(filename, "w", encoding="utf-8") as f:
            json.dump(self.captured, f, ensure_ascii=False, indent=2)
        print(f"\n💾 已保存 {len(self.captured)} 条请求到 {filename}")


if __name__ == "__main__":
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 9222
    capture = PublishApiCapture()
    try:
        capture.start(port)
    except KeyboardInterrupt:
        print("\n停止捕获...")
        capture.save()
