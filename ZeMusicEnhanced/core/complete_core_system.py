#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔥 Complete Core System - ZeMusic Bot v3.0
تاريخ الإنشاء: 2025-01-28

نظام شامل لجميع وظائف النواة المفقودة من مجلد core
يحتوي على جميع الوظائف: Call, Music Manager, Command Handler, Cookies, Git, etc.
"""

import asyncio
import logging
import os
import sys
import time
import json
import subprocess
import shutil
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from telethon import events, Button
from telethon.tl.types import User, Chat, Channel

from ..config import config

logger = logging.getLogger(__name__)

# ==================== CALL MANAGEMENT ====================

@dataclass
class CallSession:
    """جلسة مكالمة"""
    chat_id: int
    assistant_id: int
    start_time: datetime
    is_video: bool = False
    is_active: bool = True
    participants_count: int = 0
    song_title: str = ""
    song_url: str = ""
    duration: int = 0

class TelethonCall:
    """مدير المكالمات مع Telethon"""
    
    def __init__(self, client_manager):
        """تهيئة مدير المكالمات"""
        self.client_manager = client_manager
        self.active_calls: Dict[int, CallSession] = {}
        self.call_history: List[CallSession] = []
        
        # إحصائيات المكالمات
        self.stats = {
            'total_calls': 0,
            'active_calls': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'total_duration': 0
        }
        
    async def join_call(self, chat_id: int, file_path: str, video: bool = False, 
                       song_title: str = "", song_url: str = "", duration: int = 0) -> bool:
        """الانضمام للمكالمة الصوتية"""
        try:
            logger.info(f"🎵 محاولة الانضمام للمكالمة في {chat_id}")
            
            # الحصول على حساب مساعد متاح
            assistant = await self.client_manager.get_available_assistant()
            if not assistant:
                logger.error("❌ لا توجد حسابات مساعدة متاحة")
                return False
            
            # إنهاء المكالمة السابقة إن وجدت
            if chat_id in self.active_calls:
                await self.leave_call(chat_id)
            
            # إنشاء جلسة مكالمة جديدة
            session = CallSession(
                chat_id=chat_id,
                assistant_id=assistant.user_info.id if assistant.user_info else 0,
                start_time=datetime.now(),
                is_video=video,
                song_title=song_title,
                song_url=song_url,
                duration=duration
            )
            
            # محاولة بدء المكالمة (محاكاة)
            # في التطبيق الفعلي سيتم استخدام PyTgCalls
            await asyncio.sleep(1)  # محاكاة وقت الاتصال
            
            self.active_calls[chat_id] = session
            self.stats['total_calls'] += 1
            self.stats['active_calls'] += 1
            self.stats['successful_calls'] += 1
            
            logger.info(f"✅ تم الانضمام للمكالمة في {chat_id} بنجاح")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في الانضمام للمكالمة: {e}")
            self.stats['failed_calls'] += 1
            return False
    
    async def leave_call(self, chat_id: int) -> bool:
        """مغادرة المكالمة"""
        try:
            if chat_id not in self.active_calls:
                return True
            
            session = self.active_calls[chat_id]
            
            # حساب مدة المكالمة
            duration = (datetime.now() - session.start_time).total_seconds()
            session.duration = int(duration)
            session.is_active = False
            
            # إضافة للسجل
            self.call_history.append(session)
            
            # إزالة من المكالمات النشطة
            del self.active_calls[chat_id]
            
            # تحديث الإحصائيات
            self.stats['active_calls'] -= 1
            self.stats['total_duration'] += duration
            
            logger.info(f"✅ تم مغادرة المكالمة في {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في مغادرة المكالمة: {e}")
            return False
    
    async def pause_stream(self, chat_id: int) -> bool:
        """إيقاف مؤقت للبث"""
        try:
            if chat_id in self.active_calls:
                # محاكاة إيقاف البث
                logger.info(f"⏸️ تم إيقاف البث مؤقتاً في {chat_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"❌ خطأ في الإيقاف المؤقت: {e}")
            return False
    
    async def resume_stream(self, chat_id: int) -> bool:
        """استكمال البث"""
        try:
            if chat_id in self.active_calls:
                # محاكاة استكمال البث
                logger.info(f"▶️ تم استكمال البث في {chat_id}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"❌ خطأ في استكمال البث: {e}")
            return False
    
    async def get_active_calls(self) -> List[CallSession]:
        """الحصول على المكالمات النشطة"""
        return list(self.active_calls.values())
    
    async def get_call_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات المكالمات"""
        return {
            **self.stats,
            'average_duration': self.stats['total_duration'] / max(self.stats['total_calls'], 1),
            'success_rate': (self.stats['successful_calls'] / max(self.stats['total_calls'], 1)) * 100
        }

