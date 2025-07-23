#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔥 Telethon Client Manager - ZeMusic Bot v3.0
تاريخ الإنشاء: 2025-01-28

مدير عملاء Telethon المتقدم للبوت والحسابات المساعدة
"""

import asyncio
import logging
import os
import json
import time
from typing import Dict, List, Optional, Any, Union
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import (
    SessionPasswordNeededError, 
    PhoneCodeInvalidError,
    PhoneNumberInvalidError,
    FloodWaitError,
    AuthKeyUnregisteredError,
    UserDeactivatedError,
    UserDeactivatedBanError,
    PhoneNumberBannedError
)
from telethon.tl.types import User, Chat, Channel

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import config

logger = logging.getLogger(__name__)

class TelethonClient:
    """عميل Telethon محسن مع إدارة متقدمة للجلسات"""
    
    def __init__(self, session_name: str, is_bot: bool = False):
        """تهيئة عميل Telethon"""
        self.session_name = session_name
        self.is_bot = is_bot
        self.client: Optional[TelegramClient] = None
        self.is_connected = False
        self.user_info: Optional[User] = None
        
        # إحصائيات الاستخدام
        self.stats = {
            'messages_sent': 0,
            'messages_received': 0,
            'calls_joined': 0,
            'errors_count': 0,
            'uptime_start': time.time()
        }
        
    async def initialize(self, bot_token: Optional[str] = None, 
                        phone: Optional[str] = None, 
                        session_string: Optional[str] = None) -> bool:
        """تهيئة العميل"""
        try:
            logger.info(f"🔄 تهيئة عميل Telethon: {self.session_name}")
            
            # تحديد نوع الجلسة
            if session_string:
                session = StringSession(session_string)
            else:
                session_dir = "sessions"
                os.makedirs(session_dir, exist_ok=True)
                session = os.path.join(session_dir, f"{self.session_name}.session")
            
            # إنشاء العميل
            self.client = TelegramClient(
                session=session,
                api_id=config.telegram.api_id,
                api_hash=config.telegram.api_hash,
                device_model=config.telegram.device_model,
                system_version=config.telegram.system_version,
                app_version=config.telegram.app_version,
                lang_code="ar",
                system_lang_code="ar",
                timeout=30,
                retry_delay=1,
                retries=3
            )
            
            # بدء الاتصال
            await self.client.connect()
            
            # تسجيل الدخول
            if self.is_bot and bot_token:
                await self.client.start(bot_token=bot_token)
            elif phone:
                await self.client.start(phone=phone)
            else:
                if not await self.client.is_user_authorized():
                    logger.error(f"❌ العميل {self.session_name} غير مصرح له")
                    return False
            
            # الحصول على معلومات المستخدم
            self.user_info = await self.client.get_me()
            self.is_connected = True
            
            # إعداد معالجات الأحداث الأساسية
            await self._setup_event_handlers()
            
            logger.info(f"✅ تم تهيئة العميل بنجاح: {self.user_info.first_name} (@{getattr(self.user_info, 'username', 'بدون يوزر')})")
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في تهيئة العميل {self.session_name}: {e}")
            return False
    
    async def _setup_event_handlers(self):
        """إعداد معالجات الأحداث الأساسية"""
        try:
            @self.client.on(events.NewMessage)
            async def message_handler(event):
                self.stats['messages_received'] += 1
            
            logger.info(f"📝 تم إعداد معالجات الأحداث للعميل {self.session_name}")
            
        except Exception as e:
            logger.error(f"❌ خطأ في إعداد معالجات الأحداث: {e}")
    
    async def send_message(self, entity: Union[int, str], message: str, **kwargs) -> bool:
        """إرسال رسالة"""
        try:
            if not self.is_connected:
                return False
            
            await self.client.send_message(entity, message, **kwargs)
            self.stats['messages_sent'] += 1
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في إرسال الرسالة: {e}")
            self.stats['errors_count'] += 1
            return False
    
    async def get_entity(self, entity: Union[int, str]):
        """الحصول على كيان"""
        try:
            if not self.is_connected:
                return None
            
            return await self.client.get_entity(entity)
            
        except Exception as e:
            logger.error(f"❌ خطأ في جلب الكيان: {e}")
            return None
    
    async def disconnect(self):
        """قطع الاتصال"""
        try:
            if self.client and self.is_connected:
                await self.client.disconnect()
                self.is_connected = False
                logger.info(f"🔌 تم قطع اتصال العميل {self.session_name}")
                
        except Exception as e:
            logger.error(f"❌ خطأ في قطع الاتصال: {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات العميل"""
        uptime = time.time() - self.stats['uptime_start']
        return {
            **self.stats,
            'uptime_seconds': uptime,
            'is_connected': self.is_connected,
            'user_info': {
                'id': self.user_info.id if self.user_info else None,
                'name': self.user_info.first_name if self.user_info else None,
                'username': getattr(self.user_info, 'username', None) if self.user_info else None
            }
        }

