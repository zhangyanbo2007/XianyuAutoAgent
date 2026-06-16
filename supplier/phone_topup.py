"""
话费/流量充值供应商

对接蚂蚁充、聚合金服等第三方充值平台API。
这类平台通常提供 HTTP REST API，传入手机号+金额即可完成充值。

典型API文档格式:
  POST https://api.xxx.com/recharge
  参数: api_key, phone, amount, trade_no, sign(MD5)
  返回: {"code": 0, "msg": "success", "trade_no": "xxx"}

接入步骤:
  1. 注册平台账号，获取 api_key + api_secret
  2. 小额测试（10元话费）确认到账
  3. 将 api_key 填入 suppliers.yaml
"""

import time
import hashlib
import asyncio
import aiohttp
from loguru import logger

from supplier.base import SupplierBase, OrderRequest, FulfillResult


class PhoneTopupSupplier(SupplierBase):
    """话费/流量充值供应商"""

    async def query_price(self, product_id: str) -> dict:
        """
        查询话费充值价格

        Args:
            product_id: 金额，如 "50" 表示50元话费

        Returns:
            {"price": 进货价, "product_name": "50元话费", "in_stock": True}
        """
        try:
            amount = float(product_id)
            fee_rate = self.config.get("fee_rate", 0.02)
            cost_price = round(amount * (1 + fee_rate), 2)

            return {
                "price": cost_price,
                "product_name": f"{int(amount)}元话费",
                "in_stock": True,
            }
        except (ValueError, TypeError):
            return {"price": 0, "product_name": "", "in_stock": False}

    async def fulfill(self, order: OrderRequest) -> FulfillResult:
        """
        执行话费充值

        买家账号格式: 手机号
        金额: 从 order.amount 或 order.extra["amount"] 获取
        """
        phone = order.buyer_account.strip()
        amount = order.amount or order.extra.get("amount", 0)

        if not phone or len(phone) != 11:
            return FulfillResult(success=False, message=f"手机号格式错误: {phone}")

        if amount <= 0:
            return FulfillResult(success=False, message=f"充值金额无效: {amount}")

        min_amt = self.config.get("min_amount", 10)
        max_amt = self.config.get("max_amount", 500)
        if amount < min_amt or amount > max_amt:
            return FulfillResult(success=False, message=f"金额 {amount} 超出范围 [{min_amt}, {max_amt}]")

        # ── 调用上游API ──
        # 这里以通用格式实现，实际对接时根据供应商文档调整参数名
        api_url = f"{self.api_url}/recharge"
        timestamp = str(int(time.time()))

        # 构造签名（大多数平台用 MD5 签名）
        sign_str = f"{self.api_key}{phone}{amount}{timestamp}{self.api_secret}"
        sign = hashlib.md5(sign_str.encode()).hexdigest()

        payload = {
            "api_key": self.api_key,
            "phone": phone,
            "amount": int(amount),
            "trade_no": order.order_id,
            "notify_url": self.config.get("notify_url", ""),
            "timestamp": timestamp,
            "sign": sign,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, json=payload, timeout=aiohttp.ClientTimeout(total=30)) as resp:
                    data = await resp.json()

                    if data.get("code") == 0 or data.get("status") == "success":
                        return FulfillResult(
                            success=True,
                            trade_no=data.get("trade_no", order.order_id),
                            message=f"话费 {amount}元 充值已提交，手机号 {phone}",
                            raw_response=data,
                        )
                    else:
                        return FulfillResult(
                            success=False,
                            message=data.get("msg", data.get("message", "充值失败")),
                            raw_response=data,
                        )
        except asyncio.TimeoutError:
            return FulfillResult(success=False, message="上游API请求超时")
        except Exception as e:
            return FulfillResult(success=False, message=f"请求异常: {e}")

    async def query_status(self, trade_no: str) -> dict:
        """查询充值状态"""
        api_url = f"{self.api_url}/query"
        timestamp = str(int(time.time()))
        sign_str = f"{self.api_key}{trade_no}{timestamp}{self.api_secret}"
        sign = hashlib.md5(sign_str.encode()).hexdigest()

        payload = {
            "api_key": self.api_key,
            "trade_no": trade_no,
            "timestamp": timestamp,
            "sign": sign,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, json=payload, timeout=aiohttp.ClientTimeout(total=15)) as resp:
                    data = await resp.json()
                    status_map = {
                        "success": "充值成功",
                        "processing": "充值中",
                        "pending": "待处理",
                        "failed": "充值失败",
                    }
                    raw_status = data.get("status", "unknown")
                    return {
                        "status": raw_status,
                        "message": status_map.get(raw_status, raw_status),
                        "raw": data,
                    }
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def check_balance(self) -> float:
        """查询平台余额"""
        api_url = f"{self.api_url}/balance"
        timestamp = str(int(time.time()))
        sign_str = f"{self.api_key}{timestamp}{self.api_secret}"
        sign = hashlib.md5(sign_str.encode()).hexdigest()

        payload = {
            "api_key": self.api_key,
            "timestamp": timestamp,
            "sign": sign,
        }

        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(api_url, json=payload, timeout=aiohttp.ClientTimeout(total=10)) as resp:
                    data = await resp.json()
                    return float(data.get("balance", 0))
        except Exception:
            return 0.0
