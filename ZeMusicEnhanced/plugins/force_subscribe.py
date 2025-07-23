#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎵 ZeMusic Bot v3.0 - Force Subscribe System
تاريخ الإنشاء: 2025-01-28

نظام الاشتراك الإجباري المتقدم
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Set
from telethon import events, Button
from telethon.tl.types import Channel, Chat, User
from telethon.errors import UserNotParticipant, ChatAdminRequired, ChannelPrivateError
from datetime import datetime, timedelta

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import config
from ..core import TelethonClient, DatabaseManager, SecurityManager

logger = logging.getLogger(__name__)

class ForceSubscribePlugin:
    """بلاجين الاشتراك الإجباري المتقدم"""
    
    def __init__(self, client: TelethonClient, db: DatabaseManager, security_manager: SecurityManager):
        """تهيئة بلاجين الاشتراك الإجباري"""
        self.client = client
        self.db = db
        self.security_manager = security_manager
        
        # قنوات الاشتراك الإجباري
        self.force_channels: Dict[int, List[int]] = {}  # {group_id: [channel_ids]}
        
        # المستخدمون المستثنون من الاشتراك الإجباري
        self.exempted_users: Set[int] = set()
        
        # إحصائيات الاشتراك الإجباري
        self.fsub_stats = {
            'total_checks': 0,
            'blocked_users': 0,
            'successful_subscriptions': 0,
            'active_force_channels': 0
        }
        
        # ذاكرة التخزين المؤقت للفحص
        self.subscription_cache: Dict[str, Dict[str, Any]] = {}
        
    async def initialize(self) -> bool:
        """تهيئة بلاجين الاشتراك الإجباري"""
        try:
            logger.info("🔐 تهيئة بلاجين الاشتراك الإجباري...")
            
            # تحميل إعدادات الاشتراك الإجباري
            await self._load_force_subscribe_settings()
            
            # تسجيل معالجات الأحداث
            await self._register_fsub_handlers()
            
            # بدء مهام الصيانة
            asyncio.create_task(self._maintenance_tasks())
            
            logger.info("✅ تم تهيئة بلاجين الاشتراك الإجباري بنجاح")
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في تهيئة بلاجين الاشتراك الإجباري: {e}")
            return False
    
    async def _load_force_subscribe_settings(self):
        """تحميل إعدادات الاشتراك الإجباري"""
        try:
            # تحميل من قاعدة البيانات
            # force_settings = await self.db.get_all_force_subscribe_settings()
            # self.force_channels = force_settings
            
            # إضافة المستخدمين المستثنين (المطورين، المالكين)
            self.exempted_users.update(config.owner.sudo_users)
            self.exempted_users.add(config.owner.owner_id)
            
            logger.info(f"📚 تم تحميل إعدادات الاشتراك الإجباري لـ {len(self.force_channels)} مجموعة")
            
        except Exception as e:
            logger.error(f"❌ فشل في تحميل إعدادات الاشتراك الإجباري: {e}")
    
    async def _register_fsub_handlers(self):
        """تسجيل معالجات أحداث الاشتراك الإجباري"""
        try:
            # معالج فحص الاشتراك للرسائل الواردة
            @self.client.client.on(events.NewMessage(incoming=True))
            async def check_subscription(event):
                await self._check_user_subscription(event)
            
            # معالج أمر تعيين الاشتراك الإجباري
            @self.client.client.on(events.NewMessage(pattern=r'^[!/.](?:fsub|اشتراك اجباري)'))
            async def handle_fsub_command(event):
                await self._handle_fsub_command(event)
            
            # معالج عرض إعدادات الاشتراك الإجباري
            @self.client.client.on(events.NewMessage(pattern=r'^[!/.](?:fsublist|قائمة الاشتراك)'))
            async def handle_fsub_list(event):
                await self._handle_fsub_list_command(event)
            
            # معالج استعلامات الاشتراك الإجباري
            @self.client.client.on(events.CallbackQuery(pattern=b'fsub_'))
            async def handle_fsub_callback(event):
                await self._handle_fsub_callback(event)
            
            logger.info("📝 تم تسجيل معالجات الاشتراك الإجباري")
            
        except Exception as e:
            logger.error(f"❌ فشل في تسجيل معالجات الاشتراك الإجباري: {e}")
    
    async def _check_user_subscription(self, event):
        """فحص اشتراك المستخدم"""
        try:
            # تجاهل الرسائل من المجموعات أو القنوات
            if not event.is_private:
                return
            
            user_id = event.sender_id
            
            # تجاهل المستخدمين المستثنين
            if user_id in self.exempted_users:
                return
            
            # تجاهل البوتات
            sender = await event.get_sender()
            if getattr(sender, 'bot', False):
                return
            
            # التحقق من وجود قنوات اشتراك إجباري
            if not self.force_channels:
                return
            
            # فحص الاشتراك
            subscription_result = await self._verify_user_subscriptions(user_id)
            
            if not subscription_result['is_subscribed']:
                await self._handle_unsubscribed_user(event, subscription_result)
            
        except Exception as e:
            logger.error(f"❌ خطأ في فحص اشتراك المستخدم: {e}")
    
    async def _verify_user_subscriptions(self, user_id: int) -> Dict[str, Any]:
        """التحقق من اشتراكات المستخدم"""
        try:
            # التحقق من الذاكرة المؤقتة
            cache_key = f"user_sub_{user_id}"
            if cache_key in self.subscription_cache:
                cache_data = self.subscription_cache[cache_key]
                if datetime.now() - cache_data['timestamp'] < timedelta(minutes=5):
                    return cache_data['result']
            
            # قنوات غير مشترك فيها
            unsubscribed_channels = []
            
            # فحص جميع القنوات المطلوبة
            for group_id, channel_ids in self.force_channels.items():
                for channel_id in channel_ids:
                    try:
                        # التحقق من الاشتراك
                        participant = await self.client.client.get_permissions(channel_id, user_id)
                        if not participant.is_banned and participant.is_creator is False and not hasattr(participant, 'left'):
                            continue  # مشترك
                        else:
                            unsubscribed_channels.append(channel_id)
                    except UserNotParticipant:
                        unsubscribed_channels.append(channel_id)
                    except Exception:
                        # في حالة عدم القدرة على الوصول للقناة
                        continue
            
            # تحديث الإحصائيات
            self.fsub_stats['total_checks'] += 1
            
            result = {
                'is_subscribed': len(unsubscribed_channels) == 0,
                'unsubscribed_channels': unsubscribed_channels,
                'total_required': sum(len(channels) for channels in self.force_channels.values())
            }
            
            # حفظ في الذاكرة المؤقتة
            self.subscription_cache[cache_key] = {
                'result': result,
                'timestamp': datetime.now()
            }
            
            return result
            
        except Exception as e:
            logger.error(f"❌ خطأ في التحقق من الاشتراكات: {e}")
            return {'is_subscribed': True, 'unsubscribed_channels': [], 'total_required': 0}
    
    async def _handle_unsubscribed_user(self, event, subscription_result: Dict[str, Any]):
        """معالجة المستخدم غير المشترك"""
        try:
            user = await event.get_sender()
            unsubscribed_channels = subscription_result['unsubscribed_channels']
            
            # إنشاء قائمة القنوات المطلوبة
            channels_info = []
            keyboard = []
            
            for channel_id in unsubscribed_channels[:5]:  # أقصى 5 قنوات
                try:
                    channel = await self.client.client.get_entity(channel_id)
                    
                    # معلومات القناة
                    channel_info = {
                        'id': channel_id,
                        'title': channel.title,
                        'username': getattr(channel, 'username', None),
                        'subscribers': getattr(channel, 'participants_count', 0)
                    }
                    channels_info.append(channel_info)
                    
                    # زر الاشتراك
                    if channel_info['username']:
                        button_text = f"📺 {channel_info['title']}"
                        button_url = f"https://t.me/{channel_info['username']}"
                        keyboard.append([Button.url(button_text, button_url)])
                    
                except Exception:
                    continue
            
            # زر التحقق من الاشتراك
            keyboard.append([Button.inline("✅ تم الاشتراك - تحقق", b"fsub_check_subscription")])
            
            # رسالة الاشتراك الإجباري
            message = self._create_subscription_message(user, channels_info)
            
            # إرسال الرسالة
            await event.reply(message, buttons=keyboard, link_preview=False)
            
            # تحديث الإحصائيات
            self.fsub_stats['blocked_users'] += 1
            
            # إيقاف معالجة الرسالة
            raise events.StopPropagation
            
        except events.StopPropagation:
            raise
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة المستخدم غير المشترك: {e}")
    
    def _create_subscription_message(self, user: User, channels_info: List[Dict[str, Any]]) -> str:
        """إنشاء رسالة الاشتراك الإجباري"""
        try:
            user_name = user.first_name or "المستخدم"
            
            message = (
                f"🔐 **مرحباً {user_name}**\n\n"
                f"📢 **للاستمرار في استخدام البوت، يجب عليك الاشتراك في القنوات التالية:**\n\n"
            )
            
            for i, channel in enumerate(channels_info, 1):
                subscribers_text = f"{channel['subscribers']:,}" if channel['subscribers'] > 0 else "غير معروف"
                message += (
                    f"**{i}.** 📺 **{channel['title']}**\n"
                    f"     👥 المشتركين: {subscribers_text}\n"
                    f"     🔗 اضغط على الزر أدناه للاشتراك\n\n"
                )
            
            message += (
                f"⚡ **بعد الاشتراك في جميع القنوات:**\n"
                f"• اضغط على زر \"✅ تم الاشتراك - تحقق\"\n"
                f"• ستتمكن من استخدام البوت بحرية\n\n"
                f"🎵 **ميزات البوت تشمل:**\n"
                f"• تشغيل الموسيقى من جميع المنصات\n"
                f"• جودة صوتية عالية\n"
                f"• تحميل الأغاني\n"
                f"• البث المباشر\n\n"
                f"💡 **ملاحظة:** هذا الاشتراك مطلوب لدعم تطوير البوت"
            )
            
            return message
            
        except Exception as e:
            logger.error(f"❌ خطأ في إنشاء رسالة الاشتراك: {e}")
            return "🔐 يجب عليك الاشتراك في القنوات المطلوبة لاستخدام البوت"
    
    async def _handle_fsub_command(self, event):
        """معالجة أمر الاشتراك الإجباري"""
        try:
            # التحقق من صلاحيات المستخدم
            if not await self._check_admin_permissions(event):
                await event.reply("❌ يجب أن تكون مشرفاً لإدارة الاشتراك الإجباري")
                return
            
            args = event.message.text.split()[1:] if len(event.message.text.split()) > 1 else []
            
            if not args:
                help_text = (
                    "🔐 **نظام الاشتراك الإجباري**\n\n"
                    "⚙️ **الاستخدام:**\n"
                    "• `/fsub add @channel` - إضافة قناة للاشتراك الإجباري\n"
                    "• `/fsub remove @channel` - إزالة قناة من الاشتراك الإجباري\n"
                    "• `/fsub list` - عرض القنوات المضافة\n"
                    "• `/fsub disable` - تعطيل الاشتراك الإجباري\n"
                    "• `/fsub enable` - تفعيل الاشتراك الإجباري\n\n"
                    "📋 **أمثلة:**\n"
                    "• `/fsub add @mychannel`\n"
                    "• `/fsub add -1001234567890`\n"
                    "• `/fsub remove @mychannel`\n\n"
                    "💡 **ملاحظات:**\n"
                    "• يمكن إضافة حتى 5 قنوات\n"
                    "• يجب أن يكون البوت مشرفاً في القناة\n"
                    "• المطورين معفيون من الاشتراك الإجباري"
                )
                
                keyboard = [
                    [
                        Button.inline("➕ إضافة قناة", b"fsub_add_channel"),
                        Button.inline("➖ إزالة قناة", b"fsub_remove_channel")
                    ],
                    [
                        Button.inline("📋 عرض القنوات", b"fsub_list_channels"),
                        Button.inline("📊 الإحصائيات", b"fsub_statistics")
                    ],
                    [
                        Button.inline("🔴 تعطيل", b"fsub_disable"),
                        Button.inline("🟢 تفعيل", b"fsub_enable")
                    ]
                ]
                
                await event.reply(help_text, buttons=keyboard)
                return
            
            command = args[0].lower()
            
            if command == "add":
                channel_identifier = args[1] if len(args) > 1 else ""
                await self._add_force_channel(event, channel_identifier)
            elif command == "remove":
                channel_identifier = args[1] if len(args) > 1 else ""
                await self._remove_force_channel(event, channel_identifier)
            elif command == "list":
                await self._show_force_channels(event)
            elif command == "disable":
                await self._disable_force_subscribe(event)
            elif command == "enable":
                await self._enable_force_subscribe(event)
            else:
                await event.reply("❌ أمر غير معروف. استخدم `/fsub` لعرض المساعدة")
                
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة أمر الاشتراك الإجباري: {e}")
            await event.reply("❌ حدث خطأ في معالجة الأمر")
    
    async def _handle_fsub_list_command(self, event):
        """معالجة أمر عرض قائمة قنوات الاشتراك الإجباري"""
        try:
            await self._show_force_channels(event)
        except Exception as e:
            logger.error(f"❌ خطأ في عرض قائمة القنوات: {e}")
            await event.reply("❌ حدث خطأ في جلب قائمة القنوات")
    
    async def _handle_fsub_callback(self, event):
        """معالجة استعلامات الاشتراك الإجباري"""
        try:
            data = event.data.decode('utf-8')
            
            if data == "fsub_check_subscription":
                await self._recheck_user_subscription(event)
            elif data == "fsub_add_channel":
                await self._prompt_add_channel(event)
            elif data == "fsub_remove_channel":
                await self._prompt_remove_channel(event)
            elif data == "fsub_list_channels":
                await self._show_force_channels_callback(event)
            elif data == "fsub_statistics":
                await self._show_fsub_statistics(event)
            elif data == "fsub_disable":
                await self._disable_force_subscribe_callback(event)
            elif data == "fsub_enable":
                await self._enable_force_subscribe_callback(event)
            
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة استعلام الاشتراك الإجباري: {e}")
            await event.answer("❌ حدث خطأ في معالجة الطلب", alert=True)
    
    async def _recheck_user_subscription(self, event):
        """إعادة فحص اشتراك المستخدم"""
        try:
            user_id = event.sender_id
            
            # مسح الذاكرة المؤقتة للمستخدم
            cache_key = f"user_sub_{user_id}"
            if cache_key in self.subscription_cache:
                del self.subscription_cache[cache_key]
            
            # فحص الاشتراك مرة أخرى
            subscription_result = await self._verify_user_subscriptions(user_id)
            
            if subscription_result['is_subscribed']:
                # تحديث الإحصائيات
                self.fsub_stats['successful_subscriptions'] += 1
                
                await event.edit(
                    "✅ **تم التحقق بنجاح!**\n\n"
                    "🎉 **مرحباً بك في البوت!**\n\n"
                    "🎵 يمكنك الآن استخدام جميع ميزات البوت:\n"
                    "• تشغيل الموسيقى من جميع المنصات\n"
                    "• تحميل الأغاني بجودة عالية\n"
                    "• البث المباشر\n"
                    "• والمزيد...\n\n"
                    "💡 **للبدء:** أرسل `/help` لعرض قائمة الأوامر"
                )
            else:
                unsubscribed_count = len(subscription_result['unsubscribed_channels'])
                await event.answer(
                    f"❌ لم تكمل الاشتراك بعد!\n\n"
                    f"📊 متبقي: {unsubscribed_count} قناة\n"
                    f"💡 اشترك في جميع القنوات ثم اضغط التحقق مرة أخرى",
                    alert=True
                )
            
        except Exception as e:
            logger.error(f"❌ خطأ في إعادة فحص الاشتراك: {e}")
            await event.answer("❌ حدث خطأ في التحقق", alert=True)
    
    async def _add_force_channel(self, event, channel_identifier: str):
        """إضافة قناة للاشتراك الإجباري"""
        try:
            if not channel_identifier:
                await event.reply("❌ يرجى تحديد معرف أو يوزر القناة")
                return
            
            group_id = event.chat_id
            
            # التحقق من عدد القنوات الحالية
            current_channels = self.force_channels.get(group_id, [])
            if len(current_channels) >= 5:
                await event.reply("❌ لا يمكن إضافة أكثر من 5 قنوات للاشتراك الإجباري")
                return
            
            # محاولة الحصول على القناة
            try:
                if channel_identifier.startswith('@'):
                    channel = await self.client.client.get_entity(channel_identifier)
                elif channel_identifier.lstrip('-').isdigit():
                    channel_id = int(channel_identifier)
                    channel = await self.client.client.get_entity(channel_id)
                else:
                    await event.reply("❌ معرف القناة غير صحيح")
                    return
            except Exception as e:
                await event.reply(f"❌ لا يمكن العثور على القناة: {str(e)[:100]}")
                return
            
            # التحقق من أنها قناة
            if not isinstance(channel, Channel):
                await event.reply("❌ يجب أن يكون المعرف لقناة وليس مجموعة")
                return
            
            # التحقق من أن القناة ليست مضافة مسبقاً
            if channel.id in current_channels:
                await event.reply(f"❌ القناة {channel.title} مضافة مسبقاً")
                return
            
            # إضافة القناة
            if group_id not in self.force_channels:
                self.force_channels[group_id] = []
            
            self.force_channels[group_id].append(channel.id)
            
            # حفظ في قاعدة البيانات
            await self._save_force_channel_settings(group_id)
            
            # تحديث الإحصائيات
            self.fsub_stats['active_force_channels'] = len(self.force_channels)
            
            keyboard = [
                [
                    Button.inline("➕ إضافة قناة أخرى", b"fsub_add_channel"),
                    Button.inline("📋 عرض القنوات", b"fsub_list_channels")
                ]
            ]
            
            await event.reply(
                f"✅ **تم إضافة القناة بنجاح**\n\n"
                f"📺 **القناة:** {channel.title}\n"
                f"🆔 **المعرف:** `{channel.id}`\n"
                f"👥 **المشتركين:** {getattr(channel, 'participants_count', 'غير معروف'):,}\n"
                f"📊 **إجمالي القنوات:** {len(self.force_channels[group_id])}/5\n\n"
                f"🔐 **سيطلب من المستخدمين الاشتراك في هذه القناة**",
                buttons=keyboard
            )
            
        except Exception as e:
            logger.error(f"❌ خطأ في إضافة قناة الاشتراك الإجباري: {e}")
            await event.reply("❌ حدث خطأ في إضافة القناة")
    
    async def _remove_force_channel(self, event, channel_identifier: str):
        """إزالة قناة من الاشتراك الإجباري"""
        try:
            if not channel_identifier:
                await event.reply("❌ يرجى تحديد معرف أو يوزر القناة")
                return
            
            group_id = event.chat_id
            
            if group_id not in self.force_channels or not self.force_channels[group_id]:
                await event.reply("❌ لا توجد قنوات مضافة للاشتراك الإجباري")
                return
            
            # محاولة الحصول على القناة
            try:
                if channel_identifier.startswith('@'):
                    channel = await self.client.client.get_entity(channel_identifier)
                elif channel_identifier.lstrip('-').isdigit():
                    channel_id = int(channel_identifier)
                    channel = await self.client.client.get_entity(channel_id)
                else:
                    await event.reply("❌ معرف القناة غير صحيح")
                    return
            except Exception as e:
                await event.reply(f"❌ لا يمكن العثور على القناة: {str(e)[:100]}")
                return
            
            # التحقق من وجود القناة في القائمة
            if channel.id not in self.force_channels[group_id]:
                await event.reply(f"❌ القناة {channel.title} غير مضافة للاشتراك الإجباري")
                return
            
            # إزالة القناة
            self.force_channels[group_id].remove(channel.id)
            
            # إزالة المجموعة إذا لم تعد تحتوي على قنوات
            if not self.force_channels[group_id]:
                del self.force_channels[group_id]
            
            # حفظ في قاعدة البيانات
            await self._save_force_channel_settings(group_id)
            
            # تحديث الإحصائيات
            self.fsub_stats['active_force_channels'] = len(self.force_channels)
            
            remaining_count = len(self.force_channels.get(group_id, []))
            
            await event.reply(
                f"✅ **تم إزالة القناة بنجاح**\n\n"
                f"📺 **القناة:** {channel.title}\n"
                f"🆔 **المعرف:** `{channel.id}`\n"
                f"📊 **القنوات المتبقية:** {remaining_count}\n\n"
                f"🔓 **لن يطلب من المستخدمين الاشتراك في هذه القناة بعد الآن**"
            )
            
        except Exception as e:
            logger.error(f"❌ خطأ في إزالة قناة الاشتراك الإجباري: {e}")
            await event.reply("❌ حدث خطأ في إزالة القناة")
    
    async def _show_force_channels(self, event):
        """عرض قنوات الاشتراك الإجباري"""
        try:
            group_id = event.chat_id
            
            if group_id not in self.force_channels or not self.force_channels[group_id]:
                await event.reply(
                    "📭 **لا توجد قنوات للاشتراك الإجباري**\n\n"
                    "💡 **لإضافة قناة:** `/fsub add @channel`"
                )
                return
            
            message = f"🔐 **قنوات الاشتراك الإجباري**\n\n"
            
            for i, channel_id in enumerate(self.force_channels[group_id], 1):
                try:
                    channel = await self.client.client.get_entity(channel_id)
                    subscribers = getattr(channel, 'participants_count', 0)
                    username = getattr(channel, 'username', None)
                    
                    message += (
                        f"**{i}.** 📺 **{channel.title}**\n"
                        f"     🆔 المعرف: `{channel_id}`\n"
                        f"     👥 المشتركين: {subscribers:,}\n"
                    )
                    
                    if username:
                        message += f"     🔗 الرابط: @{username}\n"
                    
                    message += "\n"
                    
                except Exception:
                    message += f"**{i}.** ❌ قناة غير متاحة (ID: `{channel_id}`)\n\n"
            
            # إضافة إحصائيات
            message += (
                f"📊 **الإحصائيات:**\n"
                f"• عدد القنوات: {len(self.force_channels[group_id])}/5\n"
                f"• إجمالي الفحوصات: {self.fsub_stats['total_checks']:,}\n"
                f"• المستخدمين المحجوبين: {self.fsub_stats['blocked_users']:,}\n"
                f"• الاشتراكات الناجحة: {self.fsub_stats['successful_subscriptions']:,}"
            )
            
            keyboard = [
                [
                    Button.inline("➕ إضافة قناة", b"fsub_add_channel"),
                    Button.inline("➖ إزالة قناة", b"fsub_remove_channel")
                ],
                [
                    Button.inline("🔄 تحديث", b"fsub_list_channels"),
                    Button.inline("⚙️ إعدادات", b"fsub_settings")
                ]
            ]
            
            await event.reply(message, buttons=keyboard)
            
        except Exception as e:
            logger.error(f"❌ خطأ في عرض قنوات الاشتراك الإجباري: {e}")
            await event.reply("❌ حدث خطأ في جلب قائمة القنوات")
    
    async def _check_admin_permissions(self, event) -> bool:
        """التحقق من صلاحيات الإدارة"""
        try:
            # التحقق من المطورين أولاً
            if event.sender_id in self.exempted_users:
                return True
            
            chat = await event.get_chat()
            user = await event.get_sender()
            
            if hasattr(chat, 'admin_rights'):
                participant = await event.client.get_permissions(chat, user)
                return participant.is_admin or participant.is_creator
            
            return False
            
        except Exception as e:
            logger.error(f"❌ خطأ في التحقق من الصلاحيات: {e}")
            return False
    
    async def _save_force_channel_settings(self, group_id: int):
        """حفظ إعدادات قنوات الاشتراك الإجباري"""
        try:
            # سيتم تنفيذ هذا عندما تكون قاعدة البيانات جاهزة
            # channels = self.force_channels.get(group_id, [])
            # await self.db.save_force_subscribe_settings(group_id, channels)
            
            logger.info(f"💾 تم حفظ إعدادات الاشتراك الإجباري للمجموعة {group_id}")
            
        except Exception as e:
            logger.error(f"❌ فشل في حفظ إعدادات الاشتراك الإجباري: {e}")
    
    async def _maintenance_tasks(self):
        """مهام الصيانة الدورية"""
        while True:
            try:
                await asyncio.sleep(3600)  # كل ساعة
                
                # تنظيف ذاكرة التخزين المؤقت القديمة
                await self._cleanup_subscription_cache()
                
                # تحديث إحصائيات القنوات
                await self._update_channel_stats()
                
            except Exception as e:
                logger.error(f"❌ خطأ في مهام صيانة الاشتراك الإجباري: {e}")
    
    async def _cleanup_subscription_cache(self):
        """تنظيف ذاكرة التخزين المؤقت القديمة"""
        try:
            current_time = datetime.now()
            expired_keys = []
            
            for key, data in self.subscription_cache.items():
                if current_time - data['timestamp'] > timedelta(hours=1):
                    expired_keys.append(key)
            
            for key in expired_keys:
                del self.subscription_cache[key]
            
            logger.info(f"🧹 تم تنظيف {len(expired_keys)} عنصر من ذاكرة الاشتراك المؤقت")
            
        except Exception as e:
            logger.error(f"❌ خطأ في تنظيف ذاكرة الاشتراك المؤقت: {e}")
    
    # وظائف مساعدة للاستعلامات
    async def _prompt_add_channel(self, event):
        """مطالبة بإضافة قناة"""
        await event.edit(
            "➕ **إضافة قناة للاشتراك الإجباري**\n\n"
            "📝 **أرسل معرف أو يوزر القناة:**\n"
            "• `@channel_username`\n"
            "• `-1001234567890`\n\n"
            "💡 **استخدم الأمر:** `/fsub add @channel`"
        )
    
    async def _prompt_remove_channel(self, event):
        """مطالبة بإزالة قناة"""
        await event.edit(
            "➖ **إزالة قناة من الاشتراك الإجباري**\n\n"
            "📝 **أرسل معرف أو يوزر القناة:**\n"
            "• `@channel_username`\n"
            "• `-1001234567890`\n\n"
            "💡 **استخدم الأمر:** `/fsub remove @channel`"
        )
    
    async def _show_force_channels_callback(self, event):
        """عرض قنوات الاشتراك الإجباري عبر الاستعلام"""
        await self._show_force_channels(event)
    
    async def _show_fsub_statistics(self, event):
        """عرض إحصائيات الاشتراك الإجباري"""
        message = (
            f"📊 **إحصائيات الاشتراك الإجباري**\n\n"
            f"🔐 **المجموعات النشطة:** {len(self.force_channels)}\n"
            f"📺 **إجمالي القنوات:** {sum(len(channels) for channels in self.force_channels.values())}\n"
            f"🔍 **إجمالي الفحوصات:** {self.fsub_stats['total_checks']:,}\n"
            f"🚫 **المستخدمين المحجوبين:** {self.fsub_stats['blocked_users']:,}\n"
            f"✅ **الاشتراكات الناجحة:** {self.fsub_stats['successful_subscriptions']:,}\n"
            f"💾 **ذاكرة التخزين المؤقت:** {len(self.subscription_cache)} عنصر\n\n"
            f"📈 **معدل النجاح:** {((self.fsub_stats['successful_subscriptions'] / max(self.fsub_stats['blocked_users'], 1)) * 100):.1f}%"
        )
        
        await event.edit(message)
    
    async def _disable_force_subscribe(self, event):
        """تعطيل الاشتراك الإجباري"""
        group_id = event.chat_id
        
        if group_id in self.force_channels:
            del self.force_channels[group_id]
            await self._save_force_channel_settings(group_id)
            
            await event.reply(
                "🔓 **تم تعطيل الاشتراك الإجباري**\n\n"
                "✅ يمكن للمستخدمين الآن استخدام البوت بحرية\n"
                "💡 لإعادة التفعيل: `/fsub add @channel`"
            )
        else:
            await event.reply("❌ الاشتراك الإجباري غير مفعل أصلاً")
    
    async def _enable_force_subscribe(self, event):
        """تفعيل الاشتراك الإجباري"""
        await event.reply(
            "🔐 **لتفعيل الاشتراك الإجباري**\n\n"
            "📝 **أضف قناة أولاً:** `/fsub add @channel`\n"
            "💡 **ثم سيتم تفعيل النظام تلقائياً**"
        )
    
    async def _disable_force_subscribe_callback(self, event):
        """تعطيل الاشتراك الإجباري عبر الاستعلام"""
        await self._disable_force_subscribe(event)
    
    async def _enable_force_subscribe_callback(self, event):
        """تفعيل الاشتراك الإجباري عبر الاستعلام"""
        await self._enable_force_subscribe(event)
    
    async def get_fsub_statistics(self) -> Dict[str, Any]:
        """الحصول على إحصائيات الاشتراك الإجباري"""
        return {
            'active_groups': len(self.force_channels),
            'total_channels': sum(len(channels) for channels in self.force_channels.values()),
            'total_checks': self.fsub_stats['total_checks'],
            'blocked_users': self.fsub_stats['blocked_users'],
            'successful_subscriptions': self.fsub_stats['successful_subscriptions'],
            'cache_size': len(self.subscription_cache),
            'success_rate': ((self.fsub_stats['successful_subscriptions'] / max(self.fsub_stats['blocked_users'], 1)) * 100)
        }

# إنشاء مثيل عام لبلاجين الاشتراك الإجباري
force_subscribe_plugin = None  # سيتم تهيئته في الملف الرئيسي