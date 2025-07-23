#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎵 ZeMusic Bot v3.0 - Developer Commands System
تاريخ الإنشاء: 2025-01-28

نظام أوامر المطورين المتقدم
"""

import asyncio
import logging
import os
import sys
import subprocess
import psutil
import time
from typing import Dict, List, Optional, Any
from telethon import events, Button
from telethon.tl.types import User
from datetime import datetime, timedelta

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import config
from ..core import TelethonClient, DatabaseManager, AssistantManager, MusicEngine, SecurityManager, PerformanceMonitor

logger = logging.getLogger(__name__)

class DeveloperCommandsPlugin:
    """بلاجين أوامر المطورين المتقدم"""
    
    def __init__(self, client: TelethonClient, db: DatabaseManager, assistant_manager: AssistantManager,
                 music_engine: MusicEngine, security_manager: SecurityManager, performance_monitor: PerformanceMonitor):
        """تهيئة بلاجين أوامر المطورين"""
        self.client = client
        self.db = db
        self.assistant_manager = assistant_manager
        self.music_engine = music_engine
        self.security_manager = security_manager
        self.performance_monitor = performance_monitor
        
        # قائمة المطورين المصرح لهم
        self.authorized_developers = set(config.owner.sudo_users)
        self.authorized_developers.add(config.owner.owner_id)
        
        # إحصائيات أوامر المطورين
        self.dev_stats = {
            'commands_executed': 0,
            'system_restarts': 0,
            'database_operations': 0,
            'assistant_operations': 0,
            'security_actions': 0
        }
        
        # معلومات النظام
        self.system_info = {
            'start_time': datetime.now(),
            'last_restart': None,
            'version': '3.0.0 Enhanced',
            'python_version': f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
        }
        
    async def initialize(self) -> bool:
        """تهيئة بلاجين أوامر المطورين"""
        try:
            logger.info("👨‍💻 تهيئة بلاجين أوامر المطورين...")
            
            # تسجيل معالجات الأحداث
            await self._register_dev_handlers()
            
            logger.info("✅ تم تهيئة بلاجين أوامر المطورين بنجاح")
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في تهيئة بلاجين أوامر المطورين: {e}")
            return False
    
    async def _register_dev_handlers(self):
        """تسجيل معالجات أحداث المطورين"""
        try:
            # معالج عرض معلومات المطور
            @self.client.client.on(events.NewMessage(pattern=r'^(المبرمج|مبرمج السورس|مبرمج|مطور السورس|المطور)$'))
            async def handle_developer_info(event):
                await self._show_developer_info(event)
            
            # معالج لوحة تحكم المطور
            @self.client.client.on(events.NewMessage(pattern=r'^[!/.](?:dev|developer|مطور)$'))
            async def handle_dev_panel(event):
                await self._show_developer_panel(event)
            
            # معالج إعادة التشغيل
            @self.client.client.on(events.NewMessage(pattern=r'^[!/.](?:restart|إعادة تشغيل)$'))
            async def handle_restart(event):
                await self._handle_restart_command(event)
            
            # معالج التحديث
            @self.client.client.on(events.NewMessage(pattern=r'^[!/.](?:update|تحديث)$'))
            async def handle_update(event):
                await self._handle_update_command(event)
            
            # معالج معلومات النظام
            @self.client.client.on(events.NewMessage(pattern=r'^[!/.](?:sysinfo|معلومات النظام)$'))
            async def handle_system_info(event):
                await self._show_system_info(event)
            
            # معالج إحصائيات البوت
            @self.client.client.on(events.NewMessage(pattern=r'^[!/.](?:stats|إحصائيات)$'))
            async def handle_bot_stats(event):
                await self._show_bot_statistics(event)
            
            # معالج إدارة قاعدة البيانات
            @self.client.client.on(events.NewMessage(pattern=r'^[!/.](?:db|database|قاعدة البيانات)'))
            async def handle_database_commands(event):
                await self._handle_database_commands(event)
            
            # معالج إدارة الحسابات المساعدة
            @self.client.client.on(events.NewMessage(pattern=r'^[!/.](?:assistants|الحسابات المساعدة)'))
            async def handle_assistant_commands(event):
                await self._handle_assistant_commands(event)
            
            # معالج الأمان والحماية
            @self.client.client.on(events.NewMessage(pattern=r'^[!/.](?:security|الأمان)'))
            async def handle_security_commands(event):
                await self._handle_security_commands(event)
            
            # معالج تنفيذ الأكواد
            @self.client.client.on(events.NewMessage(pattern=r'^[!/.](?:eval|exec|تنفيذ)'))
            async def handle_code_execution(event):
                await self._handle_code_execution(event)
            
            # معالج السجلات
            @self.client.client.on(events.NewMessage(pattern=r'^[!/.](?:logs|السجلات)'))
            async def handle_logs_command(event):
                await self._handle_logs_command(event)
            
            # معالج استعلامات المطورين
            @self.client.client.on(events.CallbackQuery(pattern=b'dev_'))
            async def handle_dev_callback(event):
                await self._handle_dev_callback(event)
            
            logger.info("📝 تم تسجيل معالجات أوامر المطورين")
            
        except Exception as e:
            logger.error(f"❌ فشل في تسجيل معالجات المطورين: {e}")
    
    def _check_developer_permissions(self, user_id: int) -> bool:
        """التحقق من صلاحيات المطور"""
        return user_id in self.authorized_developers
    
    async def _show_developer_info(self, event):
        """عرض معلومات المطور"""
        try:
            # معلومات المطور الرئيسي
            dev_id = config.owner.owner_id
            
            try:
                dev_user = await self.client.client.get_entity(dev_id)
                dev_name = dev_user.first_name or "المطور"
                dev_username = getattr(dev_user, 'username', None)
                dev_bio = getattr(dev_user, 'about', 'مطور بوت الموسيقى المتقدم')
            except:
                dev_name = "المطور الرئيسي"
                dev_username = None
                dev_bio = "مطور بوت الموسيقى المتقدم"
            
            # إنشاء الرسالة
            message = (
                f"👨‍💻 **مطور البوت**\n\n"
                f"📛 **الاسم:** {dev_name}\n"
            )
            
            if dev_username:
                message += f"🔗 **المعرف:** @{dev_username}\n"
            
            message += (
                f"🆔 **الهوية:** `{dev_id}`\n"
                f"📝 **الوصف:** {dev_bio}\n\n"
                f"🎵 **معلومات البوت:**\n"
                f"• الإصدار: {self.system_info['version']}\n"
                f"• Python: {self.system_info['python_version']}\n"
                f"• وقت التشغيل: {self._get_uptime()}\n\n"
                f"💻 **التقنيات المستخدمة:**\n"
                f"• Telethon - للتفاعل مع تيليجرام\n"
                f"• PyTgCalls - للمكالمات الصوتية\n"
                f"• yt-dlp - لتحميل الموسيقى\n"
                f"• AsyncIO - للبرمجة غير المتزامنة\n\n"
                f"🌟 **ميزات البوت:**\n"
                f"• دعم 7000 مجموعة\n"
                f"• خدمة 70000 مستخدم\n"
                f"• 7 منصات موسيقية\n"
                f"• أداء فائق السرعة"
            )
            
            # لوحة مفاتيح تفاعلية
            keyboard = []
            
            # إضافة زر للتواصل مع المطور إذا كان لديه يوزر
            if dev_username:
                keyboard.append([Button.url(f"💬 تواصل مع {dev_name}", f"https://t.me/{dev_username}")])
            
            # إضافة أزرار إضافية للمطورين المصرح لهم
            if self._check_developer_permissions(event.sender_id):
                keyboard.extend([
                    [
                        Button.inline("🔧 لوحة المطور", b"dev_panel"),
                        Button.inline("📊 الإحصائيات", b"dev_stats")
                    ],
                    [
                        Button.inline("💻 معلومات النظام", b"dev_sysinfo"),
                        Button.inline("🔄 إعادة التشغيل", b"dev_restart")
                    ]
                ])
            
            keyboard.append([Button.inline("❌ إغلاق", b"close")])
            
            # إرسال الرسالة مع الصورة إذا كانت متوفرة
            try:
                # محاولة الحصول على صورة المطور
                photos = []
                async for photo in self.client.client.iter_profile_photos(dev_id, limit=1):
                    photos.append(photo)
                
                if photos:
                    await event.reply(
                        message,
                        file=photos[0],
                        buttons=keyboard
                    )
                else:
                    await event.reply(message, buttons=keyboard)
                    
            except:
                await event.reply(message, buttons=keyboard)
                
        except Exception as e:
            logger.error(f"❌ خطأ في عرض معلومات المطور: {e}")
            await event.reply("❌ حدث خطأ في جلب معلومات المطور")
    
    async def _show_developer_panel(self, event):
        """عرض لوحة تحكم المطور"""
        try:
            if not self._check_developer_permissions(event.sender_id):
                await event.reply("❌ هذا الأمر مخصص للمطورين فقط")
                return
            
            # معلومات سريعة عن النظام
            uptime = self._get_uptime()
            memory_usage = psutil.virtual_memory().percent
            cpu_usage = psutil.cpu_percent(interval=1)
            
            message = (
                f"🔧 **لوحة تحكم المطور**\n\n"
                f"⚡ **حالة النظام:**\n"
                f"• وقت التشغيل: {uptime}\n"
                f"• استخدام الذاكرة: {memory_usage:.1f}%\n"
                f"• استخدام المعالج: {cpu_usage:.1f}%\n\n"
                f"📊 **إحصائيات سريعة:**\n"
                f"• أوامر المطورين: {self.dev_stats['commands_executed']:,}\n"
                f"• إعادات التشغيل: {self.dev_stats['system_restarts']:,}\n"
                f"• عمليات قاعدة البيانات: {self.dev_stats['database_operations']:,}\n\n"
                f"🎵 **حالة البوت:**\n"
                f"• الحسابات المساعدة: {len(self.assistant_manager.assistants)}\n"
                f"• الجلسات النشطة: {len(self.music_engine.active_sessions)}\n"
                f"• المكالمات النشطة: {sum(len(calls) for calls in getattr(self.music_engine, 'active_calls', {}).values())}"
            )
            
            keyboard = [
                [
                    Button.inline("💻 معلومات النظام", b"dev_sysinfo"),
                    Button.inline("📊 الإحصائيات الكاملة", b"dev_full_stats")
                ],
                [
                    Button.inline("🗄️ قاعدة البيانات", b"dev_database"),
                    Button.inline("🤖 الحسابات المساعدة", b"dev_assistants")
                ],
                [
                    Button.inline("🛡️ الأمان", b"dev_security"),
                    Button.inline("📋 السجلات", b"dev_logs")
                ],
                [
                    Button.inline("🔄 إعادة تشغيل", b"dev_restart_confirm"),
                    Button.inline("⬆️ تحديث", b"dev_update")
                ],
                [
                    Button.inline("💻 تنفيذ كود", b"dev_exec"),
                    Button.inline("🧹 تنظيف", b"dev_cleanup")
                ]
            ]
            
            await event.reply(message, buttons=keyboard)
            
            # تحديث الإحصائيات
            self.dev_stats['commands_executed'] += 1
            
        except Exception as e:
            logger.error(f"❌ خطأ في عرض لوحة المطور: {e}")
            await event.reply("❌ حدث خطأ في عرض لوحة المطور")
    
    async def _handle_restart_command(self, event):
        """معالجة أمر إعادة التشغيل"""
        try:
            if not self._check_developer_permissions(event.sender_id):
                await event.reply("❌ هذا الأمر مخصص للمطورين فقط")
                return
            
            keyboard = [
                [
                    Button.inline("✅ تأكيد إعادة التشغيل", b"dev_restart_confirmed"),
                    Button.inline("❌ إلغاء", b"close")
                ]
            ]
            
            await event.reply(
                "🔄 **إعادة تشغيل البوت**\n\n"
                "⚠️ **تحذير:** سيتم إعادة تشغيل البوت وقطع جميع الاتصالات النشطة\n\n"
                "🔸 **سيتم حفظ:**\n"
                "• إعدادات قاعدة البيانات\n"
                "• إعدادات الحسابات المساعدة\n"
                "• السجلات والإحصائيات\n\n"
                "🔸 **سيتم فقدان:**\n"
                "• قوائم الانتظار النشطة\n"
                "• المكالمات الصوتية الجارية\n"
                "• الجلسات المؤقتة\n\n"
                "هل أنت متأكد من المتابعة؟",
                buttons=keyboard
            )
            
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة أمر إعادة التشغيل: {e}")
            await event.reply("❌ حدث خطأ في معالجة أمر إعادة التشغيل")
    
    async def _handle_update_command(self, event):
        """معالجة أمر التحديث"""
        try:
            if not self._check_developer_permissions(event.sender_id):
                await event.reply("❌ هذا الأمر مخصص للمطورين فقط")
                return
            
            update_msg = await event.reply("🔄 **جاري فحص التحديثات...**")
            
            try:
                # فحص Git للتحديثات
                result = subprocess.run(
                    ["git", "fetch", "--dry-run"],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0:
                    # فحص الاختلافات
                    diff_result = subprocess.run(
                        ["git", "log", "HEAD..origin/main", "--oneline"],
                        capture_output=True,
                        text=True,
                        timeout=30
                    )
                    
                    if diff_result.stdout.strip():
                        # يوجد تحديثات
                        updates = diff_result.stdout.strip().split('\n')
                        
                        message = (
                            f"⬆️ **تحديثات متوفرة ({len(updates)})**\n\n"
                            f"📋 **آخر التحديثات:**\n"
                        )
                        
                        for i, update in enumerate(updates[:5], 1):
                            message += f"{i}. {update[:60]}...\n"
                        
                        if len(updates) > 5:
                            message += f"... و {len(updates) - 5} تحديث آخر\n"
                        
                        message += "\n💡 **هل تريد تطبيق التحديثات؟**"
                        
                        keyboard = [
                            [
                                Button.inline("✅ تطبيق التحديثات", b"dev_apply_updates"),
                                Button.inline("❌ إلغاء", b"close")
                            ]
                        ]
                        
                        await update_msg.edit(message, buttons=keyboard)
                    else:
                        await update_msg.edit("✅ **البوت محدث بالفعل**\n\nلا توجد تحديثات جديدة متاحة")
                else:
                    await update_msg.edit("❌ **فشل في فحص التحديثات**\n\nتأكد من الاتصال بالإنترنت وإعدادات Git")
                    
            except subprocess.TimeoutExpired:
                await update_msg.edit("⏰ **انتهت مهلة فحص التحديثات**")
            except Exception as e:
                await update_msg.edit(f"❌ **خطأ في فحص التحديثات:**\n`{str(e)}`")
                
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة أمر التحديث: {e}")
            await event.reply("❌ حدث خطأ في معالجة أمر التحديث")
    
    async def _show_system_info(self, event):
        """عرض معلومات النظام"""
        try:
            if not self._check_developer_permissions(event.sender_id):
                await event.reply("❌ هذا الأمر مخصص للمطورين فقط")
                return
            
            # معلومات النظام
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            cpu_count = psutil.cpu_count()
            cpu_freq = psutil.cpu_freq()
            
            # معلومات Python
            python_version = sys.version
            
            # معلومات البوت
            uptime = self._get_uptime()
            
            message = (
                f"💻 **معلومات النظام**\n\n"
                f"🖥️ **النظام:**\n"
                f"• المنصة: {sys.platform}\n"
                f"• المعالج: {cpu_count} نواة\n"
                f"• تردد المعالج: {cpu_freq.current:.0f} MHz\n"
                f"• استخدام المعالج: {psutil.cpu_percent(interval=1):.1f}%\n\n"
                f"🧠 **الذاكرة:**\n"
                f"• الإجمالي: {self._format_bytes(memory.total)}\n"
                f"• المستخدم: {self._format_bytes(memory.used)} ({memory.percent:.1f}%)\n"
                f"• المتاح: {self._format_bytes(memory.available)}\n\n"
                f"💾 **التخزين:**\n"
                f"• الإجمالي: {self._format_bytes(disk.total)}\n"
                f"• المستخدم: {self._format_bytes(disk.used)} ({disk.percent:.1f}%)\n"
                f"• المتاح: {self._format_bytes(disk.free)}\n\n"
                f"🐍 **Python:**\n"
                f"• الإصدار: {self.system_info['python_version']}\n"
                f"• المسار: {sys.executable}\n\n"
                f"🎵 **البوت:**\n"
                f"• الإصدار: {self.system_info['version']}\n"
                f"• وقت التشغيل: {uptime}\n"
                f"• PID: {os.getpid()}\n"
                f"• الذاكرة المستخدمة: {self._format_bytes(psutil.Process().memory_info().rss)}"
            )
            
            keyboard = [
                [
                    Button.inline("🔄 تحديث", b"dev_sysinfo"),
                    Button.inline("📊 تفاصيل أكثر", b"dev_detailed_sysinfo")
                ]
            ]
            
            await event.reply(message, buttons=keyboard)
            
        except Exception as e:
            logger.error(f"❌ خطأ في عرض معلومات النظام: {e}")
            await event.reply("❌ حدث خطأ في جلب معلومات النظام")
    
    async def _show_bot_statistics(self, event):
        """عرض إحصائيات البوت"""
        try:
            if not self._check_developer_permissions(event.sender_id):
                # إحصائيات عامة للمستخدمين العاديين
                message = (
                    f"📊 **إحصائيات البوت العامة**\n\n"
                    f"🎵 **الموسيقى:**\n"
                    f"• المنصات المدعومة: 7\n"
                    f"• الجلسات النشطة: {len(getattr(self.music_engine, 'active_sessions', {}))}\n\n"
                    f"🤖 **الحسابات المساعدة:**\n"
                    f"• العدد الإجمالي: {len(getattr(self.assistant_manager, 'assistants', {}))}\n"
                    f"• النشطة: {len([a for a in getattr(self.assistant_manager, 'assistants', {}).values() if getattr(a, 'is_connected', False)])}\n\n"
                    f"⏱️ **وقت التشغيل:** {self._get_uptime()}\n"
                    f"🔢 **الإصدار:** {self.system_info['version']}"
                )
                
                await event.reply(message)
                return
            
            # إحصائيات مفصلة للمطورين
            # جمع الإحصائيات من جميع المكونات
            music_stats = await self.music_engine.get_statistics() if hasattr(self.music_engine, 'get_statistics') else {}
            assistant_stats = await self.assistant_manager.get_statistics() if hasattr(self.assistant_manager, 'get_statistics') else {}
            security_stats = await self.security_manager.get_statistics() if hasattr(self.security_manager, 'get_statistics') else {}
            
            message = (
                f"📊 **إحصائيات البوت المفصلة**\n\n"
                f"🎵 **محرك الموسيقى:**\n"
                f"• الجلسات النشطة: {music_stats.get('active_sessions', 0)}\n"
                f"• إجمالي التشغيلات: {music_stats.get('total_plays', 0):,}\n"
                f"• إجمالي التحميلات: {music_stats.get('total_downloads', 0):,}\n"
                f"• حجم قوائم الانتظار: {music_stats.get('total_queue_size', 0)}\n\n"
                f"🤖 **الحسابات المساعدة:**\n"
                f"• العدد الإجمالي: {assistant_stats.get('total_assistants', 0)}\n"
                f"• النشطة: {assistant_stats.get('active_assistants', 0)}\n"
                f"• المكالمات النشطة: {assistant_stats.get('active_calls', 0)}\n"
                f"• معدل النجاح: {assistant_stats.get('success_rate', 0):.1f}%\n\n"
                f"🛡️ **الأمان:**\n"
                f"• التحققات الأمنية: {security_stats.get('total_checks', 0):,}\n"
                f"• المستخدمين المحظورين: {security_stats.get('banned_users', 0):,}\n"
                f"• محاولات الاختراق: {security_stats.get('intrusion_attempts', 0):,}\n\n"
                f"👨‍💻 **أوامر المطورين:**\n"
                f"• الأوامر المنفذة: {self.dev_stats['commands_executed']:,}\n"
                f"• إعادات التشغيل: {self.dev_stats['system_restarts']:,}\n"
                f"• عمليات قاعدة البيانات: {self.dev_stats['database_operations']:,}\n\n"
                f"💻 **النظام:**\n"
                f"• وقت التشغيل: {self._get_uptime()}\n"
                f"• استخدام الذاكرة: {psutil.virtual_memory().percent:.1f}%\n"
                f"• استخدام المعالج: {psutil.cpu_percent(interval=1):.1f}%"
            )
            
            keyboard = [
                [
                    Button.inline("🔄 تحديث", b"dev_stats"),
                    Button.inline("📈 إحصائيات مفصلة", b"dev_detailed_stats")
                ]
            ]
            
            await event.reply(message, buttons=keyboard)
            
        except Exception as e:
            logger.error(f"❌ خطأ في عرض إحصائيات البوت: {e}")
            await event.reply("❌ حدث خطأ في جلب الإحصائيات")
    
    async def _handle_dev_callback(self, event):
        """معالجة استعلامات المطورين"""
        try:
            if not self._check_developer_permissions(event.sender_id):
                await event.answer("❌ غير مصرح لك", alert=True)
                return
            
            data = event.data.decode('utf-8')
            
            if data == "dev_panel":
                await self._show_developer_panel(event)
            elif data == "dev_stats":
                await self._show_bot_statistics(event)
            elif data == "dev_sysinfo":
                await self._show_system_info(event)
            elif data == "dev_restart_confirm":
                await self._handle_restart_command(event)
            elif data == "dev_restart_confirmed":
                await self._perform_restart(event)
            elif data == "dev_update":
                await self._handle_update_command(event)
            elif data == "dev_apply_updates":
                await self._apply_updates(event)
            elif data == "dev_database":
                await self._show_database_panel(event)
            elif data == "dev_assistants":
                await self._show_assistants_panel(event)
            elif data == "dev_security":
                await self._show_security_panel(event)
            elif data == "dev_logs":
                await self._show_logs_panel(event)
            elif data == "dev_exec":
                await self._show_code_execution_panel(event)
            elif data == "dev_cleanup":
                await self._perform_cleanup(event)
            
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة استعلام المطور: {e}")
            await event.answer("❌ حدث خطأ في معالجة الطلب", alert=True)
    
    # وظائف مساعدة
    def _get_uptime(self) -> str:
        """حساب وقت التشغيل"""
        try:
            uptime = datetime.now() - self.system_info['start_time']
            days = uptime.days
            hours, remainder = divmod(uptime.seconds, 3600)
            minutes, seconds = divmod(remainder, 60)
            
            if days > 0:
                return f"{days}د {hours}س {minutes}ق"
            elif hours > 0:
                return f"{hours}س {minutes}ق {seconds}ث"
            else:
                return f"{minutes}ق {seconds}ث"
                
        except Exception:
            return "غير معروف"
    
    def _format_bytes(self, bytes_value: int) -> str:
        """تنسيق البايتات"""
        try:
            for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
                if bytes_value < 1024.0:
                    return f"{bytes_value:.1f} {unit}"
                bytes_value /= 1024.0
            return f"{bytes_value:.1f} PB"
        except:
            return "غير معروف"
    
    async def _perform_restart(self, event):
        """تنفيذ إعادة التشغيل"""
        try:
            await event.edit(
                "🔄 **جاري إعادة تشغيل البوت...**\n\n"
                "⏳ سيعود البوت خلال دقائق قليلة\n"
                "🔄 يتم حفظ جميع الإعدادات..."
            )
            
            # تحديث الإحصائيات
            self.dev_stats['system_restarts'] += 1
            self.system_info['last_restart'] = datetime.now()
            
            # إيقاف جميع العمليات بأمان
            logger.info("🔄 بدء إعادة التشغيل...")
            
            # إعادة تشغيل البرنامج
            await asyncio.sleep(2)
            os.execv(sys.executable, ['python'] + sys.argv)
            
        except Exception as e:
            logger.error(f"❌ خطأ في إعادة التشغيل: {e}")
            await event.edit("❌ فشل في إعادة التشغيل")
    
    async def get_dev_statistics(self) -> Dict[str, Any]:
        """الحصول على إحصائيات أوامر المطورين"""
        return {
            'commands_executed': self.dev_stats['commands_executed'],
            'system_restarts': self.dev_stats['system_restarts'],
            'database_operations': self.dev_stats['database_operations'],
            'assistant_operations': self.dev_stats['assistant_operations'],
            'security_actions': self.dev_stats['security_actions'],
            'uptime': self._get_uptime(),
            'system_info': self.system_info.copy()
        }

# إنشاء مثيل عام لبلاجين أوامر المطورين
developer_commands_plugin = None  # سيتم تهيئته في الملف الرئيسي