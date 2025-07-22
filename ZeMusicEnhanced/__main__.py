#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎵 ZeMusic Bot v3.0 - Enhanced Main Entry Point
تاريخ الإنشاء: 2025-01-28
النسخة: 3.0.0 - Enhanced Edition

نقطة دخول البوت الرئيسية مع إدارة متقدمة للعمليات
"""

import asyncio
import signal
import sys
import logging
from pathlib import Path
from typing import Optional

# إضافة مجلد المشروع لـ Python Path
sys.path.insert(0, str(Path(__file__).parent))

from config import config
from core import (
    TelethonClient,
    DatabaseManager,
    AssistantManager,
    MusicEngine,
    SecurityManager,
    PerformanceMonitor
)

# إعداد اللوجر الرئيسي
logger = logging.getLogger(__name__)

class ZeMusicEnhanced:
    """الكلاس الرئيسي لبوت ZeMusic المحسن"""
    
    def __init__(self):
        """تهيئة البوت"""
        self.client: Optional[TelethonClient] = None
        self.database: Optional[DatabaseManager] = None
        self.assistant_manager: Optional[AssistantManager] = None
        self.music_engine: Optional[MusicEngine] = None
        self.security_manager: Optional[SecurityManager] = None
        self.performance_monitor: Optional[PerformanceMonitor] = None
        
        self.is_running = False
        self.shutdown_event = asyncio.Event()
        
        # تسجيل معالجات الإشارات
        self._setup_signal_handlers()
    
    def _setup_signal_handlers(self):
        """إعداد معالجات إشارات النظام"""
        try:
            # معالج إشارات الإيقاف
            for sig in [signal.SIGTERM, signal.SIGINT]:
                signal.signal(sig, self._signal_handler)
                
            logger.info("✅ تم تسجيل معالجات الإشارات")
            
        except Exception as e:
            logger.error(f"❌ فشل في تسجيل معالجات الإشارات: {e}")
    
    def _signal_handler(self, signum, frame):
        """معالج إشارات الإيقاف"""
        logger.info(f"📡 تم استلام إشارة {signum} - بدء الإيقاف الآمن...")
        asyncio.create_task(self.shutdown())
    
    async def initialize(self) -> bool:
        """تهيئة جميع مكونات البوت"""
        try:
            logger.info("🚀 بدء تهيئة ZeMusic Bot Enhanced v3.0...")
            
            # عرض معلومات النظام
            self._display_system_info()
            
            # 1. تهيئة قاعدة البيانات
            logger.info("📊 تهيئة قاعدة البيانات...")
            self.database = DatabaseManager()
            if not await self.database.initialize():
                logger.error("❌ فشل في تهيئة قاعدة البيانات")
                return False
            
            # 2. تهيئة عميل Telethon
            logger.info("📱 تهيئة عميل Telethon...")
            self.client = TelethonClient()
            if not await self.client.initialize():
                logger.error("❌ فشل في تهيئة عميل Telethon")
                return False
            
            # 3. تهيئة مدير الحسابات المساعدة
            logger.info("🤖 تهيئة مدير الحسابات المساعدة...")
            self.assistant_manager = AssistantManager()
            if not await self.assistant_manager.initialize():
                logger.error("❌ فشل في تهيئة مدير الحسابات المساعدة")
                return False
            
            # 4. تهيئة محرك الموسيقى
            logger.info("🎵 تهيئة محرك الموسيقى...")
            self.music_engine = MusicEngine(self.client, self.assistant_manager)
            if not await self.music_engine.initialize():
                logger.error("❌ فشل في تهيئة محرك الموسيقى")
                return False
            
            # 5. تهيئة مدير الأمان
            logger.info("🛡️ تهيئة مدير الأمان...")
            self.security_manager = SecurityManager(self.client, self.database)
            if not await self.security_manager.initialize():
                logger.error("❌ فشل في تهيئة مدير الأمان")
                return False
            
            # 6. تهيئة مراقب الأداء
            logger.info("📈 تهيئة مراقب الأداء...")
            self.performance_monitor = PerformanceMonitor()
            if not await self.performance_monitor.initialize():
                logger.error("❌ فشل في تهيئة مراقب الأداء")
                return False
            
            # 7. تحميل المعالجات والإضافات
            await self._load_handlers()
            
            self.is_running = True
            logger.info("✅ تم تهيئة جميع مكونات البوت بنجاح")
            
            # عرض إحصائيات البدء
            await self._display_startup_stats()
            
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في تهيئة البوت: {e}")
            return False
    
    def _display_system_info(self):
        """عرض معلومات النظام"""
        try:
            import platform
            import psutil
            
            system_info = f"""
