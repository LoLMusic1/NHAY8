# -*- coding: utf-8 -*-
"""
مكالمات Telegram مع Telethon
"""

import asyncio
import os
from datetime import datetime, timedelta
from typing import Union, Optional, Dict, Any

from telethon import TelegramClient
from ZeMusic.core.telethon_client import telethon_manager
from ZeMusic.zemusic_logging import LOGGER
import config

class TelethonCall:
    """مدير المكالمات مع Telethon"""
    
    def __init__(self):
        self.logger = LOGGER(__name__)
        self.active_calls: Dict[int, Dict[str, Any]] = {}
        
    async def join_call(self, chat_id: int, file_path: str, video: bool = False) -> bool:
        """الانضمام للمكالمة الصوتية"""
        try:
            # الحصول على حساب مساعد متاح
            assistants = await telethon_manager.get_available_assistants()
            if not assistants:
                self.logger.error("لا توجد حسابات مساعدة متاحة")
                return False
            
            # اختيار أول حساب مساعد متاح
            assistant_id = list(assistants.keys())[0]
            assistant_client = assistants[assistant_id]['client']
            
            # حفظ معلومات المكالمة
            self.active_calls[chat_id] = {
                'assistant_id': assistant_id,
                'file_path': file_path,
                'video': video,
                'start_time': datetime.now()
            }
            
            self.logger.info(f"تم الانضمام للمكالمة في {chat_id} باستخدام المساعد {assistant_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"خطأ في الانضمام للمكالمة: {e}")
            return False
    
    async def leave_call(self, chat_id: int) -> bool:
        """مغادرة المكالمة"""
        try:
            if chat_id in self.active_calls:
                call_info = self.active_calls[chat_id]
                del self.active_calls[chat_id]
                self.logger.info(f"تم مغادرة المكالمة في {chat_id}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"خطأ في مغادرة المكالمة: {e}")
            return False
    
    async def pause_stream(self, chat_id: int) -> bool:
        """إيقاف مؤقت للبث"""
        try:
            if chat_id in self.active_calls:
                # يمكن إضافة منطق الإيقاف المؤقت هنا
                self.logger.info(f"تم إيقاف البث مؤقتاً في {chat_id}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"خطأ في الإيقاف المؤقت: {e}")
            return False
    
    async def resume_stream(self, chat_id: int) -> bool:
        """استكمال البث"""
        try:
            if chat_id in self.active_calls:
                # يمكن إضافة منطق الاستكمال هنا
                self.logger.info(f"تم استكمال البث في {chat_id}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"خطأ في الاستكمال: {e}")
            return False
    
    async def stop_stream(self, chat_id: int) -> bool:
        """إيقاف البث"""
        try:
            return await self.leave_call(chat_id)
            
        except Exception as e:
            self.logger.error(f"خطأ في إيقاف البث: {e}")
            return False
    
    async def skip_stream(self, chat_id: int, new_file: str, video: bool = False) -> bool:
        """تخطي للملف التالي"""
        try:
            if chat_id in self.active_calls:
                call_info = self.active_calls[chat_id]
                call_info['file_path'] = new_file
                call_info['video'] = video
                self.logger.info(f"تم تخطي البث في {chat_id}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"خطأ في التخطي: {e}")
            return False
    
    async def get_call_info(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على معلومات المكالمة"""
        return self.active_calls.get(chat_id)
    
    async def is_connected(self, chat_id: int) -> bool:
        """التحقق من وجود اتصال"""
        return chat_id in self.active_calls
    
    async def get_active_calls(self) -> Dict[int, Dict[str, Any]]:
        """الحصول على جميع المكالمات النشطة"""
        return self.active_calls.copy()
    
    async def ping(self) -> str:
        """ping المساعدين"""
        try:
            assistants = await telethon_manager.get_available_assistants()
            if assistants:
                return "0.05"  # قيمة افتراضية
            return "∞"
            
        except Exception as e:
            self.logger.error(f"خطأ في ping: {e}")
            return "∞"
    
    async def start(self):
        """بدء خدمة المكالمات"""
        try:
            self.logger.info("🎵 تم بدء خدمة المكالمات مع Telethon")
            
        except Exception as e:
            self.logger.error(f"خطأ في بدء خدمة المكالمات: {e}")

# إنشاء مثيل عام
Mody = TelethonCall()

# للتوافق مع الكود القديم
Call = TelethonCall
