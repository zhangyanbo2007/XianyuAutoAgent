"""
闲鱼发布模块 — 逆向 Web 端发布接口，支持创建草稿和发布商品

逆向来源: 闲鱼网页版 (www.goofish.com) 发布商品流程
抓包路径: F12 → Network → 发布商品 → 找到 mtop.taobao.idle.publish.* 请求

接口清单:
  - mtop.taobao.idle.publish.category.get   获取发布分类
  - mtop.taobao.idle.publish.save           保存草稿
  - mtop.taobao.idle.publish.submit         正式发布

⚠️ 风控提醒:
  - 同一账号短时间内大量发布会触发审核
  - 建议: 每次发布间隔 30-60 秒，日发布量 < 20
  - 被限流后等 24 小时再试
"""

import time
import json
import requests
from loguru import logger
from utils.xianyu_utils import generate_sign


class XianyuPublish:
    """闲鱼商品发布"""

    BASE_URL = "https://h5api.m.goofish.com/h5"

    # 已知的闲鱼虚拟商品分类ID（逆向自 p_publish-index.js + 实际抓包）
    CATEGORIES = {
        "video_member":   {"id": "50023914", "name": "视频/音频会员充值"},
        "phone_topup":    {"id": "", "name": "话费充值"},
        "game_credit":    {"id": "", "name": "游戏充值"},
        "music_member":   {"id": "50023914", "name": "音乐/音频会员充值"},
        "software_key":   {"id": "", "name": "软件激活码"},
        "coupon_deal":    {"id": "", "name": "优惠券"},
    }

    # 已确认的发布流程 API（逆向自闲鱼 Web 端 JS）
    # 1. mtop.taobao.idleitem.badwords.prepubcheck  — 标题敏感词检查
    # 2. mtop.taobao.idle.kgraph.property.recommend — 根据标题推荐分类
    # 3. mtop.idle.item.publish.service.cards.list  — 获取服务卡片
    # 4. mtop.idle.pc.idleitem.prepublish.check     — 发布前校验
    # 5. mtop.idle.pc.idleitem.publish              — 正式发布
    # 6. mtop.idle.idleitem.draft.edit              — 编辑草稿
    # 7. mtop.idle.idleitem.draft.publish           — 从草稿发布

    def __init__(self, session: requests.Session):
        """
        Args:
            session: 已登录的 requests.Session（带 Cookie）
        """
        self.session = session

    def _build_common_params(self, api_name: str, data: str) -> dict:
        """构建通用请求参数（签名 + 基础字段）"""
        t = str(int(time.time()) * 1000)
        token = self.session.cookies.get('_m_h5_tk', '').split('_')[0]
        sign = generate_sign(t, token, data)

        return {
            'jsv': '2.7.2',
            'appKey': '34839810',
            't': t,
            'sign': sign,
            'v': '1.0',
            'type': 'originaljson',
            'accountSite': 'xianyu',
            'dataType': 'json',
            'timeout': '20000',
            'api': api_name,
            'sessionOption': 'AutoLoginOnly',
            'spm_cnt': 'a21ybx.im.0.0',
        }

    def _post_api(self, api_name: str, data_dict: dict) -> dict:
        """调用闲鱼 MTOP API 的通用方法"""
        data_str = json.dumps(data_dict, ensure_ascii=False)
        params = self._build_common_params(api_name, data_str)

        headers = {
            "Host": "h5api.m.goofish.com",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
            "accept": "application/json",
            "content-type": "application/x-www-form-urlencoded",
            "origin": "https://www.goofish.com",
            "referer": "https://www.goofish.com/",
            "sec-fetch-site": "same-site",
            "sec-fetch-mode": "cors",
            "sec-fetch-dest": "empty",
        }

        try:
            response = self.session.post(
                f"{self.BASE_URL}/{api_name}/1.0/",
                headers=headers,
                params=params,
                data={"data": data_str},
            )
            res_json = response.json()

            ret = res_json.get('ret', [])
            if any('SUCCESS' in r for r in ret):
                logger.debug(f"[{api_name}] 调用成功")
                return res_json
            else:
                logger.warning(f"[{api_name}] 调用失败: {ret}")
                return res_json

        except Exception as e:
            logger.error(f"[{api_name}] 请求异常: {e}")
            return {"ret": [f"ERROR: {e}"]}

    # ── 获取发布分类 ──

    def get_publish_categories(self) -> dict:
        """
        获取闲鱼发布的商品分类列表

        用途: 找到你商品对应的 category id
        """
        data = {"type": "1"}
        result = self._post_api("mtop.taobao.idle.publish.category.get", data)
        if "data" in result:
            categories = result["data"].get("categories", [])
            logger.info(f"获取到 {len(categories)} 个分类")
            return result["data"]
        return result

    # ── 上传图片 ──

    def upload_image(self, image_path: str) -> dict:
        """
        上传商品图片

        Args:
            image_path: 本地图片路径

        Returns:
            {"image_id": str, "image_url": str}
        """
        try:
            with open(image_path, 'rb') as f:
                files = {'image': f}
                # 图片上传走独立域名
                resp = self.session.post(
                    "https://h5api.m.goofish.com/h5/mtop.taobao.idle.image.upload/1.0/",
                    files=files,
                    headers={
                        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/133.0.0.0 Safari/537.36",
                        "origin": "https://www.goofish.com",
                        "referer": "https://www.goofish.com/",
                    },
                )
                res = resp.json()
                if any('SUCCESS' in r for r in res.get('ret', [])):
                    image_info = res.get('data', {})
                    logger.info(f"图片上传成功: {image_path}")
                    return image_info
                else:
                    logger.warning(f"图片上传失败: {res.get('ret')}")
                    return {}
        except Exception as e:
            logger.error(f"图片上传异常: {e}")
            return {}

    # ── 保存草稿 ──

    def save_draft(
        self,
        title: str,
        desc: str,
        price: float,
        category_id: str = "",
        images: list = None,
        sku_list: list = None,
        extra: dict = None,
    ) -> dict:
        """
        保存商品草稿

        Args:
            title: 商品标题（30字以内）
            desc: 商品描述
            price: 价格（元）
            category_id: 闲鱼分类ID
            images: 图片列表 [{"url": "..."}] 或 [{"path": "/local/file.jpg"}]
            sku_list: SKU列表，如 [{"name": "月卡", "price": 9.9}, {"name": "年卡", "price": 88}]
            extra: 扩展参数

        Returns:
            {"success": bool, "item_id": str, "message": str}
        """
        # 处理图片
        image_list = []
        if images:
            for img in images:
                if "url" in img:
                    image_list.append(img)
                elif "path" in img:
                    uploaded = self.upload_image(img["path"])
                    if uploaded:
                        image_list.append(uploaded)

        # 构造商品数据
        publish_data = {
            "title": title,
            "desc": desc,
            "price": str(price),
            "categoryId": category_id,
            "images": image_list,
            "status": "draft",  # draft=草稿, online=直接发布
        }

        # 处理SKU
        if sku_list:
            skus = []
            for sku in sku_list:
                skus.append({
                    "name": sku.get("name", "默认"),
                    "price": str(sku.get("price", price)),
                    "quantity": str(sku.get("quantity", 999)),
                })
            publish_data["skuList"] = skus

        # 合并扩展参数
        if extra:
            publish_data.update(extra)

        result = self._post_api("mtop.taobao.idle.publish.save", publish_data)

        # 解析结果
        ret = result.get("ret", [])
        success = any("SUCCESS" in r for r in ret)
        item_id = result.get("data", {}).get("itemId", "")

        return {
            "success": success,
            "item_id": item_id,
            "message": "草稿保存成功" if success else f"保存失败: {ret}",
            "raw": result,
        }

    # ── 正式发布 ──

    def submit_item(self, item_id: str) -> dict:
        """
        将草稿正式发布上架

        Args:
            item_id: 草稿的 item_id（来自 save_draft 返回值）

        Returns:
            {"success": bool, "message": str}
        """
        data = {"itemId": item_id}
        result = self._post_api("mtop.taobao.idle.publish.submit", data)

        ret = result.get("ret", [])
        success = any("SUCCESS" in r for r in ret)

        return {
            "success": success,
            "message": "发布成功" if success else f"发布失败: {ret}",
            "raw": result,
        }

    # ── 批量发布 ──

    def batch_create_drafts(self, products: list, interval: int = 30) -> list:
        """
        批量创建草稿

        Args:
            products: 商品列表，每项包含 title, desc, price, images 等
            interval: 每次发布间隔（秒），防风控

        Returns:
            [{"title": str, "result": dict}, ...]
        """
        results = []
        for i, product in enumerate(products):
            logger.info(f"[{i+1}/{len(products)}] 创建草稿: {product.get('title', '')[:20]}...")
            result = self.save_draft(
                title=product["title"],
                desc=product.get("desc", ""),
                price=product.get("price", 0),
                category_id=product.get("category_id", ""),
                images=product.get("images", []),
                sku_list=product.get("sku_list", []),
                extra=product.get("extra"),
            )
            results.append({"title": product["title"], "result": result})

            if i < len(products) - 1:
                logger.debug(f"等待 {interval} 秒后继续...")
                time.sleep(interval)

        success_count = sum(1 for r in results if r["result"]["success"])
        logger.info(f"批量创建完成: {success_count}/{len(products)} 成功")
        return results
