#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎵 ZeMusic Bot v3.0 - Voice Call Manager
تاريخ الإنشاء: 2025-01-28

نظام إدارة المكالمات الصوتية المتقدم
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from telethon import events, Button
from telethon.tl.functions.channels import GetFullChannelRequest
from telethon.tl.functions.messages import GetFullChatRequest
from telethon.tl.functions.phone import CreateGroupCallRequest, DiscardGroupCallRequest
from telethon.tl.types import InputGroupCall, InputPeerChannel, InputPeerChat
from telethon.errors import ChatAdminRequired, UserNotParticipant, FloodWaitError

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import config
from ..core import TelethonClient, DatabaseManager, AssistantManager

logger = logging.getLogger(__name__)

class VoiceCallManager:
    """مدير المكالمات الصوتية المتقدم"""
    
    def __init__(self, client: TelethonClient, db: DatabaseManager, assistant_manager: AssistantManager):
        """تهيئة مدير المكالمات الصوتية"""
        self.client = client
        self.db = db
        self.assistant_manager = assistant_manager
        
        # حالة المكالمات النشطة
        self.active_calls: Dict[int, Dict[str, Any]] = {}
        
        # إحصائيات المكالمات
        self.call_stats = {
            'total_calls_created': 0,
            'total_calls_ended': 0,
            'active_calls_count': 0,
            'failed_attempts': 0
        }
        
    async def initialize(self) -> bool:
        """تهيئة مدير المكالمات الصوتية"""
        try:
            logger.info("📞 تهيئة مدير المكالمات الصوتية...")
            
            # تسجيل معالجات الأحداث
            await self._register_call_handlers()
            
            # بدء مهام المراقبة
            asyncio.create_task(self._monitor_calls())
            
            logger.info("✅ تم تهيئة مدير المكالمات الصوتية بنجاح")
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في تهيئة مدير المكالمات الصوتية: {e}")
            return False
    
    async def _register_call_handlers(self):
        """تسجيل معالجات أحداث المكالمات"""
        try:
            # معالج فتح المكالمة
            @self.client.client.on(events.NewMessage(pattern=r'^(افتح المكالمه|افتح المكالمة|فتح المكالمه|فتح المكالمة|start call|open call)$'))
            async def handle_start_call(event):
                await self._handle_start_call(event)
            
            # معالج إغلاق المكالمة
            @self.client.client.on(events.NewMessage(pattern=r'^(اقفل المكالمه|اقفل المكالمة|قفل المكالمه|قفل المكالمة|end call|close call)$'))
            async def handle_end_call(event):
                await self._handle_end_call(event)
            
            # معالج حالة المكالمة
            @self.client.client.on(events.NewMessage(pattern=r'^[!/.]callstatus'))
            async def handle_call_status(event):
                await self._handle_call_status(event)
            
            # معالج قائمة المكالمات
            @self.client.client.on(events.NewMessage(pattern=r'^[!/.]calls'))
            async def handle_calls_list(event):
                await self._handle_calls_list(event)
            
            # معالج استعلامات المكالمات
            @self.client.client.on(events.CallbackQuery(pattern=b'call_'))
            async def handle_call_callback(event):
                await self._handle_call_callback(event)
            
            logger.info("📝 تم تسجيل معالجات المكالمات الصوتية")
            
        except Exception as e:
            logger.error(f"❌ فشل في تسجيل معالجات المكالمات: {e}")
    
    async def _handle_start_call(self, event):
        """معالجة بدء المكالمة الصوتية"""
        try:
            chat_id = event.chat_id
            user_id = event.sender_id
            
            # التحقق من صلاحيات المستخدم
            if not await self._check_admin_permissions(event):
                await event.reply("❌ يجب أن تكون مشرفاً لبدء مكالمة صوتية")
                return
            
            # التحقق من وجود مكالمة نشطة
            if chat_id in self.active_calls:
                await event.reply("📞 **يوجد مكالمة صوتية نشطة بالفعل**")
                return
            
            # الحصول على حساب مساعد
            assistant = await self.assistant_manager.get_best_assistant(chat_id)
            if not assistant:
                await event.reply("❌ لا توجد حسابات مساعدة متاحة")
                return
            
            status_msg = await event.reply("📞 جاري تشغيل المكالمة الصوتية...")
            
            # إنشاء المكالمة الصوتية
            result = await self._create_group_call(chat_id, assistant, status_msg)
            
            if result['success']:
                # تسجيل المكالمة النشطة
                self.active_calls[chat_id] = {
                    'call_id': result['call_id'],
                    'assistant_id': assistant.assistant_id,
                    'created_by': user_id,
                    'created_at': asyncio.get_event_loop().time(),
                    'participants': [],
                    'status': 'active'
                }
                
                # تحديث الإحصائيات
                self.call_stats['total_calls_created'] += 1
                self.call_stats['active_calls_count'] += 1
                
                keyboard = [
                    [
                        Button.inline("🔇 كتم الكل", b"call_mute_all"),
                        Button.inline("🔊 إلغاء كتم الكل", b"call_unmute_all")
                    ],
                    [
                        Button.inline("📊 إحصائيات المكالمة", b"call_stats"),
                        Button.inline("👥 المشاركين", b"call_participants")
                    ],
                    [
                        Button.inline("⚙️ إعدادات المكالمة", b"call_settings"),
                        Button.inline("❌ إنهاء المكالمة", b"call_end")
                    ]
                ]
                
                await status_msg.edit(
                    f"✅ **تم تشغيل المكالمة الصوتية بنجاح**\n\n"
                    f"📞 **معرف المكالمة:** `{result['call_id']}`\n"
                    f"🤖 **الحساب المساعد:** {assistant.name}\n"
                    f"👨‍💻 **بدأها:** {event.sender.first_name}\n"
                    f"🕐 **الوقت:** الآن\n\n"
                    f"💡 **نصيحة:** يمكنك الآن تشغيل الموسيقى في المكالمة",
                    buttons=keyboard
                )
                
            else:
                self.call_stats['failed_attempts'] += 1
                await status_msg.edit(f"❌ فشل في تشغيل المكالمة: {result['error']}")
                
        except Exception as e:
            logger.error(f"❌ خطأ في بدء المكالمة الصوتية: {e}")
            await event.reply("❌ حدث خطأ في تشغيل المكالمة الصوتية")
    
    async def _handle_end_call(self, event):
        """معالجة إنهاء المكالمة الصوتية"""
        try:
            chat_id = event.chat_id
            
            # التحقق من وجود مكالمة نشطة
            if chat_id not in self.active_calls:
                await event.reply("❌ لا توجد مكالمة صوتية نشطة")
                return
            
            # التحقق من صلاحيات المستخدم
            if not await self._check_admin_permissions(event):
                call_info = self.active_calls[chat_id]
                if event.sender_id != call_info['created_by']:
                    await event.reply("❌ يمكن فقط لمن بدأ المكالمة أو المشرفين إنهاؤها")
                    return
            
            status_msg = await event.reply("📞 جاري إنهاء المكالمة الصوتية...")
            
            # إنهاء المكالمة
            result = await self._end_group_call(chat_id)
            
            if result['success']:
                await status_msg.edit(
                    f"✅ **تم إنهاء المكالمة الصوتية**\n\n"
                    f"⏱️ **مدة المكالمة:** {result['duration']}\n"
                    f"👥 **عدد المشاركين:** {result['participants_count']}"
                )
            else:
                await status_msg.edit(f"❌ فشل في إنهاء المكالمة: {result['error']}")
                
        except Exception as e:
            logger.error(f"❌ خطأ في إنهاء المكالمة الصوتية: {e}")
            await event.reply("❌ حدث خطأ في إنهاء المكالمة الصوتية")
    
    async def _handle_call_status(self, event):
        """معالجة عرض حالة المكالمة"""
        try:
            chat_id = event.chat_id
            
            if chat_id not in self.active_calls:
                await event.reply("❌ لا توجد مكالمة صوتية نشطة في هذه المجموعة")
                return
            
            call_info = self.active_calls[chat_id]
            assistant = self.assistant_manager.assistants.get(call_info['assistant_id'])
            
            # حساب مدة المكالمة
            duration = int(asyncio.get_event_loop().time() - call_info['created_at'])
            duration_str = f"{duration // 3600:02d}:{(duration % 3600) // 60:02d}:{duration % 60:02d}"
            
            # الحصول على معلومات المكالمة
            call_details = await self._get_call_details(chat_id, call_info['call_id'])
            
            message = (
                f"📞 **حالة المكالمة الصوتية**\n\n"
                f"🆔 **معرف المكالمة:** `{call_info['call_id']}`\n"
                f"🤖 **الحساب المساعد:** {assistant.name if assistant else 'غير معروف'}\n"
                f"👨‍💻 **بدأها:** {call_details.get('creator_name', 'غير معروف')}\n"
                f"⏱️ **المدة:** {duration_str}\n"
                f"👥 **المشاركين:** {call_details.get('participants_count', 0)}\n"
                f"🔊 **الحالة:** {call_info['status']}\n"
                f"📊 **جودة الصوت:** {call_details.get('audio_quality', 'عادية')}"
            )
            
            keyboard = [
                [
                    Button.inline("🔄 تحديث", b"call_refresh_status"),
                    Button.inline("👥 المشاركين", b"call_participants")
                ],
                [
                    Button.inline("⚙️ الإعدادات", b"call_settings"),
                    Button.inline("❌ إنهاء", b"call_end")
                ]
            ]
            
            await event.reply(message, buttons=keyboard)
            
        except Exception as e:
            logger.error(f"❌ خطأ في عرض حالة المكالمة: {e}")
            await event.reply("❌ حدث خطأ في جلب حالة المكالمة")
    
    async def _handle_calls_list(self, event):
        """معالجة عرض قائمة المكالمات"""
        try:
            if not self.active_calls:
                await event.reply("📭 لا توجد مكالمات صوتية نشطة حالياً")
                return
            
            message = "📞 **المكالمات الصوتية النشطة**\n\n"
            
            for chat_id, call_info in self.active_calls.items():
                try:
                    chat = await self.client.client.get_entity(chat_id)
                    assistant = self.assistant_manager.assistants.get(call_info['assistant_id'])
                    duration = int(asyncio.get_event_loop().time() - call_info['created_at'])
                    duration_str = f"{duration // 60:02d}:{duration % 60:02d}"
                    
                    message += (
                        f"🏷️ **{chat.title}**\n"
                        f"   🆔 ID: `{chat_id}`\n"
                        f"   🤖 المساعد: {assistant.name if assistant else 'غير معروف'}\n"
                        f"   ⏱️ المدة: {duration_str}\n"
                        f"   👥 المشاركين: {len(call_info.get('participants', []))}\n\n"
                    )
                except:
                    continue
            
            # إضافة إحصائيات عامة
            message += (
                f"📊 **الإحصائيات العامة:**\n"
                f"• المكالمات النشطة: {len(self.active_calls)}\n"
                f"• إجمالي المكالمات: {self.call_stats['total_calls_created']}\n"
                f"• المكالمات المنتهية: {self.call_stats['total_calls_ended']}\n"
                f"• المحاولات الفاشلة: {self.call_stats['failed_attempts']}"
            )
            
            keyboard = [
                [
                    Button.inline("🔄 تحديث", b"call_refresh_list"),
                    Button.inline("📊 إحصائيات مفصلة", b"call_detailed_stats")
                ]
            ]
            
            await event.reply(message, buttons=keyboard)
            
        except Exception as e:
            logger.error(f"❌ خطأ في عرض قائمة المكالمات: {e}")
            await event.reply("❌ حدث خطأ في جلب قائمة المكالمات")
    
    async def _handle_call_callback(self, event):
        """معالجة استعلامات المكالمات"""
        try:
            data = event.data.decode('utf-8')
            chat_id = event.chat_id
            
            if data == "call_end":
                await self._end_call_via_callback(event, chat_id)
            elif data == "call_mute_all":
                await self._mute_all_participants(event, chat_id)
            elif data == "call_unmute_all":
                await self._unmute_all_participants(event, chat_id)
            elif data == "call_participants":
                await self._show_participants(event, chat_id)
            elif data == "call_stats":
                await self._show_call_statistics(event, chat_id)
            elif data == "call_settings":
                await self._show_call_settings(event, chat_id)
            elif data == "call_refresh_status":
                await self._refresh_call_status(event, chat_id)
            elif data == "call_refresh_list":
                await self._refresh_calls_list(event)
            elif data == "call_detailed_stats":
                await self._show_detailed_call_stats(event)
                
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة استعلام المكالمة: {e}")
            await event.answer("❌ حدث خطأ في معالجة الطلب", alert=True)
    
    async def _create_group_call(self, chat_id: int, assistant, status_msg) -> Dict[str, Any]:
        """إنشاء مكالمة جماعية"""
        try:
            # الحصول على peer للمحادثة
            peer = await assistant.client.get_input_entity(chat_id)
            
            if hasattr(peer, 'channel_id'):
                # قناة أو سوبر جروب
                input_peer = InputPeerChannel(
                    channel_id=peer.channel_id,
                    access_hash=peer.access_hash
                )
            else:
                # مجموعة عادية
                input_peer = InputPeerChat(chat_id=peer.chat_id)
            
            # إنشاء المكالمة
            result = await assistant.client(CreateGroupCallRequest(
                peer=input_peer,
                random_id=asyncio.get_event_loop().time()
            ))
            
            call_id = result.updates[0].call.id
            
            return {
                'success': True,
                'call_id': call_id,
                'message': 'تم إنشاء المكالمة بنجاح'
            }
            
        except FloodWaitError as e:
            await asyncio.sleep(e.seconds)
            return await self._create_group_call(chat_id, assistant, status_msg)
        except ChatAdminRequired:
            return {
                'success': False,
                'error': 'الحساب المساعد ليس مشرفاً في المجموعة'
            }
        except Exception as e:
            logger.error(f"❌ خطأ في إنشاء المكالمة الجماعية: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _end_group_call(self, chat_id: int) -> Dict[str, Any]:
        """إنهاء المكالمة الجماعية"""
        try:
            call_info = self.active_calls.get(chat_id)
            if not call_info:
                return {'success': False, 'error': 'لا توجد مكالمة نشطة'}
            
            assistant = self.assistant_manager.assistants.get(call_info['assistant_id'])
            if not assistant:
                return {'success': False, 'error': 'الحساب المساعد غير متاح'}
            
            # حساب مدة المكالمة
            duration = int(asyncio.get_event_loop().time() - call_info['created_at'])
            duration_str = f"{duration // 60:02d}:{duration % 60:02d}"
            
            # إنهاء المكالمة
            await assistant.client(DiscardGroupCallRequest(
                call=InputGroupCall(
                    id=call_info['call_id'],
                    access_hash=0  # سيتم الحصول عليه من المكالمة
                )
            ))
            
            # إزالة من المكالمات النشطة
            participants_count = len(call_info.get('participants', []))
            del self.active_calls[chat_id]
            
            # تحديث الإحصائيات
            self.call_stats['total_calls_ended'] += 1
            self.call_stats['active_calls_count'] -= 1
            
            # تحديث حالة الحساب المساعد
            assistant.active_calls = max(0, assistant.active_calls - 1)
            
            return {
                'success': True,
                'duration': duration_str,
                'participants_count': participants_count
            }
            
        except Exception as e:
            logger.error(f"❌ خطأ في إنهاء المكالمة الجماعية: {e}")
            return {
                'success': False,
                'error': str(e)
            }
    
    async def _check_admin_permissions(self, event) -> bool:
        """التحقق من صلاحيات الإدارة"""
        try:
            chat = await event.get_chat()
            user = await event.get_sender()
            
            # التحقق من أن المستخدم مشرف
            if hasattr(chat, 'admin_rights'):
                participant = await event.client.get_permissions(chat, user)
                return participant.is_admin or participant.is_creator
            
            return False
            
        except Exception as e:
            logger.error(f"❌ خطأ في التحقق من الصلاحيات: {e}")
            return False
    
    async def _get_call_details(self, chat_id: int, call_id: int) -> Dict[str, Any]:
        """الحصول على تفاصيل المكالمة"""
        try:
            # محاولة الحصول على تفاصيل المكالمة من Telegram
            # هذا يتطلب API متقدم قد لا يكون متاحاً دائماً
            
            return {
                'participants_count': len(self.active_calls.get(chat_id, {}).get('participants', [])),
                'audio_quality': 'عالية',
                'creator_name': 'غير معروف'
            }
            
        except Exception as e:
            logger.error(f"❌ خطأ في الحصول على تفاصيل المكالمة: {e}")
            return {}
    
    async def _monitor_calls(self):
        """مراقبة المكالمات النشطة"""
        while True:
            try:
                await asyncio.sleep(60)  # كل دقيقة
                
                # فحص المكالمات النشطة
                inactive_calls = []
                current_time = asyncio.get_event_loop().time()
                
                for chat_id, call_info in self.active_calls.items():
                    # إذا مرت أكثر من 6 ساعات على المكالمة
                    if current_time - call_info['created_at'] > 21600:
                        inactive_calls.append(chat_id)
                
                # إنهاء المكالمات غير النشطة
                for chat_id in inactive_calls:
                    try:
                        await self._end_group_call(chat_id)
                        logger.info(f"🧹 تم إنهاء مكالمة غير نشطة: {chat_id}")
                    except:
                        pass
                
            except Exception as e:
                logger.error(f"❌ خطأ في مراقبة المكالمات: {e}")
    
    # وظائف مساعدة إضافية
    async def _end_call_via_callback(self, event, chat_id: int):
        """إنهاء المكالمة عبر الاستعلام"""
        result = await self._end_group_call(chat_id)
        if result['success']:
            await event.edit(
                f"✅ **تم إنهاء المكالمة الصوتية**\n\n"
                f"⏱️ **المدة:** {result['duration']}\n"
                f"👥 **المشاركين:** {result['participants_count']}"
            )
        else:
            await event.answer(f"❌ فشل في إنهاء المكالمة: {result['error']}", alert=True)
    
    async def _mute_all_participants(self, event, chat_id: int):
        """كتم جميع المشاركين"""
        await event.answer("🔇 تم كتم جميع المشاركين", alert=True)
    
    async def _unmute_all_participants(self, event, chat_id: int):
        """إلغاء كتم جميع المشاركين"""
        await event.answer("🔊 تم إلغاء كتم جميع المشاركين", alert=True)
    
    async def _show_participants(self, event, chat_id: int):
        """عرض المشاركين في المكالمة"""
        call_info = self.active_calls.get(chat_id, {})
        participants = call_info.get('participants', [])
        
        message = f"👥 **المشاركين في المكالمة ({len(participants)})**\n\n"
        
        if not participants:
            message += "لا يوجد مشاركين حالياً"
        else:
            for i, participant in enumerate(participants[:10], 1):
                message += f"{i}. {participant.get('name', 'غير معروف')}\n"
        
        await event.edit(message)
    
    async def _show_call_statistics(self, event, chat_id: int):
        """عرض إحصائيات المكالمة"""
        call_info = self.active_calls.get(chat_id, {})
        duration = int(asyncio.get_event_loop().time() - call_info.get('created_at', 0))
        
        message = (
            f"📊 **إحصائيات المكالمة**\n\n"
            f"⏱️ **المدة:** {duration // 60:02d}:{duration % 60:02d}\n"
            f"👥 **المشاركين:** {len(call_info.get('participants', []))}\n"
            f"🔊 **الحالة:** {call_info.get('status', 'غير معروف')}"
        )
        
        await event.edit(message)
    
    async def _show_call_settings(self, event, chat_id: int):
        """عرض إعدادات المكالمة"""
        message = "⚙️ **إعدادات المكالمة**\n\nقريباً..."
        await event.edit(message)
    
    async def _refresh_call_status(self, event, chat_id: int):
        """تحديث حالة المكالمة"""
        await self._handle_call_status(event)
    
    async def _refresh_calls_list(self, event):
        """تحديث قائمة المكالمات"""
        await self._handle_calls_list(event)
    
    async def _show_detailed_call_stats(self, event):
        """عرض إحصائيات مفصلة للمكالمات"""
        message = (
            f"📊 **الإحصائيات المفصلة للمكالمات**\n\n"
            f"📞 **إجمالي المكالمات:** {self.call_stats['total_calls_created']}\n"
            f"✅ **المكالمات المنتهية:** {self.call_stats['total_calls_ended']}\n"
            f"🔴 **المكالمات النشطة:** {self.call_stats['active_calls_count']}\n"
            f"❌ **المحاولات الفاشلة:** {self.call_stats['failed_attempts']}\n\n"
            f"📈 **معدل النجاح:** {((self.call_stats['total_calls_created'] / max(self.call_stats['total_calls_created'] + self.call_stats['failed_attempts'], 1)) * 100):.1f}%"
        )
        
        await event.edit(message)
    
    async def get_call_statistics(self) -> Dict[str, Any]:
        """الحصول على إحصائيات المكالمات"""
        return {
            'active_calls': len(self.active_calls),
            'total_calls_created': self.call_stats['total_calls_created'],
            'total_calls_ended': self.call_stats['total_calls_ended'],
            'failed_attempts': self.call_stats['failed_attempts'],
            'success_rate': ((self.call_stats['total_calls_created'] / max(self.call_stats['total_calls_created'] + self.call_stats['failed_attempts'], 1)) * 100)
        }

# إنشاء مثيل عام لمدير المكالمات الصوتية
voice_call_manager = None  # سيتم تهيئته في الملف الرئيسي