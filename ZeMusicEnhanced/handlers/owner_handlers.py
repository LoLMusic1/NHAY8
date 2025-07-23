#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎵 ZeMusic Bot v3.0 - Owner Handlers
لوحة أوامر مالك البوت
"""

import asyncio
import logging
import psutil
import platform
import subprocess
import sys
import os
import re
from datetime import datetime
from telethon import events, Button

logger = logging.getLogger(__name__)

class OwnerHandlers:
    """لوحة أوامر المالك"""
    
    def __init__(self, client, db, config):
        self.client = client
        self.db = db
        self.config = config
        
    def register_handlers(self):
        """تسجيل جميع أوامر المالك"""
        
        @self.client.client.on(events.NewMessage(pattern=r'^[./!]?(owner|مالك|لوحة)$'))
        async def owner_panel_handler(event):
            """لوحة التحكم الرئيسية للمالك"""
            if event.sender_id != self.config.OWNER_ID:
                await event.respond("❌ **هذا الأمر للمالك فقط!**")
                return
            
            try:
                # جمع إحصائيات سريعة
                cpu_percent = psutil.cpu_percent()
                memory = psutil.virtual_memory()
                uptime = self._get_uptime()
                
                panel_text = f"""
🎛️ **لوحة تحكم مالك البوت**

