"""
音乐会员供应商

支持: QQ音乐、网易云音乐、酷狗音乐、酷我音乐
模式: 卡密池 + API直充（备用）

卡密池路径: data/card_pools/music_cards.json
格式同 video_member，产品ID如:
  "qqmusic_month"  — QQ音乐月卡
  "netease_month"  — 网易云音乐月卡
  "kugou_month"    — 酷狗音乐月卡
  "kuwo_month"     — 酷我音乐月卡
"""

import os
import json
from typing import Optional
from loguru import logger

from supplier.base import SupplierBase, OrderRequest, FulfillResult


class MusicMemberSupplier(SupplierBase):
    """音乐会员供应商"""

    def __init__(self, config: dict):
        super().__init__(config)
        self.card_pool_path = config.get("card_pool_path", "data/card_pools/music_cards.json")
        self._ensure_card_pool()

    def _ensure_card_pool(self):
        full_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), self.card_pool_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        if not os.path.exists(full_path):
            with open(full_path, "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=2)

    def _load_pool(self) -> dict:
        full_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), self.card_pool_path)
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save_pool(self, pool: dict):
        full_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), self.card_pool_path)
        with open(full_path, "w", encoding="utf-8") as f:
            json.dump(pool, f, ensure_ascii=False, indent=2)

    def _consume_card(self, product_id: str) -> Optional[str]:
        pool = self._load_pool()
        cards = pool.get(product_id, [])
        for card in cards:
            if card.get("status") == "unused":
                card["status"] = "used"
                self._save_pool(pool)
                return card["code"]
        return None

    def _count_stock(self, product_id: str) -> int:
        pool = self._load_pool()
        return sum(1 for c in pool.get(product_id, []) if c.get("status") == "unused")

    async def query_price(self, product_id: str) -> dict:
        stock = self._count_stock(product_id)
        prices = self.config.get("prices", {})
        name_map = {
            "qqmusic_month": "QQ音乐月卡",
            "qqmusic_year": "QQ音乐年卡",
            "netease_month": "网易云音乐月卡",
            "netease_year": "网易云音乐年卡",
            "kugou_month": "酷狗音乐月卡",
            "kuwo_month": "酷我音乐月卡",
        }
        return {
            "price": prices.get(product_id, 0),
            "product_name": name_map.get(product_id, product_id),
            "in_stock": stock > 0,
            "stock": stock,
        }

    async def fulfill(self, order: OrderRequest) -> FulfillResult:
        product_id = order.product_id

        # 优先消耗卡密
        card_code = self._consume_card(product_id)
        if card_code:
            stock = self._count_stock(product_id)
            return FulfillResult(
                success=True,
                trade_no=order.order_id,
                card_code=card_code,
                message=f"卡密: {card_code}\n\n剩余库存: {stock}张\n\n请按卡密链接兑换会员",
            )

        # 备用: API直充
        if self.api_url and self.api_key:
            return await self._api_fulfill(order)

        return FulfillResult(success=False, message=f"卡密库存不足: {product_id}")

    async def _api_fulfill(self, order: OrderRequest) -> FulfillResult:
        try:
            import aiohttp
            payload = {
                "api_key": self.api_key,
                "product_id": order.product_id,
                "account": order.buyer_account,
                "trade_no": order.order_id,
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(f"{self.api_url}/recharge", json=payload, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    data = await resp.json()
                    if data.get("code") == 0:
                        return FulfillResult(
                            success=True, trade_no=data.get("trade_no", ""),
                            message=f"直充成功: {order.buyer_account}", raw_response=data,
                        )
                    return FulfillResult(success=False, message=data.get("msg", "直充失败"))
        except Exception as e:
            return FulfillResult(success=False, message=f"API直充异常: {e}")

    async def query_status(self, trade_no: str) -> dict:
        return {"status": "completed", "message": "卡密已发放"}

    def add_cards(self, product_id: str, codes: list[str]):
        pool = self._load_pool()
        if product_id not in pool:
            pool[product_id] = []
        for code in codes:
            pool[product_id].append({"code": code, "status": "unused"})
        self._save_pool(pool)
        logger.info(f"添加卡密: {product_id} +{len(codes)}张，库存: {self._count_stock(product_id)}")
