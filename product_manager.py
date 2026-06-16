"""
商品模板管理器 — 用 YAML 维护商品信息，批量导入发布

商品模板格式 (products.yaml):
  products:
    - title: "爱奇艺黄金VIP月卡 自动充值"
      desc: "正品保证，自动充值，5分钟内到账..."
      price: 9.9
      category: "video_member"
      images: ["images/iqiyi_month.jpg"]
      sku_list:
        - name: "月卡"
          price: 9.9
        - name: "季卡"
          price: 25.9
        - name: "年卡"
          price: 88.9
"""

import os
import yaml
from loguru import logger
from typing import Optional


class ProductManager:
    """商品模板管理"""

    def __init__(self, config_path: str = None):
        if config_path is None:
            config_path = os.path.join(os.path.dirname(__file__), "products.yaml")
        self.config_path = config_path
        self.products = self._load()

    def _load(self) -> list:
        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
                return data.get("products", [])
        except FileNotFoundError:
            return []

    def save(self):
        with open(self.config_path, "w", encoding="utf-8") as f:
            yaml.dump({"products": self.products}, f, allow_unicode=True, default_flow_style=False)

    def add(self, product: dict) -> int:
        """添加商品，返回新索引"""
        self.products.append(product)
        self.save()
        return len(self.products) - 1

    def remove(self, index: int) -> bool:
        if 0 <= index < len(self.products):
            self.products.pop(index)
            self.save()
            return True
        return False

    def list_all(self) -> list:
        return self.products

    def get(self, index: int) -> Optional[dict]:
        if 0 <= index < len(self.products):
            return self.products[index]
        return None

    def update(self, index: int, product: dict) -> bool:
        if 0 <= index < len(self.products):
            self.products[index] = product
            self.save()
            return True
        return False

    def to_publish_list(self) -> list:
        """转换为 XianyuPublish.batch_create_drafts 需要的格式"""
        result = []
        for p in self.products:
            result.append({
                "title": p["title"],
                "desc": p.get("desc", ""),
                "price": p.get("price", 0),
                "category_id": p.get("category_id", ""),
                "images": [{"path": img} for img in p.get("images", [])],
                "sku_list": p.get("sku_list", []),
                "extra": p.get("extra"),
            })
        return result

    @staticmethod
    def generate_desc_template(category: str, title: str, features: list = None) -> str:
        """根据品类自动生成商品描述模板"""
        templates = {
            "video_member": (
                f"【{title}】\n\n"
                "✅ 正品保证，官方渠道\n"
                "⚡ 自动充值，拍下后填写账号即可\n"
                "⏰ 到账时间：5分钟内\n"
                "🔒 绑定后不支持退换\n\n"
                "📋 购买须知：\n"
                "1. 拍下后请在备注中填写正确的账号\n"
                "2. 充值期间请勿在其他设备登录\n"
                "3. 如有问题请第一时间联系卖家\n"
            ),
            "phone_topup": (
                f"【{title}】\n\n"
                "✅ 三网话费，移动/联通/电信\n"
                "⚡ 自动充值，秒到账\n"
                "💰 充值金额实付，无隐藏费用\n\n"
                "📋 购买须知：\n"
                "1. 请确认手机号正确，充值后无法撤回\n"
                "2. 欠费停机号码可能充值失败\n"
                "3. 到账可能有5-30分钟延迟\n"
            ),
            "game_credit": (
                f"【{title}】\n\n"
                "✅ 官方授权渠道\n"
                "⚡ 自动充值，快速到账\n"
                "🎮 请确认游戏区服和角色名正确\n\n"
                "📋 购买须知：\n"
                "1. 请在备注中填写：游戏区服 + 角色名\n"
                "2. 充值期间请勿注销或转移角色\n"
                "3. 虚拟商品充值后不支持退款\n"
            ),
            "music_member": (
                f"【{title}】\n\n"
                "✅ 正品音乐会员\n"
                "⚡ 自动充值，即买即用\n"
                "🎵 支持QQ音乐/网易云等平台\n\n"
                "📋 购买须知：\n"
                "1. 拍下后请填写正确的账号\n"
                "2. 充值后自动到账\n"
            ),
            "software_key": (
                f"【{title}】\n\n"
                "✅ 正规授权激活码\n"
                "🔑 一码一用，永久有效\n"
                "💻 支持在线激活\n\n"
                "📋 购买须知：\n"
                "1. 激活码为一次性使用\n"
                "2. 请确认购买的版本与系统兼容\n"
                "3. 激活后不支持退款\n"
            ),
            "coupon_deal": (
                f"【{title}】\n\n"
                "🎁 超值优惠券/红包\n"
                "💰 真金白银的优惠\n"
                "📱 即领即用\n\n"
                "📋 使用说明：\n"
                "1. 点击链接领取优惠券\n"
                "2. 下单时自动抵扣\n"
                "3. 有效期请以券面为准\n"
            ),
        }

        base = templates.get(category, f"【{title}】\n\n欢迎购买！\n")
        if features:
            base += "\n" + "\n".join(f"✨ {f}" for f in features)
        return base
