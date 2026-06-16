"""
供应商路由器 — 根据商品关键词匹配品类，选择最优供应商执行发货
"""

import os
import re
import importlib
import yaml
from typing import Optional
from loguru import logger

from supplier.base import (
    SupplierBase, ProductCategory, OrderRequest, FulfillResult
)


class SupplierRouter:
    """
    供应商路由器

    流程:
      1. 根据商品标题/描述关键词匹配品类
      2. 从 suppliers.yaml 加载该品类的供应商列表（按 priority 排序）
      3. 依次尝试，成功则返回，失败自动切换下一家
    """

    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "suppliers.yaml")

        with open(config_path, "r", encoding="utf-8") as f:
            self.config = yaml.safe_load(f)

        self.suppliers: dict[str, list[SupplierBase]] = {}
        self.category_keywords: dict[str, list[str]] = self.config.get("category_keywords", {})
        self._load_all_suppliers()
        logger.info(f"路由器初始化完成，已加载 {sum(len(v) for v in self.suppliers.values())} 个供应商")

    def _load_all_suppliers(self):
        """加载所有启用的供应商"""
        for category, supplier_configs in self.config.get("suppliers", {}).items():
            self.suppliers[category] = []
            # 按 priority 排序
            sorted_configs = sorted(supplier_configs, key=lambda x: x.get("priority", 99))
            for cfg in sorted_configs:
                if not cfg.get("enabled", False):
                    continue
                try:
                    module_path = cfg.get("module", "")
                    if not module_path:
                        continue
                    module = importlib.import_module(module_path)
                    # 模块内约定: 导出一个同品类名的类（如 PhoneTopupSupplier）
                    class_name = self._module_to_class(category)
                    supplier_cls = getattr(module, class_name)
                    supplier_instance = supplier_cls(cfg)
                    self.suppliers[category].append(supplier_instance)
                    logger.info(f"  ✓ [{category}] {cfg['name']} (priority={cfg.get('priority', 99)})")
                except Exception as e:
                    logger.error(f"  ✗ [{category}] {cfg['name']} 加载失败: {e}")

    @staticmethod
    def _module_to_class(category: str) -> str:
        """品类名 → 类名映射，如 phone_topup → PhoneTopupSupplier"""
        mapping = {
            "phone_topup": "PhoneTopupSupplier",
            "video_member": "VideoMemberSupplier",
            "game_credit": "GameCreditSupplier",
            "music_member": "MusicMemberSupplier",
            "coupon_deal": "CouponDealSupplier",
            "software_key": "SoftwareKeySupplier",
        }
        return mapping.get(category, "SupplierBase")

    # ── 品类识别 ──

    def classify(self, title: str, desc: str = "") -> ProductCategory:
        """
        根据商品标题+描述识别品类

        Returns:
            ProductCategory 枚举值
        """
        text = f"{title} {desc}".lower()

        # 按关键词匹配，优先匹配更具体的品类
        # 顺序: software_key > game_credit > music_member > video_member > coupon_deal > phone_topup
        # music_member 必须在 video_member 之前（否则"QQ音乐会匹配到"会员"）
        priority_order = [
            ProductCategory.SOFTWARE_KEY,
            ProductCategory.GAME_CREDIT,
            ProductCategory.MUSIC_MEMBER,
            ProductCategory.VIDEO_MEMBER,
            ProductCategory.COUPON_DEAL,
            ProductCategory.PHONE_TOPUP,
        ]

        for cat in priority_order:
            keywords = self.category_keywords.get(cat.value, [])
            for kw in keywords:
                if kw.lower() in text:
                    logger.debug(f"品类识别: '{title}' → {cat.value} (匹配关键词: '{kw}')")
                    return cat

        logger.warning(f"品类识别失败: '{title}' → UNKNOWN")
        return ProductCategory.UNKNOWN

    # ── 发货执行 ──

    async def fulfill(self, order: OrderRequest, title: str = "", desc: str = "") -> FulfillResult:
        """
        执行发货（自动匹配品类 + 选择供应商）

        Args:
            order: 发货请求
            title: 商品标题（用于品类识别）
            desc: 商品描述

        Returns:
            FulfillResult
        """
        # 如果 order 中没有品类，根据标题识别
        if order.category == ProductCategory.UNKNOWN and title:
            order.category = self.classify(title, desc)

        category_key = order.category.value
        supplier_list = self.suppliers.get(category_key, [])

        if not supplier_list:
            return FulfillResult(
                success=False,
                message=f"品类 [{category_key}] 无可用供应商"
            )

        logger.info(f"开始发货: 品类={category_key}, 商品={order.product_name}, 买家账号={order.bearer_account if hasattr(order, 'bearer_account') else order.buyer_account}")

        # 依次尝试每个供应商
        last_error = ""
        for supplier in supplier_list:
            try:
                logger.info(f"  尝试供应商: {supplier.name}")
                result = await supplier.fulfill(order)
                if result.success:
                    logger.info(f"  ✓ 发货成功: {supplier.name}, 交易号={result.trade_no}")
                    return result
                else:
                    last_error = result.message
                    logger.warning(f"  ✗ {supplier.name} 发货失败: {result.message}")
            except Exception as e:
                last_error = str(e)
                logger.error(f"  ✗ {supplier.name} 异常: {e}")

        return FulfillResult(
            success=False,
            message=f"所有供应商均失败，最后错误: {last_error}"
        )

    # ── 查询价格 ──

    async def query_price(self, category: ProductCategory, product_id: str) -> Optional[dict]:
        """查询进货价（返回第一个可用供应商的价格）"""
        supplier_list = self.suppliers.get(category.value, [])
        for supplier in supplier_list:
            try:
                result = await supplier.query_price(product_id)
                if result:
                    result["supplier"] = supplier.name
                    return result
            except Exception as e:
                logger.warning(f"[{supplier.name}] 查询价格失败: {e}")
        return None

    # ── 状态查询 ──

    async def query_status(self, trade_no: str, category: ProductCategory = None) -> Optional[dict]:
        """查询订单状态"""
        if category:
            supplier_list = self.suppliers.get(category.value, [])
            for supplier in supplier_list:
                try:
                    return await supplier.query_status(trade_no)
                except Exception:
                    continue
        return None

    # ── 信息查询 ──

    def list_categories(self) -> dict:
        """列出所有品类及其供应商数量"""
        result = {}
        for cat in ProductCategory:
            if cat == ProductCategory.UNKNOWN:
                continue
            suppliers = self.suppliers.get(cat.value, [])
            result[cat.value] = {
                "count": len(suppliers),
                "suppliers": [s.name for s in suppliers]
            }
        return result

    def health_check(self) -> dict:
        """健康检查"""
        result = {}
        for category, suppliers in self.suppliers.items():
            result[category] = []
            for s in suppliers:
                result[category].append({
                    "name": s.name,
                    "enabled": s.enabled,
                })
        return result