👤 **المالك:** [{event.sender.first_name}](tg://user?id={event.sender_id})
🤖 **البوت:** {self.config.BOT_NAME} (@{self.config.BOT_USERNAME})

📊 **حالة النظام:**
• المعالج: {cpu_percent}%
• الذاكرة: {memory.percent}%
• وقت التشغيل: {uptime}

🎯 **اختر العملية المطلوبة:**
"""
                
                buttons = [
                    [Button.inline("📊 الإحصائيات", data="owner_stats"),
                     Button.inline("👥 المستخدمين", data="owner_users")],
                    [Button.inline("💬 المجموعات", data="owner_chats"),
                     Button.inline("🤖 الحسابات المساعدة", data="owner_assistants")],
                    [Button.inline("🗃️ قاعدة البيانات", data="owner_database"),
                     Button.inline("🔄 إعادة تشغيل", data="owner_restart")],
                    [Button.inline("📝 السجلات", data="owner_logs"),
                     Button.inline("⚙️ الإعدادات", data="owner_settings")],
                    [Button.inline("🛠️ الصيانة", data="owner_maintenance"),
                     Button.inline("📤 النسخ الاحتياطي", data="owner_backup")],
                    [Button.inline("🔄 تحديث", data="owner_refresh")]
                ]
                
                await event.respond(panel_text, buttons=buttons)
                
                logger.info(f"🎛️ لوحة المالك تم فتحها من قبل {event.sender_id}")
                
            except Exception as e:
                logger.error(f"❌ خطأ في لوحة المالك: {e}")
                await event.respond("❌ حدث خطأ في فتح لوحة التحكم")
        
        @self.client.client.on(events.CallbackQuery(pattern=r'^owner_(.+)$'))
        async def owner_callback_handler(event):
            """معالج أزرار لوحة المالك"""
            if event.sender_id != self.config.OWNER_ID:
                await event.answer("❌ هذا للمالك فقط!", alert=True)
                return
            
            action = event.pattern_match.group(1)
            
            try:
                if action == "stats":
                    await self._show_detailed_stats(event)
                elif action == "users":
                    await self._show_users_info(event)
                elif action == "chats":
                    await self._show_chats_info(event)
                elif action == "assistants":
                    await self._show_assistants_info(event)
                elif action == "database":
                    await self._show_database_info(event)
                elif action == "restart":
                    await self._restart_bot(event)
                elif action == "logs":
                    await self._show_logs(event)
                elif action == "settings":
                    await self._show_settings(event)
                elif action == "maintenance":
                    await self._show_maintenance(event)
                elif action == "backup":
                    await self._create_backup(event)
                elif action == "refresh":
                    await self._refresh_panel(event)
                else:
                    await event.answer("❌ عملية غير معروفة", alert=True)
                    
            except Exception as e:
                logger.error(f"❌ خطأ في معالج المالك: {e}")
                await event.answer("❌ حدث خطأ في العملية", alert=True)
        
        @self.client.client.on(events.NewMessage(pattern=r'^[./!]?(eval|تنفيذ)\s+(.+)', flags=re.DOTALL))
        async def eval_handler(event):
            """تنفيذ كود Python (للمالك فقط)"""
            if event.sender_id != self.config.OWNER_ID:
                return
            
            try:
                code = event.pattern_match.group(2)
                
                # تنفيذ الكود
                try:
                    result = eval(code)
                    if asyncio.iscoroutine(result):
                        result = await result
                except:
                    exec(code)
                    result = "تم التنفيذ بنجاح"
                
                await event.respond(f"```python\n{code}\n```\n\n**النتيجة:**\n```\n{result}\n```")
                
            except Exception as e:
                await event.respond(f"❌ **خطأ في التنفيذ:**\n```\n{str(e)}\n```")
        
        @self.client.client.on(events.NewMessage(pattern=r'^[./!]?(shell|cmd|شل)\s+(.+)'))
        async def shell_handler(event):
            """تنفيذ أوامر Shell (للمالك فقط)"""
            if event.sender_id != self.config.OWNER_ID:
                return
            
            try:
                command = event.pattern_match.group(2)
                
                # تنفيذ الأمر
                process = subprocess.run(
                    command, 
                    shell=True, 
                    capture_output=True, 
                    text=True,
                    timeout=30
                )
                
                output = process.stdout + process.stderr
                if not output:
                    output = "تم التنفيذ بنجاح (لا يوجد مخرجات)"
                
                # تقسيم المخرجات إذا كانت طويلة
                if len(output) > 4000:
                    output = output[:4000] + "...\n[المخرجات مقطوعة]"
                
                await event.respond(f"```bash\n$ {command}\n```\n\n```\n{output}\n```")
                
            except subprocess.TimeoutExpired:
                await event.respond("❌ انتهت مهلة تنفيذ الأمر (30 ثانية)")
            except Exception as e:
                await event.respond(f"❌ **خطأ في تنفيذ الأمر:**\n```\n{str(e)}\n```")
        
        @self.client.client.on(events.NewMessage(pattern=r'^[./!]?(broadcast|إذاعة)\s+(.+)', flags=re.DOTALL))
        async def broadcast_handler(event):
            """إذاعة رسالة لجميع المستخدمين"""
            if event.sender_id != self.config.OWNER_ID:
                return
            
            try:
                message = event.pattern_match.group(2)
                
                # جلب جميع المستخدمين
                users = await self.db.get_all_users()
                
                if not users:
                    await event.respond("❌ لا يوجد مستخدمين في قاعدة البيانات")
                    return
                
                # بدء الإذاعة
                status_msg = await event.respond(f"📡 **بدء الإذاعة...**\n\n👥 المستخدمين: {len(users)}")
                
                sent = 0
                failed = 0
                
                for user in users:
                    try:
                        await self.client.client.send_message(user['user_id'], message)
                        sent += 1
                    except:
                        failed += 1
                    
                    # تحديث الحالة كل 10 مستخدمين
                    if (sent + failed) % 10 == 0:
                        await status_msg.edit(
                            f"📡 **جاري الإذاعة...**\n\n"
                            f"✅ تم الإرسال: {sent}\n"
                            f"❌ فشل: {failed}\n"
                            f"📊 التقدم: {sent + failed}/{len(users)}"
                        )
                
                # النتيجة النهائية
                await status_msg.edit(
                    f"📡 **تمت الإذاعة!**\n\n"
                    f"✅ تم الإرسال: {sent}\n"
                    f"❌ فشل: {failed}\n"
                    f"📊 إجمالي: {len(users)}"
                )
                
                logger.info(f"📡 إذاعة من المالك: {sent} نجح، {failed} فشل")
                
            except Exception as e:
                logger.error(f"❌ خطأ في الإذاعة: {e}")
                await event.respond("❌ حدث خطأ في الإذاعة")
        
        logger.info("✅ تم تسجيل جميع أوامر المالك")
    
    async def _show_detailed_stats(self, event):
        """عرض إحصائيات مفصلة"""
        try:
            # إحصائيات النظام
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            boot_time = datetime.fromtimestamp(psutil.boot_time())
            
            # إحصائيات قاعدة البيانات
            db_stats = self.db.get_stats()
            
            stats_text = f"""
📊 **إحصائيات مفصلة للنظام**

🖥️ **النظام:**
• النظام: {platform.system()} {platform.release()}
• المعمارية: {platform.machine()}
• Python: {platform.python_version()}
• المعالج: {psutil.cpu_count()} cores ({cpu_percent}%)
• الذاكرة: {memory.percent}% ({memory.used // (1024**3)} GB / {memory.total // (1024**3)} GB)
• القرص: {disk.percent}% ({disk.used // (1024**3)} GB / {disk.total // (1024**3)} GB)
• بدء النظام: {boot_time.strftime('%Y-%m-%d %H:%M:%S')}

📊 **قاعدة البيانات:**
• المستخدمين: {db_stats.get('total_users', 0)}
• المجموعات: {db_stats.get('total_chats', 0)}
• الحسابات المساعدة: {db_stats.get('total_assistants', 0)}
• الاستعلامات: {db_stats.get('queries_executed', 0)}
• Cache Hits: {db_stats.get('cache_hits', 0)}
• Cache Misses: {db_stats.get('cache_misses', 0)}

⏰ **الأداء:**
• وقت التشغيل: {self._get_uptime()}
• الأخطاء: {db_stats.get('errors_count', 0)}
"""
            
            buttons = [[Button.inline("🔄 تحديث", data="owner_stats"),
                       Button.inline("🔙 رجوع", data="owner_refresh")]]
            
            await event.edit(stats_text, buttons=buttons)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)
    
    async def _show_users_info(self, event):
        """عرض معلومات المستخدمين"""
        try:
            users = await self.db.get_all_users()
            active_users = await self.db.get_active_users_count()
            
            users_text = f"""
👥 **معلومات المستخدمين**

📊 **الإحصائيات:**
• إجمالي المستخدمين: {len(users) if users else 0}
• المستخدمين النشطين: {active_users}
• المستخدمين الجدد اليوم: {await self.db.get_new_users_today()}

📋 **آخر 10 مستخدمين:**
"""
            
            if users:
                for i, user in enumerate(users[-10:], 1):
                    users_text += f"{i}. [{user.get('first_name', 'غير معروف')}](tg://user?id={user['user_id']}) - {user['user_id']}\n"
            else:
                users_text += "لا يوجد مستخدمين"
            
            buttons = [[Button.inline("📊 تفاصيل أكثر", data="owner_users_detailed"),
                       Button.inline("🔙 رجوع", data="owner_refresh")]]
            
            await event.edit(users_text, buttons=buttons)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)
    
    async def _show_chats_info(self, event):
        """عرض معلومات المجموعات"""
        try:
            chats = await self.db.get_all_chats()
            
            chats_text = f"""
💬 **معلومات المجموعات**

📊 **الإحصائيات:**
• إجمالي المجموعات: {len(chats) if chats else 0}
• المجموعات النشطة: {await self.db.get_active_chats_count()}

📋 **آخر 10 مجموعات:**
"""
            
            if chats:
                for i, chat in enumerate(chats[-10:], 1):
                    chats_text += f"{i}. {chat.get('title', 'غير معروف')} - {chat['chat_id']}\n"
            else:
                chats_text += "لا يوجد مجموعات"
            
            buttons = [[Button.inline("🔙 رجوع", data="owner_refresh")]]
            
            await event.edit(chats_text, buttons=buttons)
            
        except Exception as e:
            await event.answer(f"❌ خطأ: {e}", alert=True)
    
    def _get_uptime(self) -> str:
        """حساب وقت التشغيل"""
        try:
            uptime_seconds = int(psutil.boot_time())
            current_time = int(datetime.now().timestamp())
            uptime = current_time - uptime_seconds
            
            days = uptime // 86400
            hours = (uptime % 86400) // 3600
            minutes = (uptime % 3600) // 60
            
            if days > 0:
                return f"{days}d {hours}h {minutes}m"
            elif hours > 0:
                return f"{hours}h {minutes}m"
            else:
                return f"{minutes}m"
        except:
            return "غير معروف"