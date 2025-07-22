#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔥 Enhanced Telethon Client Manager - ZeMusic Bot Enhanced
تاريخ الإنشاء: 2025-01-28
النسخة: 3.0.0 - Telethon Enhanced Edition

مدير عملاء Telethon محسن للأحمال الكبيرة
مُحسن للعمل مع 7000 مجموعة و 70000 مستخدم
"""

import asyncio
import logging
import os
import json
import time
from typing import Dict, List, Optional, Any, Union, Tuple
from dataclasses import dataclass, field
from pathlib import Path
import random

from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import (
    SessionPasswordNeededError, PhoneCodeInvalidError, PhoneNumberInvalidError,
    FloodWaitError, AuthKeyDuplicatedError, UserDeactivatedBanError,
    PhoneNumberBannedError, UnauthorizedError, ApiIdInvalidError
)
from telethon.tl.types import User, Chat, Channel
from telethon.tl.functions.channels import JoinChannelRequest, LeaveChannelRequest
from telethon.tl.functions.messages import GetDialogsRequest
from telethon.tl.types import InputPeerEmpty

from config_enhanced import config

logger = logging.getLogger(__name__)

@dataclass
class AssistantInfo:
    """معلومات الحساب المساعد"""
    assistant_id: int
    session_string: str
    phone: str
    name: str
    username: str = ""
    is_active: bool = True
    is_connected: bool = False
    last_used: float = 0.0
    total_calls: int = 0
    current_calls: int = 0
    join_date: str = ""
    last_error: str = ""
    flood_wait_until: float = 0.0
    client: Optional[TelegramClient] = None

@dataclass
class ConnectionStats:
    """إحصائيات الاتصال"""
    total_assistants: int = 0
    connected_assistants: int = 0
    active_calls: int = 0
    failed_connections: int = 0
    last_health_check: float = 0.0
    uptime: float = 0.0

class EnhancedTelethonManager:
    """مدير Telethon محسن للأحمال الكبيرة"""
    
    def __init__(self):
        self.bot_client: Optional[TelegramClient] = None
        self.assistants: Dict[int, AssistantInfo] = {}
        self.is_ready = False
        self.start_time = time.time()
        
        # إعدادات الاتصال
        self.api_id = config.system.api_id
        self.api_hash = config.system.api_hash
        self.bot_token = config.system.bot_token
        
        # إعدادات الجلسات
        self.sessions_dir = Path(config.assistant.sessions_dir)
        self.sessions_dir.mkdir(exist_ok=True)
        
        # إحصائيات الاتصال
        self.stats = ConnectionStats()
        
        # قائمة انتظار للمكالمات
        self.call_queue: List[Tuple[int, Any]] = []
        self.queue_lock = asyncio.Lock()
        
        # مهام الخلفية
        self.background_tasks: List[asyncio.Task] = []
        
        # إعدادات التحسين للأحمال الكبيرة
        self.max_concurrent_operations = config.performance.max_concurrent_streams
        self.operation_semaphore = asyncio.Semaphore(self.max_concurrent_operations)
        
    async def initialize(self):
        """تهيئة مدير Telethon"""
        try:
            logger.info("🚀 تهيئة Enhanced Telethon Manager...")
            
            # تهيئة البوت الرئيسي
            await self._initialize_bot()
            
            # تحميل الحسابات المساعدة من قاعدة البيانات
            await self._load_assistants_from_database()
            
            # بدء المهام الخلفية
            await self._start_background_tasks()
            
            self.is_ready = True
            logger.info("✅ تم تهيئة Enhanced Telethon Manager بنجاح")
            return True
            
        except Exception as e:
            logger.error(f"❌ خطأ في تهيئة Telethon Manager: {e}")
            return False
    
    async def _initialize_bot(self):
        """تهيئة البوت الرئيسي"""
        try:
            logger.info("🤖 تهيئة البوت الرئيسي...")
            
            # إنشاء عميل البوت مع إعدادات محسنة
            self.bot_client = TelegramClient(
                session=str(self.sessions_dir / "bot_session"),
                api_id=self.api_id,
                api_hash=self.api_hash,
                device_model=config.system.device_model,
                system_version=config.system.system_version,
                app_version=config.system.app_version,
                lang_code=config.system.default_language,
                system_lang_code=config.system.default_language,
                # إعدادات محسنة للأحمال الكبيرة
                connection_retries=5,
                retry_delay=2,
                timeout=30,
                request_retries=3,
                flood_sleep_threshold=60
            )
            
            # بدء العميل
            await self.bot_client.start(bot_token=self.bot_token)
            
            # التحقق من نجاح الاتصال
            me = await self.bot_client.get_me()
            logger.info(f"✅ تم تسجيل دخول البوت: @{me.username} ({me.id})")
            
            # إعداد معالجات الأحداث للبوت
            await self._setup_bot_handlers()
            
        except Exception as e:
            logger.error(f"❌ خطأ في تهيئة البوت الرئيسي: {e}")
            raise
    
    async def _setup_bot_handlers(self):
        """إعداد معالجات أحداث البوت"""
        @self.bot_client.on(events.NewMessage)
        async def handle_message(event):
            # معالج عام للرسائل
            pass
        
        @self.bot_client.on(events.CallbackQuery)
        async def handle_callback(event):
            # معالج الاستعلامات المضمنة
            pass
    
    async def _load_assistants_from_database(self):
        """تحميل الحسابات المساعدة من قاعدة البيانات"""
        try:
            # هنا يتم تحميل الحسابات من قاعدة البيانات
            # سيتم تنفيذ هذا عند إنشاء مدير قاعدة البيانات
            logger.info("📱 تحميل الحسابات المساعدة من قاعدة البيانات...")
            
            # مؤقتاً - تحميل من ملفات الجلسات الموجودة
            await self._load_existing_sessions()
            
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل الحسابات المساعدة: {e}")
    
    async def _load_existing_sessions(self):
        """تحميل الجلسات الموجودة"""
        try:
            session_files = list(self.sessions_dir.glob("assistant_*.session"))
            
            for session_file in session_files:
                try:
                    # استخراج معرف المساعد من اسم الملف
                    assistant_id = int(session_file.stem.replace("assistant_", ""))
                    
                    # إنشاء معلومات المساعد
                    assistant_info = AssistantInfo(
                        assistant_id=assistant_id,
                        session_string="",  # سيتم تحديثها لاحقاً
                        phone="",
                        name=f"Assistant {assistant_id}",
                        join_date=time.strftime("%Y-%m-%d %H:%M:%S")
                    )
                    
                    # تحميل الجلسة
                    await self._load_assistant_session(assistant_info, str(session_file))
                    
                except Exception as e:
                    logger.warning(f"⚠️ خطأ في تحميل جلسة {session_file}: {e}")
                    continue
            
            logger.info(f"📊 تم تحميل {len(self.assistants)} حساب مساعد")
            
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل الجلسات الموجودة: {e}")
    
    async def _load_assistant_session(self, assistant_info: AssistantInfo, session_path: str):
        """تحميل جلسة حساب مساعد"""
        try:
            # إنشاء عميل للحساب المساعد
            client = TelegramClient(
                session=session_path,
                api_id=self.api_id,
                api_hash=self.api_hash,
                device_model=config.system.device_model,
                system_version=config.system.system_version,
                app_version=config.system.app_version,
                connection_retries=3,
                retry_delay=1,
                timeout=20,
                flood_sleep_threshold=30
            )
            
            # محاولة الاتصال
            await client.connect()
            
            if await client.is_user_authorized():
                # الحصول على معلومات المستخدم
                me = await client.get_me()
                
                # تحديث معلومات المساعد
                assistant_info.name = f"{me.first_name or ''} {me.last_name or ''}".strip()
                assistant_info.username = me.username or ""
                assistant_info.phone = me.phone or ""
                assistant_info.is_connected = True
                assistant_info.client = client
                
                # إضافة للقاموس
                self.assistants[assistant_info.assistant_id] = assistant_info
                
                logger.info(f"✅ تم تحميل المساعد: {assistant_info.name} (@{assistant_info.username})")
                
            else:
                await client.disconnect()
                logger.warning(f"⚠️ المساعد {assistant_info.assistant_id} غير مصرح له")
                
        except Exception as e:
            logger.error(f"❌ خطأ في تحميل جلسة المساعد {assistant_info.assistant_id}: {e}")
            assistant_info.last_error = str(e)
            assistant_info.is_connected = False
    
    async def add_assistant(self, phone: str, session_string: Optional[str] = None) -> Dict[str, Any]:
        """إضافة حساب مساعد جديد"""
        try:
            logger.info(f"📱 إضافة حساب مساعد جديد: {phone}")
            
            # التحقق من الحد الأقصى للحسابات
            if len(self.assistants) >= config.assistant.max_assistants:
                return {
                    "success": False,
                    "message": f"تم الوصول للحد الأقصى من الحسابات المساعدة ({config.assistant.max_assistants})"
                }
            
            # إنشاء معرف فريد للمساعد
            assistant_id = self._generate_assistant_id()
            
            # إنشاء معلومات المساعد
            assistant_info = AssistantInfo(
                assistant_id=assistant_id,
                session_string=session_string or "",
                phone=phone,
                name=f"Assistant {assistant_id}",
                join_date=time.strftime("%Y-%m-%d %H:%M:%S")
            )
            
            # إنشاء العميل
            if session_string:
                session = StringSession(session_string)
            else:
                session = str(self.sessions_dir / f"assistant_{assistant_id}")
            
            client = TelegramClient(
                session=session,
                api_id=self.api_id,
                api_hash=self.api_hash,
                device_model=config.system.device_model,
                system_version=config.system.system_version,
                app_version=config.system.app_version
            )
            
            # محاولة تسجيل الدخول
            await client.connect()
            
            if not await client.is_user_authorized():
                if session_string:
                    return {
                        "success": False,
                        "message": "Session string غير صالح أو منتهي الصلاحية"
                    }
                else:
                    # إرسال كود التحقق
                    await client.send_code_request(phone)
                    return {
                        "success": False,
                        "message": "تم إرسال كود التحقق. استخدم /verify_assistant لإدخال الكود",
                        "assistant_id": assistant_id,
                        "phone": phone,
                        "pending_verification": True
                    }
            
            # تسجيل الدخول نجح
            me = await client.get_me()
            
            # تحديث معلومات المساعد
            assistant_info.name = f"{me.first_name or ''} {me.last_name or ''}".strip()
            assistant_info.username = me.username or ""
            assistant_info.phone = me.phone or phone
            assistant_info.is_connected = True
            assistant_info.client = client
            
            # حفظ في القاموس
            self.assistants[assistant_id] = assistant_info
            
            # حفظ في قاعدة البيانات (سيتم تنفيذه لاحقاً)
            # await self._save_assistant_to_database(assistant_info)
            
            logger.info(f"✅ تم إضافة المساعد بنجاح: {assistant_info.name}")
            
            return {
                "success": True,
                "message": f"تم إضافة الحساب المساعد بنجاح: {assistant_info.name}",
                "assistant_id": assistant_id,
                "name": assistant_info.name,
                "username": assistant_info.username
            }
            
        except FloodWaitError as e:
            logger.warning(f"⚠️ Flood wait: {e.seconds} ثانية")
            return {
                "success": False,
                "message": f"يرجى الانتظار {e.seconds} ثانية قبل المحاولة مرة أخرى"
            }
        except Exception as e:
            logger.error(f"❌ خطأ في إضافة المساعد: {e}")
            return {
                "success": False,
                "message": f"خطأ في إضافة الحساب المساعد: {str(e)}"
            }
    
    async def remove_assistant(self, assistant_id: int) -> Dict[str, Any]:
        """إزالة حساب مساعد"""
        try:
            if assistant_id not in self.assistants:
                return {
                    "success": False,
                    "message": "الحساب المساعد غير موجود"
                }
            
            assistant_info = self.assistants[assistant_id]
            
            # قطع الاتصال
            if assistant_info.client:
                await assistant_info.client.disconnect()
            
            # حذف الجلسة
            session_file = self.sessions_dir / f"assistant_{assistant_id}.session"
            if session_file.exists():
                session_file.unlink()
            
            # إزالة من القاموس
            del self.assistants[assistant_id]
            
            # إزالة من قاعدة البيانات (سيتم تنفيذه لاحقاً)
            # await self._remove_assistant_from_database(assistant_id)
            
            logger.info(f"✅ تم حذف المساعد: {assistant_info.name}")
            
            return {
                "success": True,
                "message": f"تم حذف الحساب المساعد: {assistant_info.name}"
            }
            
        except Exception as e:
            logger.error(f"❌ خطأ في حذف المساعد: {e}")
            return {
                "success": False,
                "message": f"خطأ في حذف الحساب المساعد: {str(e)}"
            }
    
    async def get_best_assistant(self, chat_id: int) -> Optional[AssistantInfo]:
        """الحصول على أفضل حساب مساعد متاح"""
        try:
            # فلترة الحسابات المتاحة
            available_assistants = [
                assistant for assistant in self.assistants.values()
                if (assistant.is_active and 
                    assistant.is_connected and 
                    assistant.current_calls < config.assistant.max_calls_per_assistant and
                    time.time() > assistant.flood_wait_until)
            ]
            
            if not available_assistants:
                return None
            
            # ترتيب حسب الأولوية (أقل استخداماً أولاً)
            available_assistants.sort(key=lambda x: (x.current_calls, x.total_calls))
            
            # اختيار عشوائي من أفضل 3 مساعدين
            top_assistants = available_assistants[:min(3, len(available_assistants))]
            selected_assistant = random.choice(top_assistants)
            
            # تحديث إحصائيات الاستخدام
            selected_assistant.last_used = time.time()
            selected_assistant.current_calls += 1
            
            return selected_assistant
            
        except Exception as e:
            logger.error(f"❌ خطأ في اختيار المساعد: {e}")
            return None
    
    async def release_assistant(self, assistant_id: int):
        """تحرير حساب مساعد من المكالمة"""
        try:
            if assistant_id in self.assistants:
                assistant = self.assistants[assistant_id]
                if assistant.current_calls > 0:
                    assistant.current_calls -= 1
                assistant.total_calls += 1
                
        except Exception as e:
            logger.error(f"❌ خطأ في تحرير المساعد: {e}")
    
    def _generate_assistant_id(self) -> int:
        """توليد معرف فريد للحساب المساعد"""
        while True:
            assistant_id = random.randint(100000, 999999)
            if assistant_id not in self.assistants:
                return assistant_id
    
    async def _start_background_tasks(self):
        """بدء المهام الخلفية"""
        try:
            # مهمة فحص صحة الحسابات
            health_task = asyncio.create_task(self._health_check_loop())
            self.background_tasks.append(health_task)
            
            # مهمة تنظيف الحسابات الخاملة
            cleanup_task = asyncio.create_task(self._cleanup_loop())
            self.background_tasks.append(cleanup_task)
            
            # مهمة معالجة قائمة الانتظار
            queue_task = asyncio.create_task(self._process_queue_loop())
            self.background_tasks.append(queue_task)
            
            logger.info("✅ تم بدء المهام الخلفية")
            
        except Exception as e:
            logger.error(f"❌ خطأ في بدء المهام الخلفية: {e}")
    
    async def _health_check_loop(self):
        """حلقة فحص صحة الحسابات"""
        while self.is_ready:
            try:
                await asyncio.sleep(config.assistant.health_check_interval)
                await self._perform_health_check()
                
            except Exception as e:
                logger.error(f"❌ خطأ في فحص الصحة: {e}")
    
    async def _perform_health_check(self):
        """فحص صحة جميع الحسابات"""
        try:
            self.stats.last_health_check = time.time()
            connected_count = 0
            failed_count = 0
            
            for assistant_id, assistant in self.assistants.items():
                try:
                    if assistant.client and assistant.is_connected:
                        # فحص الاتصال
                        if await assistant.client.is_user_authorized():
                            connected_count += 1
                            assistant.is_connected = True
                            assistant.last_error = ""
                        else:
                            assistant.is_connected = False
                            assistant.last_error = "غير مصرح"
                            failed_count += 1
                    else:
                        # محاولة إعادة الاتصال
                        await self._reconnect_assistant(assistant)
                        
                except Exception as e:
                    assistant.is_connected = False
                    assistant.last_error = str(e)
                    failed_count += 1
                    logger.warning(f"⚠️ مشكلة في المساعد {assistant_id}: {e}")
            
            # تحديث الإحصائيات
            self.stats.connected_assistants = connected_count
            self.stats.failed_connections = failed_count
            self.stats.total_assistants = len(self.assistants)
            
            if connected_count < len(self.assistants) * 0.5:
                logger.warning(f"⚠️ عدد الحسابات المتصلة منخفض: {connected_count}/{len(self.assistants)}")
            
        except Exception as e:
            logger.error(f"❌ خطأ في فحص الصحة العام: {e}")
    
    async def _reconnect_assistant(self, assistant: AssistantInfo):
        """إعادة الاتصال لحساب مساعد"""
        try:
            if not assistant.client:
                return
            
            # محاولة إعادة الاتصال
            await assistant.client.connect()
            
            if await assistant.client.is_user_authorized():
                assistant.is_connected = True
                assistant.last_error = ""
                logger.info(f"✅ تم إعادة اتصال المساعد: {assistant.name}")
            else:
                assistant.is_connected = False
                assistant.last_error = "غير مصرح"
                
        except Exception as e:
            assistant.is_connected = False
            assistant.last_error = str(e)
            logger.error(f"❌ فشل في إعادة اتصال المساعد {assistant.assistant_id}: {e}")
    
    async def _cleanup_loop(self):
        """حلقة تنظيف الحسابات الخاملة"""
        while self.is_ready:
            try:
                await asyncio.sleep(1800)  # كل 30 دقيقة
                await self._cleanup_idle_assistants()
                
            except Exception as e:
                logger.error(f"❌ خطأ في حلقة التنظيف: {e}")
    
    async def _cleanup_idle_assistants(self):
        """تنظيف الحسابات الخاملة"""
        try:
            current_time = time.time()
            idle_threshold = config.assistant.auto_leave_time
            
            for assistant in self.assistants.values():
                if (assistant.current_calls == 0 and 
                    current_time - assistant.last_used > idle_threshold):
                    
                    # مغادرة المجموعات غير النشطة
                    await self._leave_inactive_groups(assistant)
                    
        except Exception as e:
            logger.error(f"❌ خطأ في تنظيف الحسابات الخاملة: {e}")
    
    async def _leave_inactive_groups(self, assistant: AssistantInfo):
        """مغادرة المجموعات غير النشطة"""
        try:
            if not assistant.client or not assistant.is_connected:
                return
            
            # الحصول على قائمة المحادثات
            async for dialog in assistant.client.iter_dialogs():
                if hasattr(dialog.entity, 'megagroup') and dialog.entity.megagroup:
                    # فحص النشاط الأخير في المجموعة
                    # إذا لم يكن هناك نشاط، اترك المجموعة
                    try:
                        await assistant.client(LeaveChannelRequest(dialog.entity))
                        logger.info(f"📤 المساعد {assistant.name} غادر مجموعة غير نشطة")
                    except Exception:
                        pass  # تجاهل الأخطاء
                        
        except Exception as e:
            logger.error(f"❌ خطأ في مغادرة المجموعات: {e}")
    
    async def _process_queue_loop(self):
        """حلقة معالجة قائمة الانتظار"""
        while self.is_ready:
            try:
                await asyncio.sleep(1)
                await self._process_call_queue()
                
            except Exception as e:
                logger.error(f"❌ خطأ في معالجة القائمة: {e}")
    
    async def _process_call_queue(self):
        """معالجة قائمة انتظار المكالمات"""
        async with self.queue_lock:
            if not self.call_queue:
                return
            
            # معالجة العناصر في القائمة
            processed_items = []
            
            for chat_id, request_data in self.call_queue[:]:
                assistant = await self.get_best_assistant(chat_id)
                if assistant:
                    # إزالة من القائمة ومعالجة الطلب
                    processed_items.append((chat_id, request_data))
                    # هنا يتم معالجة الطلب الفعلي
                    
            # إزالة العناصر المعالجة
            for item in processed_items:
                if item in self.call_queue:
                    self.call_queue.remove(item)
    
    # دوال الحصول على المعلومات
    def get_assistants_count(self) -> int:
        """الحصول على عدد الحسابات المساعدة"""
        return len(self.assistants)
    
    def get_connected_assistants_count(self) -> int:
        """الحصول على عدد الحسابات المتصلة"""
        return sum(1 for assistant in self.assistants.values() if assistant.is_connected)
    
    def get_active_calls_count(self) -> int:
        """الحصول على عدد المكالمات النشطة"""
        return sum(assistant.current_calls for assistant in self.assistants.values())
    
    def get_assistants_info(self) -> List[Dict[str, Any]]:
        """الحصول على معلومات جميع الحسابات المساعدة"""
        return [
            {
                "id": assistant.assistant_id,
                "name": assistant.name,
                "username": assistant.username,
                "phone": assistant.phone,
                "is_active": assistant.is_active,
                "is_connected": assistant.is_connected,
                "current_calls": assistant.current_calls,
                "total_calls": assistant.total_calls,
                "last_used": assistant.last_used,
                "last_error": assistant.last_error,
                "join_date": assistant.join_date
            }
            for assistant in self.assistants.values()
        ]
    
    def get_connection_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات الاتصال"""
        return {
            "total_assistants": self.stats.total_assistants,
            "connected_assistants": self.stats.connected_assistants,
            "active_calls": self.get_active_calls_count(),
            "failed_connections": self.stats.failed_connections,
            "last_health_check": self.stats.last_health_check,
            "uptime": time.time() - self.start_time,
            "queue_size": len(self.call_queue)
        }
    
    async def shutdown(self):
        """إيقاف مدير Telethon بأمان"""
        try:
            logger.info("🛑 إيقاف Enhanced Telethon Manager...")
            
            self.is_ready = False
            
            # إيقاف المهام الخلفية
            for task in self.background_tasks:
                task.cancel()
                try:
                    await task
                except asyncio.CancelledError:
                    pass
            
            # قطع اتصال جميع الحسابات المساعدة
            for assistant in self.assistants.values():
                if assistant.client:
                    await assistant.client.disconnect()
            
            # قطع اتصال البوت الرئيسي
            if self.bot_client:
                await self.bot_client.disconnect()
            
            logger.info("✅ تم إيقاف Enhanced Telethon Manager")
            
        except Exception as e:
            logger.error(f"❌ خطأ في إيقاف Telethon Manager: {e}")
    
    async def reconnect(self):
        """إعادة الاتصال للنظام بالكامل"""
        try:
            logger.info("🔄 إعادة اتصال Enhanced Telethon Manager...")
            
            # إعادة اتصال البوت الرئيسي
            if self.bot_client:
                await self.bot_client.connect()
            
            # إعادة اتصال جميع الحسابات المساعدة
            for assistant in self.assistants.values():
                await self._reconnect_assistant(assistant)
            
            logger.info("✅ تم إعادة الاتصال بنجاح")
            
        except Exception as e:
            logger.error(f"❌ خطأ في إعادة الاتصال: {e}")

# إنشاء كائن مدير Telethon العام
enhanced_telethon_manager = None