"""
软件激活码供应商

支持: Office 365、Windows、Adobe、JetBrains 等
模式: 卡密池（主流）

卡密池路径: data/card_pools/software_cards.json
产品ID示例:
  "office365_1y"   — Office 365 一年
  "office365_1m"   — Office 365 一个月
  "win11_pro"      — Windows 11 Pro
  "adobe_1y"       — Adobe 全家桶一年
  "jetbrains_1y"   — JetBrains 全家桶一年

进货渠道:
  1. 正规授权分销商（微软/Adobe合作商）
  2. 批量采购教育授权
  3. OEM密钥（合法但有限制）

⚠️ 重要: 只走正规授权渠道，不卖盗版/破解
"""

import os
import json
from typing import Optional
from loguru import logger

from supplier.base import SupplierBase, OrderRequest, FulfillResult


class SoftwareKeySupplier(SupplierBase):
    """软件激活码供应商"""

    def __init__(self, config: dict):
        super().__init__(config)
        self.card_pool_path = config.get("card_pool_path", "data/card_pools/software_cards.json")
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
            "office365_1y": "Office 365 一年",
            "office365_1m": "Office 365 一个月",
            "win11_pro": "Windows 11 Pro",
            "win11_home": "Windows 11 Home",
            "adobe_1y": "Adobe 全家桶 一年",
            "adobe_1m": "Adobe 全家桶 一个月",
            "jetbrains_1y": "JetBrains 全家桶 一年",
            "jetbrains_1m": "JetBrains 全家桶 一个月",
        }
        return {
            "price": prices.get(product_id, 0),
            "product_name": name_map.get(product_id, product_id),
            "in_stock": stock > 0,
            "stock": stock,
        }

    async def fulfill(self, order: OrderRequest) -> FulfillResult:
        product_id = order.product_id

        card_code = self._consume_card(product_id)
        if card_code:
            stock = self._count_stock(product_id)
            return FulfillResult(
                success=True,
                trade_no=order.order_id,
                card_code=card_code,
                message=(
                    f"激活码: {card_code}\n\n"
                    f"剩余库存: {stock}个\n\n"
                    f"使用方法:\n"
                    f"1. 打开对应软件\n"
                    f"2. 输入激活码\n"
                    f"3. 完成激活\n\n"
                    f"如有问题请联系卖家"
                ),
            )

        return FulfillResult(success=False, message=f"激活码库存不足: {product_id}，请补充")

    async def query_status(self, trade_no: str) -> dict:
        return {"status": "completed", "message": "激活码已发放"}

    def add_cards(self, product_id: str, codes: list[str]):
        pool = self._load_pool()
        if product_id not in pool:
            pool[product_id] = []
        for code in codes:
            pool[product_id].append({"code": code, "status": "unused"})
        self._save_pool(pool)
        logger.info(f"添加激活码: {product_id} +{len(codes)}个，库存: {self._count_stock(product_id)}")