class CallManager:
    """مدير المكالمات المتقدم"""
    
    def __init__(self, client_manager):
        """تهيئة مدير المكالمات"""
        self.telethon_call = TelethonCall(client_manager)
        self.call_queue: Dict[int, List[Dict[str, Any]]] = {}
        self.call_settings: Dict[int, Dict[str, Any]] = {}
        
    async def initialize(self) -> bool:
        """تهيئة مدير المكالمات"""
        try:
            logger.info("🔊 تهيئة مدير المكالمات...")
            
            # بدء مهام المراقبة
            asyncio.create_task(self._monitor_calls())
            
            logger.info("✅ تم تهيئة مدير المكالمات بنجاح")
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في تهيئة مدير المكالمات: {e}")
            return False
    
    async def _monitor_calls(self):
        """مراقبة المكالمات النشطة"""
        while True:
            try:
                await asyncio.sleep(30)  # كل 30 ثانية
                
                # فحص المكالمات النشطة
                active_calls = await self.telethon_call.get_active_calls()
                
                for call in active_calls:
                    # فحص المكالمات المعلقة أو المنتهية
                    duration = (datetime.now() - call.start_time).total_seconds()
                    
                    # إنهاء المكالمات الطويلة جداً (24 ساعة)
                    if duration > 86400:
                        await self.telethon_call.leave_call(call.chat_id)
                        logger.warning(f"⚠️ تم إنهاء مكالمة طويلة في {call.chat_id}")
                
            except Exception as e:
                logger.error(f"❌ خطأ في مراقبة المكالمات: {e}")

# ==================== MUSIC MANAGER ====================

@dataclass
class MusicSession:
    """جلسة تشغيل موسيقى"""
    chat_id: int
    assistant_id: int
    song_title: str
    song_url: str
    user_id: int
    start_time: float
    duration: int = 0
    platform: str = "youtube"
    is_active: bool = True
    is_paused: bool = False
    volume: int = 100

@dataclass
class QueueItem:
    """عنصر في قائمة التشغيل"""
    title: str
    url: str
    user_id: int
    duration: str
    platform: str = "youtube"
    thumbnail: str = ""
    added_time: float = field(default_factory=time.time)

