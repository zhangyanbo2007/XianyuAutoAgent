"""
视频会员供应商

支持两种模式:
  1. 卡密池模式 — 从上游批发商处购买卡密，导入本地 JSON 文件，发货时逐个消耗
  2. API直充模式 — 部分供应商支持账号直充（较少见）

卡密池文件格式 (data/card_pools/video_cards.json):
{
  "iqiyi_month": [
    {"code": "XXXX-XXXX-XXXX", "status": "unused"},
    {"code": "YYYY-YYYY-YYYY", "status": "unused"}
  ],
  "youku_month": [...],
  "tencent_month": [...]
}

补充卡密: 直接编辑 JSON 文件，在对应产品ID下追加新卡密即可。
"""

import os
import json
import asyncio
from typing import Optional
from loguru import logger

from supplier.base import SupplierBase, OrderRequest, FulfillResult


class VideoMemberSupplier(SupplierBase):
    """视频会员供应商（卡密池模式为主）"""

    def __init__(self, config: dict):
        super().__init__(config)
        self.card_pool_path = config.get("card_pool_path", "data/card_pools/video_cards.json")
        self._ensure_card_pool()

    def _ensure_card_pool(self):
        """确保卡密池文件存在"""
        full_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), self.card_pool_path)
        os.makedirs(os.path.dirname(full_path), exist_ok=True)
        if not os.path.exists(full_path):
            with open(full_path, "w", encoding="utf-8") as f:
                json.dump({}, f, ensure_ascii=False, indent=2)
            logger.info(f"创建空卡密池: {full_path}")

    def _load_card_pool(self) -> dict:
        """加载卡密池"""
        full_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), self.card_pool_path)
        try:
            with open(full_path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, FileNotFoundError):
            return {}

    def _save_card_pool(self, pool: dict):
        """保存卡密池"""
        full_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), self.card_pool_path)
        with open(full_path, "w", encoding="utf-8") as f:
            json.dump(pool, f, ensure_ascii=False, indent=2)

    def _consume_card(self, product_id: str) -> Optional[str]:
        """从卡密池消耗一张卡密"""
        pool = self._load_card_pool()
        cards = pool.get(product_id, [])
        for card in cards:
            if card.get("status") == "unused":
                card["status"] = "used"
                self._save_card_pool(pool)
                return card["code"]
        return None

    def _count_stock(self, product_id: str) -> int:
        """统计某产品剩余库存"""
        pool = self._load_card_pool()
        cards = pool.get(product_id, [])
        return sum(1 for c in cards if c.get("status") == "unused")

    async def query_price(self, product_id: str) -> dict:
        """查询视频会员进货价"""
        stock = self._count_stock(product_id)
        # 价格从配置读取，或用默认值
        prices = self.config.get("prices", {})
        price = prices.get(product_id, 0)

        name_map = {
            "iqiyi_month": "爱奇艺月卡",
            "youku_month": "优酷月卡",
            "tencent_month": "腾讯视频月卡",
            "mango_month": "芒果TV月卡",
            "iqiyi_year": "爱奇艺年卡",
            "youku_year": "优酷年卡",
            "tencent_year": "腾讯视频年卡",
        }

        return {
            "price": price,
            "product_name": name_map.get(product_id, product_id),
            "in_stock": stock > 0,
            "stock": stock,
        }

    async def fulfill(self, order: OrderRequest) -> FulfillResult:
        """
        发放视频会员卡密

        买家账号格式: 不需要账号，直接发卡密
        产品ID从 order.product_id 获取，如 "iqiyi_month"
        """
        product_id = order.product_id

        # 尝试消耗卡密
        card_code = self._consume_card(product_id)
        if card_code:
            stock = self._count_stock(product_id)
            return FulfillResult(
                success=True,
                trade_no=order.order_id,
                card_code=card_code,
                message=f"卡密: {card_code}\n\n剩余库存: {stock}张\n\n请按卡密链接兑换会员",
            )

        # 无库存，尝试API直充（如果配置了）
        if self.api_url and self.api_key:
            return await self._api_fulfill(order)

        return FulfillResult(
            success=False,
            message=f"卡密库存不足: {product_id}，请补充卡密",
        )

    async def _api_fulfill(self, order: OrderRequest) -> FulfillResult:
        """API直充模式（备用）"""
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
                            success=True,
                            trade_no=data.get("trade_no", ""),
                            message=f"直充成功: {order.buyer_account}",
                            raw_response=data,
                        )
                    return FulfillResult(success=False, message=data.get("msg", "直充失败"))
        except Exception as e:
            return FulfillResult(success=False, message=f"API直充异常: {e}")

    async def query_status(self, trade_no: str) -> dict:
        return {"status": "completed", "message": "卡密已发放"}

    def add_cards(self, product_id: str, codes: list[str]):
        """批量添加卡密（管理接口）"""
        pool = self._load_card_pool()
        if product_id not in pool:
            pool[product_id] = []
        for code in codes:
            pool[product_id].append({"code": code, "status": "unused"})
        self._save_card_pool(pool)
        logger.info(f"添加卡密: {product_id} +{len(codes)}张，当前库存: {self._count_stock(product_id)}")
