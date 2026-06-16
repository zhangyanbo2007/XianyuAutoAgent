"""
游戏点券/皮肤供应商

对接游戏充值平台API，支持:
  - 原神创世结晶
  - 王者荣耀点券
  - 和平精英UC
  - Steam钱包充值
  - 其他手游点券

典型对接方式:
  1. 注册游戏充值分销平台（如 5173、交易猫、九一游戏）
  2. 获取 API 接口文档
  3. 传入玩家账号/区服 + 充值档位 → 自动到账

注意: 不同游戏的充值参数差异较大:
  - 手游: 通常需要 游戏区服 + 角色名/ID
  - Steam: 需要 钱包充值链接 或 账号
  - 主机: 需要 对应平台账号
"""

import time
import hashlib
import asyncio
from loguru import logger

from supplier.base import SupplierBase, OrderRequest, FulfillResult


# ── 游戏充值档位映射 ──
GAME_PRODUCTS = {
    # 原神
    "genshin_60": {"name": "原神 创世结晶×60", "amount": 60, "real_price": 6.0},
    "genshin_300": {"name": "原神 创世结晶×300", "amount": 300, "real_price": 30.0},
    "genshin_980": {"name": "原神 创世结晶×980", "amount": 980, "real_price": 98.0},
    "genshin_1980": {"name": "原神 创世结晶×1980", "amount": 1980, "real_price": 198.0},
    "genshin_3280": {"name": "原神 创世结晶×3280", "amount": 3280, "real_price": 328.0},
    "genshin_6480": {"name": "原神 创世结晶×6480", "amount": 6480, "real_price": 648.0},

    # 王者荣耀
    "wzry_10": {"name": "王者荣耀 点券×10", "amount": 10, "real_price": 1.0},
    "wzry_60": {"name": "王者荣耀 点券×60", "amount": 60, "real_price": 6.0},
    "wzry_300": {"name": "王者荣耀 点券×300", "amount": 300, "real_price": 30.0},
    "wzry_680": {"name": "王者荣耀 点券×680", "amount": 680, "real_price": 68.0},
    "wzry_1280": {"name": "王者荣耀 点券×1280", "amount": 1280, "real_price": 128.0},
    "wzry_3480": {"name": "王者荣耀 点券×3480", "amount": 3480, "real_price": 348.0},
    "wzry_6480": {"name": "王者荣耀 点券×6480", "amount": 6480, "real_price": 648.0},

    # 和平精英
    "pubg_60": {"name": "和平精英 UC×60", "amount": 60, "real_price": 6.0},
    "pubg_300": {"name": "和平精英 UC×300", "amount": 300, "real_price": 30.0},
    "pubg_980": {"name": "和平精英 UC×980", "amount": 980, "real_price": 98.0},
    "pubg_1980": {"name": "和平精英 UC×1980", "amount": 1980, "real_price": 198.0},
    "pubg_3280": {"name": "和平精英 UC×3280", "amount": 3280, "real_price": 328.0},
    "pubg_6480": {"name": "和平精英 UC×6480", "amount": 6480, "real_price": 648.0},

    # Steam
    "steam_30": {"name": "Steam钱包 ¥30", "amount": 30, "real_price": 30.0},
    "steam_60": {"name": "Steam钱包 ¥60", "amount": 60, "real_price": 60.0},
    "steam_98": {"name": "Steam钱包 ¥98", "amount": 98, "real_price": 98.0},
    "steam_198": {"name": "Steam钱包 ¥198", "amount": 198, "real_price": 198.0},
    "steam_298": {"name": "Steam钱包 ¥298", "amount": 298, "real_price": 298.0},
}


class GameCreditSupplier(SupplierBase):
    """游戏点券充值供应商"""

    async def query_price(self, product_id: str) -> dict:
        """查询游戏充值价格"""
        product = GAME_PRODUCTS.get(product_id)
        if not product:
            return {"price": 0, "product_name": "", "in_stock": False}

        fee_rate = self.config.get("fee_rate", 0.05)
        cost_price = round(product["real_price"] * (1 + fee_rate), 2)

        return {
            "price": cost_price,
            "product_name": product["name"],
            "in_stock": True,
        }

    async def fulfill(self, order: OrderRequest) -> FulfillResult:
        """
        执行游戏充值

        买家需提供:
          - order.buyer_account: 游戏角色ID或账号
          - order.extra["game_server"]: 游戏区服（手游必需）
          - order.extra["game_role"]: 角色名（手游必需）
          - order.product_id: 充值档位ID（如 "genshin_6480"）
        """
        product = GAME_PRODUCTS.get(order.product_id)
        if not product:
            return FulfillResult(success=False, message=f"未知充值档位: {order.product_id}")

        game_account = order.buyer_account
        game_server = order.extra.get("game_server", "")
        game_role = order.extra.get("game_role", "")

        # ── 调用上游API ──
        if not self.api_url or not self.api_key:
            return FulfillResult(
                success=False,
                message=f"游戏充值供应商未配置，请在 suppliers.yaml 中填写 api_url 和 api_key\n"
                        f"需要充值: {product['name']}，账号: {game_account}",
            )

        timestamp = str(int(time.time()))
        sign_str = f"{self.api_key}{order.product_id}{game_account}{timestamp}{self.api_secret}"
        sign = hashlib.md5(sign_str.encode()).hexdigest()

        payload = {
            "api_key": self.api_key,
            "product_id": order.product_id,
            "account": game_account,
            "server": game_server,
            "role": game_role,
            "trade_no": order.order_id,
            "timestamp": timestamp,
            "sign": sign,
        }

        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/game/recharge",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=30),
                ) as resp:
                    data = await resp.json()

                    if data.get("code") == 0:
                        return FulfillResult(
                            success=True,
                            trade_no=data.get("trade_no", order.order_id),
                            message=f"{product['name']} 充值已提交\n账号: {game_account}\n区服: {game_server}\n角色: {game_role}",
                            raw_response=data,
                        )
                    return FulfillResult(
                        success=False,
                        message=data.get("msg", "游戏充值失败"),
                        raw_response=data,
                    )
        except Exception as e:
            return FulfillResult(success=False, message=f"请求异常: {e}")

    async def query_status(self, trade_no: str) -> dict:
        if not self.api_url:
            return {"status": "unknown", "message": "未配置API"}
        try:
            import aiohttp
            async with aiohttp.ClientSession() as session:
                async with session.get(
                    f"{self.api_url}/game/query",
                    params={"api_key": self.api_key, "trade_no": trade_no},
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    data = await resp.json()
                    return {
                        "status": data.get("status", "unknown"),
                        "message": data.get("msg", ""),
                        "raw": data,
                    }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    @staticmethod
    def list_products() -> dict:
        """列出所有支持的游戏充值产品"""
        return {k: v["name"] for k, v in GAME_PRODUCTS.items()}
