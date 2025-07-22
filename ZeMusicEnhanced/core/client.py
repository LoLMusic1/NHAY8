#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎵 ZeMusic Bot v3.0 - Enhanced Telethon Client
تاريخ الإنشاء: 2025-01-28

عميل Telethon محسن مع إدارة متقدمة للاتصالات والأخطاء
"""

import asyncio
import logging
from typing import Optional, Dict, Any, List
from telethon import TelegramClient, events
from telethon.errors import (
    SessionPasswordNeededError, AuthKeyUnregisteredError,
    PhoneNumberInvalidError, FloodWaitError, RPCError
)
from telethon.sessions import StringSession

from ..config import config

logger = logging.getLogger(__name__)

class TelethonClient:
    """عميل Telethon محسن مع إدارة ذكية للاتصالات"""
    
    def __init__(self):
        """تهيئة العميل"""
        self.client: Optional[TelegramClient] = None
        self.is_connected = False
        self.is_authorized = False
        self.bot_info: Optional[Dict[str, Any]] = None
        self.connection_attempts = 0
        self.max_connection_attempts = 5
        
    async def initialize(self) -> bool:
        """تهيئة وتشغيل العميل"""
        try:
            logger.info("🚀 بدء تهيئة عميل Telethon...")
            
            # إنشاء العميل
            self.client = TelegramClient(
                session="bot_session",
                api_id=config.telegram.api_id,
                api_hash=config.telegram.api_hash,
                device_model=config.telegram.device_model,
                system_version=config.telegram.system_version,
                app_version=config.telegram.app_version,
                lang_code="ar",
                system_lang_code="ar"
            )
            
            # الاتصال بـ Telegram
            if not await self._connect_with_retry():
                return False
            
            # تسجيل الدخول كبوت
            if not await self._authorize_bot():
                return False
            
            # الحصول على معلومات البوت
            await self._get_bot_info()
            
            # تسجيل معالجات الأحداث
            self._register_handlers()
            
            logger.info("✅ تم تهيئة عميل Telethon بنجاح")
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في تهيئة العميل: {e}")
            return False
    
    async def _connect_with_retry(self) -> bool:
        """الاتصال مع إعادة المحاولة"""
        for attempt in range(1, self.max_connection_attempts + 1):
            try:
                logger.info(f"🔄 محاولة الاتصال {attempt}/{self.max_connection_attempts}")
                
                await self.client.connect()
                
                if self.client.is_connected():
                    self.is_connected = True
                    logger.info("✅ تم الاتصال بـ Telegram بنجاح")
                    return True
                    
            except FloodWaitError as e:
                logger.warning(f"⏳ انتظار {e.seconds} ثانية بسبب حد المعدل")
                await asyncio.sleep(e.seconds)
                
            except Exception as e:
                logger.error(f"❌ فشل في الاتصال (محاولة {attempt}): {e}")
                
                if attempt < self.max_connection_attempts:
                    wait_time = min(2 ** attempt, 30)  # Exponential backoff
                    logger.info(f"⏳ انتظار {wait_time} ثانية قبل المحاولة التالية")
                    await asyncio.sleep(wait_time)
        
        logger.error("❌ فشل في جميع محاولات الاتصال")
        return False
    
    async def _authorize_bot(self) -> bool:
        """تسجيل دخول البوت"""
        try:
            logger.info("🔐 تسجيل دخول البوت...")
            
            await self.client.start(bot_token=config.telegram.bot_token)
            
            if await self.client.is_user_authorized():
                self.is_authorized = True
                logger.info("✅ تم تسجيل دخول البوت بنجاح")
                return True
            else:
                logger.error("❌ فشل في تسجيل دخول البوت")
                return False
                
        except AuthKeyUnregisteredError:
            logger.error("❌ مفتاح التفويض غير مسجل - يرجى إعادة إنشاء الجلسة")
            return False
            
        except Exception as e:
            logger.error(f"❌ خطأ في تسجيل دخول البوت: {e}")
            return False
    
    async def _get_bot_info(self):
        """الحصول على معلومات البوت"""
        try:
            me = await self.client.get_me()
            self.bot_info = {
                'id': me.id,
                'username': me.username,
                'first_name': me.first_name,
                'is_bot': me.bot,
                'is_verified': me.verified,
                'is_premium': getattr(me, 'premium', False)
            }
            
            logger.info(f"🤖 معلومات البوت: @{me.username} (ID: {me.id})")
            
        except Exception as e:
            logger.error(f"❌ فشل في الحصول على معلومات البوت: {e}")
    
    def _register_handlers(self):
        """تسجيل معالجات الأحداث الأساسية"""
        
        @self.client.on(events.NewMessage)
        async def message_handler(event):
            """معالج الرسائل الأساسي"""
            try:
                # سيتم توسيعه في المعالجات المتخصصة
                pass
            except Exception as e:
                logger.error(f"❌ خطأ في معالج الرسائل: {e}")
        
        @self.client.on(events.CallbackQuery)
        async def callback_handler(event):
            """معالج الأزرار التفاعلية"""
            try:
                # سيتم توسيعه في المعالجات المتخصصة
                pass
            except Exception as e:
                logger.error(f"❌ خطأ في معالج الأزرار: {e}")
        
        logger.info("📝 تم تسجيل معالجات الأحداث الأساسية")
    
    async def send_message(self, chat_id: int, text: str, **kwargs) -> Optional[Any]:
        """إرسال رسالة مع معالجة الأخطاء"""
        try:
            return await self.client.send_message(chat_id, text, **kwargs)
            
        except FloodWaitError as e:
            logger.warning(f"⏳ انتظار {e.seconds} ثانية بسبب حد المعدل")
            await asyncio.sleep(e.seconds)
            return await self.client.send_message(chat_id, text, **kwargs)
            
        except Exception as e:
            logger.error(f"❌ فشل في إرسال الرسالة: {e}")
            return None
    
    async def edit_message(self, message, text: str, **kwargs) -> bool:
        """تعديل رسالة مع معالجة الأخطاء"""
        try:
            await message.edit(text, **kwargs)
            return True
            
        except FloodWaitError as e:
            logger.warning(f"⏳ انتظار {e.seconds} ثانية بسبب حد المعدل")
            await asyncio.sleep(e.seconds)
            await message.edit(text, **kwargs)
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في تعديل الرسالة: {e}")
            return False
    
    async def get_chat_info(self, chat_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على معلومات المحادثة"""
        try:
            chat = await self.client.get_entity(chat_id)
            return {
                'id': chat.id,
                'title': getattr(chat, 'title', ''),
                'username': getattr(chat, 'username', ''),
                'type': 'channel' if hasattr(chat, 'broadcast') else 'group',
                'members_count': getattr(chat, 'participants_count', 0)
            }
            
        except Exception as e:
            logger.error(f"❌ فشل في الحصول على معلومات المحادثة {chat_id}: {e}")
            return None
    
    async def get_user_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """الحصول على معلومات المستخدم"""
        try:
            user = await self.client.get_entity(user_id)
            return {
                'id': user.id,
                'first_name': getattr(user, 'first_name', ''),
                'last_name': getattr(user, 'last_name', ''),
                'username': getattr(user, 'username', ''),
                'phone': getattr(user, 'phone', ''),
                'is_bot': getattr(user, 'bot', False),
                'is_verified': getattr(user, 'verified', False),
                'is_premium': getattr(user, 'premium', False)
            }
            
        except Exception as e:
            logger.error(f"❌ فشل في الحصول على معلومات المستخدم {user_id}: {e}")
            return None
    
    async def check_admin_permissions(self, chat_id: int, user_id: int) -> Dict[str, bool]:
        """فحص صلاحيات المشرف"""
        try:
            participant = await self.client.get_permissions(chat_id, user_id)
            
            return {
                'is_admin': participant.is_admin,
                'is_creator': participant.is_creator,
                'can_delete_messages': participant.delete_messages,
                'can_ban_users': participant.ban_users,
                'can_invite_users': participant.invite_users,
                'can_pin_messages': participant.pin_messages,
                'can_manage_call': participant.manage_call,
                'can_change_info': participant.change_info
            }
            
        except Exception as e:
            logger.error(f"❌ فشل في فحص صلاحيات المشرف: {e}")
            return {key: False for key in [
                'is_admin', 'is_creator', 'can_delete_messages', 
                'can_ban_users', 'can_invite_users', 'can_pin_messages',
                'can_manage_call', 'can_change_info'
            ]}
    
    async def join_chat(self, chat_link: str) -> bool:
        """الانضمام لمحادثة"""
        try:
            await self.client.join_chat(chat_link)
            logger.info(f"✅ تم الانضمام للمحادثة: {chat_link}")
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في الانضمام للمحادثة {chat_link}: {e}")
            return False
    
    async def leave_chat(self, chat_id: int) -> bool:
        """مغادرة المحادثة"""
        try:
            await self.client.leave_chat(chat_id)
            logger.info(f"✅ تم مغادرة المحادثة: {chat_id}")
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في مغادرة المحادثة {chat_id}: {e}")
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """فحص صحة الاتصال"""
        try:
            if not self.client or not self.is_connected:
                return {
                    'status': 'disconnected',
                    'connected': False,
                    'authorized': False,
                    'ping': None
                }
            
            # قياس ping
            import time
            start_time = time.time()
            await self.client.get_me()
            ping = round((time.time() - start_time) * 1000, 2)
            
            return {
                'status': 'healthy',
                'connected': self.is_connected,
                'authorized': self.is_authorized,
                'ping': f"{ping}ms",
                'bot_info': self.bot_info
            }
            
        except Exception as e:
            logger.error(f"❌ فشل في فحص الصحة: {e}")
            return {
                'status': 'error',
                'connected': False,
                'authorized': False,
                'ping': None,
                'error': str(e)
            }
    
    async def reconnect(self) -> bool:
        """إعادة الاتصال"""
        try:
            logger.info("🔄 محاولة إعادة الاتصال...")
            
            if self.client:
                try:
                    await self.client.disconnect()
                except:
                    pass
            
            # إعادة تعيين الحالة
            self.is_connected = False
            self.is_authorized = False
            self.connection_attempts = 0
            
            # إعادة التهيئة
            return await self.initialize()
            
        except Exception as e:
            logger.error(f"❌ فشل في إعادة الاتصال: {e}")
            return False
    
    async def run_until_disconnected(self):
        """تشغيل العميل حتى الانقطاع"""
        if self.client:
            await self.client.run_until_disconnected()
    
    async def disconnect(self):
        """قطع الاتصال"""
        try:
            if self.client and self.is_connected:
                await self.client.disconnect()
                self.is_connected = False
                self.is_authorized = False
                logger.info("✅ تم قطع الاتصال بنجاح")
                
        except Exception as e:
            logger.error(f"❌ خطأ في قطع الاتصال: {e}")
    
    def __del__(self):
        """تنظيف الموارد"""
        try:
            if hasattr(self, 'client') and self.client and self.is_connected:
                asyncio.create_task(self.disconnect())
        except:
            pass