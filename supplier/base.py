"""
供应商抽象基类 — 所有品类的上游API统一接口
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from enum import Enum
from typing import Optional
from loguru import logger


class ProductCategory(Enum):
    """商品品类枚举"""
    PHONE_TOPUP = "phone_topup"          # 话费/流量充值
    VIDEO_MEMBER = "video_member"        # 视频会员（爱奇艺/优酷/腾讯）
    GAME_CREDIT = "game_credit"          # 游戏点券/皮肤
    MUSIC_MEMBER = "music_member"        # 音乐会员（QQ音乐/网易云）
    COUPON_DEAL = "coupon_deal"          # 外卖/电商红包券
    SOFTWARE_KEY = "software_key"        # 软件激活码
    UNKNOWN = "unknown"


@dataclass
class OrderRequest:
    """发货请求"""
    order_id: str                      # 闲鱼订单ID
    category: ProductCategory          # 品类
    product_id: str                    # 商品ID（SKU或产品编码）
    buyer_account: str                 # 买家账号（手机号/账号等）
    product_name: str = ""             # 商品名称（用于日志）
    amount: float = 0.0                # 金额
    extra: dict = field(default_factory=dict)  # 扩展参数


@dataclass
class FulfillResult:
    """发货结果"""
    success: bool                      # 是否成功
    trade_no: str = ""                 # 上游交易号
    message: str = ""                  # 结果描述
    card_code: str = ""                # 卡密/激活码（如有）
    card_url: str = ""                 # 卡密链接（如有）
    expire_time: str = ""              # 到期时间（如有）
    raw_response: dict = field(default_factory=dict)  # 原始响应


class SupplierBase(ABC):
    """
    供应商抽象基类

    子类必须实现:
      - query_price: 查询进货价
      - fulfill: 执行充值/发货
      - query_status: 查询订单状态

    可选覆写:
      - check_balance: 查询余额
      - health_check: 健康检查
    """

    def __init__(self, config: dict):
        """
        Args:
            config: 供应商配置，从 suppliers.yaml 加载
        """
        self.config = config
        self.name = config.get("name", self.__class__.__name__)
        self.api_url = config.get("api_url", "")
        self.api_key = config.get("api_key", "")
        self.api_secret = config.get("api_secret", "")
        self.enabled = config.get("enabled", True)
        logger.info(f"[{self.name}] 供应商初始化完成 (enabled={self.enabled})")

    @abstractmethod
    async def query_price(self, product_id: str) -> dict:
        """
        查询进货价

        Args:
            product_id: 商品ID

        Returns:
            {"price": float, "product_name": str, "in_stock": bool}
        """
        ...

    @abstractmethod
    async def fulfill(self, order: OrderRequest) -> FulfillResult:
        """
        执行充值/发货

        Args:
            order: 发货请求

        Returns:
            FulfillResult
        """
        ...

    @abstractmethod
    async def query_status(self, trade_no: str) -> dict:
        """
        查询订单状态

        Args:
            trade_no: 上游交易号

        Returns:
            {"status": str, "message": str, ...}
        """
        ...

    async def check_balance(self) -> Optional[float]:
        """查询供应商余额（可选实现）"""
        logger.warning(f"[{self.name}] check_balance 未实现")
        return None

    async def health_check(self) -> bool:
        """健康检查（可选实现，默认返回 enabled 状态）"""
        return self.enabled
