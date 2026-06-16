"""订单分发器 - 用于自动发货"""

from loguru import logger


class OrderDispatcher:
    """订单分发器"""
    
    def __init__(self):
        """初始化"""
        logger.info("OrderDispatcher 初始化完成")
    
    async def dispatch(self, buyer_user_id, buyer_name, item_id):
        """分发订单给上家"""
        # 当前版本使用消息方式通知上家
        # 后续可以扩展为 API 方式
        logger.info(f"订单分发: 买家 {buyer_name}, 商品 {item_id}")
        return True
