#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎵 ZeMusic Bot v3.0 - Enhanced Assistant Manager
تاريخ الإنشاء: 2025-01-28

نظام إدارة الحسابات المساعدة المحسن مع توزيع الأحمال الذكي
"""

import asyncio
import logging
import random
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import (
    AuthKeyUnregisteredError, SessionPasswordNeededError,
    FloodWaitError, PhoneNumberBannedError, UserDeactivatedError
)

from ..config import config
from .database import db, AssistantData

logger = logging.getLogger(__name__)

@dataclass
class AssistantClient:
    """كلاس للحساب المساعد"""
    assistant_id: int
    client: TelegramClient
    session_string: str
    name: str = ""
    username: str = ""
    phone: str = ""
    is_connected: bool = False
    is_authorized: bool = False
    active_calls: int = 0
    last_health_check: datetime = None
    connection_attempts: int = 0
    max_connection_attempts: int = 3
    user_info: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.user_info is None:
            self.user_info = {}

class AssistantManager:
    """مدير الحسابات المساعدة المحسن"""
    
    def __init__(self):
        """تهيئة مدير الحسابات المساعدة"""
        self.assistants: Dict[int, AssistantClient] = {}
        self.active_calls: Dict[int, List[int]] = {}  # chat_id -> [assistant_ids]
        self.load_balancer_index = 0
        self.health_check_task = None
        self.auto_management_task = None
        self.is_initialized = False
        
    async def initialize(self) -> bool:
        """تهيئة مدير الحسابات المساعدة"""
        try:
            logger.info("🤖 تهيئة مدير الحسابات المساعدة...")
            
            # تحميل الحسابات من قاعدة البيانات
            await self._load_assistants_from_database()
            
            # تحميل الحسابات من متغيرات البيئة
            await self._load_assistants_from_config()
            
            # بدء الحسابات المساعدة
            await self._start_all_assistants()
            
            # بدء مهام المراقبة
            if config.assistant.auto_management:
                self._start_monitoring_tasks()
            
            self.is_initialized = True
            logger.info(f"✅ تم تهيئة {len(self.assistants)} حساب مساعد")
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في تهيئة مدير الحسابات المساعدة: {e}")
            return False
    
    async def _load_assistants_from_database(self):
        """تحميل الحسابات من قاعدة البيانات"""
        try:
            assistants_data = await db.get_all_assistants()
            
            for assistant_data in assistants_data:
                await self._create_assistant_client(
                    assistant_data.assistant_id,
                    assistant_data.session_string,
                    assistant_data.name
                )
                
            logger.info(f"📚 تم تحميل {len(assistants_data)} حساب من قاعدة البيانات")
            
        except Exception as e:
            logger.error(f"❌ فشل في تحميل الحسابات من قاعدة البيانات: {e}")
    
    async def _load_assistants_from_config(self):
        """تحميل الحسابات من متغيرات البيئة"""
        try:
            loaded_count = 0
            
            for i, session_string in enumerate(config.assistant.session_strings, 1):
                if session_string and session_string.strip():
                    # التحقق من عدم وجود الحساب مسبقاً
                    assistant_id = await self._get_assistant_id_from_session(session_string)
                    
                    if assistant_id and assistant_id not in self.assistants:
                        await self._create_assistant_client(
                            assistant_id,
                            session_string,
                            f"Assistant_{i}"
                        )
                        loaded_count += 1
            
            if loaded_count > 0:
                logger.info(f"⚙️ تم تحميل {loaded_count} حساب من متغيرات البيئة")
                
        except Exception as e:
            logger.error(f"❌ فشل في تحميل الحسابات من الإعدادات: {e}")
    
    async def _get_assistant_id_from_session(self, session_string: str) -> Optional[int]:
        """الحصول على معرف الحساب من session string"""
        try:
            temp_client = TelegramClient(
                StringSession(session_string),
                config.telegram.api_id,
                config.telegram.api_hash
            )
            
            await temp_client.connect()
            
            if await temp_client.is_user_authorized():
                me = await temp_client.get_me()
                await temp_client.disconnect()
                return me.id
            
            await temp_client.disconnect()
            return None
            
        except Exception as e:
            logger.error(f"❌ فشل في الحصول على معرف الحساب: {e}")
            return None
    
    async def _create_assistant_client(self, assistant_id: int, session_string: str, name: str) -> bool:
        """إنشاء عميل الحساب المساعد"""
        try:
            client = TelegramClient(
                StringSession(session_string),
                config.telegram.api_id,
                config.telegram.api_hash,
                device_model=f"ZeMusic Assistant {assistant_id}",
                system_version=config.telegram.system_version,
                app_version=config.telegram.app_version,
                lang_code="ar",
                system_lang_code="ar"
            )
            
            assistant = AssistantClient(
                assistant_id=assistant_id,
                client=client,
                session_string=session_string,
                name=name
            )
            
            self.assistants[assistant_id] = assistant
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في إنشاء عميل الحساب المساعد {assistant_id}: {e}")
            return False
    
    async def _start_all_assistants(self):
        """بدء جميع الحسابات المساعدة"""
        tasks = []
        
        for assistant_id, assistant in self.assistants.items():
            task = asyncio.create_task(
                self._start_assistant(assistant),
                name=f"start_assistant_{assistant_id}"
            )
            tasks.append(task)
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            success_count = sum(1 for result in results if result is True)
            logger.info(f"✅ تم تشغيل {success_count}/{len(tasks)} حساب مساعد بنجاح")
    
    async def _start_assistant(self, assistant: AssistantClient) -> bool:
        """بدء حساب مساعد واحد"""
        try:
            logger.info(f"🔄 بدء الحساب المساعد {assistant.assistant_id}...")
            
            # الاتصال
            await assistant.client.connect()
            
            if not assistant.client.is_connected():
                logger.error(f"❌ فشل في الاتصال للحساب {assistant.assistant_id}")
                return False
            
            # التحقق من التفويض
            if not await assistant.client.is_user_authorized():
                logger.error(f"❌ الحساب {assistant.assistant_id} غير مفوض")
                return False
            
            # الحصول على معلومات الحساب
            me = await assistant.client.get_me()
            assistant.user_info = {
                'id': me.id,
                'first_name': getattr(me, 'first_name', ''),
                'username': getattr(me, 'username', ''),
                'phone': getattr(me, 'phone', ''),
                'is_premium': getattr(me, 'premium', False)
            }
            
            if not assistant.name or assistant.name.startswith("Assistant_"):
                assistant.name = me.first_name or f"Assistant_{assistant.assistant_id}"
            
            assistant.username = getattr(me, 'username', '')
            assistant.phone = getattr(me, 'phone', '')
            assistant.is_connected = True
            assistant.is_authorized = True
            assistant.connection_attempts = 0
            
            # حفظ في قاعدة البيانات
            await self._save_assistant_to_database(assistant)
            
            logger.info(f"✅ تم تشغيل الحساب المساعد {assistant.name} ({assistant.assistant_id})")
            return True
            
        except AuthKeyUnregisteredError:
            logger.error(f"❌ مفتاح التفويض للحساب {assistant.assistant_id} غير مسجل")
            return False
            
        except UserDeactivatedError:
            logger.error(f"❌ الحساب {assistant.assistant_id} معطل")
            return False
            
        except PhoneNumberBannedError:
            logger.error(f"❌ الحساب {assistant.assistant_id} محظور")
            return False
            
        except FloodWaitError as e:
            logger.warning(f"⏳ انتظار {e.seconds} ثانية للحساب {assistant.assistant_id}")
            await asyncio.sleep(e.seconds)
            return await self._start_assistant(assistant)
            
        except Exception as e:
            logger.error(f"❌ فشل في تشغيل الحساب المساعد {assistant.assistant_id}: {e}")
            assistant.connection_attempts += 1
            return False
    
    async def _save_assistant_to_database(self, assistant: AssistantClient):
        """حفظ الحساب المساعد في قاعدة البيانات"""
        try:
            assistant_data = AssistantData(
                assistant_id=assistant.assistant_id,
                session_string=assistant.session_string,
                name=assistant.name,
                username=assistant.username,
                phone=assistant.phone,
                is_active=True,
                is_connected=assistant.is_connected,
                total_calls=0,
                active_calls=assistant.active_calls
            )
            
            await db.add_assistant(assistant_data)
            
        except Exception as e:
            logger.error(f"❌ فشل في حفظ الحساب المساعد {assistant.assistant_id}: {e}")
    
    def _start_monitoring_tasks(self):
        """بدء مهام المراقبة"""
        # مهمة فحص الصحة
        self.health_check_task = asyncio.create_task(
            self._health_check_loop(),
            name="assistant_health_check"
        )
        
        # مهمة الإدارة التلقائية
        self.auto_management_task = asyncio.create_task(
            self._auto_management_loop(),
            name="assistant_auto_management"
        )
        
        logger.info("📊 تم بدء مهام مراقبة الحسابات المساعدة")
    
    async def _health_check_loop(self):
        """حلقة فحص صحة الحسابات"""
        while True:
            try:
                await asyncio.sleep(config.assistant.health_check_interval)
                await self._perform_health_checks()
                
            except Exception as e:
                logger.error(f"❌ خطأ في حلقة فحص الصحة: {e}")
    
    async def _auto_management_loop(self):
        """حلقة الإدارة التلقائية"""
        while True:
            try:
                await asyncio.sleep(1800)  # كل 30 دقيقة
                await self._auto_leave_inactive_chats()
                
            except Exception as e:
                logger.error(f"❌ خطأ في حلقة الإدارة التلقائية: {e}")
    
    async def _perform_health_checks(self):
        """فحص صحة جميع الحسابات"""
        tasks = []
        
        for assistant_id, assistant in self.assistants.items():
            task = asyncio.create_task(
                self._check_assistant_health(assistant),
                name=f"health_check_{assistant_id}"
            )
            tasks.append(task)
        
        if tasks:
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            healthy_count = sum(1 for result in results if result is True)
            if healthy_count < len(self.assistants):
                logger.warning(f"⚠️ {healthy_count}/{len(self.assistants)} حساب مساعد بحالة جيدة")
    
    async def _check_assistant_health(self, assistant: AssistantClient) -> bool:
        """فحص صحة حساب مساعد واحد"""
        try:
            if not assistant.client.is_connected():
                logger.warning(f"⚠️ الحساب {assistant.assistant_id} غير متصل - محاولة إعادة الاتصال")
                return await self._reconnect_assistant(assistant)
            
            # فحص ping
            import time
            start_time = time.time()
            await assistant.client.get_me()
            ping_time = (time.time() - start_time) * 1000
            
            assistant.last_health_check = datetime.now()
            
            # تحديث حالة قاعدة البيانات
            await db.update_assistant_status(
                assistant.assistant_id,
                assistant.is_connected,
                assistant.active_calls
            )
            
            if ping_time > 5000:  # أكثر من 5 ثواني
                logger.warning(f"⚠️ ping عالي للحساب {assistant.assistant_id}: {ping_time:.2f}ms")
            
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في فحص صحة الحساب {assistant.assistant_id}: {e}")
            assistant.is_connected = False
            
            # محاولة إعادة الاتصال
            return await self._reconnect_assistant(assistant)
    
    async def _reconnect_assistant(self, assistant: AssistantClient) -> bool:
        """إعادة اتصال حساب مساعد"""
        try:
            if assistant.connection_attempts >= assistant.max_connection_attempts:
                logger.error(f"❌ تم تجاوز الحد الأقصى لمحاولات الاتصال للحساب {assistant.assistant_id}")
                return False
            
            assistant.connection_attempts += 1
            logger.info(f"🔄 إعادة اتصال الحساب {assistant.assistant_id} (محاولة {assistant.connection_attempts})")
            
            # قطع الاتصال أولاً
            try:
                await assistant.client.disconnect()
            except:
                pass
            
            # إعادة الاتصال
            return await self._start_assistant(assistant)
            
        except Exception as e:
            logger.error(f"❌ فشل في إعادة اتصال الحساب {assistant.assistant_id}: {e}")
            return False
    
    async def get_best_assistant(self, chat_id: int) -> Optional[AssistantClient]:
        """الحصول على أفضل حساب مساعد للمحادثة"""
        try:
            # فلترة الحسابات المتصلة والمفوضة
            available_assistants = [
                assistant for assistant in self.assistants.values()
                if assistant.is_connected and assistant.is_authorized
            ]
            
            if not available_assistants:
                logger.error("❌ لا توجد حسابات مساعدة متاحة")
                return None
            
            # توزيع الأحمال
            if config.assistant.load_balancing:
                return self._get_load_balanced_assistant(available_assistants)
            else:
                return random.choice(available_assistants)
                
        except Exception as e:
            logger.error(f"❌ فشل في الحصول على حساب مساعد: {e}")
            return None
    
    def _get_load_balanced_assistant(self, assistants: List[AssistantClient]) -> AssistantClient:
        """توزيع الأحمال بين الحسابات المساعدة"""
        # ترتيب الحسابات حسب عدد المكالمات النشطة
        assistants.sort(key=lambda x: x.active_calls)
        
        # اختيار الحساب الأقل استخداماً
        best_assistant = assistants[0]
        
        # التحقق من الحد الأقصى للمكالمات
        if best_assistant.active_calls >= config.assistant.max_calls_per_assistant:
            # البحث عن حساب آخر
            for assistant in assistants[1:]:
                if assistant.active_calls < config.assistant.max_calls_per_assistant:
                    return assistant
            
            # إذا لم نجد حساب متاح، نستخدم الأفضل المتاح
            logger.warning("⚠️ جميع الحسابات المساعدة مشغولة")
        
        return best_assistant
    
    async def add_assistant_with_session(self, session_string: str, name: str = None) -> Dict[str, Any]:
        """إضافة حساب مساعد جديد بـ session string"""
        try:
            # التحقق من صحة session string
            assistant_id = await self._get_assistant_id_from_session(session_string)
            
            if not assistant_id:
                return {
                    'success': False,
                    'message': 'session string غير صالح أو منتهي الصلاحية'
                }
            
            # التحقق من عدم وجود الحساب مسبقاً
            if assistant_id in self.assistants:
                return {
                    'success': False,
                    'message': 'الحساب موجود بالفعل'
                }
            
            # التحقق من الحد الأقصى للحسابات
            if len(self.assistants) >= config.assistant.max_assistants:
                return {
                    'success': False,
                    'message': f'تم الوصول للحد الأقصى ({config.assistant.max_assistants}) حساب'
                }
            
            # إنشاء الحساب
            if not name:
                name = f"Assistant_{assistant_id}"
            
            success = await self._create_assistant_client(assistant_id, session_string, name)
            
            if not success:
                return {
                    'success': False,
                    'message': 'فشل في إنشاء الحساب المساعد'
                }
            
            # بدء الحساب
            assistant = self.assistants[assistant_id]
            start_success = await self._start_assistant(assistant)
            
            if start_success:
                return {
                    'success': True,
                    'message': f'تم إضافة الحساب المساعد {assistant.name} بنجاح',
                    'assistant_id': assistant_id,
                    'assistant_info': {
                        'name': assistant.name,
                        'username': assistant.username,
                        'phone': assistant.phone
                    }
                }
            else:
                # حذف الحساب إذا فشل التشغيل
                del self.assistants[assistant_id]
                return {
                    'success': False,
                    'message': 'فشل في تشغيل الحساب المساعد'
                }
                
        except Exception as e:
            logger.error(f"❌ فشل في إضافة الحساب المساعد: {e}")
            return {
                'success': False,
                'message': f'خطأ في إضافة الحساب: {str(e)}'
            }
    
    async def remove_assistant(self, assistant_id: int) -> bool:
        """حذف حساب مساعد"""
        try:
            if assistant_id not in self.assistants:
                return False
            
            assistant = self.assistants[assistant_id]
            
            # قطع الاتصال
            try:
                await assistant.client.disconnect()
            except:
                pass
            
            # حذف من الذاكرة
            del self.assistants[assistant_id]
            
            # تحديث قاعدة البيانات
            await db.update_assistant_status(assistant_id, False, 0)
            
            logger.info(f"🗑️ تم حذف الحساب المساعد {assistant_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في حذف الحساب المساعد {assistant_id}: {e}")
            return False
    
    async def restart_all_assistants(self) -> Dict[str, Any]:
        """إعادة تشغيل جميع الحسابات المساعدة"""
        try:
            logger.info("🔄 إعادة تشغيل جميع الحسابات المساعدة...")
            
            # قطع اتصال جميع الحسابات
            disconnect_tasks = []
            for assistant in self.assistants.values():
                task = asyncio.create_task(assistant.client.disconnect())
                disconnect_tasks.append(task)
            
            if disconnect_tasks:
                await asyncio.gather(*disconnect_tasks, return_exceptions=True)
            
            # إعادة تشغيل جميع الحسابات
            await self._start_all_assistants()
            
            # حساب النتائج
            connected_count = sum(1 for a in self.assistants.values() if a.is_connected)
            total_count = len(self.assistants)
            
            return {
                'success': True,
                'message': f'تم إعادة تشغيل {connected_count}/{total_count} حساب مساعد بنجاح',
                'connected_count': connected_count,
                'total_count': total_count
            }
            
        except Exception as e:
            logger.error(f"❌ فشل في إعادة تشغيل الحسابات المساعدة: {e}")
            return {
                'success': False,
                'message': f'فشل في إعادة التشغيل: {str(e)}'
            }
    
    async def get_assistants_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات الحسابات المساعدة"""
        try:
            total_assistants = len(self.assistants)
            connected_assistants = sum(1 for a in self.assistants.values() if a.is_connected)
            active_calls = sum(a.active_calls for a in self.assistants.values())
            
            assistants_info = []
            for assistant in self.assistants.values():
                assistants_info.append({
                    'id': assistant.assistant_id,
                    'name': assistant.name,
                    'username': assistant.username,
                    'is_connected': assistant.is_connected,
                    'active_calls': assistant.active_calls,
                    'last_health_check': assistant.last_health_check.isoformat() if assistant.last_health_check else None
                })
            
            return {
                'total_assistants': total_assistants,
                'connected_assistants': connected_assistants,
                'active_calls': active_calls,
                'max_assistants': config.assistant.max_assistants,
                'load_balancing_enabled': config.assistant.load_balancing,
                'auto_management_enabled': config.assistant.auto_management,
                'assistants': assistants_info
            }
            
        except Exception as e:
            logger.error(f"❌ فشل في الحصول على إحصائيات الحسابات المساعدة: {e}")
            return {}
    
    def get_connected_assistants_count(self) -> int:
        """الحصول على عدد الحسابات المتصلة"""
        return sum(1 for assistant in self.assistants.values() if assistant.is_connected)
    
    async def check_assistant(self, assistant_id: int) -> Dict[str, Any]:
        """فحص حساب مساعد محدد"""
        try:
            if assistant_id not in self.assistants:
                return {
                    'connected': False,
                    'error': 'الحساب غير موجود'
                }
            
            assistant = self.assistants[assistant_id]
            health_check = await self._check_assistant_health(assistant)
            
            return {
                'connected': health_check,
                'assistant_info': {
                    'id': assistant.assistant_id,
                    'name': assistant.name,
                    'username': assistant.username,
                    'active_calls': assistant.active_calls,
                    'last_health_check': assistant.last_health_check.isoformat() if assistant.last_health_check else None
                }
            }
            
        except Exception as e:
            logger.error(f"❌ فشل في فحص الحساب المساعد {assistant_id}: {e}")
            return {
                'connected': False,
                'error': str(e)
            }
    
    async def _auto_leave_inactive_chats(self):
        """مغادرة المحادثات غير النشطة تلقائياً"""
        try:
            if not config.assistant.auto_management:
                return
            
            cutoff_time = datetime.now() - timedelta(seconds=config.assistant.auto_leave_time)
            
            for assistant in self.assistants.values():
                if not assistant.is_connected:
                    continue
                
                try:
                    # الحصول على المحادثات
                    dialogs = await assistant.client.get_dialogs()
                    
                    for dialog in dialogs:
                        # تخطي المحادثات الخاصة والقنوات المهمة
                        if dialog.is_user or dialog.is_channel:
                            continue
                        
                        # فحص آخر نشاط
                        if dialog.date and dialog.date < cutoff_time:
                            try:
                                await assistant.client.leave_chat(dialog.id)
                                logger.info(f"👋 غادر الحساب {assistant.assistant_id} المحادثة {dialog.id}")
                            except Exception as e:
                                logger.error(f"❌ فشل في مغادرة المحادثة {dialog.id}: {e}")
                
                except Exception as e:
                    logger.error(f"❌ فشل في تنظيف المحادثات للحساب {assistant.assistant_id}: {e}")
                    
        except Exception as e:
            logger.error(f"❌ فشل في المغادرة التلقائية: {e}")
    
    async def shutdown(self):
        """إيقاف مدير الحسابات المساعدة"""
        try:
            logger.info("🛑 إيقاف مدير الحسابات المساعدة...")
            
            # إيقاف مهام المراقبة
            if self.health_check_task:
                self.health_check_task.cancel()
                
            if self.auto_management_task:
                self.auto_management_task.cancel()
            
            # قطع اتصال جميع الحسابات
            disconnect_tasks = []
            for assistant in self.assistants.values():
                task = asyncio.create_task(assistant.client.disconnect())
                disconnect_tasks.append(task)
            
            if disconnect_tasks:
                await asyncio.gather(*disconnect_tasks, return_exceptions=True)
            
            logger.info("✅ تم إيقاف مدير الحسابات المساعدة")
            
        except Exception as e:
            logger.error(f"❌ خطأ في إيقاف مدير الحسابات المساعدة: {e}")

# إنشاء مثيل عام لمدير الحسابات المساعدة
assistant_manager = AssistantManager()