class TelethonClientManager:
    """إدارة عملاء Telethon للبوت والحسابات المساعدة"""
    
    def __init__(self):
        """تهيئة مدير العملاء"""
        self.bot_client: Optional[TelethonClient] = None
        self.assistant_clients: Dict[int, TelethonClient] = {}
        self.session_data: Dict[str, Dict[str, Any]] = {}
        
        # إعدادات الإدارة
        self.max_assistants = getattr(config, 'MAX_ASSISTANTS', 10)
        self.assistant_rotation = True
        self.health_check_interval = 300  # 5 دقائق
        
        # إحصائيات النظام
        self.system_stats = {
            'total_clients': 0,
            'active_clients': 0,
            'failed_clients': 0,
            'last_health_check': 0
        }
        
    async def initialize(self) -> bool:
        """تهيئة جميع العملاء"""
        try:
            logger.info("🚀 بدء تهيئة مدير عملاء Telethon...")
            
            # تهيئة البوت الرئيسي
            bot_success = await self._initialize_bot()
            if not bot_success:
                logger.error("❌ فشل في تهيئة البوت الرئيسي")
                return False
            
            # تهيئة الحسابات المساعدة
            assistants_success = await self._initialize_assistants()
            
            # بدء مهام الصيانة
            asyncio.create_task(self._health_check_loop())
            asyncio.create_task(self._statistics_updater())
            
            logger.info(f"✅ تم تهيئة مدير العملاء - البوت: {'✅' if bot_success else '❌'}, المساعدين: {len(self.assistant_clients)}")
            return bot_success
            
        except Exception as e:
            logger.error(f"❌ فشل في تهيئة مدير العملاء: {e}")
            return False
    
    async def _initialize_bot(self) -> bool:
        """تهيئة البوت الرئيسي"""
        try:
            self.bot_client = TelethonClient("main_bot", is_bot=True)
            success = await self.bot_client.initialize(bot_token=config.telegram.bot_token)
            
            if success:
                self.system_stats['total_clients'] += 1
                self.system_stats['active_clients'] += 1
            else:
                self.system_stats['failed_clients'] += 1
            
            return success
            
        except Exception as e:
            logger.error(f"❌ خطأ في تهيئة البوت: {e}")
            return False
    
    async def _initialize_assistants(self) -> bool:
        """تهيئة الحسابات المساعدة"""
        try:
            logger.info("👥 تهيئة الحسابات المساعدة...")
            
            # تحميل بيانات الجلسات
            await self._load_session_data()
            
            success_count = 0
            for i, session_info in enumerate(self.session_data.values(), 1):
                if i > self.max_assistants:
                    break
                
                try:
                    assistant = TelethonClient(f"assistant_{i}")
                    success = await assistant.initialize(
                        session_string=session_info.get('session_string'),
                        phone=session_info.get('phone')
                    )
                    
                    if success:
                        self.assistant_clients[i] = assistant
                        success_count += 1
                        self.system_stats['active_clients'] += 1
                    else:
                        self.system_stats['failed_clients'] += 1
                    
                    self.system_stats['total_clients'] += 1
                    
                except Exception as e:
                    logger.error(f"❌ فشل في تهيئة المساعد {i}: {e}")
                    self.system_stats['failed_clients'] += 1
            
            logger.info(f"✅ تم تهيئة {success_count} حساب مساعد من أصل {len(self.session_data)}")
            return success_count > 0
            
        except Exception as e:
            logger.error(f"❌ خطأ في تهيئة المساعدين: {e}")
            return False
    
    async def _load_session_data(self):
        """تحميل بيانات الجلسات"""
        try:
            sessions_file = "sessions_data.json"
            
            if os.path.exists(sessions_file):
                with open(sessions_file, 'r', encoding='utf-8') as f:
                    self.session_data = json.load(f)
            else:
                # إنشاء ملف جلسات فارغ
                self.session_data = {}
                await self._save_session_data()
            
            logger.info(f"📚 تم تحميل {len(self.session_data)} جلسة")
            
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل بيانات الجلسات: {e}")
            self.session_data = {}
    
    async def _save_session_data(self):
        """حفظ بيانات الجلسات"""
        try:
            sessions_file = "sessions_data.json"
            with open(sessions_file, 'w', encoding='utf-8') as f:
                json.dump(self.session_data, f, indent=2, ensure_ascii=False)
                
        except Exception as e:
            logger.error(f"❌ خطأ في حفظ بيانات الجلسات: {e}")
    
    async def add_assistant(self, phone: str, session_string: str, name: str = "") -> Dict[str, Any]:
        """إضافة حساب مساعد جديد"""
        try:
            if len(self.assistant_clients) >= self.max_assistants:
                return {
                    'success': False,
                    'error': 'max_limit',
                    'message': f"تم الوصول للحد الأقصى من المساعدين ({self.max_assistants})"
                }
            
            # تحديد معرف المساعد الجديد
            assistant_id = max(self.assistant_clients.keys(), default=0) + 1
            
            # إنشاء العميل
            assistant = TelethonClient(f"assistant_{assistant_id}")
            success = await assistant.initialize(session_string=session_string, phone=phone)
            
            if success:
                self.assistant_clients[assistant_id] = assistant
                
                # حفظ بيانات الجلسة
                self.session_data[str(assistant_id)] = {
                    'phone': phone,
                    'session_string': session_string,
                    'name': name or f"مساعد {assistant_id}",
                    'added_date': time.time(),
                    'is_active': True
                }
                await self._save_session_data()
                
                self.system_stats['total_clients'] += 1
                self.system_stats['active_clients'] += 1
                
                return {
                    'success': True,
                    'assistant_id': assistant_id,
                    'message': f"✅ تم إضافة المساعد {assistant_id} بنجاح"
                }
            else:
                return {
                    'success': False,
                    'error': 'initialization_failed',
                    'message': "❌ فشل في تهيئة الحساب المساعد"
                }
                
        except Exception as e:
            logger.error(f"❌ خطأ في إضافة المساعد: {e}")
            return {
                'success': False,
                'error': 'general_error',
                'message': f"❌ خطأ: {str(e)}"
            }
    
    async def remove_assistant(self, assistant_id: int) -> Dict[str, Any]:
        """إزالة حساب مساعد"""
        try:
            if assistant_id not in self.assistant_clients:
                return {
                    'success': False,
                    'error': 'not_found',
                    'message': f"❌ المساعد {assistant_id} غير موجود"
                }
            
            # قطع الاتصال وإزالة العميل
            assistant = self.assistant_clients[assistant_id]
            await assistant.disconnect()
            del self.assistant_clients[assistant_id]
            
            # إزالة بيانات الجلسة
            if str(assistant_id) in self.session_data:
                del self.session_data[str(assistant_id)]
                await self._save_session_data()
            
            self.system_stats['active_clients'] -= 1
            
            return {
                'success': True,
                'message': f"✅ تم إزالة المساعد {assistant_id} بنجاح"
            }
            
        except Exception as e:
            logger.error(f"❌ خطأ في إزالة المساعد: {e}")
            return {
                'success': False,
                'error': 'general_error',
                'message': f"❌ خطأ: {str(e)}"
            }
    
    async def get_available_assistant(self) -> Optional[TelethonClient]:
        """الحصول على حساب مساعد متاح"""
        try:
            if not self.assistant_clients:
                return None
            
            # البحث عن مساعد متصل
            for assistant in self.assistant_clients.values():
                if assistant.is_connected:
                    return assistant
            
            return None
            
        except Exception as e:
            logger.error(f"❌ خطأ في الحصول على مساعد متاح: {e}")
            return None
    
    async def get_assistant_by_id(self, assistant_id: int) -> Optional[TelethonClient]:
        """الحصول على مساعد محدد بالمعرف"""
        return self.assistant_clients.get(assistant_id)
    
    async def get_all_assistants(self) -> Dict[int, TelethonClient]:
        """الحصول على جميع المساعدين"""
        return self.assistant_clients.copy()
    
    async def _health_check_loop(self):
        """حلقة فحص صحة العملاء"""
        while True:
            try:
                await asyncio.sleep(self.health_check_interval)
                await self._perform_health_check()
                
            except Exception as e:
                logger.error(f"❌ خطأ في فحص الصحة: {e}")
    
    async def _perform_health_check(self):
        """فحص صحة جميع العملاء"""
        try:
            self.system_stats['last_health_check'] = time.time()
            
            # فحص البوت الرئيسي
            if self.bot_client and not self.bot_client.is_connected:
                logger.warning("⚠️ البوت الرئيسي غير متصل - محاولة إعادة الاتصال...")
                await self._reconnect_client(self.bot_client)
            
            # فحص المساعدين
            disconnected_assistants = []
            for assistant_id, assistant in self.assistant_clients.items():
                if not assistant.is_connected:
                    disconnected_assistants.append(assistant_id)
            
            # إعادة اتصال المساعدين المنقطعين
            for assistant_id in disconnected_assistants:
                logger.warning(f"⚠️ المساعد {assistant_id} غير متصل - محاولة إعادة الاتصال...")
                assistant = self.assistant_clients[assistant_id]
                await self._reconnect_client(assistant)
            
            # تحديث الإحصائيات
            active_count = sum(1 for client in [self.bot_client] + list(self.assistant_clients.values()) 
                             if client and client.is_connected)
            self.system_stats['active_clients'] = active_count
            
            logger.info(f"🔍 فحص الصحة مكتمل - العملاء النشطين: {active_count}")
            
        except Exception as e:
            logger.error(f"❌ خطأ في فحص الصحة: {e}")
    
    async def _reconnect_client(self, client: TelethonClient) -> bool:
        """إعادة اتصال عميل"""
        try:
            if client.client:
                await client.client.connect()
                client.is_connected = True
                return True
            return False
            
        except Exception as e:
            logger.error(f"❌ فشل في إعادة الاتصال: {e}")
            return False
    
    async def _statistics_updater(self):
        """محدث الإحصائيات"""
        while True:
            try:
                await asyncio.sleep(60)  # كل دقيقة
                
                # تحديث إحصائيات العملاء
                for client in [self.bot_client] + list(self.assistant_clients.values()):
                    if client:
                        stats = client.get_stats()
                        # يمكن حفظ الإحصائيات في قاعدة البيانات هنا
                
            except Exception as e:
                logger.error(f"❌ خطأ في تحديث الإحصائيات: {e}")
    
    async def get_system_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات النظام"""
        try:
            bot_stats = self.bot_client.get_stats() if self.bot_client else {}
            assistant_stats = {}
            
            for assistant_id, assistant in self.assistant_clients.items():
                assistant_stats[assistant_id] = assistant.get_stats()
            
            return {
                'system': self.system_stats,
                'bot': bot_stats,
                'assistants': assistant_stats,
                'summary': {
                    'total_clients': len(self.assistant_clients) + (1 if self.bot_client else 0),
                    'active_clients': sum(1 for c in [self.bot_client] + list(self.assistant_clients.values()) 
                                        if c and c.is_connected),
                    'assistant_count': len(self.assistant_clients),
                    'last_health_check': self.system_stats['last_health_check']
                }
            }
            
        except Exception as e:
            logger.error(f"❌ خطأ في جلب إحصائيات النظام: {e}")
            return {}
    
    async def shutdown(self):
        """إغلاق جميع العملاء"""
        try:
            logger.info("🔌 إغلاق جميع عملاء Telethon...")
            
            # إغلاق البوت الرئيسي
            if self.bot_client:
                await self.bot_client.disconnect()
            
            # إغلاق جميع المساعدين
            for assistant in self.assistant_clients.values():
                await assistant.disconnect()
            
            logger.info("✅ تم إغلاق جميع العملاء بنجاح")
            
        except Exception as e:
            logger.error(f"❌ خطأ في الإغلاق: {e}")

# إنشاء مثيل عام لمدير العملاء
telethon_manager = TelethonClientManager()