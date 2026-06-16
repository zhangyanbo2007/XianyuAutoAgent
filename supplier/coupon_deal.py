"""
外卖/电商红包券供应商

对接各联盟推广API，生成优惠券/红包链接发给买家。

支持:
  - 淘宝联盟（阿里妈妈）— 淘宝/天猫优惠券
  - 京东联盟 — 京东优惠券
  - 美团联盟 — 外卖红包
  - 饿了么联盟 — 外卖红包

模式: 不是"充值"，而是生成推广链接/券码
  1. 买家提供想买的商品链接
  2. 通过联盟API生成隐藏优惠券+推广链接
  3. 将链接发给买家，买家通过链接下单省钱

盈利方式:
  - 买家通过你的推广链接下单，你赚佣金
  - 或者：你把券码以低价卖给买家，赚差价
"""

import time
import hashlib
import asyncio
from loguru import logger

from supplier.base import SupplierBase, OrderRequest, FulfillResult


class CouponDealSupplier(SupplierBase):
    """外卖/电商红包券供应商"""

    async def query_price(self, product_id: str) -> dict:
        """
        查询优惠券/红包成本

        product_id 格式示例:
          "meituan_5"    — 美团5元红包
          "ele_5"        — 饿了么5元红包
          "taobao_auto"  — 淘宝自动搜券
        """
        # 红包类产品通常是推广获得，成本极低
        coupon_config = self.config.get("coupon_products", {})
        if product_id in coupon_config:
            return {
                "price": coupon_config[product_id].get("cost", 0),
                "product_name": coupon_config[product_id].get("name", product_id),
                "in_stock": True,
            }
        return {"price": 0, "product_name": product_id, "in_stock": False}

    async def fulfill(self, order: OrderRequest) -> FulfillResult:
        """
        生成优惠券/红包链接

        根据不同平台:
          - 美团/饿了么: 生成红包分享链接
          - 淘宝/京东: 根据商品链接生成隐藏券+推广链接
        """
        product_id = order.product_id
        buyer_msg = order.extra.get("buyer_message", "")

        # ── 美团红包 ──
        if product_id.startswith("meituan"):
            return await self._meituan_coupon(order)

        # ── 饿了么红包 ──
        if product_id.startswith("ele"):
            return await self._eleme_coupon(order)

        # ── 淘宝/天猫 ──
        if product_id.startswith("taobao") or product_id.startswith("tmall"):
            return await self._taobao_coupon(order)

        # ── 京东 ──
        if product_id.startswith("jd"):
            return await self._jd_coupon(order)

        return FulfillResult(success=False, message=f"未知优惠券类型: {product_id}")

    async def _meituan_coupon(self, order: OrderRequest) -> FulfillResult:
        """美团红包 — 通过联盟API生成分享链接"""
        if not self.api_url or not self.api_key:
            return FulfillResult(
                success=False,
                message="美团联盟API未配置，请在 suppliers.yaml 中填写",
            )

        try:
            import aiohttp
            payload = {
                "api_key": self.api_key,
                "activity_type": "red_packet",
                "amount": order.amount or 5,
                "trade_no": order.order_id,
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/meituan/coupon",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    data = await resp.json()
                    if data.get("code") == 0:
                        link = data.get("share_url", "")
                        return FulfillResult(
                            success=True,
                            trade_no=order.order_id,
                            card_url=link,
                            message=f"美团红包链接:\n{link}\n\n点击领取红包，下单自动抵扣",
                        )
                    return FulfillResult(success=False, message=data.get("msg", "生成失败"))
        except Exception as e:
            return FulfillResult(success=False, message=f"请求异常: {e}")

    async def _eleme_coupon(self, order: OrderRequest) -> FulfillResult:
        """饿了么红包 — 通过联盟API生成分享链接"""
        if not self.api_url or not self.api_key:
            return FulfillResult(
                success=False,
                message="饿了么联盟API未配置，请在 suppliers.yaml 中填写",
            )

        try:
            import aiohttp
            payload = {
                "api_key": self.api_key,
                "activity_type": "red_packet",
                "amount": order.amount or 5,
                "trade_no": order.order_id,
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.api_url}/eleme/coupon",
                    json=payload,
                    timeout=aiohttp.ClientTimeout(total=15),
                ) as resp:
                    data = await resp.json()
                    if data.get("code") == 0:
                        link = data.get("share_url", "")
                        return FulfillResult(
                            success=True,
                            trade_no=order.order_id,
                            card_url=link,
                            message=f"饿了么红包链接:\n{link}\n\n点击领取红包，下单自动抵扣",
                        )
                    return FulfillResult(success=False, message=data.get("msg", "生成失败"))
        except Exception as e:
            return FulfillResult(success=False, message=f"请求异常: {e}")

    async def _taobao_coupon(self, order: OrderRequest) -> FulfillResult:
        """淘宝隐藏券 — 根据商品链接查券"""
        if not self.app_key or not self.api_secret:
            return FulfillResult(success=False, message="淘宝联盟API未配置")

        # 需要买家提供淘宝商品链接
        product_url = order.extra.get("product_url", "")
        if not product_url:
            return FulfillResult(
                success=False,
                message="请发送淘宝/天猫商品链接，我帮你查隐藏优惠券",
            )

        try:
            import aiohttp
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            sign_str = f"app_key{self.app_key}methodtaobao.tbk.dg.material.optionaltimestamp{timestamp}{self.api_secret}"
            sign = hashlib.md5(sign_str.encode()).hexdigest().upper()

            params = {
                "method": "taobao.tbk.dg.material.optional",
                "app_key": self.app_key,
                "timestamp": timestamp,
                "format": "json",
                "v": "2.0",
                "sign_method": "md5",
                "sign": sign,
                "q": product_url,
            }
            async with aiohttp.ClientSession() as session:
                async with session.get(self.api_url, params=params, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    data = await resp.json()
                    # 解析淘宝联盟返回
                    items = data.get("tbk_dg_material_optional_response", {}).get("result_list", {}).get("map_data", [])
                    if items:
                        item = items[0]
                        coupon_amount = item.get("coupon_amount", "0")
                        coupon_url = item.get("click_url", "")
                        return FulfillResult(
                            success=True,
                            trade_no=order.order_id,
                            card_url=coupon_url,
                            message=f"找到隐藏优惠券 ¥{coupon_amount}\n领券链接: {coupon_url}",
                        )
                    return FulfillResult(success=False, message="未找到可用优惠券")
        except Exception as e:
            return FulfillResult(success=False, message=f"查询异常: {e}")

    async def _jd_coupon(self, order: OrderRequest) -> FulfillResult:
        """京东优惠券 — 通过联盟API查券"""
        if not self.api_key or not self.api_secret:
            return FulfillResult(success=False, message="京东联盟API未配置")

        product_url = order.extra.get("product_url", "")
        if not product_url:
            return FulfillResult(success=False, message="请发送京东商品链接，我帮你查优惠券")

        try:
            import aiohttp
            timestamp = time.strftime("%Y-%m-%d %H:%M:%S")
            sign_str = f"{self.api_key}methodjd.union.open.goods.querytimestamp{timestamp}{self.api_secret}"
            sign = hashlib.md5(sign_str.encode()).hexdigest().upper()

            payload = {
                "method": "jd.union.open.goods.query",
                "app_key": self.api_key,
                "timestamp": timestamp,
                "format": "json",
                "v": "1.0",
                "sign_method": "md5",
                "sign": sign,
                "360buy_param_json": json.dumps({"goodsReq": {"keyword": product_url}}),
            }
            async with aiohttp.ClientSession() as session:
                async with session.post(self.api_url, data=payload, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    data = await resp.json()
                    goods = data.get("jd_union_open_goods_query_responce", {}).get("result", {}).get("data", [])
                    if goods:
                        link = goods[0].get("materialUrl", "")
                        return FulfillResult(
                            success=True, trade_no=order.order_id, card_url=link,
                            message=f"京东商品链接:\n{link}",
                        )
                    return FulfillResult(success=False, message="未找到商品")
        except Exception as e:
            return FulfillResult(success=False, message=f"查询异常: {e}")

    async def query_status(self, trade_no: str) -> dict:
        return {"status": "completed", "message": "链接已发送"}