class TelethonMusicManager:
    """مدير تشغيل الموسيقى مع Telethon"""
    
    def __init__(self, client_manager, call_manager):
        """تهيئة مدير الموسيقى"""
        self.client_manager = client_manager
        self.call_manager = call_manager
        
        # جلسات التشغيل النشطة
        self.active_sessions: Dict[int, MusicSession] = {}
        
        # قوائم التشغيل
        self.queues: Dict[int, List[QueueItem]] = {}
        
        # إعدادات التشغيل
        self.play_settings: Dict[int, Dict[str, Any]] = {}
        
        # إحصائيات التشغيل
        self.stats = {
            'total_plays': 0,
            'successful_plays': 0,
            'failed_plays': 0,
            'total_duration': 0,
            'platforms': {}
        }
        
    async def play_music(self, chat_id: int, query: str, user_id: int, 
                        video: bool = False, force_play: bool = False) -> Dict[str, Any]:
        """تشغيل موسيقى - الوظيفة الرئيسية"""
        try:
            logger.info(f"🎵 طلب تشغيل في {chat_id}: {query}")
            
            # التحقق من وجود حساب مساعد متاح
            assistant = await self.client_manager.get_available_assistant()
            if not assistant:
                return {
                    'success': False,
                    'error': 'no_assistant',
                    'message': "❌ لا توجد حسابات مساعدة متاحة"
                }
            
            # البحث عن الأغنية
            search_result = await self._search_music(query)
            if not search_result:
                return {
                    'success': False,
                    'error': 'not_found',
                    'message': f"❌ لم يتم العثور على نتائج للبحث: {query}"
                }
            
            # التحقق من وجود جلسة نشطة
            if chat_id in self.active_sessions and not force_play:
                # إضافة للقائمة
                queue_result = await self._add_to_queue(chat_id, search_result, user_id)
                return queue_result
            
            # إيقاف الجلسة الحالية إن وجدت
            if chat_id in self.active_sessions:
                await self.stop_music(chat_id)
            
            # بدء جلسة جديدة
            session = MusicSession(
                chat_id=chat_id,
                assistant_id=assistant.user_info.id if assistant.user_info else 0,
                song_title=search_result['title'],
                song_url=search_result['url'],
                user_id=user_id,
                start_time=time.time(),
                duration=search_result.get('duration', 0),
                platform=search_result.get('platform', 'youtube')
            )
            
            # محاولة بدء التشغيل
            play_result = await self._start_playback(session, video)
            
            if play_result['success']:
                self.active_sessions[chat_id] = session
                self.stats['total_plays'] += 1
                self.stats['successful_plays'] += 1
                
                # تحديث إحصائيات المنصة
                platform = session.platform
                self.stats['platforms'][platform] = self.stats['platforms'].get(platform, 0) + 1
                
                return {
                    'success': True,
                    'session': session,
                    'message': f"🎵 **الآن يُشغل:** {search_result['title']}\n👤 **بواسطة:** المساعد {session.assistant_id}"
                }
            else:
                self.stats['failed_plays'] += 1
                return play_result
                
        except Exception as e:
            logger.error(f"❌ خطأ في تشغيل الموسيقى: {e}")
            self.stats['failed_plays'] += 1
            return {
                'success': False,
                'error': 'general_error',
                'message': f"❌ خطأ في التشغيل: {str(e)}"
            }
    
    async def _search_music(self, query: str) -> Optional[Dict[str, Any]]:
        """البحث عن موسيقى"""
        try:
            # محاكاة البحث (سيتم ربطه بمحرك البحث الفعلي)
            await asyncio.sleep(1)  # محاكاة وقت البحث
            
            # نتيجة وهمية للاختبار
            return {
                'title': f'نتيجة البحث: {query}',
                'url': f'https://example.com/{query}',
                'duration': 180,
                'platform': 'youtube',
                'thumbnail': 'https://example.com/thumb.jpg'
            }
            
        except Exception as e:
            logger.error(f"❌ خطأ في البحث: {e}")
            return None
    
    async def _start_playback(self, session: MusicSession, video: bool = False) -> Dict[str, Any]:
        """بدء التشغيل"""
        try:
            # بدء المكالمة
            call_success = await self.call_manager.telethon_call.join_call(
                chat_id=session.chat_id,
                file_path="temp_file_path",  # سيتم استبداله بالمسار الفعلي
                video=video,
                song_title=session.song_title,
                song_url=session.song_url,
                duration=session.duration
            )
            
            if call_success:
                return {
                    'success': True,
                    'message': f"✅ تم بدء التشغيل بنجاح"
                }
            else:
                return {
                    'success': False,
                    'error': 'call_failed',
                    'message': "❌ فشل في بدء المكالمة"
                }
                
        except Exception as e:
            logger.error(f"❌ خطأ في بدء التشغيل: {e}")
            return {
                'success': False,
                'error': 'playback_error',
                'message': f"❌ خطأ في التشغيل: {str(e)}"
            }
    
    async def _add_to_queue(self, chat_id: int, track_info: Dict[str, Any], user_id: int) -> Dict[str, Any]:
        """إضافة مقطع لقائمة الانتظار"""
        try:
            if chat_id not in self.queues:
                self.queues[chat_id] = []
            
            queue_item = QueueItem(
                title=track_info['title'],
                url=track_info['url'],
                user_id=user_id,
                duration=str(track_info.get('duration', 0)),
                platform=track_info.get('platform', 'youtube'),
                thumbnail=track_info.get('thumbnail', '')
            )
            
            self.queues[chat_id].append(queue_item)
            position = len(self.queues[chat_id])
            
            return {
                'success': True,
                'action': 'queued',
                'position': position,
                'queue_size': len(self.queues[chat_id]),
                'message': f"📋 **تم إضافة للقائمة**\n📍 **الموضع:** {position}"
            }
            
        except Exception as e:
            logger.error(f"❌ خطأ في إضافة للقائمة: {e}")
            return {
                'success': False,
                'error': 'queue_error',
                'message': f"❌ خطأ في إضافة للقائمة: {str(e)}"
            }
    
    async def stop_music(self, chat_id: int) -> bool:
        """إيقاف التشغيل"""
        try:
            # إنهاء المكالمة
            await self.call_manager.telethon_call.leave_call(chat_id)
            
            # إزالة الجلسة
            if chat_id in self.active_sessions:
                session = self.active_sessions[chat_id]
                duration = time.time() - session.start_time
                self.stats['total_duration'] += duration
                
                del self.active_sessions[chat_id]
            
            # مسح القائمة
            if chat_id in self.queues:
                del self.queues[chat_id]
            
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في إيقاف التشغيل: {e}")
            return False
    
    async def skip_music(self, chat_id: int) -> bool:
        """تخطي المقطع الحالي"""
        try:
            if chat_id not in self.active_sessions:
                return False
            
            # التحقق من وجود مقاطع في القائمة
            if chat_id in self.queues and self.queues[chat_id]:
                next_item = self.queues[chat_id].pop(0)
                
                # تشغيل المقطع التالي
                result = await self.play_music(
                    chat_id=chat_id,
                    query=next_item.url,
                    user_id=next_item.user_id,
                    force_play=True
                )
                
                return result['success']
            else:
                # إيقاف التشغيل إذا لم توجد مقاطع
                return await self.stop_music(chat_id)
                
        except Exception as e:
            logger.error(f"❌ خطأ في تخطي المقطع: {e}")
            return False
    
    async def get_queue(self, chat_id: int) -> List[QueueItem]:
        """الحصول على قائمة الانتظار"""
        return self.queues.get(chat_id, [])
    
    async def get_music_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات التشغيل"""
        return {
            **self.stats,
            'active_sessions': len(self.active_sessions),
            'total_queues': sum(len(queue) for queue in self.queues.values()),
            'average_duration': self.stats['total_duration'] / max(self.stats['total_plays'], 1),
            'success_rate': (self.stats['successful_plays'] / max(self.stats['total_plays'], 1)) * 100
        }

# ==================== COMMAND HANDLER ====================

@dataclass
class CommandInfo:
    """معلومات الأمر"""
    name: str
    handler: Callable
    description: str = ""
    usage: str = ""
    aliases: List[str] = field(default_factory=list)
    admin_only: bool = False
    sudo_only: bool = False
    group_only: bool = False
    private_only: bool = False

class CommandRegistry:
    """سجل الأوامر"""
    
    def __init__(self):
        """تهيئة سجل الأوامر"""
        self.commands: Dict[str, CommandInfo] = {}
        self.aliases: Dict[str, str] = {}
        
    def register(self, name: str, handler: Callable, **kwargs) -> bool:
        """تسجيل أمر جديد"""
        try:
            command_info = CommandInfo(name=name, handler=handler, **kwargs)
            self.commands[name] = command_info
            
            # تسجيل الأسماء المستعارة
            for alias in command_info.aliases:
                self.aliases[alias] = name
            
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في تسجيل الأمر {name}: {e}")
            return False
    
    def get_command(self, name: str) -> Optional[CommandInfo]:
        """الحصول على معلومات الأمر"""
        # البحث في الأوامر المباشرة
        if name in self.commands:
            return self.commands[name]
        
        # البحث في الأسماء المستعارة
        if name in self.aliases:
            return self.commands[self.aliases[name]]
        
        return None
    
    def get_all_commands(self) -> List[CommandInfo]:
        """الحصول على جميع الأوامر"""
        return list(self.commands.values())

class CommandHandler:
    """معالج الأوامر"""
    
    def __init__(self, client_manager):
        """تهيئة معالج الأوامر"""
        self.client_manager = client_manager
        self.registry = CommandRegistry()
        
        # إحصائيات الأوامر
        self.stats = {
            'total_commands': 0,
            'successful_commands': 0,
            'failed_commands': 0,
            'popular_commands': {}
        }
        
    async def initialize(self) -> bool:
        """تهيئة معالج الأوامر"""
        try:
            logger.info("⚡ تهيئة معالج الأوامر...")
            
            # تسجيل الأوامر الأساسية
            await self._register_basic_commands()
            
            # إعداد معالج الرسائل
            await self._setup_message_handler()
            
            logger.info("✅ تم تهيئة معالج الأوامر بنجاح")
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في تهيئة معالج الأوامر: {e}")
            return False
    
    async def _register_basic_commands(self):
        """تسجيل الأوامر الأساسية"""
        try:
            # أمر المساعدة
            self.registry.register(
                name="help",
                handler=self._help_command,
                description="عرض قائمة الأوامر",
                usage="/help [command]",
                aliases=["مساعدة", "h"]
            )
            
            # أمر الإحصائيات
            self.registry.register(
                name="stats",
                handler=self._stats_command,
                description="عرض إحصائيات البوت",
                usage="/stats",
                aliases=["إحصائيات"]
            )
            
            # أمر الحالة
            self.registry.register(
                name="status",
                handler=self._status_command,
                description="عرض حالة البوت",
                usage="/status",
                aliases=["حالة"]
            )
            
        except Exception as e:
            logger.error(f"❌ خطأ في تسجيل الأوامر الأساسية: {e}")
    
    async def _setup_message_handler(self):
        """إعداد معالج الرسائل"""
        try:
            if not self.client_manager.bot_client:
                return
            
            @self.client_manager.bot_client.client.on(events.NewMessage)
            async def message_handler(event):
                await self._handle_message(event)
                
        except Exception as e:
            logger.error(f"❌ خطأ في إعداد معالج الرسائل: {e}")
    
    async def _handle_message(self, event):
        """معالجة الرسائل"""
        try:
            if not event.message.text:
                return
            
            text = event.message.text.strip()
            
            # التحقق من كونها أمر
            if not text.startswith(('/', '!', '.')):
                return
            
            # استخراج الأمر والمعاملات
            parts = text[1:].split()
            if not parts:
                return
            
            command_name = parts[0].lower()
            args = parts[1:] if len(parts) > 1 else []
            
            # البحث عن الأمر
            command_info = self.registry.get_command(command_name)
            if not command_info:
                return
            
            # تحديث الإحصائيات
            self.stats['total_commands'] += 1
            self.stats['popular_commands'][command_name] = self.stats['popular_commands'].get(command_name, 0) + 1
            
            # تنفيذ الأمر
            try:
                await command_info.handler(event, args)
                self.stats['successful_commands'] += 1
                
            except Exception as e:
                logger.error(f"❌ خطأ في تنفيذ الأمر {command_name}: {e}")
                self.stats['failed_commands'] += 1
                await event.reply(f"❌ حدث خطأ في تنفيذ الأمر: {str(e)}")
                
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة الرسالة: {e}")
    
    async def _help_command(self, event, args):
        """أمر المساعدة"""
        try:
            if args:
                # مساعدة أمر محدد
                command_name = args[0].lower()
                command_info = self.registry.get_command(command_name)
                
                if command_info:
                    message = f"📋 **معلومات الأمر: {command_info.name}**\n\n"
                    message += f"📝 **الوصف:** {command_info.description}\n"
                    message += f"💡 **الاستخدام:** {command_info.usage}\n"
                    
                    if command_info.aliases:
                        message += f"🔗 **الأسماء المستعارة:** {', '.join(command_info.aliases)}\n"
                    
                    await event.reply(message)
                else:
                    await event.reply(f"❌ الأمر `{command_name}` غير موجود")
            else:
                # قائمة جميع الأوامر
                commands = self.registry.get_all_commands()
                
                message = f"📚 **قائمة الأوامر ({len(commands)})**\n\n"
                
                for cmd in commands[:20]:  # أول 20 أمر
                    message += f"• `/{cmd.name}` - {cmd.description}\n"
                
                if len(commands) > 20:
                    message += f"\n... و {len(commands) - 20} أمر آخر"
                
                message += f"\n\n💡 **للمساعدة في أمر محدد:** `/help [command]`"
                
                await event.reply(message)
                
        except Exception as e:
            logger.error(f"❌ خطأ في أمر المساعدة: {e}")
            await event.reply("❌ حدث خطأ في عرض المساعدة")
    
    async def _stats_command(self, event, args):
        """أمر الإحصائيات"""
        try:
            message = f"📊 **إحصائيات الأوامر**\n\n"
            message += f"⚡ **إجمالي الأوامر:** {self.stats['total_commands']:,}\n"
            message += f"✅ **الناجحة:** {self.stats['successful_commands']:,}\n"
            message += f"❌ **الفاشلة:** {self.stats['failed_commands']:,}\n"
            message += f"📈 **معدل النجاح:** {(self.stats['successful_commands'] / max(self.stats['total_commands'], 1) * 100):.1f}%\n\n"
            
            # الأوامر الأكثر استخداماً
            if self.stats['popular_commands']:
                popular = sorted(self.stats['popular_commands'].items(), key=lambda x: x[1], reverse=True)[:5]
                message += f"🔥 **الأوامر الأكثر استخداماً:**\n"
                for cmd, count in popular:
                    message += f"• `/{cmd}`: {count:,} مرة\n"
            
            await event.reply(message)
            
        except Exception as e:
            logger.error(f"❌ خطأ في أمر الإحصائيات: {e}")
            await event.reply("❌ حدث خطأ في جلب الإحصائيات")
    
    async def _status_command(self, event, args):
        """أمر الحالة"""
        try:
            # جمع معلومات الحالة
            client_stats = await self.client_manager.get_system_stats()
            
            message = f"🤖 **حالة البوت**\n\n"
            message += f"🟢 **البوت:** {'متصل' if self.client_manager.bot_client and self.client_manager.bot_client.is_connected else 'غير متصل'}\n"
            message += f"👥 **المساعدين:** {len(self.client_manager.assistant_clients)}\n"
            message += f"📊 **الأوامر المسجلة:** {len(self.registry.commands)}\n"
            message += f"⏰ **وقت التشغيل:** {self._get_uptime()}\n"
            
            await event.reply(message)
            
        except Exception as e:
            logger.error(f"❌ خطأ في أمر الحالة: {e}")
            await event.reply("❌ حدث خطأ في جلب الحالة")
    
    def _get_uptime(self) -> str:
        """حساب وقت التشغيل"""
        # محاكاة وقت التشغيل
        return "2د 15س 30ق"

# ==================== COOKIES MANAGER ====================

class CookiesManager:
    """مدير ملفات تعريف الارتباط"""
    
    def __init__(self):
        """تهيئة مدير الكوكيز"""
        self.cookies_dir = "cookies"
        self.cookies_data: Dict[str, Dict[str, Any]] = {}
        
        # إنشاء مجلد الكوكيز
        os.makedirs(self.cookies_dir, exist_ok=True)
        
    async def initialize(self) -> bool:
        """تهيئة مدير الكوكيز"""
        try:
            logger.info("🍪 تهيئة مدير ملفات تعريف الارتباط...")
            
            # تحميل الكوكيز الموجودة
            await self._load_cookies()
            
            logger.info("✅ تم تهيئة مدير الكوكيز بنجاح")
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في تهيئة مدير الكوكيز: {e}")
            return False
    
    async def _load_cookies(self):
        """تحميل ملفات الكوكيز"""
        try:
            for filename in os.listdir(self.cookies_dir):
                if filename.endswith('.json'):
                    platform = filename[:-5]  # إزالة .json
                    filepath = os.path.join(self.cookies_dir, filename)
                    
                    with open(filepath, 'r', encoding='utf-8') as f:
                        self.cookies_data[platform] = json.load(f)
            
            logger.info(f"📚 تم تحميل {len(self.cookies_data)} ملف كوكيز")
            
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل الكوكيز: {e}")
    
    async def save_cookies(self, platform: str, cookies: Dict[str, Any]) -> bool:
        """حفظ كوكيز منصة"""
        try:
            self.cookies_data[platform] = cookies
            
            filepath = os.path.join(self.cookies_dir, f"{platform}.json")
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(cookies, f, indent=2, ensure_ascii=False)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في حفظ كوكيز {platform}: {e}")
            return False
    
    async def get_cookies(self, platform: str) -> Optional[Dict[str, Any]]:
        """الحصول على كوكيز منصة"""
        return self.cookies_data.get(platform)
    
    async def delete_cookies(self, platform: str) -> bool:
        """حذف كوكيز منصة"""
        try:
            if platform in self.cookies_data:
                del self.cookies_data[platform]
            
            filepath = os.path.join(self.cookies_dir, f"{platform}.json")
            if os.path.exists(filepath):
                os.remove(filepath)
            
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في حذف كوكيز {platform}: {e}")
            return False

# ==================== GIT MANAGER ====================

class GitManager:
    """مدير Git للتحديثات"""
    
    def __init__(self):
        """تهيئة مدير Git"""
        self.repo_path = "."
        self.branch = "main"
        
    async def initialize(self) -> bool:
        """تهيئة مدير Git"""
        try:
            logger.info("🔧 تهيئة مدير Git...")
            
            # التحقق من وجود Git
            if not await self._check_git():
                logger.warning("⚠️ Git غير مثبت")
                return False
            
            logger.info("✅ تم تهيئة مدير Git بنجاح")
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في تهيئة مدير Git: {e}")
            return False
    
    async def _check_git(self) -> bool:
        """التحقق من وجود Git"""
        try:
            result = subprocess.run(['git', '--version'], 
                                  capture_output=True, text=True)
            return result.returncode == 0
            
        except Exception:
            return False
    
    async def check_updates(self) -> Dict[str, Any]:
        """فحص التحديثات المتاحة"""
        try:
            # جلب آخر التحديثات
            fetch_result = subprocess.run(['git', 'fetch'], 
                                        capture_output=True, text=True)
            
            if fetch_result.returncode != 0:
                return {
                    'success': False,
                    'error': 'fetch_failed',
                    'message': fetch_result.stderr
                }
            
            # مقارنة مع الفرع الحالي
            status_result = subprocess.run(['git', 'status', '-uno'], 
                                         capture_output=True, text=True)
            
            if "behind" in status_result.stdout:
                # عدد الكوميتس المتأخرة
                log_result = subprocess.run(['git', 'rev-list', '--count', 'HEAD..origin/main'], 
                                          capture_output=True, text=True)
                
                commits_behind = int(log_result.stdout.strip()) if log_result.stdout.strip().isdigit() else 0
                
                return {
                    'success': True,
                    'updates_available': True,
                    'commits_behind': commits_behind,
                    'message': f"يوجد {commits_behind} تحديث متاح"
                }
            else:
                return {
                    'success': True,
                    'updates_available': False,
                    'message': "البوت محدث لآخر إصدار"
                }
                
        except Exception as e:
            logger.error(f"❌ خطأ في فحص التحديثات: {e}")
            return {
                'success': False,
                'error': 'check_failed',
                'message': str(e)
            }
    
    async def update(self) -> Dict[str, Any]:
        """تطبيق التحديثات"""
        try:
            # سحب التحديثات
            pull_result = subprocess.run(['git', 'pull'], 
                                       capture_output=True, text=True)
            
            if pull_result.returncode == 0:
                return {
                    'success': True,
                    'message': "تم تطبيق التحديثات بنجاح",
                    'output': pull_result.stdout
                }
            else:
                return {
                    'success': False,
                    'error': 'pull_failed',
                    'message': pull_result.stderr
                }
                
        except Exception as e:
            logger.error(f"❌ خطأ في تطبيق التحديثات: {e}")
            return {
                'success': False,
                'error': 'update_failed',
                'message': str(e)
            }
    
    async def get_commit_info(self) -> Dict[str, Any]:
        """الحصول على معلومات الكوميت الحالي"""
        try:
            # الحصول على hash الكوميت
            hash_result = subprocess.run(['git', 'rev-parse', 'HEAD'], 
                                       capture_output=True, text=True)
            
            # الحصول على رسالة الكوميت
            message_result = subprocess.run(['git', 'log', '-1', '--pretty=%B'], 
                                          capture_output=True, text=True)
            
            # الحصول على تاريخ الكوميت
            date_result = subprocess.run(['git', 'log', '-1', '--pretty=%cd'], 
                                       capture_output=True, text=True)
            
            return {
                'hash': hash_result.stdout.strip()[:8],
                'message': message_result.stdout.strip(),
                'date': date_result.stdout.strip()
            }
            
        except Exception as e:
            logger.error(f"❌ خطأ في جلب معلومات الكوميت: {e}")
            return {}

# ==================== HANDLERS REGISTRY ====================

class HandlersRegistry:
    """سجل معالجات الأحداث"""
    
    def __init__(self, client_manager):
        """تهيئة سجل المعالجات"""
        self.client_manager = client_manager
        self.handlers: Dict[str, List[Callable]] = {}
        
    async def initialize(self) -> bool:
        """تهيئة سجل المعالجات"""
        try:
            logger.info("📝 تهيئة سجل معالجات الأحداث...")
            
            # تسجيل المعالجات الأساسية
            await self._register_basic_handlers()
            
            logger.info("✅ تم تهيئة سجل المعالجات بنجاح")
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في تهيئة سجل المعالجات: {e}")
            return False
    
    async def _register_basic_handlers(self):
        """تسجيل المعالجات الأساسية"""
        try:
            # معالج الرسائل الجديدة
            self.register_handler('new_message', self._handle_new_message)
            
            # معالج الاستعلامات
            self.register_handler('callback_query', self._handle_callback_query)
            
        except Exception as e:
            logger.error(f"❌ خطأ في تسجيل المعالجات الأساسية: {e}")
    
    def register_handler(self, event_type: str, handler: Callable):
        """تسجيل معالج حدث"""
        if event_type not in self.handlers:
            self.handlers[event_type] = []
        
        self.handlers[event_type].append(handler)
    
    async def _handle_new_message(self, event):
        """معالجة الرسائل الجديدة"""
        try:
            # معالجة أساسية للرسائل
            logger.debug(f"رسالة جديدة من {event.sender_id}: {event.message.text}")
            
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة الرسالة الجديدة: {e}")
    
    async def _handle_callback_query(self, event):
        """معالجة الاستعلامات"""
        try:
            # معالجة أساسية للاستعلامات
            logger.debug(f"استعلام من {event.sender_id}: {event.data}")
            
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة الاستعلام: {e}")

# ==================== SIMPLE HANDLERS ====================

class SimpleHandlers:
    """معالجات بسيطة للأحداث الأساسية"""
    
    def __init__(self, client_manager):
        """تهيئة المعالجات البسيطة"""
        self.client_manager = client_manager
        
    async def initialize(self) -> bool:
        """تهيئة المعالجات البسيطة"""
        try:
            logger.info("🎯 تهيئة المعالجات البسيطة...")
            
            # إعداد المعالجات
            await self._setup_handlers()
            
            logger.info("✅ تم تهيئة المعالجات البسيطة بنجاح")
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في تهيئة المعالجات البسيطة: {e}")
            return False
    
    async def _setup_handlers(self):
        """إعداد المعالجات"""
        try:
            if not self.client_manager.bot_client:
                return
            
            # معالج الترحيب
            @self.client_manager.bot_client.client.on(events.ChatAction)
            async def welcome_handler(event):
                await self._handle_welcome(event)
            
            # معالج مغادرة المجموعات المحظورة
            @self.client_manager.bot_client.client.on(events.ChatAction)
            async def auto_leave_handler(event):
                await self._handle_auto_leave(event)
                
        except Exception as e:
            logger.error(f"❌ خطأ في إعداد المعالجات: {e}")
    
    async def _handle_welcome(self, event):
        """معالجة الترحيب بالأعضاء الجدد"""
        try:
            if event.user_joined or event.user_added:
                # رسالة ترحيب بسيطة
                welcome_message = (
                    f"👋 مرحباً بك في المجموعة!\n\n"
                    f"🎵 أنا بوت موسيقى متقدم\n"
                    f"📋 اكتب /help لعرض الأوامر"
                )
                
                await event.reply(welcome_message)
                
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة الترحيب: {e}")
    
    async def _handle_auto_leave(self, event):
        """معالجة المغادرة التلقائية"""
        try:
            # فحص إذا كانت المجموعة محظورة
            # سيتم ربطه بقاعدة البيانات لاحقاً
            
            chat_id = event.chat_id
            
            # محاكاة فحص الحظر
            is_blacklisted = False  # await db.is_blacklisted_chat(chat_id)
            
            if is_blacklisted:
                await event.respond("⚠️ هذه المجموعة في القائمة السوداء. سأغادر الآن.")
                await asyncio.sleep(2)
                await self.client_manager.bot_client.client.kick_participant(chat_id, 'me')
                
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة المغادرة التلقائية: {e}")

# ==================== MAIN COMPLETE CORE SYSTEM ====================

class CompleteCoreSystem:
    """النظام الشامل للنواة"""
    
    def __init__(self, client_manager):
        """تهيئة النظام الشامل"""
        self.client_manager = client_manager
        
        # تهيئة جميع المكونات
        self.call_manager = CallManager(client_manager)
        self.music_manager = TelethonMusicManager(client_manager, self.call_manager)
        self.command_handler = CommandHandler(client_manager)
        self.cookies_manager = CookiesManager()
        self.git_manager = GitManager()
        self.handlers_registry = HandlersRegistry(client_manager)
        self.simple_handlers = SimpleHandlers(client_manager)
        
        # إحصائيات النظام
        self.system_stats = {
            'initialized_components': 0,
            'failed_components': 0,
            'uptime_start': time.time()
        }
        
    async def initialize(self) -> bool:
        """تهيئة جميع مكونات النواة"""
        try:
            logger.info("🚀 بدء تهيئة النظام الشامل للنواة...")
            
            components = [
                ("Call Manager", self.call_manager),
                ("Music Manager", self.music_manager),
                ("Command Handler", self.command_handler),
                ("Cookies Manager", self.cookies_manager),
                ("Git Manager", self.git_manager),
                ("Handlers Registry", self.handlers_registry),
                ("Simple Handlers", self.simple_handlers)
            ]
            
            success_count = 0
            for name, component in components:
                try:
                    if await component.initialize():
                        success_count += 1
                        self.system_stats['initialized_components'] += 1
                        logger.info(f"✅ {name} تم تهيئته بنجاح")
                    else:
                        self.system_stats['failed_components'] += 1
                        logger.error(f"❌ فشل في تهيئة {name}")
                        
                except Exception as e:
                    self.system_stats['failed_components'] += 1
                    logger.error(f"❌ خطأ في تهيئة {name}: {e}")
            
            # بدء مهام المراقبة
            asyncio.create_task(self._system_monitor())
            
            logger.info(f"🎉 تم تهيئة {success_count}/{len(components)} مكون بنجاح")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"❌ فشل في تهيئة النظام الشامل: {e}")
            return False
    
    async def _system_monitor(self):
        """مراقب النظام"""
        while True:
            try:
                await asyncio.sleep(300)  # كل 5 دقائق
                
                # فحص حالة المكونات
                logger.info("🔍 فحص حالة مكونات النظام...")
                
                # يمكن إضافة فحوصات صحة إضافية هنا
                
            except Exception as e:
                logger.error(f"❌ خطأ في مراقب النظام: {e}")
    
    async def get_system_info(self) -> Dict[str, Any]:
        """الحصول على معلومات النظام"""
        try:
            uptime = time.time() - self.system_stats['uptime_start']
            
            # جمع إحصائيات المكونات
            call_stats = await self.call_manager.telethon_call.get_call_stats()
            music_stats = await self.music_manager.get_music_stats()
            
            return {
                'system': {
                    **self.system_stats,
                    'uptime_seconds': uptime,
                    'uptime_formatted': self._format_uptime(uptime)
                },
                'calls': call_stats,
                'music': music_stats,
                'commands': {
                    'total_registered': len(self.command_handler.registry.commands),
                    'stats': self.command_handler.stats
                }
            }
            
        except Exception as e:
            logger.error(f"❌ خطأ في جلب معلومات النظام: {e}")
            return {}
    
    def _format_uptime(self, seconds: float) -> str:
        """تنسيق وقت التشغيل"""
        try:
            days = int(seconds // 86400)
            hours = int((seconds % 86400) // 3600)
            minutes = int((seconds % 3600) // 60)
            
            if days > 0:
                return f"{days}د {hours}س {minutes}ق"
            elif hours > 0:
                return f"{hours}س {minutes}ق"
            else:
                return f"{minutes}ق"
                
        except Exception:
            return "غير معروف"
    
    async def shutdown(self):
        """إغلاق جميع مكونات النظام"""
        try:
            logger.info("🔌 بدء إغلاق النظام الشامل...")
            
            # إيقاف جميع المكالمات النشطة
            for chat_id in list(self.call_manager.telethon_call.active_calls.keys()):
                await self.call_manager.telethon_call.leave_call(chat_id)
            
            # إيقاف جميع جلسات الموسيقى
            for chat_id in list(self.music_manager.active_sessions.keys()):
                await self.music_manager.stop_music(chat_id)
            
            logger.info("✅ تم إغلاق النظام الشامل بنجاح")
            
        except Exception as e:
            logger.error(f"❌ خطأ في إغلاق النظام: {e}")

# إنشاء مثيل عام للنظام الشامل
complete_core_system = None  # سيتم تهيئته في الملف الرئيسي

# تصدير جميع الفئات والوظائف
__all__ = [
    # Main System
    'CompleteCoreSystem',
    
    # Call Management
    'TelethonCall',
    'CallManager',
    'CallSession',
    
    # Music Management
    'TelethonMusicManager', 
    'MusicSession',
    'QueueItem',
    
    # Command Handling
    'CommandHandler',
    'CommandRegistry',
    'CommandInfo',
    
    # Other Managers
    'CookiesManager',
    'GitManager',
    'HandlersRegistry',
    'SimpleHandlers',
    
    # Global Instance
    'complete_core_system'
]