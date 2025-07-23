#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎵 ZeMusic Bot v3.0 - Enhanced Music Engine
تاريخ الإنشاء: 2025-01-28

محرك الموسيقى المتقدم مع دعم جميع المنصات والميزات
"""

import asyncio
import logging
import random
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
from dataclasses import dataclass
from pathlib import Path

try:
    from pytgcalls import PyTgCalls, StreamType
    from pytgcalls.types import Update, AudioPiped, VideoPiped
    from pytgcalls.exceptions import NoActiveGroupCall, GroupCallNotFound
    PYTGCALLS_AVAILABLE = True
except ImportError:
    # إنشاء فئات وهمية للتوافق
    class PyTgCalls:
        def __init__(self, client): pass
        async def start(self): pass
    
    class StreamType:
        pass
    
    class Update:
        pass
    
    class AudioPiped:
        pass
    
    class VideoPiped:
        pass
    
    class NoActiveGroupCall(Exception):
        pass
    
    class GroupCallNotFound(Exception):
        pass
    
    PYTGCALLS_AVAILABLE = False

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import config
from .database import db, PlayHistory
from .assistant_manager import assistant_manager

logger = logging.getLogger(__name__)

@dataclass
class TrackInfo:
    """معلومات المقطع الصوتي"""
    title: str
    url: str
    duration: int
    platform: str
    thumbnail: str = ""
    artist: str = ""
    requested_by: int = 0
    file_path: Optional[str] = None
    stream_url: Optional[str] = None
    lyrics: Optional[str] = None
    
@dataclass
class PlaySession:
    """جلسة التشغيل"""
    chat_id: int
    assistant_id: int
    current_track: Optional[TrackInfo] = None
    queue: List[TrackInfo] = None
    is_playing: bool = False
    is_paused: bool = False
    loop_mode: str = "off"  # off, track, queue
    shuffle_mode: bool = False
    volume: int = 100
    created_at: datetime = None
    last_activity: datetime = None
    
    def __post_init__(self):
        if self.queue is None:
            self.queue = []
        if self.created_at is None:
            self.created_at = datetime.now()
        if self.last_activity is None:
            self.last_activity = datetime.now()

class MusicEngine:
    """محرك الموسيقى المتقدم"""
    
    def __init__(self, client, assistant_manager):
        """تهيئة محرك الموسيقى"""
        self.client = client
        self.assistant_manager = assistant_manager
        
        # جلسات التشغيل النشطة
        self.active_sessions: Dict[int, PlaySession] = {}
        
        # مكالمات PyTgCalls
        self.pytgcalls_clients: Dict[int, PyTgCalls] = {}
        
        # إحصائيات
        self.total_plays = 0
        self.total_downloads = 0
        
        # مهام الصيانة
        self.cleanup_task = None
        self.stats_task = None
        
        # وضع محدود (بدون PyTgCalls)
        self.limited_mode = False
        
    async def initialize(self) -> bool:
        """تهيئة محرك الموسيقى"""
        try:
            logger.info("🎵 تهيئة محرك الموسيقى...")
            
            if not PYTGCALLS_AVAILABLE:
                logger.warning("⚠️ PyTgCalls غير متاح - سيعمل البوت في وضع محدود بدون تشغيل موسيقى")
                self.limited_mode = True
                return True
            
            # تهيئة PyTgCalls للحسابات المساعدة
            await self._initialize_pytgcalls()
            
            # بدء مهام الصيانة
            self._start_maintenance_tasks()
            
            logger.info("✅ تم تهيئة محرك الموسيقى بنجاح")
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في تهيئة محرك الموسيقى: {e}")
            return False
    
    async def _initialize_pytgcalls(self):
        """تهيئة PyTgCalls للحسابات المساعدة"""
        try:
            for assistant_id, assistant in self.assistant_manager.assistants.items():
                if assistant.is_connected and assistant.is_authorized:
                    pytgcalls = PyTgCalls(assistant.client)
                    await pytgcalls.start()
                    self.pytgcalls_clients[assistant_id] = pytgcalls
                    logger.info(f"✅ تم تهيئة PyTgCalls للحساب {assistant_id}")
                    
        except Exception as e:
            logger.error(f"❌ فشل في تهيئة PyTgCalls: {e}")
    
    def _start_maintenance_tasks(self):
        """بدء مهام الصيانة"""
        # تنظيف الجلسات غير النشطة
        self.cleanup_task = asyncio.create_task(self._cleanup_inactive_sessions())
        
        # تحديث الإحصائيات
        self.stats_task = asyncio.create_task(self._update_stats())
        
        logger.info("📊 تم بدء مهام صيانة محرك الموسيقى")
    
    async def play_track(self, chat_id: int, track: TrackInfo, user_id: int = 0) -> Dict[str, Any]:
        """تشغيل مقطع صوتي"""
        try:
            # الحصول على حساب مساعد
            assistant = await self.assistant_manager.get_best_assistant(chat_id)
            if not assistant:
                return {
                    'success': False,
                    'message': 'لا توجد حسابات مساعدة متاحة'
                }
            
            # إنشاء أو تحديث جلسة التشغيل
            if chat_id not in self.active_sessions:
                self.active_sessions[chat_id] = PlaySession(
                    chat_id=chat_id,
                    assistant_id=assistant.assistant_id
                )
            
            session = self.active_sessions[chat_id]
            
            # إضافة المقطع لقائمة الانتظار أو التشغيل المباشر
            if session.is_playing:
                session.queue.append(track)
                position = len(session.queue)
                
                return {
                    'success': True,
                    'message': f'تم إضافة المقطع لقائمة الانتظار في الموضع {position}',
                    'queue_position': position
                }
            else:
                # تشغيل مباشر
                result = await self._start_playback(session, track)
                
                if result['success']:
                    # تسجيل في قاعدة البيانات
                    await self._log_play_history(chat_id, user_id, track)
                    
                    # تحديث إحصائيات الحساب المساعد
                    assistant.active_calls += 1
                    await db.update_assistant_status(
                        assistant.assistant_id, 
                        assistant.is_connected, 
                        assistant.active_calls
                    )
                
                return result
                
        except Exception as e:
            logger.error(f"❌ فشل في تشغيل المقطع: {e}")
            return {
                'success': False,
                'message': f'خطأ في التشغيل: {str(e)}'
            }
    
    async def _start_playback(self, session: PlaySession, track: TrackInfo) -> Dict[str, Any]:
        """بدء التشغيل الفعلي"""
        try:
            # الحصول على PyTgCalls client
            if session.assistant_id not in self.pytgcalls_clients:
                return {
                    'success': False,
                    'message': 'عميل PyTgCalls غير متاح'
                }
            
            pytgcalls = self.pytgcalls_clients[session.assistant_id]
            
            # تحضير الستريم
            if track.file_path:
                # ملف محلي
                stream = AudioPiped(track.file_path)
            elif track.stream_url:
                # رابط مباشر
                stream = AudioPiped(track.stream_url)
            else:
                return {
                    'success': False,
                    'message': 'لا يوجد مصدر صوتي صالح'
                }
            
            # بدء التشغيل
            await pytgcalls.join_group_call(
                session.chat_id,
                stream,
                stream_type=StreamType().local_stream
            )
            
            # تحديث حالة الجلسة
            session.current_track = track
            session.is_playing = True
            session.is_paused = False
            session.last_activity = datetime.now()
            
            self.total_plays += 1
            
            return {
                'success': True,
                'message': f'🎵 يتم الآن تشغيل: {track.title}'
            }
            
        except NoActiveGroupCall:
            return {
                'success': False,
                'message': 'يجب بدء مكالمة صوتية في المجموعة أولاً'
            }
        except Exception as e:
            logger.error(f"❌ فشل في بدء التشغيل: {e}")
            return {
                'success': False,
                'message': f'خطأ في بدء التشغيل: {str(e)}'
            }
    
    async def pause_playback(self, chat_id: int) -> Dict[str, Any]:
        """إيقاف التشغيل مؤقتاً"""
        try:
            if chat_id not in self.active_sessions:
                return {
                    'success': False,
                    'message': 'لا يوجد تشغيل نشط'
                }
            
            session = self.active_sessions[chat_id]
            
            if not session.is_playing:
                return {
                    'success': False,
                    'message': 'لا يوجد تشغيل نشط'
                }
            
            if session.is_paused:
                return {
                    'success': False,
                    'message': 'التشغيل متوقف مسبقاً'
                }
            
            # إيقاف مؤقت
            pytgcalls = self.pytgcalls_clients[session.assistant_id]
            await pytgcalls.pause_stream(chat_id)
            
            session.is_paused = True
            session.last_activity = datetime.now()
            
            return {
                'success': True,
                'message': '⏸️ تم إيقاف التشغيل مؤقتاً'
            }
            
        except Exception as e:
            logger.error(f"❌ فشل في إيقاف التشغيل: {e}")
            return {
                'success': False,
                'message': f'خطأ في إيقاف التشغيل: {str(e)}'
            }
    
    async def resume_playback(self, chat_id: int) -> Dict[str, Any]:
        """استئناف التشغيل"""
        try:
            if chat_id not in self.active_sessions:
                return {
                    'success': False,
                    'message': 'لا يوجد تشغيل نشط'
                }
            
            session = self.active_sessions[chat_id]
            
            if not session.is_paused:
                return {
                    'success': False,
                    'message': 'التشغيل غير متوقف'
                }
            
            # استئناف التشغيل
            pytgcalls = self.pytgcalls_clients[session.assistant_id]
            await pytgcalls.resume_stream(chat_id)
            
            session.is_paused = False
            session.last_activity = datetime.now()
            
            return {
                'success': True,
                'message': '▶️ تم استئناف التشغيل'
            }
            
        except Exception as e:
            logger.error(f"❌ فشل في استئناف التشغيل: {e}")
            return {
                'success': False,
                'message': f'خطأ في استئناف التشغيل: {str(e)}'
            }
    
    async def skip_track(self, chat_id: int) -> Dict[str, Any]:
        """تخطي المقطع الحالي"""
        try:
            if chat_id not in self.active_sessions:
                return {
                    'success': False,
                    'message': 'لا يوجد تشغيل نشط'
                }
            
            session = self.active_sessions[chat_id]
            
            if not session.is_playing:
                return {
                    'success': False,
                    'message': 'لا يوجد تشغيل نشط'
                }
            
            # التحقق من وجود مقاطع في قائمة الانتظار
            if not session.queue:
                # إيقاف التشغيل
                await self.stop_playback(chat_id)
                return {
                    'success': True,
                    'message': '⏹️ لا توجد مقاطع أخرى - تم إيقاف التشغيل'
                }
            
            # تشغيل المقطع التالي
            next_track = session.queue.pop(0)
            result = await self._start_playback(session, next_track)
            
            if result['success']:
                return {
                    'success': True,
                    'message': f'⏭️ تم التخطي - يتم الآن تشغيل: {next_track.title}'
                }
            else:
                return result
                
        except Exception as e:
            logger.error(f"❌ فشل في تخطي المقطع: {e}")
            return {
                'success': False,
                'message': f'خطأ في التخطي: {str(e)}'
            }
    
    async def stop_playback(self, chat_id: int) -> Dict[str, Any]:
        """إيقاف التشغيل نهائياً"""
        try:
            if chat_id not in self.active_sessions:
                return {
                    'success': False,
                    'message': 'لا يوجد تشغيل نشط'
                }
            
            session = self.active_sessions[chat_id]
            
            # إيقاف PyTgCalls
            pytgcalls = self.pytgcalls_clients[session.assistant_id]
            await pytgcalls.leave_group_call(chat_id)
            
            # تحديث إحصائيات الحساب المساعد
            assistant = self.assistant_manager.assistants[session.assistant_id]
            assistant.active_calls = max(0, assistant.active_calls - 1)
            await db.update_assistant_status(
                assistant.assistant_id,
                assistant.is_connected,
                assistant.active_calls
            )
            
            # حذف الجلسة
            del self.active_sessions[chat_id]
            
            return {
                'success': True,
                'message': '⏹️ تم إيقاف التشغيل'
            }
            
        except Exception as e:
            logger.error(f"❌ فشل في إيقاف التشغيل: {e}")
            return {
                'success': False,
                'message': f'خطأ في إيقاف التشغيل: {str(e)}'
            }
    
    async def set_loop_mode(self, chat_id: int, mode: str) -> Dict[str, Any]:
        """تعيين نمط التكرار"""
        try:
            if chat_id not in self.active_sessions:
                return {
                    'success': False,
                    'message': 'لا يوجد تشغيل نشط'
                }
            
            if mode not in ['off', 'track', 'queue']:
                return {
                    'success': False,
                    'message': 'نمط التكرار غير صحيح'
                }
            
            session = self.active_sessions[chat_id]
            session.loop_mode = mode
            session.last_activity = datetime.now()
            
            mode_text = {
                'off': 'إيقاف التكرار',
                'track': 'تكرار المقطع الحالي',
                'queue': 'تكرار قائمة الانتظار'
            }
            
            return {
                'success': True,
                'message': f'🔁 تم تعيين نمط التكرار: {mode_text[mode]}'
            }
            
        except Exception as e:
            logger.error(f"❌ فشل في تعيين نمط التكرار: {e}")
            return {
                'success': False,
                'message': f'خطأ في تعيين التكرار: {str(e)}'
            }
    
    async def toggle_shuffle(self, chat_id: int) -> Dict[str, Any]:
        """تبديل نمط الخلط"""
        try:
            if chat_id not in self.active_sessions:
                return {
                    'success': False,
                    'message': 'لا يوجد تشغيل نشط'
                }
            
            session = self.active_sessions[chat_id]
            session.shuffle_mode = not session.shuffle_mode
            session.last_activity = datetime.now()
            
            if session.shuffle_mode and session.queue:
                # خلط قائمة الانتظار
                random.shuffle(session.queue)
            
            status = 'تم تفعيل' if session.shuffle_mode else 'تم إلغاء'
            
            return {
                'success': True,
                'message': f'🔀 {status} نمط الخلط'
            }
            
        except Exception as e:
            logger.error(f"❌ فشل في تبديل الخلط: {e}")
            return {
                'success': False,
                'message': f'خطأ في تبديل الخلط: {str(e)}'
            }
    
    async def get_queue(self, chat_id: int) -> Dict[str, Any]:
        """الحصول على قائمة الانتظار"""
        try:
            if chat_id not in self.active_sessions:
                return {
                    'success': False,
                    'message': 'لا يوجد تشغيل نشط'
                }
            
            session = self.active_sessions[chat_id]
            
            queue_info = {
                'current_track': session.current_track.__dict__ if session.current_track else None,
                'queue': [track.__dict__ for track in session.queue],
                'queue_length': len(session.queue),
                'is_playing': session.is_playing,
                'is_paused': session.is_paused,
                'loop_mode': session.loop_mode,
                'shuffle_mode': session.shuffle_mode,
                'volume': session.volume
            }
            
            return {
                'success': True,
                'queue_info': queue_info
            }
            
        except Exception as e:
            logger.error(f"❌ فشل في جلب قائمة الانتظار: {e}")
            return {
                'success': False,
                'message': f'خطأ في جلب القائمة: {str(e)}'
            }
    
    async def clear_queue(self, chat_id: int) -> Dict[str, Any]:
        """مسح قائمة الانتظار"""
        try:
            if chat_id not in self.active_sessions:
                return {
                    'success': False,
                    'message': 'لا يوجد تشغيل نشط'
                }
            
            session = self.active_sessions[chat_id]
            cleared_count = len(session.queue)
            session.queue.clear()
            session.last_activity = datetime.now()
            
            return {
                'success': True,
                'message': f'🗑️ تم مسح {cleared_count} مقطع من قائمة الانتظار'
            }
            
        except Exception as e:
            logger.error(f"❌ فشل في مسح قائمة الانتظار: {e}")
            return {
                'success': False,
                'message': f'خطأ في مسح القائمة: {str(e)}'
            }
    
    async def _log_play_history(self, chat_id: int, user_id: int, track: TrackInfo):
        """تسجيل سجل التشغيل"""
        try:
            history = PlayHistory(
                chat_id=chat_id,
                user_id=user_id,
                title=track.title,
                url=track.url,
                duration=track.duration,
                platform=track.platform
            )
            
            # حفظ في قاعدة البيانات (سيتم تنفيذ هذا في database.py)
            # await db.add_play_history(history)
            
        except Exception as e:
            logger.error(f"❌ فشل في تسجيل سجل التشغيل: {e}")
    
    async def get_statistics(self) -> Dict[str, Any]:
        """الحصول على إحصائيات محرك الموسيقى"""
        try:
            active_sessions_count = len(self.active_sessions)
            total_queue_size = sum(len(session.queue) for session in self.active_sessions.values())
            
            # إحصائيات PyTgCalls
            connected_calls = len(self.pytgcalls_clients)
            
            return {
                'active_sessions': active_sessions_count,
                'total_queue_size': total_queue_size,
                'connected_calls': connected_calls,
                'total_plays': self.total_plays,
                'total_downloads': self.total_downloads,
                'sessions_info': [
                    {
                        'chat_id': session.chat_id,
                        'assistant_id': session.assistant_id,
                        'current_track': session.current_track.title if session.current_track else None,
                        'queue_length': len(session.queue),
                        'is_playing': session.is_playing,
                        'is_paused': session.is_paused,
                        'created_at': session.created_at.isoformat(),
                        'last_activity': session.last_activity.isoformat()
                    }
                    for session in self.active_sessions.values()
                ]
            }
            
        except Exception as e:
            logger.error(f"❌ فشل في جلب الإحصائيات: {e}")
            return {}
    
    async def _cleanup_inactive_sessions(self):
        """تنظيف الجلسات غير النشطة"""
        while True:
            try:
                await asyncio.sleep(300)  # كل 5 دقائق
                
                current_time = datetime.now()
                inactive_sessions = []
                
                for chat_id, session in self.active_sessions.items():
                    # إذا لم يكن هناك نشاط لأكثر من 30 دقيقة
                    if current_time - session.last_activity > timedelta(minutes=30):
                        inactive_sessions.append(chat_id)
                
                # إيقاف الجلسات غير النشطة
                for chat_id in inactive_sessions:
                    await self.stop_playback(chat_id)
                    logger.info(f"🧹 تم تنظيف الجلسة غير النشطة: {chat_id}")
                
            except Exception as e:
                logger.error(f"❌ خطأ في تنظيف الجلسات: {e}")
    
    async def _update_stats(self):
        """تحديث الإحصائيات"""
        while True:
            try:
                await asyncio.sleep(60)  # كل دقيقة
                
                # تحديث إحصائيات قاعدة البيانات
                stats = await self.get_statistics()
                # حفظ في قاعدة البيانات إذا لزم الأمر
                
            except Exception as e:
                logger.error(f"❌ خطأ في تحديث الإحصائيات: {e}")
    
    async def shutdown(self):
        """إيقاف محرك الموسيقى"""
        try:
            logger.info("🛑 إيقاف محرك الموسيقى...")
            
            # إيقاف مهام الصيانة
            if self.cleanup_task:
                self.cleanup_task.cancel()
            
            if self.stats_task:
                self.stats_task.cancel()
            
            # إيقاف جميع الجلسات النشطة
            for chat_id in list(self.active_sessions.keys()):
                await self.stop_playback(chat_id)
            
            # إيقاف PyTgCalls clients
            for pytgcalls in self.pytgcalls_clients.values():
                try:
                    await pytgcalls.stop()
                except:
                    pass
            
            self.pytgcalls_clients.clear()
            
            logger.info("✅ تم إيقاف محرك الموسيقى")
            
        except Exception as e:
            logger.error(f"❌ خطأ في إيقاف محرك الموسيقى: {e}")

# إنشاء مثيل عام لمحرك الموسيقى
music_engine = None  # سيتم تهيئته في الملف الرئيسي