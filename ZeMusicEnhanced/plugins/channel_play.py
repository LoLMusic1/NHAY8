#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎵 ZeMusic Bot v3.0 - Channel Play System
تاريخ الإنشاء: 2025-01-28

نظام تشغيل القنوات المتقدم
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from telethon import events, Button
from telethon.tl.types import Channel, Chat
from telethon.errors import ChatAdminRequired, UserNotParticipant, ChannelPrivateError

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import config
from ..core import TelethonClient, DatabaseManager, MusicEngine

logger = logging.getLogger(__name__)

class ChannelPlayPlugin:
    """بلاجين تشغيل القنوات المتقدم"""
    
    def __init__(self, client: TelethonClient, db: DatabaseManager, music_engine: MusicEngine):
        """تهيئة بلاجين تشغيل القنوات"""
        self.client = client
        self.db = db
        self.music_engine = music_engine
        
        # قائمة القنوات المربوطة بالمجموعات
        self.channel_links: Dict[int, int] = {}  # {group_id: channel_id}
        
        # إحصائيات تشغيل القنوات
        self.channel_stats = {
            'total_linked_channels': 0,
            'active_channel_plays': 0,
            'total_channel_plays': 0
        }
        
    async def initialize(self) -> bool:
        """تهيئة بلاجين تشغيل القنوات"""
        try:
            logger.info("📺 تهيئة بلاجين تشغيل القنوات...")
            
            # تحميل القنوات المربوطة من قاعدة البيانات
            await self._load_channel_links()
            
            # تسجيل معالجات الأحداث
            await self._register_channel_handlers()
            
            logger.info("✅ تم تهيئة بلاجين تشغيل القنوات بنجاح")
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في تهيئة بلاجين تشغيل القنوات: {e}")
            return False
    
    async def _load_channel_links(self):
        """تحميل القنوات المربوطة من قاعدة البيانات"""
        try:
            # سيتم تنفيذ هذا عندما تكون قاعدة البيانات جاهزة
            # channel_links = await self.db.get_all_channel_links()
            # self.channel_links = {link['group_id']: link['channel_id'] for link in channel_links}
            
            logger.info(f"📚 تم تحميل {len(self.channel_links)} رابط قناة")
            
        except Exception as e:
            logger.error(f"❌ فشل في تحميل روابط القنوات: {e}")
    
    async def _register_channel_handlers(self):
        """تسجيل معالجات أحداث القنوات"""
        try:
            # معالج أمر ربط القناة
            @self.client.client.on(events.NewMessage(pattern=r'^[!/.](?:channelplay|ربط)'))
            async def handle_channel_play(event):
                await self._handle_channel_play_command(event)
            
            # معالج عرض القنوات المربوطة
            @self.client.client.on(events.NewMessage(pattern=r'^[!/.](?:channellist|قائمة القنوات)'))
            async def handle_channel_list(event):
                await self._handle_channel_list_command(event)
            
            # معالج حذف رابط القناة
            @self.client.client.on(events.NewMessage(pattern=r'^[!/.](?:unchannelplay|إلغاء الربط)'))
            async def handle_unchannel_play(event):
                await self._handle_unchannel_play_command(event)
            
            # معالج استعلامات القنوات
            @self.client.client.on(events.CallbackQuery(pattern=b'channel_'))
            async def handle_channel_callback(event):
                await self._handle_channel_callback(event)
            
            logger.info("📝 تم تسجيل معالجات تشغيل القنوات")
            
        except Exception as e:
            logger.error(f"❌ فشل في تسجيل معالجات القنوات: {e}")
    
    async def _handle_channel_play_command(self, event):
        """معالجة أمر ربط القناة"""
        try:
            # التحقق من صلاحيات المستخدم
            if not await self._check_admin_permissions(event):
                await event.reply("❌ يجب أن تكون مشرفاً لربط قناة")
                return
            
            args = event.message.text.split()[1:] if len(event.message.text.split()) > 1 else []
            
            if not args:
                help_text = (
                    "📺 **نظام ربط القنوات**\n\n"
                    "🔗 **الاستخدام:**\n"
                    "• `/channelplay disable` - إلغاء ربط القناة\n"
                    "• `/channelplay linked` - ربط بالقناة المرتبطة\n"
                    "• `/channelplay @channel` - ربط بقناة محددة\n"
                    "• `/channelplay [معرف القناة]` - ربط بمعرف القناة\n\n"
                    "📋 **أمثلة:**\n"
                    "• `/channelplay @mychannel`\n"
                    "• `/channelplay -1001234567890`\n"
                    "• `/channelplay linked`\n"
                    "• `/channelplay disable`\n\n"
                    "💡 **ملاحظة:** يجب أن تكون مشرفاً في القناة المراد ربطها"
                )
                
                keyboard = [
                    [
                        Button.inline("🔗 ربط بالقناة المرتبطة", b"channel_link_auto"),
                        Button.inline("❌ إلغاء الربط", b"channel_unlink")
                    ],
                    [
                        Button.inline("📋 عرض القنوات", b"channel_list"),
                        Button.inline("❓ المساعدة", b"channel_help")
                    ]
                ]
                
                await event.reply(help_text, buttons=keyboard)
                return
            
            command = args[0].lower()
            
            if command == "disable":
                await self._disable_channel_play(event)
            elif command == "linked":
                await self._link_to_linked_channel(event)
            else:
                # محاولة ربط بقناة محددة
                channel_identifier = args[0]
                await self._link_to_specific_channel(event, channel_identifier)
                
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة أمر ربط القناة: {e}")
            await event.reply("❌ حدث خطأ في معالجة أمر ربط القناة")
    
    async def _handle_channel_list_command(self, event):
        """معالجة أمر عرض قائمة القنوات"""
        try:
            if not self.channel_links:
                await event.reply("📭 لا توجد قنوات مربوطة حالياً")
                return
            
            message = "📺 **القنوات المربوطة**\n\n"
            
            for group_id, channel_id in self.channel_links.items():
                try:
                    group = await self.client.client.get_entity(group_id)
                    channel = await self.client.client.get_entity(channel_id)
                    
                    message += (
                        f"🏷️ **{group.title}**\n"
                        f"   📺 القناة: {channel.title}\n"
                        f"   🆔 معرف المجموعة: `{group_id}`\n"
                        f"   🆔 معرف القناة: `{channel_id}`\n\n"
                    )
                except:
                    continue
            
            # إضافة إحصائيات
            message += (
                f"📊 **الإحصائيات:**\n"
                f"• القنوات المربوطة: {len(self.channel_links)}\n"
                f"• التشغيل النشط: {self.channel_stats['active_channel_plays']}\n"
                f"• إجمالي التشغيل: {self.channel_stats['total_channel_plays']}"
            )
            
            keyboard = [
                [
                    Button.inline("🔄 تحديث", b"channel_refresh_list"),
                    Button.inline("⚙️ إعدادات", b"channel_settings")
                ]
            ]
            
            await event.reply(message, buttons=keyboard)
            
        except Exception as e:
            logger.error(f"❌ خطأ في عرض قائمة القنوات: {e}")
            await event.reply("❌ حدث خطأ في جلب قائمة القنوات")
    
    async def _handle_unchannel_play_command(self, event):
        """معالجة أمر إلغاء ربط القناة"""
        try:
            # التحقق من صلاحيات المستخدم
            if not await self._check_admin_permissions(event):
                await event.reply("❌ يجب أن تكون مشرفاً لإلغاء ربط القناة")
                return
            
            await self._disable_channel_play(event)
            
        except Exception as e:
            logger.error(f"❌ خطأ في إلغاء ربط القناة: {e}")
            await event.reply("❌ حدث خطأ في إلغاء ربط القناة")
    
    async def _handle_channel_callback(self, event):
        """معالجة استعلامات القنوات"""
        try:
            data = event.data.decode('utf-8')
            
            if data == "channel_link_auto":
                await self._link_to_linked_channel_callback(event)
            elif data == "channel_unlink":
                await self._disable_channel_play_callback(event)
            elif data == "channel_list":
                await self._show_channel_list_callback(event)
            elif data == "channel_help":
                await self._show_channel_help(event)
            elif data == "channel_refresh_list":
                await self._refresh_channel_list(event)
            elif data == "channel_settings":
                await self._show_channel_settings(event)
            
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة استعلام القناة: {e}")
            await event.answer("❌ حدث خطأ في معالجة الطلب", alert=True)
    
    async def _disable_channel_play(self, event):
        """إلغاء ربط القناة"""
        try:
            group_id = event.chat_id
            
            if group_id not in self.channel_links:
                await event.reply("❌ لا توجد قناة مربوطة بهذه المجموعة")
                return
            
            # إزالة الرابط
            channel_id = self.channel_links.pop(group_id)
            
            # حفظ في قاعدة البيانات
            await self._save_channel_link(group_id, None)
            
            # تحديث الإحصائيات
            self.channel_stats['total_linked_channels'] -= 1
            
            try:
                channel = await self.client.client.get_entity(channel_id)
                channel_name = channel.title
            except:
                channel_name = f"القناة {channel_id}"
            
            await event.reply(
                f"✅ **تم إلغاء ربط القناة**\n\n"
                f"📺 **القناة:** {channel_name}\n"
                f"🏷️ **المجموعة:** {event.chat.title}\n\n"
                f"💡 سيتم الآن تشغيل الموسيقى في المجموعة مباشرة"
            )
            
        except Exception as e:
            logger.error(f"❌ خطأ في إلغاء ربط القناة: {e}")
            await event.reply("❌ حدث خطأ في إلغاء ربط القناة")
    
    async def _link_to_linked_channel(self, event):
        """ربط بالقناة المرتبطة تلقائياً"""
        try:
            chat = await event.get_chat()
            
            if not hasattr(chat, 'linked_chat') or not chat.linked_chat:
                await event.reply(
                    "❌ **لا توجد قناة مرتبطة بهذه المجموعة**\n\n"
                    "💡 **لربط قناة يدوياً:**\n"
                    "• `/channelplay @channel_username`\n"
                    "• `/channelplay [معرف القناة]`"
                )
                return
            
            linked_channel = chat.linked_chat
            
            # التحقق من صلاحيات القناة
            if not await self._check_channel_permissions(linked_channel.id):
                await event.reply(
                    f"❌ **لا يمكن الوصول للقناة المرتبطة**\n\n"
                    f"📺 **القناة:** {linked_channel.title}\n"
                    f"🆔 **المعرف:** `{linked_channel.id}`\n\n"
                    f"💡 **تأكد من أن البوت مشرف في القناة**"
                )
                return
            
            # حفظ الرابط
            group_id = event.chat_id
            channel_id = linked_channel.id
            
            self.channel_links[group_id] = channel_id
            await self._save_channel_link(group_id, channel_id)
            
            # تحديث الإحصائيات
            self.channel_stats['total_linked_channels'] += 1
            
            keyboard = [
                [
                    Button.inline("🎵 تشغيل تجريبي", f"channel_test_play_{channel_id}".encode()),
                    Button.inline("⚙️ إعدادات القناة", f"channel_config_{channel_id}".encode())
                ],
                [
                    Button.inline("❌ إلغاء الربط", b"channel_unlink"),
                    Button.inline("📊 الإحصائيات", b"channel_stats")
                ]
            ]
            
            await event.reply(
                f"✅ **تم ربط القناة بنجاح**\n\n"
                f"📺 **القناة:** {linked_channel.title}\n"
                f"🆔 **المعرف:** `{channel_id}`\n"
                f"🏷️ **المجموعة:** {event.chat.title}\n\n"
                f"🎵 **سيتم الآن تشغيل الموسيقى في القناة المربوطة**",
                buttons=keyboard
            )
            
        except Exception as e:
            logger.error(f"❌ خطأ في ربط القناة المرتبطة: {e}")
            await event.reply("❌ حدث خطأ في ربط القناة المرتبطة")
    
    async def _link_to_specific_channel(self, event, channel_identifier: str):
        """ربط بقناة محددة"""
        try:
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
                await event.reply(
                    f"❌ **لا يمكن العثور على القناة**\n\n"
                    f"🔍 **المعرف المدخل:** `{channel_identifier}`\n"
                    f"❓ **السبب:** {str(e)[:100]}...\n\n"
                    f"💡 **تأكد من:**\n"
                    f"• صحة معرف أو يوزر القناة\n"
                    f"• أن القناة عامة أو البوت عضو فيها\n"
                    f"• أن البوت لديه صلاحيات في القناة"
                )
                return
            
            # التحقق من نوع القناة
            if not isinstance(channel, Channel):
                await event.reply("❌ يجب أن يكون المعرف لقناة وليس مجموعة")
                return
            
            # التحقق من ملكية القناة
            if not await self._check_channel_ownership(event.sender_id, channel.id):
                await event.reply(
                    f"❌ **ليس لديك صلاحية ربط هذه القناة**\n\n"
                    f"📺 **القناة:** {channel.title}\n"
                    f"🆔 **المعرف:** `{channel.id}`\n\n"
                    f"💡 **يجب أن تكون مالك أو مشرف في القناة**"
                )
                return
            
            # حفظ الرابط
            group_id = event.chat_id
            channel_id = channel.id
            
            self.channel_links[group_id] = channel_id
            await self._save_channel_link(group_id, channel_id)
            
            # تحديث الإحصائيات
            self.channel_stats['total_linked_channels'] += 1
            
            keyboard = [
                [
                    Button.inline("🎵 تشغيل تجريبي", f"channel_test_play_{channel_id}".encode()),
                    Button.inline("📊 إحصائيات القناة", f"channel_stats_{channel_id}".encode())
                ],
                [
                    Button.inline("⚙️ إعدادات", f"channel_config_{channel_id}".encode()),
                    Button.inline("❌ إلغاء الربط", b"channel_unlink")
                ]
            ]
            
            await event.reply(
                f"✅ **تم ربط القناة بنجاح**\n\n"
                f"📺 **القناة:** {channel.title}\n"
                f"🆔 **المعرف:** `{channel_id}`\n"
                f"👥 **المشتركين:** {getattr(channel, 'participants_count', 'غير معروف'):,}\n"
                f"🏷️ **المجموعة:** {event.chat.title}\n\n"
                f"🎵 **سيتم الآن تشغيل الموسيقى في القناة المربوطة**",
                buttons=keyboard
            )
            
        except Exception as e:
            logger.error(f"❌ خطأ في ربط القناة المحددة: {e}")
            await event.reply("❌ حدث خطأ في ربط القناة")
    
    async def _check_admin_permissions(self, event) -> bool:
        """التحقق من صلاحيات الإدارة"""
        try:
            chat = await event.get_chat()
            user = await event.get_sender()
            
            if hasattr(chat, 'admin_rights'):
                participant = await event.client.get_permissions(chat, user)
                return participant.is_admin or participant.is_creator
            
            return False
            
        except Exception as e:
            logger.error(f"❌ خطأ في التحقق من الصلاحيات: {e}")
            return False
    
    async def _check_channel_permissions(self, channel_id: int) -> bool:
        """التحقق من صلاحيات القناة"""
        try:
            # محاولة الوصول للقناة
            channel = await self.client.client.get_entity(channel_id)
            
            # التحقق من أن البوت عضو في القناة
            try:
                me = await self.client.client.get_me()
                participant = await self.client.client.get_permissions(channel, me)
                return participant.is_admin or participant.post_messages
            except:
                return False
                
        except Exception as e:
            logger.error(f"❌ خطأ في التحقق من صلاحيات القناة: {e}")
            return False
    
    async def _check_channel_ownership(self, user_id: int, channel_id: int) -> bool:
        """التحقق من ملكية القناة"""
        try:
            channel = await self.client.client.get_entity(channel_id)
            participant = await self.client.client.get_permissions(channel, user_id)
            
            return participant.is_creator or participant.is_admin
            
        except Exception as e:
            logger.error(f"❌ خطأ في التحقق من ملكية القناة: {e}")
            return False
    
    async def _save_channel_link(self, group_id: int, channel_id: Optional[int]):
        """حفظ رابط القناة في قاعدة البيانات"""
        try:
            # سيتم تنفيذ هذا عندما تكون قاعدة البيانات جاهزة
            # if channel_id:
            #     await self.db.set_channel_link(group_id, channel_id)
            # else:
            #     await self.db.remove_channel_link(group_id)
            
            logger.info(f"💾 تم حفظ رابط القناة: {group_id} -> {channel_id}")
            
        except Exception as e:
            logger.error(f"❌ فشل في حفظ رابط القناة: {e}")
    
    def get_linked_channel(self, group_id: int) -> Optional[int]:
        """الحصول على القناة المربوطة بالمجموعة"""
        return self.channel_links.get(group_id)
    
    async def play_in_channel(self, group_id: int, track_info: Dict[str, Any]) -> Dict[str, Any]:
        """تشغيل الموسيقى في القناة المربوطة"""
        try:
            channel_id = self.get_linked_channel(group_id)
            
            if not channel_id:
                return {
                    'success': False,
                    'message': 'لا توجد قناة مربوطة بهذه المجموعة'
                }
            
            # تشغيل في القناة بدلاً من المجموعة
            result = await self.music_engine.play_track(channel_id, track_info['track'], track_info['user_id'])
            
            if result['success']:
                self.channel_stats['active_channel_plays'] += 1
                self.channel_stats['total_channel_plays'] += 1
            
            return result
            
        except Exception as e:
            logger.error(f"❌ خطأ في تشغيل الموسيقى في القناة: {e}")
            return {
                'success': False,
                'message': f'خطأ في التشغيل: {str(e)}'
            }
    
    # وظائف مساعدة للاستعلامات
    async def _disable_channel_play_callback(self, event):
        """إلغاء ربط القناة عبر الاستعلام"""
        await self._disable_channel_play(event)
    
    async def _link_to_linked_channel_callback(self, event):
        """ربط بالقناة المرتبطة عبر الاستعلام"""
        await self._link_to_linked_channel(event)
    
    async def _show_channel_list_callback(self, event):
        """عرض قائمة القنوات عبر الاستعلام"""
        await self._handle_channel_list_command(event)
    
    async def _show_channel_help(self, event):
        """عرض مساعدة القنوات"""
        help_text = (
            "📺 **مساعدة نظام ربط القنوات**\n\n"
            "🔗 **الأوامر الأساسية:**\n"
            "• `/channelplay linked` - ربط بالقناة المرتبطة\n"
            "• `/channelplay @channel` - ربط بقناة محددة\n"
            "• `/channelplay disable` - إلغاء الربط\n\n"
            "📋 **الأوامر الإضافية:**\n"
            "• `/channellist` - عرض القنوات المربوطة\n"
            "• `/unchannelplay` - إلغاء الربط\n\n"
            "💡 **نصائح:**\n"
            "• يجب أن تكون مشرفاً في المجموعة والقناة\n"
            "• البوت يجب أن يكون مشرفاً في القناة\n"
            "• يمكن ربط قناة واحدة فقط لكل مجموعة"
        )
        
        await event.edit(help_text)
    
    async def _refresh_channel_list(self, event):
        """تحديث قائمة القنوات"""
        await self._handle_channel_list_command(event)
    
    async def _show_channel_settings(self, event):
        """عرض إعدادات القنوات"""
        message = "⚙️ **إعدادات نظام القنوات**\n\nقريباً..."
        await event.edit(message)
    
    async def get_channel_statistics(self) -> Dict[str, Any]:
        """الحصول على إحصائيات القنوات"""
        return {
            'total_linked_channels': len(self.channel_links),
            'active_channel_plays': self.channel_stats['active_channel_plays'],
            'total_channel_plays': self.channel_stats['total_channel_plays'],
            'channel_links': self.channel_links.copy()
        }

# إنشاء مثيل عام لبلاجين تشغيل القنوات
channel_play_plugin = None  # سيتم تهيئته في الملف الرئيسي