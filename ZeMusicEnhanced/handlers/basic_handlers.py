#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎵 ZeMusic Bot v3.0 - Basic Handlers
معالجات الأوامر الأساسية للبوت
"""

import asyncio
import logging
import time
import psutil
import platform
from datetime import datetime
from telethon import events

logger = logging.getLogger(__name__)

class BasicHandlers:
    """معالجات الأوامر الأساسية"""
    
    def __init__(self, client, db, config):
        self.client = client
        self.db = db
        self.config = config
        self.start_time = time.time()
        
    def register_handlers(self):
        """تسجيل جميع المعالجات"""
        
        @self.client.client.on(events.NewMessage(pattern=r'^/start'))
        async def start_handler(event):
            """معالج أمر /start"""
            try:
                user_id = event.sender_id
                user_name = event.sender.first_name or "المستخدم"
                
                start_message = f"""
🎵 **مرحباً بك في {self.config.BOT_NAME}!**

✨ **البوت المحسن v3.0 يعمل بنجاح!**

🤖 **معلومات البوت:**
• الاسم: {self.config.BOT_NAME}
• اليوزر: @{self.config.BOT_USERNAME}
• المطور: [المطور](tg://user?id={self.config.OWNER_ID})

🎯 **الأوامر المتاحة:**
• /ping - فحص حالة البوت
• /stats - إحصائيات النظام
• /help - قائمة الأوامر الكاملة
• /info - معلومات البوت

📱 **الدعم:** {self.config.SUPPORT_CHAT}

🎵 **جاهز لخدمتك!**
"""
                
                await event.respond(start_message)
                
                # حفظ المستخدم في قاعدة البيانات
                await self.db.add_user(user_id, user_name)
                
                logger.info(f"📨 /start من المستخدم: {user_id} ({user_name})")
                
            except Exception as e:
                logger.error(f"❌ خطأ في معالج /start: {e}")
                await event.respond("❌ حدث خطأ، يرجى المحاولة مرة أخرى")
        
        @self.client.client.on(events.NewMessage(pattern=r'^/ping'))
        async def ping_handler(event):
            """معالج أمر /ping"""
            try:
                start_time = time.time()
                
                ping_message = await event.respond("🏓 **جاري الفحص...**")
                
                end_time = time.time()
                ping_time = round((end_time - start_time) * 1000, 2)
                
                uptime = self._get_uptime()
                
                response = f"""
🏓 **Pong!**

⚡ **سرعة الاستجابة:** `{ping_time} ms`
⏰ **وقت التشغيل:** `{uptime}`
✅ **الحالة:** يعمل بشكل طبيعي

🎵 **{self.config.BOT_NAME} جاهز للخدمة!**
"""
                
                await ping_message.edit(response)
                
                logger.info(f"🏓 /ping من المستخدم: {event.sender_id} - {ping_time}ms")
                
            except Exception as e:
                logger.error(f"❌ خطأ في معالج /ping: {e}")
                await event.respond("❌ حدث خطأ في فحص الاتصال")
        
        @self.client.client.on(events.NewMessage(pattern=r'^/stats'))
        async def stats_handler(event):
            """معالج أمر /stats"""
            try:
                # جمع إحصائيات النظام
                cpu_percent = psutil.cpu_percent(interval=1)
                memory = psutil.virtual_memory()
                disk = psutil.disk_usage('/')
                uptime = self._get_uptime()
                
                # إحصائيات قاعدة البيانات
                db_stats = self.db.get_stats()
                
                stats_message = f"""
📊 **إحصائيات {self.config.BOT_NAME}**

🖥️ **النظام:**
• المعالج: {cpu_percent}%
• الذاكرة: {memory.percent}%
• القرص: {disk.percent}%
• النظام: {platform.system()} {platform.release()}
• Python: {platform.python_version()}

⏰ **الأداء:**
• وقت التشغيل: {uptime}
• بدء التشغيل: {datetime.fromtimestamp(self.start_time).strftime('%Y-%m-%d %H:%M:%S')}

📊 **قاعدة البيانات:**
• المستخدمين: {db_stats.get('total_users', 0)}
• المجموعات: {db_stats.get('total_chats', 0)}
• الحسابات المساعدة: {db_stats.get('total_assistants', 0)}
• الاستعلامات: {db_stats.get('queries_executed', 0)}

🤖 **معلومات البوت:**
• الاسم: {self.config.BOT_NAME}
• اليوزر: @{self.config.BOT_USERNAME}
• المطور: [المطور](tg://user?id={self.config.OWNER_ID})

📞 **الدعم:** {self.config.SUPPORT_CHAT}
"""
                
                await event.respond(stats_message)
                
                logger.info(f"📊 /stats من المستخدم: {event.sender_id}")
                
            except Exception as e:
                logger.error(f"❌ خطأ في معالج /stats: {e}")
                await event.respond("❌ حدث خطأ في جلب الإحصائيات")
        
        @self.client.client.on(events.NewMessage(pattern=r'^/help'))
        async def help_handler(event):
            """معالج أمر /help"""
            try:
                help_message = f"""
📚 **مساعدة {self.config.BOT_NAME}**

🔧 **الأوامر الأساسية:**
• `/start` - بدء البوت
• `/ping` - فحص حالة البوت
• `/stats` - إحصائيات النظام
• `/help` - هذه الرسالة
• `/info` - معلومات البوت

🎵 **أوامر الموسيقى:**
• `/play` - تشغيل موسيقى
• `/pause` - إيقاف مؤقت
• `/resume` - استكمال التشغيل
• `/stop` - إيقاف التشغيل
• `/skip` - تخطي المقطع الحالي

👨‍💼 **أوامر الإدارة:**
• `/ban` - حظر مستخدم
• `/unban` - إلغاء حظر مستخدم
• `/kick` - طرد مستخدم
• `/mute` - كتم مستخدم

⚙️ **أوامر الإعدادات:**
• `/settings` - إعدادات المجموعة
• `/lang` - تغيير اللغة
• `/prefix` - تغيير البادئة

📞 **للدعم:** {self.config.SUPPORT_CHAT}
👤 **المطور:** [المطور](tg://user?id={self.config.OWNER_ID})

🎵 **استمتع بالموسيقى!**
"""
                
                await event.respond(help_message)
                
                logger.info(f"📚 /help من المستخدم: {event.sender_id}")
                
            except Exception as e:
                logger.error(f"❌ خطأ في معالج /help: {e}")
                await event.respond("❌ حدث خطأ في عرض المساعدة")
        
        @self.client.client.on(events.NewMessage(pattern=r'^/info'))
        async def info_handler(event):
            """معالج أمر /info"""
            try:
                info_message = f"""
ℹ️ **معلومات {self.config.BOT_NAME}**

🎵 **النسخة:** v3.0 Enhanced Edition
📅 **تاريخ الإنشاء:** 2025-01-28
⚡ **المحرك:** Telethon v{self.client.client._version}

🔧 **الميزات:**
✅ تشغيل موسيقى متقدم
✅ نظام أمان محسن
✅ قاعدة بيانات ذكية
✅ مراقبة الأداء
✅ إدارة الحسابات المساعدة
✅ دعم متعدد المنصات

👨‍💻 **المطور:** [المطور](tg://user?id={self.config.OWNER_ID})
📞 **الدعم:** {self.config.SUPPORT_CHAT}
🔗 **القناة:** @{self.config.CHANNEL_ASHTRAK}

🎯 **الهدف:** توفير أفضل تجربة موسيقى على تيليجرام

💝 **شكراً لاستخدام البوت!**
"""
                
                await event.respond(info_message)
                
                logger.info(f"ℹ️ /info من المستخدم: {event.sender_id}")
                
            except Exception as e:
                logger.error(f"❌ خطأ في معالج /info: {e}")
                await event.respond("❌ حدث خطأ في عرض المعلومات")
        
        logger.info("✅ تم تسجيل جميع المعالجات الأساسية")
    
    def _get_uptime(self) -> str:
        """حساب وقت التشغيل"""
        uptime_seconds = int(time.time() - self.start_time)
        
        days = uptime_seconds // 86400
        hours = (uptime_seconds % 86400) // 3600
        minutes = (uptime_seconds % 3600) // 60
        seconds = uptime_seconds % 60
        
        if days > 0:
            return f"{days}d {hours}h {minutes}m {seconds}s"
        elif hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"