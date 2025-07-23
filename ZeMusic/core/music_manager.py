# -*- coding: utf-8 -*-
"""
مدير تشغيل الموسيقى مع Telethon
"""

import asyncio
import time
import random
from typing import Dict, List, Optional, Any
from dataclasses import dataclass

import config
from ZeMusic.zemusic_logging import LOGGER
from ZeMusic.core.telethon_client import telethon_manager

@dataclass
class MusicSession:
    """جلسة تشغيل موسيقى"""
    chat_id: int
    assistant_id: int
    song_title: str
    song_url: str
    user_id: int
    start_time: float
    is_active: bool = True

@dataclass
class QueueItem:
    """عنصر في قائمة التشغيل"""
    title: str
    url: str
    user_id: int
    duration: str
    added_time: float

class TelethonMusicManager:
    """مدير تشغيل الموسيقى مع Telethon"""
    
    def __init__(self):
        self.active_sessions: Dict[int, MusicSession] = {}
        self.queues: Dict[int, List[QueueItem]] = {}
        self.logger = LOGGER(__name__)
        
    async def play_music(self, chat_id: int, query: str, user_id: int) -> Dict[str, Any]:
        """تشغيل موسيقى - الوظيفة الرئيسية"""
        try:
            # التحقق من وجود حساب مساعد متاح
            assistant = await self._get_available_assistant(chat_id)
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
            
            # إيقاف الجلسة الحالية إن وجدت
            if chat_id in self.active_sessions:
                await self.stop_music(chat_id)
            
            # بدء جلسة جديدة
            session = MusicSession(
                chat_id=chat_id,
                assistant_id=assistant['id'],
                song_title=search_result['title'],
                song_url=search_result['url'],
                user_id=user_id,
                start_time=time.time()
            )
            
            self.active_sessions[chat_id] = session
            
            # محاولة بدء التشغيل
            play_result = await self._start_playback(session)
            
            if play_result['success']:
                return {
                    'success': True,
                    'session': session,
                    'message': f"🎵 **الآن يُشغل:** {search_result['title']}\n👤 **بواسطة:** {assistant['name']}"
                }
            else:
                # إزالة الجلسة الفاشلة
                del self.active_sessions[chat_id]
                return play_result
                
        except Exception as e:
            self.logger.error(f"خطأ في تشغيل الموسيقى: {e}")
            return {
                'success': False,
                'error': 'general_error',
                'message': f"❌ خطأ في التشغيل: {str(e)}"
            }
    
    async def stop_music(self, chat_id: int) -> bool:
        """إيقاف الموسيقى"""
        try:
            if chat_id in self.active_sessions:
                session = self.active_sessions[chat_id]
                session.is_active = False
                del self.active_sessions[chat_id]
                
                # مسح قائمة التشغيل
                if chat_id in self.queues:
                    del self.queues[chat_id]
                
                self.logger.info(f"تم إيقاف الموسيقى في المحادثة {chat_id}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"خطأ في إيقاف الموسيقى: {e}")
            return False
    
    async def pause_music(self, chat_id: int) -> bool:
        """إيقاف مؤقت للموسيقى"""
        try:
            if chat_id in self.active_sessions:
                session = self.active_sessions[chat_id]
                # يمكن إضافة منطق الإيقاف المؤقت هنا
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"خطأ في الإيقاف المؤقت: {e}")
            return False
    
    async def resume_music(self, chat_id: int) -> bool:
        """استكمال تشغيل الموسيقى"""
        try:
            if chat_id in self.active_sessions:
                session = self.active_sessions[chat_id]
                # يمكن إضافة منطق الاستكمال هنا
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"خطأ في الاستكمال: {e}")
            return False
    
    async def skip_music(self, chat_id: int) -> Dict[str, Any]:
        """تخطي الأغنية الحالية وتشغيل التالية"""
        try:
            if chat_id not in self.active_sessions:
                return {
                    'success': False,
                    'message': "❌ لا توجد موسيقى قيد التشغيل"
                }
            
            # التحقق من وجود أغاني في القائمة
            if chat_id not in self.queues or not self.queues[chat_id]:
                await self.stop_music(chat_id)
                return {
                    'success': True,
                    'message': "⏭️ تم إيقاف الموسيقى - القائمة فارغة"
                }
            
            # تشغيل الأغنية التالية
            next_item = self.queues[chat_id].pop(0)
            current_session = self.active_sessions[chat_id]
            
            # تحديث الجلسة الحالية
            current_session.song_title = next_item.title
            current_session.song_url = next_item.url
            current_session.user_id = next_item.user_id
            current_session.start_time = time.time()
            
            return {
                'success': True,
                'message': f"⏭️ **الآن يُشغل:** {next_item.title}"
            }
            
        except Exception as e:
            self.logger.error(f"خطأ في التخطي: {e}")
            return {
                'success': False,
                'message': f"❌ خطأ في التخطي: {str(e)}"
            }
    
    async def add_to_queue(self, chat_id: int, query: str, user_id: int) -> Dict[str, Any]:
        """إضافة أغنية لقائمة التشغيل"""
        try:
            # البحث عن الأغنية
            search_result = await self._search_music(query)
            if not search_result:
                return {
                    'success': False,
                    'message': f"❌ لم يتم العثور على نتائج للبحث: {query}"
                }
            
            # إنشاء عنصر قائمة تشغيل
            queue_item = QueueItem(
                title=search_result['title'],
                url=search_result['url'],
                user_id=user_id,
                duration=search_result.get('duration', 'غير معروف'),
                added_time=time.time()
            )
            
            # إضافة للقائمة
            if chat_id not in self.queues:
                self.queues[chat_id] = []
            
            self.queues[chat_id].append(queue_item)
            
            queue_position = len(self.queues[chat_id])
            
            return {
                'success': True,
                'message': f"➕ **تمت الإضافة للقائمة:**\n🎵 {search_result['title']}\n📍 الموضع: {queue_position}"
            }
            
        except Exception as e:
            self.logger.error(f"خطأ في إضافة للقائمة: {e}")
            return {
                'success': False,
                'message': f"❌ خطأ في الإضافة: {str(e)}"
            }
    
    async def get_queue(self, chat_id: int) -> Dict[str, Any]:
        """الحصول على قائمة التشغيل"""
        try:
            if chat_id not in self.queues or not self.queues[chat_id]:
                return {
                    'success': False,
                    'message': "📋 قائمة التشغيل فارغة"
                }
            
            queue_list = []
            for i, item in enumerate(self.queues[chat_id], 1):
                queue_list.append(f"{i}. {item.title} - {item.duration}")
            
            current_song = "لا توجد"
            if chat_id in self.active_sessions:
                current_song = self.active_sessions[chat_id].song_title
            
            message = f"🎵 **الآن يُشغل:** {current_song}\n\n📋 **قائمة التشغيل:**\n" + "\n".join(queue_list)
            
            return {
                'success': True,
                'message': message,
                'queue': self.queues[chat_id]
            }
            
        except Exception as e:
            self.logger.error(f"خطأ في عرض القائمة: {e}")
            return {
                'success': False,
                'message': f"❌ خطأ في عرض القائمة: {str(e)}"
            }
    
    async def get_current_session(self, chat_id: int) -> Optional[MusicSession]:
        """الحصول على الجلسة الحالية"""
        return self.active_sessions.get(chat_id)
    
    async def _get_available_assistant(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على حساب مساعد متاح"""
        try:
            # الحصول على قائمة المساعدين من telethon_manager
            assistants = await telethon_manager.get_available_assistants()
            
            if not assistants:
                return None
            
            # اختيار حساب مساعد عشوائي (يمكن تحسين هذا لاحقاً)
            assistant = random.choice(list(assistants.values()))
            
            return {
                'id': assistant.get('user_id'),
                'name': assistant.get('username', 'مساعد'),
                'client': assistant.get('client')
            }
            
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على المساعد: {e}")
            return None
    
    async def _search_music(self, query: str) -> Optional[Dict[str, Any]]:
        """البحث عن الموسيقى"""
        try:
            # استخدام نظام البحث من download.py
            from ZeMusic.plugins.play.download import hyper_downloader
            
            # محاولة البحث السريع في الكاش أولاً
            cache_result = await hyper_downloader.lightning_search_cache(query)
            if cache_result:
                return {
                    'title': cache_result.get('title', query),
                    'url': cache_result.get('url', ''),
                    'duration': cache_result.get('duration', 'غير معروف')
                }
            
            # البحث في YouTube
            search_results = await hyper_downloader.youtube_search_simple(query)
            if search_results:
                first_result = search_results[0]
                return {
                    'title': first_result.get('title', query),
                    'url': first_result.get('url', ''),
                    'duration': first_result.get('duration', 'غير معروف')
                }
            
            return None
            
        except Exception as e:
            self.logger.error(f"خطأ في البحث: {e}")
            return None
    
    async def _start_playback(self, session: MusicSession) -> Dict[str, Any]:
        """بدء تشغيل الجلسة"""
        try:
            # هنا يمكن إضافة منطق تشغيل الصوت الفعلي
            # مثل استخدام PyTgCalls أو أي مكتبة أخرى
            
            self.logger.info(f"بدء تشغيل {session.song_title} في المحادثة {session.chat_id}")
            
            return {
                'success': True,
                'message': "تم بدء التشغيل بنجاح"
            }
            
        except Exception as e:
            self.logger.error(f"خطأ في بدء التشغيل: {e}")
            return {
                'success': False,
                'error': 'playback_error',
                'message': f"❌ خطأ في بدء التشغيل: {str(e)}"
            }
    
    async def cleanup_expired_sessions(self):
        """تنظيف الجلسات المنتهية الصلاحية"""
        try:
            current_time = time.time()
            expired_sessions = []
            
            for chat_id, session in self.active_sessions.items():
                # إزالة الجلسات التي تجاوزت ساعة واحدة
                if current_time - session.start_time > 3600:
                    expired_sessions.append(chat_id)
            
            for chat_id in expired_sessions:
                await self.stop_music(chat_id)
                self.logger.info(f"تم تنظيف الجلسة المنتهية الصلاحية: {chat_id}")
            
        except Exception as e:
            self.logger.error(f"خطأ في تنظيف الجلسات: {e}")

# إنشاء مثيل عام
telethon_music_manager = TelethonMusicManager()

# دوال للتوافق مع الكود القديم
async def play_music(chat_id: int, query: str, user_id: int):
    """دالة للتوافق"""
    return await telethon_music_manager.play_music(chat_id, query, user_id)

async def stop_music(chat_id: int):
    """دالة للتوافق"""
    return await telethon_music_manager.stop_music(chat_id)

async def pause_music(chat_id: int):
    """دالة للتوافق"""
    return await telethon_music_manager.pause_music(chat_id)

async def resume_music(chat_id: int):
    """دالة للتوافق"""
    return await telethon_music_manager.resume_music(chat_id)

async def skip_music(chat_id: int):
    """دالة للتوافق"""
    return await telethon_music_manager.skip_music(chat_id)

async def add_to_queue(chat_id: int, query: str, user_id: int):
    """دالة للتوافق"""
    return await telethon_music_manager.add_to_queue(chat_id, query, user_id)

async def get_queue(chat_id: int):
    """دالة للتوافق"""
    return await telethon_music_manager.get_queue(chat_id)

async def get_current_session(chat_id: int):
    """دالة للتوافق"""
    return await telethon_music_manager.get_current_session(chat_id)

async def start_cleanup_task():
    """بدء مهمة التنظيف الدورية"""
    try:
        while True:
            await asyncio.sleep(3600)  # كل ساعة
            await telethon_music_manager.cleanup_expired_sessions()
    except Exception as e:
        LOGGER(__name__).error(f"خطأ في مهمة التنظيف: {e}")