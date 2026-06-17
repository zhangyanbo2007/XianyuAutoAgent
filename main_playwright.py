import json
import asyncio
import time
import os
from loguru import logger
from dotenv import load_dotenv
from playwright.async_api import async_playwright
from XianyuAgent import XianyuReplyBot
from context_manager import ChatContextManager

load_dotenv()

class XianyuPlaywright:
    def __init__(self):
        self.reply_bot = XianyuReplyBot()
        self.context_manager = ChatContextManager()
        self.cookies_str = os.getenv('COOKIES_STR', '')
        self.page = None
        self.browser = None
        self.context = None
        
        # 配置
        self.check_interval = int(os.getenv('CHECK_INTERVAL', '10'))  # 检查间隔（秒）
        self.headless = os.getenv('HEADLESS', 'false').lower() == 'true'
        
    async def init_browser(self):
        初始化浏览器
        logger.info('初始化浏览器...')
        
        self.p = await async_playwright().start()
        
        # 反检测启动参数
        launch_args = [
            '--disable-blink-features=AutomationControlled',
            '--disable-dev-shm-usage',
            '--no-sandbox',
            '--disable-setuid-sandbox',
        ]
        
        self.browser = await self.p.chromium.launch(
            headless=self.headless,
            args=launch_args
        )
        
        # 创建上下文
        self.context = await self.browser.new_context(
            viewport={'width': 1280, 'height': 800},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )
        
        # 注入Cookie
        if self.cookies_str:
            cookies = self._parse_cookies(self.cookies_str)
            await self.context.add_cookies(cookies)
            logger.info(f'已注入 {len(cookies)} 个Cookie')
        
        # 反检测脚本
        await self.context.add_init_script('''
            Object.defineProperty(navigator, 'webdriver', {get: () => undefined});
            Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]});
            Object.defineProperty(navigator, 'languages', {get: () => ['zh-CN', 'zh', 'en-US', 'en']});
            window.chrome = {runtime: {}, loadTimes: function() {}, csi: function() {}};
        ''')
        
        self.page = await self.context.new_page()
        logger.info('浏览器初始化完成')
    
    def _parse_cookies(self, cookies_str):
        解析Cookie字符串
        cookies = []
        for pair in cookies_str.split('; '):
            if '=' in pair:
                name, value = pair.split('=', 1)
                cookies.append({
                    'name': name.strip(),
                    'value': value.strip(),
                    'domain': '.goofish.com',
                    'path': '/'
                })
        return cookies
    
    async def navigate_to_messages(self):
        导航到消息页面
        logger.info('导航到闲鱼消息页面...')
        await self.page.goto('https://www.goofish.com/message', wait_until='networkidle')
        await asyncio.sleep(3)
        
        # 检查是否登录
        if 'passport' in self.page.url or 'login' in self.page.url:
            logger.error('未登录，请先登录闲鱼账号')
            return False
        
        logger.info('已进入消息页面')
        return True
    
    async def check_new_messages(self):
        检查新消息
        try:
            # 查找未读消息标记
            unread_elements = await self.page.query_selector_all('.unread-dot, .badge, [class*=unread]')
            
            if unread_elements:
                logger.info(f'发现 {len(unread_elements)} 个未读消息')
                return True
            return False
        except Exception as e:
            logger.error(f'检查消息失败: {e}')
            return False
    
    async def get_message_list(self):
        获取消息列表
        try:
            # 查找消息列表项
            message_items = await self.page.query_selector_all('.message-item, .conversation-item, [class*=conversation]')
            
            messages = []
            for item in message_items[:10]:  # 只处理前10条
                try:
                    name = await item.query_selector('.name, .nickname, [class*=name]')
                    preview = await item.query_selector('.preview, .last-message, [class*=preview]')
                    
                    if name and preview:
                        name_text = await name.inner_text()
                        preview_text = await preview.inner_text()
                        messages.append({
                            'name': name_text.strip(),
                            'preview': preview_text.strip(),
                            'element': item
                        })
                except:
                    continue
            
            return messages
        except Exception as e:
            logger.error(f'获取消息列表失败: {e}')
            return []
    
    async def open_conversation(self, element):
        打开对话
        try:
            await element.click()
            await asyncio.sleep(2)
            return True
        except Exception as e:
            logger.error(f'打开对话失败: {e}')
            return False
    
    async def get_last_message(self):
        获取最后一条消息
        try:
            # 查找消息气泡
            messages = await self.page.query_selector_all('.message-bubble, .chat-message, [class*=message-content]')
            
            if messages:
                last_msg = messages[-1]
                text = await last_msg.inner_text()
                return text.strip()
            return None
        except Exception as e:
            logger.error(f'获取消息失败: {e}')
            return None
    
    async def send_message(self, text):
        发送消息
        try:
            # 查找输入框
            input_box = await self.page.query_selector('textarea, input[type=text], [class*=input]')
            
            if input_box:
                await input_box.click()
                await input_box.fill(text)
                await asyncio.sleep(0.5)
                
                # 查找发送按钮
                send_btn = await self.page.query_selector('button[class*=send], .send-btn, [class*=submit]')
                if send_btn:
                    await send_btn.click()
                    logger.info(f'已发送消息: {text[:50]}...')
                    return True
            return False
        except Exception as e:
            logger.error(f'发送消息失败: {e}')
            return False
    
    async def process_message(self, message_text):
        处理消息并生成回复
        try:
            # 使用现有的回复机器人
            reply = self.reply_bot.generate_reply(
                user_msg=message_text,
                item_desc='闲鱼商品',
                context=[]
            )
            return reply
        except Exception as e:
            logger.error(f'生成回复失败: {e}')
            return '您好，有什么可以帮您的吗？'
    
    async def run(self):
        主运行循环
        try:
            await self.init_browser()
            
            if not await self.navigate_to_messages():
                logger.error('无法进入消息页面，退出')
                return
            
            logger.info('开始监听消息...')
            
            while True:
                try:
                    # 检查新消息
                    has_new = await self.check_new_messages()
                    
                    if has_new:
                        # 获取消息列表
                        messages = await self.get_message_list()
                        
                        for msg in messages:
                            logger.info(f'处理消息: {msg[name]} - {msg[preview][:30]}')
                            
                            # 打开对话
                            if await self.open_conversation(msg['element']):
                                # 获取最后一条消息
                                last_msg = await self.get_last_message()
                                
                                if last_msg and not last_msg.startswith('我:'):
                                    # 生成回复
                                    reply = await self.process_message(last_msg)
                                    
                                    # 发送回复
                                    await self.send_message(reply)
                                    
                                    # 保存到数据库
                                    self.context_manager.save_message(
                                        user_id=msg['name'],
                                        role='user',
                                        content=last_msg
                                    )
                                    self.context_manager.save_message(
                                        user_id=msg['name'],
                                        role='assistant',
                                        content=reply
                                    )
                                    
                                    logger.info(f'已回复 {msg[name]}: {reply[:50]}...')
                                
                                # 返回消息列表
                                await self.page.go_back()
                                await asyncio.sleep(1)
                    
                    # 等待下次检查
                    await asyncio.sleep(self.check_interval)
                    
                except Exception as e:
                    logger.error(f'处理消息时出错: {e}')
                    await asyncio.sleep(5)
        
        except Exception as e:
            logger.error(f'运行出错: {e}')
        finally:
            if self.browser:
                await self.browser.close()
            if self.p:
                await self.p.stop()

async def main():
    bot = XianyuPlaywright()
    await bot.run()

if __name__ == '__main__':
    asyncio.run(main())
