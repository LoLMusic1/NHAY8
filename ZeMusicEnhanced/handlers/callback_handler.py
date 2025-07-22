#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎵 ZeMusic Bot v3.0 - Enhanced Callback Handler
تاريخ الإنشاء: 2025-01-28

معالج الاستعلامات الشامل مع جميع وظائف البوت
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from telethon import events, Button
from telethon.tl.types import Message

from ..config import config
from ..core import (
    TelethonClient, DatabaseManager, AssistantManager,
    MusicEngine, SecurityManager, PerformanceMonitor
)

logger = logging.getLogger(__name__)

class CallbackHandler:
    """معالج الاستعلامات المحسن"""
    
    def __init__(self, client: TelethonClient, db: DatabaseManager,
                 assistant_manager: AssistantManager, music_engine: MusicEngine,
                 security_manager: SecurityManager, performance_monitor: PerformanceMonitor):
        """تهيئة معالج الاستعلامات"""
        self.client = client
        self.db = db
        self.assistant_manager = assistant_manager
        self.music_engine = music_engine
        self.security_manager = security_manager
        self.performance_monitor = performance_monitor
        
        self.is_initialized = False
    
    async def initialize(self) -> bool:
        """تهيئة معالج الاستعلامات"""
        try:
            logger.info("📞 تهيئة معالج الاستعلامات...")
            
            # تسجيل معالجات الاستعلامات
            await self._register_callback_handlers()
            
            self.is_initialized = True
            logger.info("✅ تم تهيئة معالج الاستعلامات بنجاح")
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في تهيئة معالج الاستعلامات: {e}")
            return False
    
    async def _register_callback_handlers(self):
        """تسجيل معالجات الاستعلامات"""
        try:
            # معالج الاستعلامات العام
            @self.client.client.on(events.CallbackQuery)
            async def handle_callback_query(event):
                await self._handle_callback_query(event)
            
            logger.info("📝 تم تسجيل معالجات الاستعلامات")
            
        except Exception as e:
            logger.error(f"❌ فشل في تسجيل معالجات الاستعلامات: {e}")
    
    async def _handle_callback_query(self, event):
        """معالجة استعلام الاستدعاء"""
        try:
            data = event.data.decode('utf-8')
            user_id = event.sender_id
            chat_id = event.chat_id
            
            # فحص الأمان
            permission_check = await self.security_manager.check_user_permission(
                user_id, chat_id, 'callback'
            )
            
            if not permission_check['allowed']:
                await event.answer(f"❌ {permission_check['message']}", alert=True)
                return
            
            # معالجة الاستعلامات حسب النوع
            if data.startswith("play_"):
                await self._handle_play_callback(event, data)
            elif data.startswith("queue_"):
                await self._handle_queue_callback(event, data)
            elif data.startswith("control_"):
                await self._handle_control_callback(event, data)
            elif data.startswith("search_"):
                await self._handle_search_callback(event, data)
            elif data.startswith("settings_"):
                await self._handle_settings_callback(event, data)
            elif data.startswith("help_"):
                await self._handle_help_callback(event, data)
            elif data.startswith("owner_"):
                # معالجة أوامر المالك في owner_panel.py
                pass
            else:
                # استعلامات عامة أخرى
                await self._handle_general_callback(event, data)
                
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة الاستعلام: {e}")
            try:
                await event.answer("❌ حدث خطأ في معالجة الطلب", alert=True)
            except:
                pass
    
    async def _handle_play_callback(self, event, data: str):
        """معالجة استعلامات التشغيل"""
        try:
            parts = data.split("_")
            action = parts[1] if len(parts) > 1 else ""
            
            if action == "track":
                # تشغيل مقطع محدد
                track_id = parts[2] if len(parts) > 2 else ""
                platform = parts[3] if len(parts) > 3 else ""
                
                await self._play_selected_track(event, track_id, platform)
                
            elif action == "pause":
                # إيقاف مؤقت
                result = await self.music_engine.pause_playback(event.chat_id)
                await event.answer(result['message'])
                
            elif action == "resume":
                # استئناف
                result = await self.music_engine.resume_playback(event.chat_id)
                await event.answer(result['message'])
                
            elif action == "skip":
                # تخطي
                result = await self.music_engine.skip_track(event.chat_id)
                await event.answer(result['message'])
                
            elif action == "stop":
                # إيقاف نهائي
                result = await self.music_engine.stop_playback(event.chat_id)
                await event.answer(result['message'])
                
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة استعلام التشغيل: {e}")
            await event.answer("❌ حدث خطأ في التشغيل", alert=True)
    
    async def _handle_queue_callback(self, event, data: str):
        """معالجة استعلامات قائمة الانتظار"""
        try:
            parts = data.split("_")
            action = parts[1] if len(parts) > 1 else ""
            
            if action == "show":
                # عرض قائمة الانتظار
                await self._show_queue_details(event)
                
            elif action == "clear":
                # مسح قائمة الانتظار
                result = await self.music_engine.clear_queue(event.chat_id)
                await event.answer(result['message'])
                
            elif action == "shuffle":
                # خلط قائمة الانتظار
                result = await self.music_engine.toggle_shuffle(event.chat_id)
                await event.answer(result['message'])
                
            elif action == "loop":
                # تبديل التكرار
                mode = parts[2] if len(parts) > 2 else "track"
                result = await self.music_engine.set_loop_mode(event.chat_id, mode)
                await event.answer(result['message'])
                
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة استعلام القائمة: {e}")
            await event.answer("❌ حدث خطأ في القائمة", alert=True)
    
    async def _handle_control_callback(self, event, data: str):
        """معالجة استعلامات التحكم"""
        try:
            parts = data.split("_")
            action = parts[1] if len(parts) > 1 else ""
            
            if action == "volume":
                # تغيير مستوى الصوت
                volume = int(parts[2]) if len(parts) > 2 else 100
                await self._set_volume(event, volume)
                
            elif action == "seek":
                # التنقل في المقطع
                position = int(parts[2]) if len(parts) > 2 else 0
                await self._seek_track(event, position)
                
            elif action == "speed":
                # تغيير سرعة التشغيل
                speed = float(parts[2]) if len(parts) > 2 else 1.0
                await self._set_playback_speed(event, speed)
                
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة استعلام التحكم: {e}")
            await event.answer("❌ حدث خطأ في التحكم", alert=True)
    
    async def _handle_search_callback(self, event, data: str):
        """معالجة استعلامات البحث"""
        try:
            parts = data.split("_")
            action = parts[1] if len(parts) > 1 else ""
            
            if action == "result":
                # اختيار نتيجة بحث
                result_index = int(parts[2]) if len(parts) > 2 else 0
                await self._select_search_result(event, result_index)
                
            elif action == "platform":
                # البحث في منصة محددة
                platform = parts[2] if len(parts) > 2 else ""
                query = parts[3] if len(parts) > 3 else ""
                await self._search_in_platform(event, platform, query)
                
            elif action == "more":
                # عرض المزيد من النتائج
                await self._show_more_results(event)
                
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة استعلام البحث: {e}")
            await event.answer("❌ حدث خطأ في البحث", alert=True)
    
    async def _handle_settings_callback(self, event, data: str):
        """معالجة استعلامات الإعدادات"""
        try:
            parts = data.split("_")
            action = parts[1] if len(parts) > 1 else ""
            
            if action == "language":
                # تغيير اللغة
                lang = parts[2] if len(parts) > 2 else "ar"
                await self._change_language(event, lang)
                
            elif action == "quality":
                # تغيير جودة الصوت
                quality = parts[2] if len(parts) > 2 else "medium"
                await self._change_quality(event, quality)
                
            elif action == "mode":
                # تغيير نمط التشغيل
                mode = parts[2] if len(parts) > 2 else "everyone"
                await self._change_play_mode(event, mode)
                
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة استعلام الإعدادات: {e}")
            await event.answer("❌ حدث خطأ في الإعدادات", alert=True)
    
    async def _handle_help_callback(self, event, data: str):
        """معالجة استعلامات المساعدة"""
        try:
            parts = data.split("_")
            section = parts[1] if len(parts) > 1 else "main"
            
            help_texts = {
                "main": "🎵 **مساعدة البوت الرئيسية**\n\nاختر قسماً للحصول على المساعدة:",
                "play": "🎧 **أوامر التشغيل**\n\n• `/play` - تشغيل موسيقى\n• `/pause` - إيقاف مؤقت\n• `/resume` - استئناف\n• `/skip` - تخطي\n• `/stop` - إيقاف نهائي",
                "queue": "📋 **إدارة قائمة الانتظار**\n\n• `/queue` - عرض القائمة\n• `/shuffle` - خلط\n• `/loop` - تكرار\n• `/clear` - مسح القائمة",
                "settings": "⚙️ **الإعدادات**\n\n• `/settings` - إعدادات المجموعة\n• `/language` - تغيير اللغة\n• `/quality` - جودة الصوت"
            }
            
            help_text = help_texts.get(section, help_texts["main"])
            
            keyboard = [
                [
                    Button.inline("🎧 التشغيل", b"help_play"),
                    Button.inline("📋 القائمة", b"help_queue")
                ],
                [
                    Button.inline("⚙️ الإعدادات", b"help_settings"),
                    Button.inline("🔙 الرئيسية", b"help_main")
                ]
            ]
            
            await event.edit(help_text, buttons=keyboard)
            
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة استعلام المساعدة: {e}")
            await event.answer("❌ حدث خطأ في المساعدة", alert=True)
    
    async def _handle_general_callback(self, event, data: str):
        """معالجة الاستعلامات العامة"""
        try:
            if data == "close":
                # إغلاق الرسالة
                await event.delete()
                
            elif data == "refresh":
                # تحديث المعلومات
                await self._refresh_message(event)
                
            elif data == "back":
                # العودة للقائمة السابقة
                await self._go_back(event)
                
            elif data.startswith("page_"):
                # التنقل بين الصفحات
                page = int(data.split("_")[1])
                await self._change_page(event, page)
                
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة الاستعلام العام: {e}")
            await event.answer("❌ حدث خطأ", alert=True)
    
    # وظائف مساعدة
    async def _play_selected_track(self, event, track_id: str, platform: str):
        """تشغيل مقطع محدد"""
        try:
            # الحصول على معلومات المقطع من المنصة
            from ..platforms import platform_manager
            track_info = await platform_manager.get_track_info(platform, track_id)
            
            if not track_info:
                await event.answer("❌ لم يتم العثور على المقطع", alert=True)
                return
            
            # تحويل إلى TrackInfo
            from ..core.music_engine import TrackInfo
            track = TrackInfo(
                title=track_info['title'],
                url=track_info['url'],
                duration=track_info.get('duration', 0),
                platform=platform,
                thumbnail=track_info.get('thumbnail', ''),
                artist=track_info.get('artist', ''),
                requested_by=event.sender_id
            )
            
            # تشغيل المقطع
            result = await self.music_engine.play_track(event.chat_id, track, event.sender_id)
            
            if result['success']:
                await event.answer(f"🎵 {result['message']}")
            else:
                await event.answer(f"❌ {result['message']}", alert=True)
                
        except Exception as e:
            logger.error(f"❌ خطأ في تشغيل المقطع: {e}")
            await event.answer("❌ حدث خطأ في التشغيل", alert=True)
    
    async def _show_queue_details(self, event):
        """عرض تفاصيل قائمة الانتظار"""
        try:
            result = await self.music_engine.get_queue(event.chat_id)
            
            if not result['success']:
                await event.answer(result['message'], alert=True)
                return
            
            queue_info = result['queue_info']
            # تحديث الرسالة بتفاصيل القائمة
            # (سيتم تنفيذ التفاصيل حسب التصميم المطلوب)
            
        except Exception as e:
            logger.error(f"❌ خطأ في عرض تفاصيل القائمة: {e}")
    
    # باقي الوظائف المساعدة...
    async def _set_volume(self, event, volume: int):
        """تعيين مستوى الصوت"""
        pass
    
    async def _seek_track(self, event, position: int):
        """التنقل في المقطع"""
        pass
    
    async def _set_playback_speed(self, event, speed: float):
        """تعيين سرعة التشغيل"""
        pass
    
    async def _select_search_result(self, event, index: int):
        """اختيار نتيجة بحث"""
        pass
    
    async def _search_in_platform(self, event, platform: str, query: str):
        """البحث في منصة محددة"""
        pass
    
    async def _show_more_results(self, event):
        """عرض المزيد من النتائج"""
        pass
    
    async def _change_language(self, event, lang: str):
        """تغيير اللغة"""
        pass
    
    async def _change_quality(self, event, quality: str):
        """تغيير جودة الصوت"""
        pass
    
    async def _change_play_mode(self, event, mode: str):
        """تغيير نمط التشغيل"""
        pass
    
    async def _refresh_message(self, event):
        """تحديث الرسالة"""
        pass
    
    async def _go_back(self, event):
        """العودة للقائمة السابقة"""
        pass
    
    async def _change_page(self, event, page: int):
        """تغيير الصفحة"""
        pass

# إنشاء مثيل عام لمعالج الاستعلامات
callback_handler = None  # سيتم تهيئته في الملف الرئيسي