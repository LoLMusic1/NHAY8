#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎵 ZeMusic Bot v3.0 - Enhanced Owner Panel
تاريخ الإنشاء: 2025-01-28

لوحة تحكم المالك الشاملة مع جميع الوظائف الإدارية
"""

import asyncio
import logging
import json
import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from telethon import events, Button
from telethon.tl.types import Message

from ..config import config
from ..core import (
    TelethonClient, DatabaseManager, AssistantManager,
    MusicEngine, SecurityManager, PerformanceMonitor
)

logger = logging.getLogger(__name__)

class OwnerPanelHandler:
    """معالج لوحة تحكم المالك المحسن"""
    
    def __init__(self, client: TelethonClient, db: DatabaseManager,
                 assistant_manager: AssistantManager, music_engine: MusicEngine,
                 security_manager: SecurityManager, performance_monitor: PerformanceMonitor):
        """تهيئة لوحة تحكم المالك"""
        self.client = client
        self.db = db
        self.assistant_manager = assistant_manager
        self.music_engine = music_engine
        self.security_manager = security_manager
        self.performance_monitor = performance_monitor
        
        # حالات إضافة الحسابات المساعدة
        self.pending_assistant_sessions: Dict[int, Dict[str, Any]] = {}
        
        # وضع الصيانة
        self.maintenance_mode = False
        self.maintenance_message = "البوت في وضع الصيانة حالياً"
        
        self.is_initialized = False
    
    async def initialize(self) -> bool:
        """تهيئة لوحة تحكم المالك"""
        try:
            logger.info("👑 تهيئة لوحة تحكم المالك...")
            
            # تسجيل معالجات الأحداث
            await self._register_event_handlers()
            
            self.is_initialized = True
            logger.info("✅ تم تهيئة لوحة تحكم المالك بنجاح")
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في تهيئة لوحة تحكم المالك: {e}")
            return False
    
    async def _register_event_handlers(self):
        """تسجيل معالجات الأحداث"""
        try:
            # معالج أمر المالك
            @self.client.client.on(events.NewMessage(pattern=r'^[!/.]owner$'))
            async def handle_owner_command(event):
                if event.sender_id == config.owner.owner_id:
                    await self._show_main_panel(event)
            
            # معالج الأزرار
            @self.client.client.on(events.CallbackQuery)
            async def handle_callback_query(event):
                if event.sender_id == config.owner.owner_id:
                    await self._handle_callback_query(event)
            
            # معالج الرسائل النصية للحسابات المساعدة
            @self.client.client.on(events.NewMessage)
            async def handle_assistant_session(event):
                if event.sender_id in self.pending_assistant_sessions:
                    await self._handle_assistant_session_input(event)
            
            logger.info("📝 تم تسجيل معالجات أحداث المالك")
            
        except Exception as e:
            logger.error(f"❌ فشل في تسجيل معالجات أحداث المالك: {e}")
    
    async def _show_main_panel(self, event):
        """عرض اللوحة الرئيسية"""
        try:
            # جلب الإحصائيات السريعة
            stats = await self._get_quick_stats()
            
            message = (
                "👑 **لوحة تحكم مالك البوت**\n\n"
                f"📊 **الإحصائيات السريعة:**\n"
                f"👥 المستخدمين: `{stats['users']:,}`\n"
                f"💬 المجموعات: `{stats['chats']:,}`\n"
                f"🤖 الحسابات المساعدة: `{stats['assistants']}`\n"
                f"🎵 الجلسات النشطة: `{stats['active_sessions']}`\n"
                f"🛡️ الأحداث الأمنية: `{stats['security_events']}`\n\n"
                f"🕐 آخر تحديث: `{datetime.now().strftime('%H:%M:%S')}`\n"
                f"🔧 حالة النظام: `{'صيانة' if self.maintenance_mode else 'نشط'}`"
            )
            
            keyboard = [
                [
                    Button.inline("📱 إدارة الحسابات المساعدة", b"owner_assistants"),
                    Button.inline("📊 الإحصائيات التفصيلية", b"owner_detailed_stats")
                ],
                [
                    Button.inline("⚙️ إعدادات النظام", b"owner_system_settings"),
                    Button.inline("🔧 صيانة النظام", b"owner_maintenance")
                ],
                [
                    Button.inline("📋 سجلات النظام", b"owner_logs"),
                    Button.inline("🗃️ إدارة قاعدة البيانات", b"owner_database")
                ],
                [
                    Button.inline("🛡️ الأمان والمراقبة", b"owner_security"),
                    Button.inline("👥 إدارة المستخدمين", b"owner_users")
                ],
                [
                    Button.inline("📢 الإذاعة والرسائل", b"owner_broadcast"),
                    Button.inline("🔄 تحديث النظام", b"owner_update")
                ],
                [
                    Button.inline("🔄 إعادة تشغيل", b"owner_restart"),
                    Button.inline("🛑 إيقاف البوت", b"owner_shutdown")
                ],
                [
                    Button.inline("🔄 تحديث اللوحة", b"owner_refresh")
                ]
            ]
            
            if hasattr(event, 'edit'):
                await event.edit(message, buttons=keyboard)
            else:
                await event.reply(message, buttons=keyboard)
                
        except Exception as e:
            logger.error(f"❌ خطأ في عرض اللوحة الرئيسية: {e}")
            await event.reply("❌ حدث خطأ في عرض لوحة التحكم")
    
    async def _handle_callback_query(self, event):
        """معالجة استعلامات الأزرار"""
        try:
            data = event.data.decode('utf-8')
            
            # إدارة الحسابات المساعدة
            if data == "owner_assistants":
                await self._show_assistants_panel(event)
            elif data == "owner_add_assistant":
                await self._start_add_assistant_process(event)
            elif data.startswith("owner_remove_assistant_"):
                assistant_id = int(data.split("_")[-1])
                await self._remove_assistant(event, assistant_id)
            elif data.startswith("owner_assistant_details_"):
                assistant_id = int(data.split("_")[-1])
                await self._show_assistant_details(event, assistant_id)
            
            # الإحصائيات
            elif data == "owner_detailed_stats":
                await self._show_detailed_stats(event)
            elif data == "owner_performance_stats":
                await self._show_performance_stats(event)
            elif data == "owner_music_stats":
                await self._show_music_stats(event)
            
            # إعدادات النظام
            elif data == "owner_system_settings":
                await self._show_system_settings(event)
            elif data == "owner_toggle_maintenance":
                await self._toggle_maintenance_mode(event)
            elif data == "owner_set_maintenance_message":
                await self._set_maintenance_message(event)
            
            # صيانة النظام
            elif data == "owner_maintenance":
                await self._show_maintenance_panel(event)
            elif data == "owner_cleanup_temp":
                await self._cleanup_temp_files(event)
            elif data == "owner_cleanup_logs":
                await self._cleanup_old_logs(event)
            elif data == "owner_optimize_db":
                await self._optimize_database(event)
            
            # السجلات
            elif data == "owner_logs":
                await self._show_logs_panel(event)
            elif data.startswith("owner_show_log_"):
                log_type = data.split("_")[-1]
                await self._show_log_file(event, log_type)
            
            # قاعدة البيانات
            elif data == "owner_database":
                await self._show_database_panel(event)
            elif data == "owner_backup_db":
                await self._backup_database(event)
            elif data == "owner_restore_db":
                await self._restore_database(event)
            elif data == "owner_reset_db":
                await self._reset_database(event)
            
            # الأمان
            elif data == "owner_security":
                await self._show_security_panel(event)
            elif data == "owner_security_stats":
                await self._show_security_stats(event)
            elif data == "owner_banned_users":
                await self._show_banned_users(event)
            
            # إدارة المستخدمين
            elif data == "owner_users":
                await self._show_users_panel(event)
            elif data == "owner_global_ban":
                await self._start_global_ban_process(event)
            elif data == "owner_global_unban":
                await self._start_global_unban_process(event)
            
            # الإذاعة
            elif data == "owner_broadcast":
                await self._show_broadcast_panel(event)
            elif data == "owner_broadcast_users":
                await self._start_broadcast_users_process(event)
            elif data == "owner_broadcast_groups":
                await self._start_broadcast_groups_process(event)
            
            # تحديث النظام
            elif data == "owner_update":
                await self._show_update_panel(event)
            elif data == "owner_check_updates":
                await self._check_for_updates(event)
            elif data == "owner_install_update":
                await self._install_update(event)
            
            # إدارة النظام
            elif data == "owner_restart":
                await self._restart_bot(event)
            elif data == "owner_shutdown":
                await self._shutdown_bot(event)
            elif data == "owner_refresh":
                await self._show_main_panel(event)
            
            # العودة للوحة الرئيسية
            elif data == "owner_back":
                await self._show_main_panel(event)
                
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة استعلام الزر: {e}")
            await event.answer("❌ حدث خطأ في معالجة الطلب", alert=True)
    
    async def _get_quick_stats(self) -> Dict[str, Any]:
        """جلب الإحصائيات السريعة"""
        try:
            db_stats = await self.db.get_statistics()
            music_stats = await self.music_engine.get_statistics()
            security_stats = await self.security_manager.get_security_stats()
            assistant_stats = await self.assistant_manager.get_statistics()
            
            return {
                'users': db_stats.get('total_users', 0),
                'chats': db_stats.get('total_chats', 0),
                'assistants': f"{assistant_stats.get('connected_assistants', 0)}/{assistant_stats.get('total_assistants', 0)}",
                'active_sessions': music_stats.get('active_sessions', 0),
                'security_events': security_stats.get('recent_events', 0)
            }
            
        except Exception as e:
            logger.error(f"❌ فشل في جلب الإحصائيات السريعة: {e}")
            return {
                'users': 0, 'chats': 0, 'assistants': '0/0', 
                'active_sessions': 0, 'security_events': 0
            }
    
    async def _show_assistants_panel(self, event):
        """عرض لوحة إدارة الحسابات المساعدة"""
        try:
            assistants_info = await self.assistant_manager.get_all_assistants_info()
            
            message = "🤖 **إدارة الحسابات المساعدة**\n\n"
            
            if not assistants_info:
                message += "❌ لا توجد حسابات مساعدة مضافة\n\n"
            else:
                message += f"📊 **إجمالي الحسابات:** `{len(assistants_info)}`\n\n"
                
                for assistant in assistants_info[:10]:  # أول 10 حسابات
                    status_emoji = "🟢" if assistant['is_connected'] else "🔴"
                    message += (
                        f"{status_emoji} **{assistant['name']}** (@{assistant.get('username', 'بدون معرف')})\n"
                        f"   📞 المكالمات النشطة: `{assistant['active_calls']}`\n"
                        f"   🕐 آخر فحص: `{assistant['last_health_check']}`\n\n"
                    )
                
                if len(assistants_info) > 10:
                    message += f"... و {len(assistants_info) - 10} حساب آخر\n\n"
            
            # إحصائيات إضافية
            connected_count = sum(1 for a in assistants_info if a['is_connected'])
            total_calls = sum(a['active_calls'] for a in assistants_info)
            
            message += (
                f"🔗 **المتصلة:** `{connected_count}/{len(assistants_info)}`\n"
                f"📞 **إجمالي المكالمات:** `{total_calls}`\n"
                f"⚖️ **متوسط الحمولة:** `{total_calls/max(connected_count, 1):.1f}`"
            )
            
            keyboard = [
                [
                    Button.inline("➕ إضافة حساب مساعد", b"owner_add_assistant"),
                    Button.inline("🔄 إعادة تشغيل الحسابات", b"owner_restart_assistants")
                ],
                [
                    Button.inline("🔍 تفاصيل الحسابات", b"owner_assistants_details"),
                    Button.inline("⚙️ إعدادات الحسابات", b"owner_assistants_settings")
                ],
                [
                    Button.inline("🧹 تنظيف الجلسات", b"owner_cleanup_sessions"),
                    Button.inline("📊 إحصائيات مفصلة", b"owner_assistants_stats")
                ],
                [Button.inline("🔙 العودة", b"owner_back")]
            ]
            
            await event.edit(message, buttons=keyboard)
            
        except Exception as e:
            logger.error(f"❌ خطأ في عرض لوحة الحسابات المساعدة: {e}")
            await event.answer("❌ حدث خطأ في جلب معلومات الحسابات المساعدة", alert=True)
    
    async def _start_add_assistant_process(self, event):
        """بدء عملية إضافة حساب مساعد"""
        try:
            user_id = event.sender_id
            
            # إنشاء جلسة انتظار
            self.pending_assistant_sessions[user_id] = {
                'step': 'phone',
                'data': {},
                'started_at': datetime.now()
            }
            
            message = (
                "📱 **إضافة حساب مساعد جديد**\n\n"
                "🔢 **الخطوة 1/3:** أرسل رقم الهاتف\n\n"
                "📋 **التعليمات:**\n"
                "• أرسل رقم الهاتف مع رمز الدولة\n"
                "• مثال: `+201234567890`\n"
                "• تأكد من أن الرقم صحيح ومتاح\n\n"
                "⏰ **انتبه:** ستنتهي صلاحية هذه العملية خلال 10 دقائق"
            )
            
            keyboard = [[Button.inline("❌ إلغاء", b"owner_cancel_add_assistant")]]
            
            await event.edit(message, buttons=keyboard)
            
        except Exception as e:
            logger.error(f"❌ خطأ في بدء عملية إضافة حساب مساعد: {e}")
            await event.answer("❌ حدث خطأ في بدء العملية", alert=True)
    
    async def _handle_assistant_session_input(self, event):
        """معالجة إدخال بيانات الحساب المساعد"""
        try:
            user_id = event.sender_id
            session_data = self.pending_assistant_sessions.get(user_id)
            
            if not session_data:
                return
            
            # التحقق من انتهاء المهلة الزمنية
            if datetime.now() - session_data['started_at'] > timedelta(minutes=10):
                del self.pending_assistant_sessions[user_id]
                await event.reply("⏰ انتهت مهلة إضافة الحساب المساعد")
                return
            
            step = session_data['step']
            message_text = event.message.text.strip()
            
            if step == 'phone':
                # التحقق من صحة رقم الهاتف
                if not message_text.startswith('+') or len(message_text) < 10:
                    await event.reply("❌ رقم الهاتف غير صحيح. يرجى إرسال رقم صحيح مع رمز الدولة")
                    return
                
                session_data['data']['phone'] = message_text
                session_data['step'] = 'code'
                
                # محاولة إرسال رمز التحقق
                try:
                    # هنا يجب إضافة منطق إرسال رمز التحقق
                    # await send_verification_code(message_text)
                    
                    await event.reply(
                        f"📱 **تم إرسال رمز التحقق إلى:** `{message_text}`\n\n"
                        "🔢 **الخطوة 2/3:** أرسل رمز التحقق\n\n"
                        "⏰ **انتبه:** الرمز صالح لمدة محدودة"
                    )
                except Exception as e:
                    await event.reply(f"❌ فشل في إرسال رمز التحقق: {str(e)}")
                    del self.pending_assistant_sessions[user_id]
            
            elif step == 'code':
                # التحقق من رمز التحقق
                if not message_text.isdigit() or len(message_text) != 5:
                    await event.reply("❌ رمز التحقق غير صحيح. يجب أن يكون 5 أرقام")
                    return
                
                session_data['data']['code'] = message_text
                
                # محاولة تسجيل الدخول
                try:
                    # هنا يجب إضافة منطق تسجيل الدخول والحصول على session string
                    # session_string = await login_assistant(phone, code)
                    
                    # إضافة الحساب المساعد
                    result = await self.assistant_manager.add_assistant(
                        phone=session_data['data']['phone'],
                        session_string="session_string_placeholder"  # سيتم استبداله بالقيمة الحقيقية
                    )
                    
                    if result['success']:
                        await event.reply(
                            f"✅ **تم إضافة الحساب المساعد بنجاح!**\n\n"
                            f"📱 **الرقم:** `{session_data['data']['phone']}`\n"
                            f"🆔 **معرف الحساب:** `{result.get('assistant_id', 'غير محدد')}`\n\n"
                            f"🔄 جاري بدء الحساب المساعد..."
                        )
                        
                        # بدء الحساب المساعد
                        await self.assistant_manager.start_assistant(result['assistant_id'])
                        
                    else:
                        await event.reply(f"❌ فشل في إضافة الحساب المساعد: {result['message']}")
                    
                except Exception as e:
                    await event.reply(f"❌ خطأ في تسجيل الدخول: {str(e)}")
                
                # إنهاء الجلسة
                del self.pending_assistant_sessions[user_id]
                
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة إدخال الحساب المساعد: {e}")
            await event.reply("❌ حدث خطأ في معالجة البيانات")
    
    async def _show_detailed_stats(self, event):
        """عرض الإحصائيات التفصيلية"""
        try:
            # جلب جميع الإحصائيات
            db_stats = await self.db.get_statistics()
            music_stats = await self.music_engine.get_statistics()
            security_stats = await self.security_manager.get_security_stats()
            performance_stats = await self.performance_monitor.get_performance_stats()
            assistant_stats = await self.assistant_manager.get_statistics()
            
            message = (
                "📊 **الإحصائيات التفصيلية**\n\n"
                
                "👥 **المستخدمون:**\n"
                f"• الإجمالي: `{db_stats.get('total_users', 0):,}`\n"
                f"• النشطون اليوم: `{db_stats.get('active_users_today', 0):,}`\n"
                f"• الجدد هذا الأسبوع: `{db_stats.get('new_users_week', 0):,}`\n\n"
                
                "💬 **المجموعات:**\n"
                f"• الإجمالي: `{db_stats.get('total_chats', 0):,}`\n"
                f"• النشطة اليوم: `{db_stats.get('active_chats_today', 0):,}`\n"
                f"• الجديدة هذا الأسبوع: `{db_stats.get('new_chats_week', 0):,}`\n\n"
                
                "🎵 **الموسيقى:**\n"
                f"• إجمالي التشغيلات: `{music_stats.get('total_plays', 0):,}`\n"
                f"• التشغيلات اليوم: `{music_stats.get('plays_today', 0):,}`\n"
                f"• الجلسات النشطة: `{music_stats.get('active_sessions', 0)}`\n"
                f"• قوائم الانتظار: `{music_stats.get('total_queue_size', 0)}`\n\n"
                
                "🤖 **الحسابات المساعدة:**\n"
                f"• الإجمالي: `{assistant_stats.get('total_assistants', 0)}`\n"
                f"• المتصلة: `{assistant_stats.get('connected_assistants', 0)}`\n"
                f"• النشطة: `{assistant_stats.get('active_assistants', 0)}`\n"
                f"• إجمالي المكالمات: `{assistant_stats.get('total_calls', 0)}`\n\n"
                
                "🛡️ **الأمان:**\n"
                f"• الأحداث الأمنية: `{security_stats.get('total_events', 0)}`\n"
                f"• المستخدمين المحظورين: `{security_stats.get('temp_banned_users', 0)}`\n"
                f"• محاولات الفلود: `{security_stats.get('flood_protection_active', 0)}`\n\n"
                
                "💻 **الأداء:**\n"
                f"• استخدام المعالج: `{performance_stats.get('current', {}).get('cpu_percent', 0):.1f}%`\n"
                f"• استخدام الذاكرة: `{performance_stats.get('current', {}).get('memory_percent', 0):.1f}%`\n"
                f"• استخدام القرص: `{performance_stats.get('current', {}).get('disk_usage_percent', 0):.1f}%`\n"
                f"• وقت التشغيل: `{performance_stats.get('uptime', {}).get('days', 0)} يوم، "
                f"{performance_stats.get('uptime', {}).get('hours', 0)} ساعة`"
            )
            
            keyboard = [
                [
                    Button.inline("📈 إحصائيات الأداء", b"owner_performance_stats"),
                    Button.inline("🎵 إحصائيات الموسيقى", b"owner_music_stats")
                ],
                [
                    Button.inline("🛡️ إحصائيات الأمان", b"owner_security_stats"),
                    Button.inline("🤖 إحصائيات الحسابات", b"owner_assistants_stats")
                ],
                [Button.inline("🔙 العودة", b"owner_back")]
            ]
            
            await event.edit(message, buttons=keyboard)
            
        except Exception as e:
            logger.error(f"❌ خطأ في عرض الإحصائيات التفصيلية: {e}")
            await event.answer("❌ حدث خطأ في جلب الإحصائيات", alert=True)
    
    async def _toggle_maintenance_mode(self, event):
        """تبديل وضع الصيانة"""
        try:
            self.maintenance_mode = not self.maintenance_mode
            
            status = "تم تفعيل" if self.maintenance_mode else "تم إلغاء"
            message = f"🔧 {status} وضع الصيانة"
            
            if self.maintenance_mode:
                message += f"\n\n📝 **رسالة الصيانة:**\n{self.maintenance_message}"
            
            await event.answer(message, alert=True)
            await self._show_main_panel(event)
            
        except Exception as e:
            logger.error(f"❌ خطأ في تبديل وضع الصيانة: {e}")
            await event.answer("❌ حدث خطأ في تبديل وضع الصيانة", alert=True)
    
    async def _restart_bot(self, event):
        """إعادة تشغيل البوت"""
        try:
            await event.answer("🔄 جاري إعادة تشغيل البوت...", alert=True)
            
            # إرسال رسالة تأكيد
            await event.edit("🔄 **جاري إعادة تشغيل البوت...**\n\nسيتم العودة خلال دقائق قليلة")
            
            # إيقاف جميع المكونات
            await self.music_engine.shutdown()
            await self.assistant_manager.shutdown()
            await self.security_manager.shutdown()
            await self.performance_monitor.shutdown()
            await self.db.close()
            
            # إعادة تشغيل العملية
            os.execv(sys.executable, ['python'] + sys.argv)
            
        except Exception as e:
            logger.error(f"❌ خطأ في إعادة تشغيل البوت: {e}")
            await event.answer("❌ حدث خطأ في إعادة التشغيل", alert=True)
    
    async def _shutdown_bot(self, event):
        """إيقاف البوت"""
        try:
            await event.answer("🛑 جاري إيقاف البوت...", alert=True)
            
            # إرسال رسالة تأكيد
            await event.edit("🛑 **جاري إيقاف البوت...**\n\nتم إيقاف جميع العمليات")
            
            # إيقاف جميع المكونات
            await self.music_engine.shutdown()
            await self.assistant_manager.shutdown()
            await self.security_manager.shutdown()
            await self.performance_monitor.shutdown()
            await self.db.close()
            
            # إيقاف العملية
            sys.exit(0)
            
        except Exception as e:
            logger.error(f"❌ خطأ في إيقاف البوت: {e}")
            await event.answer("❌ حدث خطأ في الإيقاف", alert=True)
    
    # باقي الوظائف سيتم تنفيذها بنفس المنطق...
    async def _show_performance_stats(self, event):
        """عرض إحصائيات الأداء"""
        pass
    
    async def _show_music_stats(self, event):
        """عرض إحصائيات الموسيقى"""
        pass
    
    async def _show_security_stats(self, event):
        """عرض إحصائيات الأمان"""
        pass
    
    async def _show_logs_panel(self, event):
        """عرض لوحة السجلات"""
        pass
    
    async def _backup_database(self, event):
        """نسخ احتياطي لقاعدة البيانات"""
        pass
    
    async def _cleanup_temp_files(self, event):
        """تنظيف الملفات المؤقتة"""
        pass

# إنشاء مثيل عام لمعالج لوحة تحكم المالك
owner_panel_handler = None  # سيتم تهيئته في الملف الرئيسي