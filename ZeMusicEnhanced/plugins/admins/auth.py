#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎵 ZeMusic Bot v3.0 - Auth Management System
تاريخ الإنشاء: 2025-01-28

نظام إدارة التراخيص والمستخدمين المصرح لهم
"""

import asyncio
import logging
from typing import List, Dict, Optional, Any
from telethon import events, Button
from telethon.tl.types import User

from ...config import config
from ...core import TelethonClient, DatabaseManager
from ...utils.decorators import admin_check, maintenance_check
from ...utils.database import get_authuser_names

logger = logging.getLogger(__name__)

class AuthManagementSystem:
    """نظام إدارة التراخيص المتقدم"""
    
    def __init__(self, client: TelethonClient, db: DatabaseManager):
        """تهيئة نظام إدارة التراخيص"""
        self.client = client
        self.db = db
        
        # قاعدة بيانات المستخدمين المصرح لهم
        self.auth_users: Dict[int, List[int]] = {}  # {chat_id: [user_ids]}
        
        # إحصائيات التراخيص
        self.auth_stats = {
            'total_auth_users': 0,
            'auth_operations': 0,
            'successful_auths': 0,
            'failed_auths': 0
        }
        
    async def initialize(self) -> bool:
        """تهيئة نظام التراخيص"""
        try:
            logger.info("🔐 تهيئة نظام إدارة التراخيص...")
            
            # تحميل المستخدمين المصرح لهم من قاعدة البيانات
            await self._load_auth_users()
            
            # تسجيل معالجات الأحداث
            await self._register_auth_handlers()
            
            logger.info("✅ تم تهيئة نظام إدارة التراخيص بنجاح")
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في تهيئة نظام التراخيص: {e}")
            return False
    
    async def _load_auth_users(self):
        """تحميل المستخدمين المصرح لهم من قاعدة البيانات"""
        try:
            # سيتم تطبيق هذا مع قاعدة البيانات الفعلية
            # auth_data = await self.db.get_all_auth_users()
            # self.auth_users = auth_data
            
            logger.info(f"📚 تم تحميل {len(self.auth_users)} مجموعة مع مستخدمين مصرح لهم")
            
        except Exception as e:
            logger.error(f"❌ فشل في تحميل المستخدمين المصرح لهم: {e}")
    
    async def _register_auth_handlers(self):
        """تسجيل معالجات أحداث التراخيص"""
        try:
            # معالج أمر إضافة مستخدم مصرح له
            @self.client.client.on(events.NewMessage(pattern=r'^[!/.](?:auth|ترخيص)'))
            @maintenance_check
            @admin_check
            async def handle_auth_command(event):
                await self._handle_auth_command(event)
            
            # معالج أمر إزالة ترخيص
            @self.client.client.on(events.NewMessage(pattern=r'^[!/.](?:unauth|إلغاء ترخيص)'))
            @maintenance_check
            @admin_check
            async def handle_unauth_command(event):
                await self._handle_unauth_command(event)
            
            # معالج عرض المستخدمين المصرح لهم
            @self.client.client.on(events.NewMessage(pattern=r'^[!/.](?:authusers|المصرح لهم)'))
            @maintenance_check
            @admin_check
            async def handle_authusers_command(event):
                await self._handle_authusers_command(event)
            
            # معالج استعلامات التراخيص
            @self.client.client.on(events.CallbackQuery(pattern=b'auth_'))
            async def handle_auth_callback(event):
                await self._handle_auth_callback(event)
            
            logger.info("📝 تم تسجيل معالجات التراخيص")
            
        except Exception as e:
            logger.error(f"❌ فشل في تسجيل معالجات التراخيص: {e}")
    
    async def _handle_auth_command(self, event):
        """معالجة أمر إضافة ترخيص"""
        try:
            chat_id = event.chat_id
            args = event.message.text.split()[1:] if len(event.message.text.split()) > 1 else []
            
            if not args:
                help_text = (
                    "🔐 **نظام إدارة التراخيص**\n\n"
                    "⚙️ **الاستخدام:**\n"
                    "• `/auth` - عرض هذه المساعدة\n"
                    "• `/auth @username` - إضافة مستخدم للتراخيص\n"
                    "• `/auth reply` - ترخيص المستخدم المرد عليه\n"
                    "• `/authusers` - عرض المستخدمين المصرح لهم\n"
                    "• `/unauth @username` - إلغاء ترخيص مستخدم\n\n"
                    "🔸 **المستخدمون المصرح لهم يمكنهم:**\n"
                    "• تشغيل الموسيقى بدون قيود\n"
                    "• تخطي القائمة\n"
                    "• التحكم في التشغيل\n"
                    "• إدارة قائمة الانتظار\n\n"
                    "💡 **ملاحظة:** المشرفون لديهم تراخيص تلقائية"
                )
                
                keyboard = [
                    [
                        Button.inline("➕ إضافة مستخدم", b"auth_add_user"),
                        Button.inline("➖ إزالة مستخدم", b"auth_remove_user")
                    ],
                    [
                        Button.inline("📋 عرض المصرح لهم", b"auth_list_users"),
                        Button.inline("🔄 تحديث", b"auth_refresh")
                    ],
                    [
                        Button.inline("📊 الإحصائيات", b"auth_stats"),
                        Button.inline("⚙️ الإعدادات", b"auth_settings")
                    ]
                ]
                
                await event.reply(help_text, buttons=keyboard)
                return
            
            # معالجة الرد على رسالة
            if event.is_reply:
                replied_message = await event.get_reply_message()
                if replied_message and replied_message.sender:
                    target_user = replied_message.sender
                    await self._add_auth_user(event, target_user, chat_id)
                    return
            
            # معالجة المعرف أو اليوزر
            identifier = args[0]
            target_user = await self._get_user_from_identifier(identifier)
            
            if target_user:
                await self._add_auth_user(event, target_user, chat_id)
            else:
                await event.reply("❌ لا يمكن العثور على المستخدم المحدد")
                
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة أمر الترخيص: {e}")
            await event.reply("❌ حدث خطأ في معالجة الأمر")
    
    async def _handle_unauth_command(self, event):
        """معالجة أمر إلغاء الترخيص"""
        try:
            chat_id = event.chat_id
            args = event.message.text.split()[1:] if len(event.message.text.split()) > 1 else []
            
            if not args:
                await event.reply(
                    "❌ **يرجى تحديد المستخدم**\n\n"
                    "💡 **الاستخدام:**\n"
                    "• `/unauth @username`\n"
                    "• `/unauth reply` (رد على رسالة المستخدم)\n"
                    "• `/unauth user_id`"
                )
                return
            
            # معالجة الرد على رسالة
            if event.is_reply:
                replied_message = await event.get_reply_message()
                if replied_message and replied_message.sender:
                    target_user = replied_message.sender
                    await self._remove_auth_user(event, target_user, chat_id)
                    return
            
            # معالجة المعرف أو اليوزر
            identifier = args[0]
            target_user = await self._get_user_from_identifier(identifier)
            
            if target_user:
                await self._remove_auth_user(event, target_user, chat_id)
            else:
                await event.reply("❌ لا يمكن العثور على المستخدم المحدد")
                
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة أمر إلغاء الترخيص: {e}")
            await event.reply("❌ حدث خطأ في معالجة الأمر")
    
    async def _handle_authusers_command(self, event):
        """معالجة أمر عرض المستخدمين المصرح لهم"""
        try:
            chat_id = event.chat_id
            
            if chat_id not in self.auth_users or not self.auth_users[chat_id]:
                await event.reply(
                    "📭 **لا يوجد مستخدمين مصرح لهم**\n\n"
                    "💡 **لإضافة مستخدم:** `/auth @username`"
                )
                return
            
            auth_list = self.auth_users[chat_id]
            message = f"🔐 **المستخدمون المصرح لهم ({len(auth_list)})**\n\n"
            
            for i, user_id in enumerate(auth_list[:20], 1):  # أول 20 مستخدم
                try:
                    user = await self.client.client.get_entity(user_id)
                    user_name = user.first_name or "مستخدم"
                    username = getattr(user, 'username', None)
                    
                    message += f"**{i}.** {user_name}"
                    if username:
                        message += f" (@{username})"
                    message += f" - `{user_id}`\n"
                    
                except Exception:
                    message += f"**{i}.** مستخدم غير متاح - `{user_id}`\n"
            
            if len(auth_list) > 20:
                message += f"\n... و {len(auth_list) - 20} مستخدم آخر"
            
            # إضافة إحصائيات
            message += (
                f"\n\n📊 **الإحصائيات:**\n"
                f"• إجمالي المصرح لهم: {len(auth_list)}\n"
                f"• عمليات الترخيص: {self.auth_stats['auth_operations']:,}\n"
                f"• الناجحة: {self.auth_stats['successful_auths']:,}\n"
                f"• الفاشلة: {self.auth_stats['failed_auths']:,}"
            )
            
            keyboard = [
                [
                    Button.inline("➕ إضافة", b"auth_add_user"),
                    Button.inline("➖ إزالة", b"auth_remove_user")
                ],
                [
                    Button.inline("🔄 تحديث", b"auth_refresh"),
                    Button.inline("🗑️ مسح الكل", b"auth_clear_all")
                ]
            ]
            
            await event.reply(message, buttons=keyboard)
            
        except Exception as e:
            logger.error(f"❌ خطأ في عرض المستخدمين المصرح لهم: {e}")
            await event.reply("❌ حدث خطأ في جلب قائمة المستخدمين")
    
    async def _add_auth_user(self, event, target_user: User, chat_id: int):
        """إضافة مستخدم للتراخيص"""
        try:
            user_id = target_user.id
            user_name = target_user.first_name or "مستخدم"
            username = getattr(target_user, 'username', None)
            
            # التحقق من عدم وجود المستخدم مسبقاً
            if chat_id in self.auth_users and user_id in self.auth_users[chat_id]:
                await event.reply(f"⚠️ **{user_name} مصرح له مسبقاً**")
                return
            
            # إضافة المستخدم
            if chat_id not in self.auth_users:
                self.auth_users[chat_id] = []
            
            self.auth_users[chat_id].append(user_id)
            
            # حفظ في قاعدة البيانات
            await self._save_auth_users(chat_id)
            
            # تحديث الإحصائيات
            self.auth_stats['auth_operations'] += 1
            self.auth_stats['successful_auths'] += 1
            self.auth_stats['total_auth_users'] = sum(len(users) for users in self.auth_users.values())
            
            # رسالة التأكيد
            message = f"✅ **تم ترخيص المستخدم بنجاح**\n\n"
            message += f"👤 **المستخدم:** {user_name}"
            if username:
                message += f" (@{username})"
            message += f"\n🆔 **المعرف:** `{user_id}`"
            message += f"\n📊 **إجمالي المصرح لهم:** {len(self.auth_users[chat_id])}"
            message += f"\n\n🎵 **يمكنه الآن استخدام أوامر الموسيقى بحرية**"
            
            keyboard = [
                [
                    Button.inline("📋 عرض المصرح لهم", b"auth_list_users"),
                    Button.inline("➕ إضافة آخر", b"auth_add_user")
                ]
            ]
            
            await event.reply(message, buttons=keyboard)
            
        except Exception as e:
            logger.error(f"❌ خطأ في إضافة المستخدم للتراخيص: {e}")
            self.auth_stats['failed_auths'] += 1
            await event.reply("❌ حدث خطأ في إضافة المستخدم")
    
    async def _remove_auth_user(self, event, target_user: User, chat_id: int):
        """إزالة مستخدم من التراخيص"""
        try:
            user_id = target_user.id
            user_name = target_user.first_name or "مستخدم"
            username = getattr(target_user, 'username', None)
            
            # التحقق من وجود المستخدم
            if chat_id not in self.auth_users or user_id not in self.auth_users[chat_id]:
                await event.reply(f"⚠️ **{user_name} غير مصرح له أصلاً**")
                return
            
            # إزالة المستخدم
            self.auth_users[chat_id].remove(user_id)
            
            # إزالة المجموعة إذا لم تعد تحتوي على مستخدمين
            if not self.auth_users[chat_id]:
                del self.auth_users[chat_id]
            
            # حفظ في قاعدة البيانات
            await self._save_auth_users(chat_id)
            
            # تحديث الإحصائيات
            self.auth_stats['auth_operations'] += 1
            self.auth_stats['total_auth_users'] = sum(len(users) for users in self.auth_users.values())
            
            # رسالة التأكيد
            message = f"✅ **تم إلغاء ترخيص المستخدم**\n\n"
            message += f"👤 **المستخدم:** {user_name}"
            if username:
                message += f" (@{username})"
            message += f"\n🆔 **المعرف:** `{user_id}`"
            message += f"\n📊 **المتبقي من المصرح لهم:** {len(self.auth_users.get(chat_id, []))}"
            message += f"\n\n🚫 **لن يتمكن من استخدام أوامر الموسيقى بعد الآن**"
            
            await event.reply(message)
            
        except Exception as e:
            logger.error(f"❌ خطأ في إزالة المستخدم من التراخيص: {e}")
            await event.reply("❌ حدث خطأ في إزالة المستخدم")
    
    async def _get_user_from_identifier(self, identifier: str) -> Optional[User]:
        """الحصول على المستخدم من المعرف أو اليوزر"""
        try:
            if identifier.startswith('@'):
                # يوزر نيم
                return await self.client.client.get_entity(identifier)
            elif identifier.isdigit():
                # معرف رقمي
                return await self.client.client.get_entity(int(identifier))
            else:
                return None
                
        except Exception as e:
            logger.error(f"خطأ في جلب المستخدم: {e}")
            return None
    
    async def _save_auth_users(self, chat_id: int):
        """حفظ المستخدمين المصرح لهم في قاعدة البيانات"""
        try:
            # سيتم تطبيق هذا مع قاعدة البيانات الفعلية
            # auth_users = self.auth_users.get(chat_id, [])
            # await self.db.save_auth_users(chat_id, auth_users)
            
            logger.info(f"💾 تم حفظ تراخيص المجموعة {chat_id}")
            
        except Exception as e:
            logger.error(f"❌ فشل في حفظ التراخيص: {e}")
    
    async def _handle_auth_callback(self, event):
        """معالجة استعلامات التراخيص"""
        try:
            data = event.data.decode('utf-8')
            
            if data == "auth_add_user":
                await event.edit(
                    "➕ **إضافة مستخدم مصرح له**\n\n"
                    "📝 **استخدم أحد الطرق التالية:**\n"
                    "• `/auth @username`\n"
                    "• `/auth user_id`\n"
                    "• رد على رسالة المستخدم واكتب `/auth`"
                )
            elif data == "auth_remove_user":
                await event.edit(
                    "➖ **إزالة مستخدم من التراخيص**\n\n"
                    "📝 **استخدم أحد الطرق التالية:**\n"
                    "• `/unauth @username`\n"
                    "• `/unauth user_id`\n"
                    "• رد على رسالة المستخدم واكتب `/unauth`"
                )
            elif data == "auth_list_users":
                await self._handle_authusers_command(event)
            elif data == "auth_refresh":
                await self._load_auth_users()
                await event.answer("🔄 تم تحديث قائمة المستخدمين المصرح لهم")
            elif data == "auth_stats":
                await self._show_auth_statistics(event)
            elif data == "auth_clear_all":
                await self._confirm_clear_all_auth(event)
                
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة استعلام التراخيص: {e}")
            await event.answer("❌ حدث خطأ في معالجة الطلب", alert=True)
    
    async def _show_auth_statistics(self, event):
        """عرض إحصائيات التراخيص"""
        try:
            message = (
                f"📊 **إحصائيات نظام التراخيص**\n\n"
                f"👥 **إجمالي المستخدمين المصرح لهم:** {self.auth_stats['total_auth_users']:,}\n"
                f"🏢 **المجموعات النشطة:** {len(self.auth_users)}\n"
                f"⚙️ **إجمالي العمليات:** {self.auth_stats['auth_operations']:,}\n"
                f"✅ **العمليات الناجحة:** {self.auth_stats['successful_auths']:,}\n"
                f"❌ **العمليات الفاشلة:** {self.auth_stats['failed_auths']:,}\n\n"
                f"📈 **معدل النجاح:** {((self.auth_stats['successful_auths'] / max(self.auth_stats['auth_operations'], 1)) * 100):.1f}%\n"
                f"📊 **متوسط المستخدمين/مجموعة:** {(self.auth_stats['total_auth_users'] / max(len(self.auth_users), 1)):.1f}"
            )
            
            await event.edit(message)
            
        except Exception as e:
            logger.error(f"❌ خطأ في عرض إحصائيات التراخيص: {e}")
            await event.answer("❌ حدث خطأ في جلب الإحصائيات", alert=True)
    
    # وظائف عامة للاستخدام من البلاجينز الأخرى
    async def is_auth_user(self, chat_id: int, user_id: int) -> bool:
        """التحقق من كون المستخدم مصرح له"""
        try:
            return chat_id in self.auth_users and user_id in self.auth_users[chat_id]
        except Exception:
            return False
    
    async def get_auth_users_list(self, chat_id: int) -> List[int]:
        """الحصول على قائمة المستخدمين المصرح لهم"""
        try:
            return self.auth_users.get(chat_id, [])
        except Exception:
            return []
    
    async def get_auth_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات التراخيص"""
        return self.auth_stats.copy()

# إنشاء مثيل عام لنظام التراخيص
auth_system = None  # سيتم تهيئته في الملف الرئيسي

# وظائف للتوافق مع الكود القديم
async def add_auth_user(chat_id: int, user_id: int) -> bool:
    """إضافة مستخدم للتراخيص (للتوافق)"""
    if auth_system:
        if chat_id not in auth_system.auth_users:
            auth_system.auth_users[chat_id] = []
        if user_id not in auth_system.auth_users[chat_id]:
            auth_system.auth_users[chat_id].append(user_id)
            await auth_system._save_auth_users(chat_id)
            return True
    return False

async def remove_auth_user(chat_id: int, user_id: int) -> bool:
    """إزالة مستخدم من التراخيص (للتوافق)"""
    if auth_system and chat_id in auth_system.auth_users:
        if user_id in auth_system.auth_users[chat_id]:
            auth_system.auth_users[chat_id].remove(user_id)
            await auth_system._save_auth_users(chat_id)
            return True
    return False

async def get_auth_users(chat_id: int) -> List[int]:
    """الحصول على المستخدمين المصرح لهم (للتوافق)"""
    if auth_system:
        return await auth_system.get_auth_users_list(chat_id)
    return []