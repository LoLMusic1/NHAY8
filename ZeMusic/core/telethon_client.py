#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🔥 Telethon Client Manager - ZeMusic Bot
تاريخ الإنشاء: 2025-01-28
"""

import asyncio
import logging
import os
from typing import Dict, List, Optional, Any
from telethon import TelegramClient, events
from telethon.sessions import StringSession
from telethon.errors import (
    SessionPasswordNeededError, 
    PhoneCodeInvalidError,
    PhoneNumberInvalidError,
    FloodWaitError
)

import config
from ZeMusic.logging import LOGGER

class TelethonClientManager:
    """إدارة عملاء Telethon للبوت والحسابات المساعدة"""
    
    def __init__(self):
        self.bot_client: Optional[TelegramClient] = None
        self.assistant_clients: Dict[int, TelegramClient] = {}
        self.active_sessions: Dict[str, TelegramClient] = {}
        self.logger = logging.getLogger(__name__)
        
        # معلومات الاتصال
        self.api_id = config.API_ID
        self.api_hash = config.API_HASH
        self.bot_token = config.BOT_TOKEN
        
        # إعدادات الجلسات
        self.sessions_dir = "telethon_sessions"
        os.makedirs(self.sessions_dir, exist_ok=True)
        
    async def initialize_bot(self) -> bool:
        """تهيئة البوت الرئيسي"""
        try:
            self.logger.info("🤖 تهيئة البوت الرئيسي باستخدام Telethon...")
            
            # إنشاء عميل البوت
            self.bot_client = TelegramClient(
                session=f"{self.sessions_dir}/bot_session",
                api_id=self.api_id,
                api_hash=self.api_hash,
                device_model=config.DEVICE_MODEL,
                system_version=config.SYSTEM_VERSION,
                app_version=config.APPLICATION_VERSION,
                lang_code="ar",
                system_lang_code="ar"
            )
            
            # بدء العميل
            await self.bot_client.start(bot_token=self.bot_token)
            
            # التحقق من نجاح الاتصال
            me = await self.bot_client.get_me()
            self.logger.info(f"✅ تم تسجيل دخول البوت: @{me.username} ({me.id})")
            
            # إعداد معالجات الأحداث
            await self._setup_bot_handlers()
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ فشل في تهيئة البوت: {e}")
            return False
    
    async def add_assistant(self, phone: str, session_string: Optional[str] = None) -> Dict[str, Any]:
        """إضافة حساب مساعد جديد"""
        try:
            self.logger.info(f"📱 إضافة حساب مساعد: {phone}")
            
            # إنشاء عميل للحساب المساعد
            if session_string:
                session = StringSession(session_string)
            else:
                session = f"{self.sessions_dir}/assistant_{phone.replace('+', '')}"
            
            assistant_client = TelegramClient(
                session=session,
                api_id=self.api_id,
                api_hash=self.api_hash,
                device_model=config.DEVICE_MODEL,
                system_version=config.SYSTEM_VERSION,
                app_version=config.APPLICATION_VERSION,
                lang_code="ar",
                system_lang_code="ar"
            )
            
            # محاولة تسجيل الدخول
            await assistant_client.connect()
            
            if not await assistant_client.is_user_authorized():
                # إرسال كود التحقق
                try:
                    sent_code = await assistant_client.send_code_request(phone)
                    return {
                        'success': False,
                        'requires_code': True,
                        'phone_code_hash': sent_code.phone_code_hash,
                        'client_id': id(assistant_client),
                        'message': f'تم إرسال كود التحقق إلى {phone}'
                    }
                except PhoneNumberInvalidError:
                    return {
                        'success': False,
                        'error': 'رقم الهاتف غير صحيح'
                    }
                except Exception as e:
                    return {
                        'success': False,
                        'error': f'خطأ في إرسال الكود: {str(e)}'
                    }
            else:
                # المستخدم مسجل مسبقاً
                me = await assistant_client.get_me()
                assistant_id = len(self.assistant_clients) + 1
                self.assistant_clients[assistant_id] = assistant_client
                
                # حفظ في قاعدة البيانات
                from ZeMusic.core.database import db
                await db.add_assistant(assistant_id, phone, session_string or "", me.id, me.username or "")
                
                self.logger.info(f"✅ تم إضافة الحساب المساعد: @{me.username} ({me.id})")
                
                return {
                    'success': True,
                    'user_info': {
                        'id': me.id,
                        'username': me.username,
                        'first_name': me.first_name,
                        'phone': phone
                    }
                }
                
        except Exception as e:
            self.logger.error(f"❌ خطأ في إضافة المساعد: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def add_assistant_with_session(self, session_string: str, name: str) -> Dict[str, Any]:
        """إضافة حساب مساعد باستخدام session string"""
        try:
            self.logger.info(f"📱 إضافة حساب مساعد بـ session string: {name}")
            
            # إنشاء جلسة من session string
            session = StringSession(session_string)
            
            # إنشاء عميل Telethon للحساب المساعد
            assistant_client = TelegramClient(
                session=session,
                api_id=self.api_id,
                api_hash=self.api_hash,
                device_model=config.DEVICE_MODEL,
                system_version=config.SYSTEM_VERSION,
                app_version=config.APPLICATION_VERSION,
                lang_code="ar",
                system_lang_code="ar"
            )
            
            await assistant_client.connect()
            
            # التحقق من تفويض المستخدم
            if not await assistant_client.is_user_authorized():
                await assistant_client.disconnect()
                return {
                    'success': False,
                    'error': 'Session غير مصرح أو منتهي الصلاحية'
                }
            
            # الحصول على معلومات المستخدم
            me = await assistant_client.get_me()
            
            # تحديد معرف المساعد
            assistant_id = len(self.assistant_clients) + 1
            
            # إضافة العميل إلى القائمة
            self.assistant_clients[assistant_id] = assistant_client
            
            # حفظ في قاعدة البيانات
            try:
                from ZeMusic.core.database import db
                await db.add_assistant(
                    assistant_id=assistant_id,
                    phone=me.phone or f"+{me.id}",
                    session_string=session_string,
                    user_id=me.id,
                    username=me.username or ""
                )
                self.logger.info(f"✅ تم حفظ الحساب المساعد في قاعدة البيانات: {assistant_id}")
            except Exception as db_error:
                self.logger.error(f"❌ خطأ في حفظ المساعد في قاعدة البيانات: {db_error}")
            
            self.logger.info(f"✅ تم إضافة الحساب المساعد: {name} (@{me.username or me.id})")
            
            return {
                'success': True,
                'assistant_id': assistant_id,
                'connected': True,
                'user_info': {
                    'id': me.id,
                    'username': me.username,
                    'first_name': me.first_name,
                    'last_name': me.last_name,
                    'phone': me.phone
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في إضافة المساعد بـ session string: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def verify_assistant_code(self, client_id: int, phone: str, code: str, phone_code_hash: str, password: Optional[str] = None) -> Dict[str, Any]:
        """التحقق من كود التحقق للحساب المساعد"""
        try:
            # العثور على العميل
            assistant_client = None
            for client in [self.bot_client] + list(self.assistant_clients.values()):
                if id(client) == client_id:
                    assistant_client = client
                    break
            
            if not assistant_client:
                return {'success': False, 'error': 'العميل غير موجود'}
            
            try:
                # التحقق من الكود
                await assistant_client.sign_in(phone, code, phone_code_hash=phone_code_hash)
                
            except SessionPasswordNeededError:
                if not password:
                    return {
                        'success': False,
                        'requires_password': True,
                        'message': 'يتطلب كلمة مرور التحقق بخطوتين'
                    }
                else:
                    # التحقق من كلمة المرور
                    await assistant_client.sign_in(password=password)
            
            except PhoneCodeInvalidError:
                return {'success': False, 'error': 'كود التحقق غير صحيح'}
            
            # الحصول على معلومات المستخدم
            me = await assistant_client.get_me()
            assistant_id = len(self.assistant_clients) + 1
            self.assistant_clients[assistant_id] = assistant_client
            
            # حفظ في قاعدة البيانات
            session_string = assistant_client.session.save()
            from ZeMusic.core.database import db
            await db.add_assistant(assistant_id, phone, session_string, me.id, me.username or "")
            
            self.logger.info(f"✅ تم التحقق من الحساب المساعد: @{me.username} ({me.id})")
            
            return {
                'success': True,
                'user_info': {
                    'id': me.id,
                    'username': me.username,
                    'first_name': me.first_name,
                    'phone': phone
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في التحقق من الكود: {e}")
            return {'success': False, 'error': str(e)}
    
    async def add_assistant_by_session(self, session_string: str) -> Dict[str, Any]:
        """إضافة حساب مساعد بـ session string - يستخرج المعلومات تلقائياً"""
        try:
            session = StringSession(session_string)
            
            # إنشاء عميل مؤقت للتحقق
            temp_client = TelegramClient(
                session=session,
                api_id=self.api_id,
                api_hash=self.api_hash,
                device_model=config.DEVICE_MODEL,
                system_version=config.SYSTEM_VERSION,
                app_version=config.APPLICATION_VERSION,
                lang_code="ar",
                system_lang_code="ar"
            )
            
            await temp_client.connect()
            
            if not await temp_client.is_user_authorized():
                await temp_client.disconnect()
                return {'success': False, 'error': 'الحساب غير مُصرح - Session String غير صالح'}
            
            # الحصول على معلومات المستخدم
            me = await temp_client.get_me()
            
            # التحقق من عدم وجود الحساب مسبقاً
            from ZeMusic.core.database import db
            existing_assistants = await db.get_assistants()
            
            for assistant in existing_assistants:
                if assistant.get('user_id') == me.id:
                    await temp_client.disconnect()
                    return {
                        'success': False, 
                        'error': f'الحساب موجود مسبقاً: @{me.username or me.first_name}'
                    }
            
            # إنشاء معرف جديد للمساعد
            assistant_id = len(self.assistant_clients) + 1
            if existing_assistants:
                assistant_id = max([a.get('id', 0) for a in existing_assistants]) + 1
            
            # إضافة للذاكرة
            self.assistant_clients[assistant_id] = temp_client
            
            # إنشاء اسم تلقائي للمساعد
            auto_name = f"@{me.username}" if me.username else me.first_name or f"User_{me.id}"
            
            # حفظ في قاعدة البيانات مع جميع المعلومات المستخرجة
            try:
                await db.add_assistant(
                    assistant_id=assistant_id,
                    phone=me.phone or "",
                    session_string=session_string,
                    user_id=me.id,
                    username=me.username or "",
                    name=auto_name
                )
                self.logger.info(f"✅ تم حفظ الحساب المساعد في قاعدة البيانات: {assistant_id}")
            except Exception as db_error:
                # في حالة فشل قاعدة البيانات، نحذف من الذاكرة
                if assistant_id in self.assistant_clients:
                    await self.assistant_clients[assistant_id].disconnect()
                    del self.assistant_clients[assistant_id]
                
                self.logger.error(f"❌ خطأ في حفظ المساعد في قاعدة البيانات: {db_error}")
                return {'success': False, 'error': f'خطأ في حفظ البيانات: {str(db_error)}'}
            
            self.logger.info(f"✅ تم إضافة الحساب المساعد: {auto_name} (ID: {me.id})")
            
            return {
                'success': True,
                'assistant_id': assistant_id,
                'connected': True,
                'user_info': {
                    'id': me.id,
                    'username': me.username,
                    'first_name': me.first_name,
                    'last_name': me.last_name,
                    'phone': me.phone,
                    'auto_name': auto_name
                }
            }
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في إضافة المساعد بـ session string: {e}")
            return {
                'success': False,
                'error': f'خطأ تقني: {str(e)}'
            }
    
    async def load_assistants_from_db(self) -> int:
        """تحميل الحسابات المساعدة من قاعدة البيانات"""
        try:
            from ZeMusic.core.database import db
            assistants = await db.get_assistants()
            loaded_count = 0
            
            for assistant in assistants:
                try:
                    if assistant['session_string']:
                        session = StringSession(assistant['session_string'])
                    else:
                        # استخدام معرف المساعد كاسم الجلسة إذا لم يكن هناك رقم هاتف
                        phone_safe = assistant.get('phone', f"assistant_{assistant['id']}")
                        if phone_safe and '+' in phone_safe:
                            phone_safe = phone_safe.replace('+', '')
                        session = f"{self.sessions_dir}/assistant_{phone_safe}"
                    
                    assistant_client = TelegramClient(
                        session=session,
                        api_id=self.api_id,
                        api_hash=self.api_hash,
                        device_model=config.DEVICE_MODEL,
                        system_version=config.SYSTEM_VERSION,
                        app_version=config.APPLICATION_VERSION,
                        lang_code="ar",
                        system_lang_code="ar"
                    )
                    
                    await assistant_client.connect()
                    
                    if await assistant_client.is_user_authorized():
                        self.assistant_clients[assistant['id']] = assistant_client
                        loaded_count += 1
                        
                        me = await assistant_client.get_me()
                        self.logger.info(f"✅ تم تحميل المساعد: @{me.username or 'Unknown'} ({me.id})")
                    else:
                        assistant_name = assistant.get('phone') or assistant.get('name') or f"ID_{assistant['id']}"
                        self.logger.warning(f"⚠️ المساعد {assistant_name} غير مُصرح")
                        
                except Exception as e:
                    assistant_name = assistant.get('phone') or assistant.get('name') or f"ID_{assistant['id']}"
                    self.logger.error(f"❌ خطأ في تحميل المساعد {assistant_name}: {e}")
                    
            self.logger.info(f"📊 تم تحميل {loaded_count} من {len(assistants)} حساب مساعد")
            return loaded_count
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في تحميل المساعدين: {e}")
            return 0
    
    async def get_available_assistant(self, chat_id: int) -> Optional[TelegramClient]:
        """الحصول على حساب مساعد متاح"""
        try:
            # التحقق من وجود مساعدين
            if not self.assistant_clients:
                return None
            
            # اختيار مساعد عشوائي
            import random
            assistant_id = random.choice(list(self.assistant_clients.keys()))
            return self.assistant_clients[assistant_id]
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في اختيار المساعد: {e}")
            return None
    
    async def _setup_bot_handlers(self):
        """إعداد معالجات أحداث البوت"""
        try:
            # معالج الرسائل
            @self.bot_client.on(events.NewMessage)
            async def message_handler(event):
                try:
                    from ZeMusic.core.command_handler import telethon_command_handler
                    await telethon_command_handler.handle_message(event)
                except Exception as e:
                    self.logger.error(f"خطأ في معالج الرسائل: {e}")
            
            # معالج الاستعلامات المضمنة
            @self.bot_client.on(events.CallbackQuery)
            async def callback_handler(event):
                try:
                    from ZeMusic.core.command_handler import telethon_command_handler
                    await telethon_command_handler.handle_callback_query(event)
                except Exception as e:
                    self.logger.error(f"خطأ في معالج الcallbacks: {e}")
            
            # تم نقل معالج البحث إلى handlers_registry.py لتجنب التكرار
            # @self.bot_client.on(events.NewMessage(pattern=r'(?i)(song|/song|بحث|يوت)'))
            # async def download_handler(event):
            #     try:
            #         from ZeMusic.plugins.play.download import smart_download_handler
            #         await smart_download_handler(event)
            #     except Exception as e:
            #         self.logger.error(f"خطأ في معالج التحميل: {e}")
            
            # معالجات أوامر المطور للتخزين الذكي
            @self.bot_client.on(events.NewMessage(pattern=r'/cache_stats'))
            async def cache_stats_handler_event(event):
                try:
                    from ZeMusic.plugins.play.download import cache_stats_handler
                    await cache_stats_handler(event)
                except Exception as e:
                    self.logger.error(f"خطأ في معالج cache_stats: {e}")
            
            @self.bot_client.on(events.NewMessage(pattern=r'/test_cache_channel'))
            async def test_cache_channel_handler_event(event):
                try:
                    from ZeMusic.plugins.play.download import test_cache_channel_handler
                    await test_cache_channel_handler(event)
                except Exception as e:
                    self.logger.error(f"خطأ في معالج test_cache_channel: {e}")
            
            @self.bot_client.on(events.NewMessage(pattern=r'/clear_cache'))
            async def clear_cache_handler_event(event):
                try:
                    from ZeMusic.plugins.play.download import clear_cache_handler
                    await clear_cache_handler(event)
                except Exception as e:
                    self.logger.error(f"خطأ في معالج clear_cache: {e}")
            
            @self.bot_client.on(events.NewMessage(pattern=r'/cache_help'))
            async def cache_help_handler_event(event):
                try:
                    from ZeMusic.plugins.play.download import cache_help_handler
                    await cache_help_handler(event)
                except Exception as e:
                    self.logger.error(f"خطأ في معالج cache_help: {e}")
            
            # معالج أمر /start
            @self.bot_client.on(events.NewMessage(pattern=r'/start'))
            async def start_handler(event):
                try:
                    from ZeMusic.plugins.bot.telethon_start import handle_start_command
                    await handle_start_command(event)
                except Exception as e:
                    self.logger.error(f"خطأ في معالج /start: {e}")
            
            # معالج أمر /help
            @self.bot_client.on(events.NewMessage(pattern=r'/help|/مساعده|المساعده'))
            async def help_handler(event):
                try:
                    from ZeMusic.plugins.bot.telethon_help import handle_help_command
                    await handle_help_command(event)
                except Exception as e:
                    self.logger.error(f"خطأ في معالج /help: {e}")
            
            self.logger.info("🎛️ تم إعداد معالجات أحداث Telethon مع وظائف التحميل والأوامر الأساسية")
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في إعداد المعالجات: {e}")
    
    def get_assistants_count(self) -> int:
        """الحصول على عدد الحسابات المساعدة"""
        return len(self.assistant_clients)
    
    def get_connected_assistants_count(self) -> int:
        """الحصول على عدد الحسابات المتصلة"""
        connected = 0
        for client in self.assistant_clients.values():
            if client.is_connected():
                connected += 1
        return connected
    
    def is_assistant_connected(self, assistant_id: int) -> bool:
        """التحقق من اتصال حساب مساعد محدد"""
        try:
            assistant_client = self.assistant_clients.get(assistant_id)
            return assistant_client and assistant_client.is_connected()
        except:
            return False
    
    def assistant_exists(self, assistant_id: int) -> bool:
        """التحقق من وجود حساب مساعد (متصل أو غير متصل)"""
        return assistant_id in self.assistant_clients
    
    async def get_assistant_info(self, assistant_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على معلومات حساب مساعد"""
        try:
            if assistant_id in self.assistant_clients:
                assistant_client = self.assistant_clients[assistant_id]
                if assistant_client.is_connected():
                    me = await assistant_client.get_me()
                    return {
                        'id': me.id,
                        'username': me.username,
                        'first_name': me.first_name,
                        'phone': me.phone,
                        'connected': True
                    }
                else:
                    return {'connected': False}
            return None
        except Exception as e:
            self.logger.error(f"خطأ في الحصول على معلومات المساعد {assistant_id}: {e}")
            return None
    
    async def remove_assistant(self, assistant_id: int) -> bool:
        """حذف حساب مساعد"""
        try:
            if assistant_id in self.assistant_clients:
                assistant_client = self.assistant_clients[assistant_id]
                if assistant_client:
                    await assistant_client.disconnect()
                del self.assistant_clients[assistant_id]
                self.logger.info(f"✅ تم حذف الحساب المساعد: {assistant_id}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"❌ خطأ في حذف الحساب المساعد {assistant_id}: {e}")
            return False
    
    async def cleanup_idle_assistants(self):
        """تنظيف الحسابات الخاملة"""
        try:
            # مهمة تنظيف بسيطة
            self.logger.info("🧹 تنظيف الحسابات الخاملة")
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في تنظيف المساعدين: {e}")
    
    async def stop_all(self):
        """إيقاف جميع العملاء"""
        try:
            self.logger.info("🛑 إيقاف جميع عملاء Telethon...")
            
            # إيقاف البوت الرئيسي
            if self.bot_client:
                await self.bot_client.disconnect()
                self.logger.info("✅ تم إيقاف البوت الرئيسي")
            
            # إيقاف الحسابات المساعدة
            for assistant_id, client in self.assistant_clients.items():
                try:
                    await client.disconnect()
                    self.logger.info(f"✅ تم إيقاف المساعد {assistant_id}")
                except Exception as e:
                    self.logger.error(f"❌ خطأ في إيقاف المساعد {assistant_id}: {e}")
            
            self.assistant_clients.clear()
            self.logger.info("🎯 تم إيقاف جميع العملاء")
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في إيقاف العملاء: {e}")

# المثيل العام
telethon_manager = TelethonClientManager()