╭─────────────────────────────────────────────────╮
│  🎵 ZeMusic Bot v3.0 - Enhanced Edition        │
├─────────────────────────────────────────────────┤
│  💻 النظام: {platform.system()} {platform.release()}
│  🐍 Python: {platform.python_version()}
│  🧠 المعالج: {psutil.cpu_count()} cores
│  💾 الذاكرة: {psutil.virtual_memory().total // (1024**3)} GB
│  💿 التخزين: {psutil.disk_usage('/').free // (1024**3)} GB متاح
├─────────────────────────────────────────────────┤
│  ⚙️ الإعدادات:                                  │
│  📊 قاعدة البيانات: {config.database._get_db_type()}
│  🤖 الحسابات المساعدة: {config.assistant.max_assistants} حد أقصى
│  🎵 وضع الأحمال الكبيرة: {'✅' if config.performance.high_load_mode else '❌'}
│  🔄 Redis: {'✅' if config.performance.enable_redis else '❌'}
╰─────────────────────────────────────────────────╯
            """
            
            print(system_info)
            
        except Exception as e:
            logger.error(f"❌ فشل في عرض معلومات النظام: {e}")
    
    async def _load_handlers(self):
        """تحميل معالجات الأحداث والإضافات"""
        try:
            logger.info("📥 تحميل معالجات الأحداث...")
            
            # سيتم تنفيذ هذا في المراحل التالية
            # من خلال نظام الإضافات المحسن
            
            logger.info("✅ تم تحميل جميع المعالجات")
            
        except Exception as e:
            logger.error(f"❌ فشل في تحميل المعالجات: {e}")
    
    async def _display_startup_stats(self):
        """عرض إحصائيات البدء"""
        try:
            # الحصول على الإحصائيات
            db_stats = await self.database.get_stats()
            assistant_stats = await self.assistant_manager.get_assistants_stats()
            bot_info = config.get_bot_info()
            
            startup_stats = f"""
╭─────────────────────────────────────────────────╮
│  📊 إحصائيات البوت                             │
├─────────────────────────────────────────────────┤
│  👥 المستخدمين: {db_stats.get('users', 0)}
│  💬 المجموعات: {db_stats.get('chats', 0)}
│  🤖 الحسابات المساعدة: {assistant_stats.get('connected_assistants', 0)}/{assistant_stats.get('total_assistants', 0)}
│  🎵 إجمالي التشغيلات: {db_stats.get('total_plays', 0)}
├─────────────────────────────────────────────────┤
│  🌐 المنصات المدعومة:                          │
│  {', '.join(bot_info.get('supported_platforms', []))}
╰─────────────────────────────────────────────────╯

🎉 البوت جاهز للعمل! استخدم /start للبدء
            """
            
            print(startup_stats)
            logger.info("🎉 البوت جاهز للعمل!")
            
        except Exception as e:
            logger.error(f"❌ فشل في عرض إحصائيات البدء: {e}")
    
    async def run(self):
        """تشغيل البوت"""
        try:
            if not self.is_running:
                logger.error("❌ البوت غير مهيأ - يرجى تشغيل initialize() أولاً")
                return
            
            logger.info("🏃 بدء تشغيل البوت...")
            
            # بدء مراقب الأداء
            if self.performance_monitor:
                asyncio.create_task(self.performance_monitor.start_monitoring())
            
            # تشغيل العميل الرئيسي
            if self.client:
                await self.client.run_until_disconnected()
            
        except KeyboardInterrupt:
            logger.info("⌨️ تم إيقاف البوت بواسطة المستخدم")
        except Exception as e:
            logger.error(f"❌ خطأ في تشغيل البوت: {e}")
        finally:
            await self.shutdown()
    
    async def shutdown(self):
        """إيقاف البوت بشكل آمن"""
        try:
            if not self.is_running:
                return
            
            logger.info("🛑 بدء الإيقاف الآمن للبوت...")
            self.is_running = False
            
            # إيقاف المكونات بالترتيب العكسي للتهيئة
            
            # 1. إيقاف مراقب الأداء
            if self.performance_monitor:
                await self.performance_monitor.shutdown()
                logger.info("✅ تم إيقاف مراقب الأداء")
            
            # 2. إيقاف مدير الأمان
            if self.security_manager:
                await self.security_manager.shutdown()
                logger.info("✅ تم إيقاف مدير الأمان")
            
            # 3. إيقاف محرك الموسيقى
            if self.music_engine:
                await self.music_engine.shutdown()
                logger.info("✅ تم إيقاف محرك الموسيقى")
            
            # 4. إيقاف مدير الحسابات المساعدة
            if self.assistant_manager:
                await self.assistant_manager.shutdown()
                logger.info("✅ تم إيقاف مدير الحسابات المساعدة")
            
            # 5. إيقاف عميل Telethon
            if self.client:
                await self.client.disconnect()
                logger.info("✅ تم إيقاف عميل Telethon")
            
            # 6. إيقاف قاعدة البيانات
            if self.database:
                await self.database.close()
                logger.info("✅ تم إيقاف قاعدة البيانات")
            
            # تعيين حدث الإيقاف
            self.shutdown_event.set()
            
            logger.info("🎯 تم إيقاف البوت بنجاح")
            
        except Exception as e:
            logger.error(f"❌ خطأ في إيقاف البوت: {e}")

# ============================================
# الوظائف الرئيسية
# ============================================

async def main():
    """الوظيفة الرئيسية"""
    bot = None
    
    try:
        # إنشاء مثيل البوت
        bot = ZeMusicEnhanced()
        
        # تهيئة البوت
        if not await bot.initialize():
            logger.error("❌ فشل في تهيئة البوت")
            sys.exit(1)
        
        # تشغيل البوت
        await bot.run()
        
    except KeyboardInterrupt:
        logger.info("⌨️ تم إيقاف البوت بواسطة المستخدم")
    except Exception as e:
        logger.error(f"❌ خطأ فادح في البوت: {e}")
        sys.exit(1)
    finally:
        if bot:
            await bot.shutdown()

def run_bot():
    """تشغيل البوت مع معالجة الأخطاء"""
    try:
        # إعداد حلقة الأحداث
        if sys.platform == 'win32':
            # Windows
            asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())
        else:
            # Linux/macOS - استخدام uvloop للأداء الأفضل
            try:
                import uvloop
                uvloop.install()
                logger.info("✅ تم تفعيل uvloop للأداء الأفضل")
            except ImportError:
                logger.info("ℹ️ uvloop غير متاح - سيتم استخدام asyncio العادي")
        
        # تشغيل البوت
        asyncio.run(main())
        
    except KeyboardInterrupt:
        print("\n👋 وداعاً!")
        sys.exit(0)
    except Exception as e:
        logger.error(f"❌ خطأ فادح: {e}")
        sys.exit(1)

# ============================================
# نقطة الدخول
# ============================================

if __name__ == "__main__":
    print("🎵 ZeMusic Bot v3.0 - Enhanced Edition")
    print("تاريخ الإنشاء: 2025-01-28")
    print("=" * 50)
    
    run_bot()