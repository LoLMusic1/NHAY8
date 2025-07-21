import asyncio
import json
from typing import Dict, List
from telethon import events

import config
from ZeMusic.logging import LOGGER
from ZeMusic.core.telethon_client import telethon_manager
from ZeMusic.core.database import db
from ZeMusic.core.music_manager import telethon_music_manager as music_manager

class OwnerPanel:
    """لوحة تحكم مالك البوت"""
    
    def __init__(self):
        self.pending_sessions = {}  # جلسات انتظار إضافة الحسابات
    
    async def handle_owner_command(self, event):
        """معالج أمر /owner"""
        try:
            user_id = event.sender_id
            result = await self.show_main_panel(user_id)
            
            if result['success']:
                keyboard_data = result.get('keyboard')
                if keyboard_data:
                    # تحويل إلى أزرار Telethon
                    from telethon import Button
                    buttons = []
                    for row in keyboard_data:
                        button_row = []
                        for btn in row:
                            button_row.append(Button.inline(btn['text'], data=btn['callback_data']))
                        buttons.append(button_row)
                    await event.reply(result['message'], buttons=buttons)
                else:
                    await event.reply(result['message'])
            else:
                await event.reply(result['message'])
                
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في معالج /owner: {e}")
            await event.reply("❌ حدث خطأ في معالجة الأمر")
    
    async def show_main_panel(self, user_id: int) -> Dict:
        """عرض اللوحة الرئيسية"""
        if user_id != config.OWNER_ID:
            return {
                'success': False,
                'message': "❌ هذا الأمر مخصص لمالك البوت فقط"
            }
        
        stats = await self._get_bot_stats()
        
        keyboard = [
            [
                {'text': '📱 إدارة الحسابات المساعدة', 'callback_data': 'owner_assistants'},
                {'text': '📊 الإحصائيات', 'callback_data': 'owner_stats'}
            ],
            [
                {'text': '⚙️ إعدادات البوت', 'callback_data': 'owner_settings'},
                {'text': '🔧 صيانة النظام', 'callback_data': 'owner_maintenance'}
            ],
            [
                {'text': '📋 سجلات النظام', 'callback_data': 'owner_logs'},
                {'text': '🗃️ قاعدة البيانات', 'callback_data': 'owner_database'}
            ],
            [
                {'text': '🔄 إعادة تشغيل', 'callback_data': 'owner_restart'},
                {'text': '🛑 إيقاف البوت', 'callback_data': 'owner_shutdown'}
            ]
        ]
        
        message = (
            "🎛️ **لوحة تحكم مالك البوت**\n\n"
            f"📊 **الإحصائيات السريعة:**\n"
            f"👥 المستخدمين: `{stats['users']}`\n"
            f"💬 المجموعات: `{stats['chats']}`\n"
            f"🤖 الحسابات المساعدة: `{stats['assistants']}`\n"
            f"🎵 الجلسات النشطة: `{stats['active_sessions']}`\n\n"
            f"🕐 آخر تحديث: `{stats['last_update']}`"
        )
        
        return {
            'success': True,
            'message': message,
            'keyboard': keyboard
        }
    
    async def show_assistants_panel(self, user_id: int) -> Dict:
        """عرض لوحة إدارة الحسابات المساعدة"""
        if user_id != config.OWNER_ID:
            return {'success': False, 'message': "❌ غير مصرح"}
        
        assistants = await db.get_all_assistants()
        connected_count = telethon_manager.get_connected_assistants_count()
        
        keyboard = [
            [
                {'text': '➕ إضافة حساب مساعد', 'callback_data': 'add_assistant'},
                {'text': '🗑️ حذف حساب مساعد', 'callback_data': 'remove_assistant'}
            ],
            [
                {'text': '📋 قائمة الحسابات', 'callback_data': 'list_assistants'},
                {'text': '🔄 إعادة تشغيل الحسابات', 'callback_data': 'restart_assistants'}
            ],
            [
                {'text': '⚠️ إلغاء تفعيل حساب', 'callback_data': 'deactivate_assistant'},
                {'text': '✅ تفعيل حساب', 'callback_data': 'activate_assistant'}
            ],
            [
                {'text': '📊 إحصائيات مفصلة', 'callback_data': 'assistant_stats'},
                {'text': '🧹 تنظيف الحسابات الخاملة', 'callback_data': 'cleanup_assistants'}
            ],
            [
                {'text': '🔙 العودة للوحة الرئيسية', 'callback_data': 'owner_main'}
            ]
        ]
        
        message = (
            "📱 **إدارة الحسابات المساعدة**\n\n"
            f"📊 **الحالة الحالية:**\n"
            f"🤖 إجمالي الحسابات: `{len(assistants)}`\n"
            f"🟢 متصل: `{connected_count}`\n"
            f"🔴 غير متصل: `{len(assistants) - connected_count}`\n\n"
            f"⚡ **الأداء:**\n"
            f"🎵 الجلسات النشطة: `{len(music_manager.active_sessions)}`\n"
            f"📈 الحد الأقصى: `{config.MAX_ASSISTANTS}`\n"
            f"📉 الحد الأدنى: `{config.MIN_ASSISTANTS}`\n\n"
            "اختر العملية المطلوبة:"
        )
        
        return {
            'success': True,
            'message': message,
            'keyboard': keyboard
        }
    
    async def start_add_assistant(self, user_id: int) -> Dict:
        """بدء عملية إضافة حساب مساعد"""
        if user_id != config.OWNER_ID:
            return {'success': False, 'message': "❌ غير مصرح"}
        
        # إنشاء جلسة انتظار
        session_id = f"add_assistant_{user_id}_{int(asyncio.get_event_loop().time())}"
        self.pending_sessions[user_id] = {
            'type': 'add_assistant',
            'session_id': session_id,
            'step': 'waiting_session'
        }
        
        keyboard = [
            [{'text': '❌ إلغاء', 'callback_data': 'cancel_add_assistant'}]
        ]
        
        message = (
            "➕ **إضافة حساب مساعد جديد**\n\n"
            "📝 **الخطوات:**\n"
            "1️⃣ أرسل session string للحساب\n"
            "2️⃣ أدخل اسم مميز للحساب\n"
            "3️⃣ تأكيد الإضافة\n\n"
            "🔗 **ملاحظة:** تأكد من صحة الـ session string\n"
            "⚠️ يُفضل استخدام حسابات عمرها أكثر من سنة\n\n"
            "📎 أرسل session string الآن:"
        )
        
        return {
            'success': True,
            'message': message,
            'keyboard': keyboard,
            'waiting_input': True
        }
    
    async def process_add_assistant_input(self, user_id: int, text: str) -> Dict:
        """معالجة إدخالات إضافة الحساب المساعد"""
        # إنشاء جلسة جديدة إذا لم تكن موجودة
        if user_id not in self.pending_sessions:
            session_id = f"add_assistant_{user_id}_{int(asyncio.get_event_loop().time())}"
            self.pending_sessions[user_id] = {
                'type': 'add_assistant',
                'session_id': session_id,
                'step': 'waiting_session'
            }
        
        session = self.pending_sessions[user_id]
        
        if session['step'] == 'waiting_session':
            # فحص وإضافة الحساب مباشرة
            return await self._process_session_directly(user_id, text)
        
        elif session['step'] == 'waiting_name':
            if len(text) < 3 or len(text) > 50:
                return {
                    'success': False,
                    'message': "❌ الاسم يجب أن يكون بين 3-50 حرف\nأرسل اسم صحيح:"
                }
            
            session['name'] = text
            session['step'] = 'confirmation'
            
            # اختيار معرف تلقائي
            assistants = await db.get_all_assistants()
            used_ids = [a['assistant_id'] for a in assistants]
            assistant_id = 1
            while assistant_id in used_ids:
                assistant_id += 1
            
            session['assistant_id'] = assistant_id
            
            keyboard = [
                [
                    {'text': '✅ تأكيد الإضافة', 'callback_data': 'confirm_add_assistant'},
                    {'text': '❌ إلغاء', 'callback_data': 'cancel_add_assistant'}
                ]
            ]
            
            message = (
                "📋 **تأكيد إضافة الحساب المساعد**\n\n"
                f"🆔 **المعرف:** `{assistant_id}`\n"
                f"📝 **الاسم:** `{text}`\n"
                f"🔗 **Session:** `{session['session_string'][:20]}...`\n\n"
                "❓ هل تريد إضافة هذا الحساب؟"
            )
            
            return {
                'success': True,
                'message': message,
                'keyboard': keyboard
            }
        
        return {'success': False, 'message': "❌ خطأ في المعالجة"}
    
    async def confirm_add_assistant(self, user_id: int) -> Dict:
        """تأكيد إضافة الحساب المساعد"""
        if user_id not in self.pending_sessions:
            return {'success': False, 'message': "❌ لا توجد جلسة نشطة"}
        
        session = self.pending_sessions[user_id]
        
        try:
            # إضافة الحساب للنظام
            success = await telethon_manager.add_assistant(
                session['session_string'],
                session['assistant_id'],
                session['name']
            )
            
            if success:
                # تنظيف الجلسة
                del self.pending_sessions[user_id]
                
                keyboard = [
                    [{'text': '📱 إدارة الحسابات', 'callback_data': 'owner_assistants'}]
                ]
                
                message = (
                    "✅ **تم إضافة الحساب المساعد بنجاح!**\n\n"
                    f"🆔 المعرف: `{session['assistant_id']}`\n"
                    f"📝 الاسم: `{session['name']}`\n"
                    f"🟢 الحالة: متصل ونشط\n\n"
                    "🎵 الحساب جاهز لتشغيل الموسيقى الآن!"
                )
                
                return {
                    'success': True,
                    'message': message,
                    'keyboard': keyboard
                }
            else:
                return {
                    'success': False,
                    'message': "❌ فشل في إضافة الحساب\nتحقق من صحة session string وحاول مرة أخرى"
                }
        
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في إضافة المساعد: {e}")
            return {
                'success': False,
                'message': f"❌ خطأ في إضافة الحساب: {str(e)}"
            }
    
    async def list_assistants(self, user_id: int) -> Dict:
        """عرض قائمة الحسابات المساعدة"""
        if user_id != config.OWNER_ID:
            return {'success': False, 'message': "❌ غير مصرح"}
        
        assistants = await db.get_all_assistants()
        
        if not assistants:
            keyboard = [
                [{'text': '➕ إضافة حساب مساعد', 'callback_data': 'add_assistant'}],
                [{'text': '🔙 العودة', 'callback_data': 'owner_assistants'}]
            ]
            
            return {
                'success': True,
                'message': "📝 **قائمة الحسابات المساعدة**\n\n❌ لا توجد حسابات مساعدة مضافة",
                'keyboard': keyboard
            }
        
        message_parts = ["📝 **قائمة الحسابات المساعدة:**\n"]
        
        for assistant in assistants:
            # التحقق من حالة الاتصال
            is_connected = False
            active_calls = 0
            
            for telethon_assistant in telethon_manager.assistants:
                if telethon_assistant.assistant_id == assistant['assistant_id']:
                    is_connected = telethon_assistant.is_connected
                    active_calls = telethon_assistant.get_active_calls_count()
                    break
            
            status_emoji = "🟢" if is_connected else "🔴"
            status_text = "متصل" if is_connected else "غير متصل"
            
            assistant_info = (
                f"\n{status_emoji} **الحساب {assistant['assistant_id']}**\n"
                f"📝 الاسم: `{assistant['name']}`\n"
                f"🔌 الحالة: `{status_text}`\n"
                f"🎵 المكالمات النشطة: `{active_calls}`\n"
                f"📊 إجمالي الاستخدام: `{assistant['total_calls']}`\n"
                f"🕐 آخر استخدام: `{assistant['last_used'][:19]}`\n"
            )
            
            message_parts.append(assistant_info)
        
        keyboard = [
            [
                {'text': '➕ إضافة حساب', 'callback_data': 'add_assistant'},
                {'text': '🗑️ حذف حساب', 'callback_data': 'remove_assistant'}
            ],
            [
                {'text': '🔄 تحديث القائمة', 'callback_data': 'list_assistants'},
                {'text': '🔙 العودة', 'callback_data': 'owner_assistants'}
            ]
        ]
        
        return {
            'success': True,
            'message': ''.join(message_parts),
            'keyboard': keyboard
        }
    
    async def show_detailed_stats(self, user_id: int) -> Dict:
        """عرض إحصائيات مفصلة"""
        if user_id != config.OWNER_ID:
            return {'success': False, 'message': "❌ غير مصرح"}
        
        stats = await db.get_stats()
        
        # إحصائيات الحسابات المساعدة
        assistants = await db.get_all_assistants()
        connected_assistants = telethon_manager.get_connected_assistants_count()
        
        # إحصائيات الجلسات النشطة
        active_sessions = len(music_manager.active_sessions)
        
        # إحصائيات النظام
        import psutil
        import platform
        
        cpu_percent = psutil.cpu_percent()
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        message = (
            "📊 **إحصائيات البوت المفصلة**\n\n"
            
            "👥 **المستخدمين والمجموعات:**\n"
            f"👤 إجمالي المستخدمين: `{stats['users']}`\n"
            f"💬 إجمالي المجموعات: `{stats['chats']}`\n"
            f"👨‍💼 المديرين: `{stats['sudoers']}`\n"
            f"🚫 المحظورين: `{stats['banned']}`\n\n"
            
            "🤖 **الحسابات المساعدة:**\n"
            f"📱 إجمالي الحسابات: `{len(assistants)}`\n"
            f"🟢 متصل: `{connected_assistants}`\n"
            f"🔴 غير متصل: `{len(assistants) - connected_assistants}`\n"
            f"🎵 الجلسات النشطة: `{active_sessions}`\n\n"
            
            "🖥️ **موارد النظام:**\n"
            f"🧠 المعالج: `{cpu_percent}%`\n"
            f"💾 الذاكرة: `{memory.percent}%`\n"
            f"💿 التخزين: `{disk.percent}%`\n"
            f"🖥️ النظام: `{platform.system()}`\n\n"
            
            "📈 **الأداء:**\n"
            f"⚡ وقت التشغيل: `{self._get_uptime()}`\n"
            f"🔄 آخر إعادة تشغيل: `{self._get_last_restart()}`\n"
        )
        
        keyboard = [
            [
                {'text': '🔄 تحديث الإحصائيات', 'callback_data': 'owner_stats'},
                {'text': '📊 إحصائيات الاستخدام', 'callback_data': 'usage_stats'}
            ],
            [
                {'text': '🔙 العودة للوحة الرئيسية', 'callback_data': 'owner_main'}
            ]
        ]
        
        return {
            'success': True,
            'message': message,
            'keyboard': keyboard
        }
    
    async def _process_session_directly(self, user_id: int, session_string: str) -> Dict:
        """فحص وإضافة session string مباشرة بدون خطوات إضافية"""
        try:
            # إزالة الجلسة من pending_sessions
            if user_id in self.pending_sessions:
                del self.pending_sessions[user_id]
            
            # تنظيف session string
            session_string = session_string.strip().replace('\n', '').replace('\r', '').replace(' ', '')
            
            # التحقق الأساسي من صيغة session string
            if not self._validate_session_string(session_string):
                return {
                    'success': False,
                    'message': f"❌ **صيغة session string غير صحيحة**\n\n📏 **الطول الحالي:** {len(session_string)} حرف\n💡 **المطلوب:** أكثر من 100 حرف من base64\n\n🔄 تأكد من نسخ الكود بشكل كامل وصحيح"
                }
            
            # محاولة إنشاء واختبار الاتصال
            import tempfile
            import os
            from telethon import TelegramClient
            
            # إنشاء ملف جلسة مؤقت
            temp_session = tempfile.NamedTemporaryFile(delete=False, suffix='.session')
            temp_session.close()
            
            try:
                # إنشاء عميل جديد باستخدام StringSession مباشرة
                from telethon.sessions import StringSession
                test_client = TelegramClient(StringSession(session_string), config.API_ID, config.API_HASH)
                
                # اختبار الاتصال
                await test_client.connect()
                
                # التحقق من التفويض
                if not await test_client.is_user_authorized():
                    await test_client.disconnect()
                    return {
                        'success': False,
                        'message': "❌ **session string غير صالح أو منتهي الصلاحية**\n\n🔄 احصل على session string جديد وأرسله"
                    }
                
                # الحصول على معلومات الحساب
                user_info = await test_client.get_me()
                await test_client.disconnect()
                
                # إنشاء اسم تلقائي للحساب
                auto_name = f"Assistant_{user_info.id}"
                if user_info.first_name:
                    auto_name = f"{user_info.first_name}_{user_info.id}"
                
                # إضافة الحساب للنظام
                from ZeMusic.core.telethon_client import telethon_manager
                success = await telethon_manager.add_assistant(session_string, auto_name)
                
                if success:
                    # تحديث الإحصائيات
                    assistants = await db.get_all_assistants()
                    connected_count = telethon_manager.get_connected_assistants_count()
                    
                    return {
                        'success': True,
                        'message': f"""✅ **تم إضافة الحساب المساعد بنجاح!**

👤 **معلومات الحساب:**
• الاسم: {user_info.first_name or 'غير محدد'}
• المعرف: `{user_info.id}`
• اليوزر: {'@' + user_info.username if user_info.username else 'غير متاح'}

📊 **إحصائيات محدثة:**
• إجمالي الحسابات: `{len(assistants)}`
• متصل الآن: `{connected_count}`

🎉 **الحساب جاهز للاستخدام فوراً!**""",
                        'keyboard': [
                            [{'text': '📱 إدارة الحسابات', 'callback_data': 'owner_assistants'}],
                            [{'text': '🔙 العودة للوحة الرئيسية', 'callback_data': 'owner_main'}]
                        ]
                    }
                else:
                    return {
                        'success': False,
                        'message': "❌ **فشل في إضافة الحساب للنظام**\n\n🔧 تحقق من سجلات النظام أو أعد المحاولة"
                    }
                 
            except Exception as e:
                error_msg = str(e)
                if "Unauthorized" in error_msg or "AUTH_KEY" in error_msg:
                    return {
                        'success': False,
                        'message': "❌ **session string منتهي الصلاحية**\n\n🔄 **الحل:** احصل على session string جديد من:\n• https://my.telegram.org\n• أو استخدم session generator\n\n💡 تأكد من عدم تسجيل الخروج من الحساب"
                    }
                elif "Invalid" in error_msg or "400" in error_msg:
                    return {
                        'success': False,
                        'message': f"❌ **session string غير صالح**\n\n📝 **السبب:** تنسيق خاطئ\n🔄 **الحل:** تأكد من نسخ الكود كاملاً بدون مسافات إضافية\n\n💡 **طول الكود الحالي:** {len(session_string)} حرف"
                    }
                else:
                    return {
                        'success': False,
                        'message': f"❌ **خطأ في التحقق من الجلسة**\n\n📝 **التفاصيل:** {error_msg[:100]}{'...' if len(error_msg) > 100 else ''}\n\n🔄 جرب session string آخر أو تواصل مع المطور"
                    }
            finally:
                # حذف الملف المؤقت
                try:
                    if os.path.exists(temp_session.name):
                        os.unlink(temp_session.name)
                    if os.path.exists(temp_session.name + '.session'):
                        os.unlink(temp_session.name + '.session')
                except:
                    pass
                    
        except Exception as e:
            return {
                'success': False,
                'message': f"❌ **حدث خطأ عام**\n\n📝 **التفاصيل:** {str(e)[:100]}..."
            }
    
    def _validate_session_string(self, session_string: str) -> bool:
        """التحقق من صحة session string"""
        try:
            # إزالة المسافات والسطور الجديدة
            session_string = session_string.strip()
            
            # التحقق من الطول الأدنى
            if len(session_string) < 100:
                return False
            
            # التحقق من أنه يحتوي على أحرف base64 صالحة
            import base64
            import string
            valid_chars = string.ascii_letters + string.digits + '+/='
            if not all(c in valid_chars for c in session_string):
                return False
            
            # محاولة فك التشفير للتأكد من صحة التنسيق
            try:
                # تجربة StringSession مع الـ string
                from telethon.sessions import StringSession
                StringSession(session_string)
                return True
            except:
                return False
            
        except Exception:
            return False
    
    def _get_uptime(self) -> str:
        """الحصول على وقت التشغيل"""
        # يمكن حفظ وقت البدء في متغير عام
        return "غير متاح"
    
    def _get_last_restart(self) -> str:
        """الحصول على وقت آخر إعادة تشغيل"""
        return "غير متاح"
    
    async def _get_bot_stats(self) -> Dict:
        """الحصول على إحصائيات سريعة للبوت"""
        stats = await db.get_stats()
        stats['active_sessions'] = len(music_manager.active_sessions)
        stats['last_update'] = "الآن"
        return stats
    
    async def cancel_operation(self, user_id: int) -> Dict:
        """إلغاء العملية الحالية"""
        if user_id in self.pending_sessions:
            del self.pending_sessions[user_id]
        
        return await self.show_assistants_panel(user_id)
    
    async def show_stats_panel(self, user_id: int) -> Dict:
        """عرض لوحة الإحصائيات المفصلة"""
        if user_id != config.OWNER_ID:
            return {'success': False, 'message': "❌ غير مصرح"}
        
        stats = await self._get_bot_stats()
        
        message = f"""📊 **إحصائيات مفصلة للبوت**

👥 **المستخدمين:**
• إجمالي المستخدمين: `{stats['users']}`
• مستخدمين جدد اليوم: `{stats.get('new_users_today', 0)}`
• المستخدمين النشطين: `{stats.get('active_users', 0)}`

💬 **المجموعات:**
• إجمالي المجموعات: `{stats['chats']}`
• مجموعات جديدة اليوم: `{stats.get('new_chats_today', 0)}`
• المجموعات النشطة: `{stats.get('active_chats', 0)}`

🤖 **الحسابات المساعدة:**
• إجمالي الحسابات: `{stats['assistants']}`
• الحسابات المتصلة: `{stats.get('connected_assistants', 0)}`
• الحسابات النشطة: `{stats.get('active_assistants', 0)}`

🎵 **الجلسات الموسيقية:**
• الجلسات النشطة: `{stats['active_sessions']}`
• إجمالي التشغيلات: `{stats.get('total_plays', 0)}`
• أغاني اليوم: `{stats.get('plays_today', 0)}`

💾 **النظام:**
• وقت التشغيل: `{self._get_uptime()}`
• آخر إعادة تشغيل: `{self._get_last_restart()}`
• استخدام الذاكرة: `{stats.get('memory_usage', 'غير متاح')}`"""

        keyboard = [
            [
                {'text': '🔄 تحديث', 'callback_data': 'owner_stats'},
                {'text': '📊 تفاصيل أكثر', 'callback_data': 'owner_detailed_stats'}
            ],
            [{'text': '🔙 العودة', 'callback_data': 'owner_main'}]
        ]
        
        return {
            'success': True,
            'message': message,
            'keyboard': keyboard
        }
    
    async def show_settings_panel(self, user_id: int) -> Dict:
        """عرض لوحة إعدادات البوت"""
        if user_id != config.OWNER_ID:
            return {'success': False, 'message': "❌ غير مصرح"}
        
        message = """⚙️ **إعدادات البوت**

🔧 **الإعدادات المتاحة:**

📱 **الحسابات المساعدة:**
• إدارة الحسابات المساعدة
• إعدادات المغادرة التلقائية
• حدود الاستخدام

🎵 **إعدادات الموسيقى:**
• جودة الصوت الافتراضية
• حد مدة الأغاني
• إعدادات التخزين

🛡️ **الأمان:**
• قائمة المحظورين
• إعدادات الصلاحيات
• حماية من السبام

🌐 **عام:**
• لغة البوت
• رسائل الترحيب
• إعدادات السجلات"""

        keyboard = [
            [
                {'text': '📱 إعدادات المساعدين', 'callback_data': 'settings_assistants'},
                {'text': '🎵 إعدادات الموسيقى', 'callback_data': 'settings_music'}
            ],
            [
                {'text': '🛡️ إعدادات الأمان', 'callback_data': 'settings_security'},
                {'text': '🌐 إعدادات عامة', 'callback_data': 'settings_general'}
            ],
            [{'text': '🔙 العودة', 'callback_data': 'owner_main'}]
        ]
        
        return {
            'success': True,
            'message': message,
            'keyboard': keyboard
        }
    
    async def show_maintenance_panel(self, user_id: int) -> Dict:
        """عرض لوحة صيانة النظام"""
        if user_id != config.OWNER_ID:
            return {'success': False, 'message': "❌ غير مصرح"}
        
        message = """🔧 **صيانة النظام**

🛠️ **الأدوات المتاحة:**

🧹 **التنظيف:**
• تنظيف الملفات المؤقتة
• تنظيف ذاكرة التخزين المؤقت
• تنظيف سجلات قديمة

🔄 **التحديث:**
• تحديث المكتبات
• تحديث قاعدة البيانات
• إعادة تحميل الإعدادات

🔍 **الفحص:**
• فحص سلامة النظام
• فحص الاتصالات
• فحص قاعدة البيانات

⚡ **الأداء:**
• تحسين قاعدة البيانات
• تحسين الذاكرة
• إعادة تشغيل الخدمات"""

        keyboard = [
            [
                {'text': '🧹 تنظيف النظام', 'callback_data': 'maintenance_cleanup'},
                {'text': '🔄 تحديث النظام', 'callback_data': 'maintenance_update'}
            ],
            [
                {'text': '🔍 فحص النظام', 'callback_data': 'maintenance_check'},
                {'text': '⚡ تحسين الأداء', 'callback_data': 'maintenance_optimize'}
            ],
            [{'text': '🔙 العودة', 'callback_data': 'owner_main'}]
        ]
        
        return {
            'success': True,
            'message': message,
            'keyboard': keyboard
        }
    
    async def show_logs_panel(self, user_id: int) -> Dict:
        """عرض لوحة سجلات النظام"""
        if user_id != config.OWNER_ID:
            return {'success': False, 'message': "❌ غير مصرح"}
        
        # قراءة آخر 20 سطر من السجل
        try:
            import subprocess
            result = subprocess.run(['tail', '-20', 'final_bot_log.txt'], 
                                  capture_output=True, text=True, timeout=5)
            recent_logs = result.stdout if result.stdout else "لا توجد سجلات متاحة"
        except:
            recent_logs = "تعذر قراءة السجلات"
        
        message = f"""📋 **سجلات النظام**

📝 **آخر العمليات:**
```
{recent_logs[-1000:]}  
```

🔍 **خيارات السجلات:**"""

        keyboard = [
            [
                {'text': '📄 سجل كامل', 'callback_data': 'logs_full'},
                {'text': '⚠️ الأخطاء فقط', 'callback_data': 'logs_errors'}
            ],
            [
                {'text': '📊 إحصائيات السجل', 'callback_data': 'logs_stats'},
                {'text': '🗑️ مسح السجلات', 'callback_data': 'logs_clear'}
            ],
            [{'text': '🔙 العودة', 'callback_data': 'owner_main'}]
        ]
        
        return {
            'success': True,
            'message': message,
            'keyboard': keyboard
        }
    
    async def show_database_panel(self, user_id: int) -> Dict:
        """عرض لوحة قاعدة البيانات"""
        if user_id != config.OWNER_ID:
            return {'success': False, 'message': "❌ غير مصرح"}
        
        stats = await self._get_bot_stats()
        
        message = f"""🗃️ **إدارة قاعدة البيانات**

📊 **حالة قاعدة البيانات:**
• نوع قاعدة البيانات: `SQLite`
• حجم قاعدة البيانات: `{stats.get('db_size', 'غير متاح')}`
• آخر نسخة احتياطية: `{stats.get('last_backup', 'لم يتم عمل نسخة')}`

📋 **الجداول:**
• جدول المستخدمين: `{stats['users']} سجل`
• جدول المجموعات: `{stats['chats']} سجل`
• جدول الحسابات المساعدة: `{stats['assistants']} سجل`

🛠️ **العمليات المتاحة:**"""

        keyboard = [
            [
                {'text': '💾 نسخة احتياطية', 'callback_data': 'db_backup'},
                {'text': '📤 استيراد نسخة', 'callback_data': 'db_restore'}
            ],
            [
                {'text': '🧹 تنظيف البيانات', 'callback_data': 'db_cleanup'},
                {'text': '🔧 تحسين قاعدة البيانات', 'callback_data': 'db_optimize'}
            ],
            [
                {'text': '📊 إحصائيات مفصلة', 'callback_data': 'db_detailed_stats'},
                {'text': '🔍 فحص سلامة البيانات', 'callback_data': 'db_integrity_check'}
            ],
            [{'text': '🔙 العودة', 'callback_data': 'owner_main'}]
        ]
        
        return {
            'success': True,
            'message': message,
            'keyboard': keyboard
        }
    
    async def handle_add_assistant(self, user_id: int) -> Dict:
        """بدء عملية إضافة حساب مساعد"""
        return {
            'success': True,
            'message': """📱 **إضافة حساب مساعد جديد**

🔧 **الخطوات:**
1. احصل على Session String للحساب
2. أرسله هنا لإضافته للنظام

📝 **ملاحظات:**
• تأكد من صحة Session String
• الحساب يجب أن يكون صالحاً
• سيتم التحقق تلقائياً

⚠️ **تحذير:** لا تشارك Session String مع أحد!

💡 **للحصول على Session String:**
استخدم بوت Session Generator

📝 **أرسل Session String الآن:**""",
            'keyboard': [
                [{'text': '❌ إلغاء', 'callback_data': 'owner_assistants'}]
            ]
        }
    
    async def handle_remove_assistant(self, user_id: int, assistant_id: str) -> Dict:
        """حذف حساب مساعد"""
        try:
            success = await telethon_manager.remove_assistant(assistant_id)
            
            if success:
                message = f"✅ **تم حذف الحساب المساعد بنجاح!**\n\n🆔 المعرف: `{assistant_id}`"
            else:
                message = f"❌ **فشل في حذف الحساب المساعد**\n\n🆔 المعرف: `{assistant_id}`"
            
            return {
                'success': True,
                'message': message,
                'keyboard': [
                    [{'text': '📱 إدارة الحسابات', 'callback_data': 'owner_assistants'}]
                ]
            }
            
        except Exception as e:
            return {
                'success': False,
                'message': f"❌ حدث خطأ: {str(e)}"
            }
    
    async def handle_restart(self, user_id: int) -> Dict:
        """إعادة تشغيل البوت"""
        if user_id != config.OWNER_ID:
            return {'success': False, 'message': "❌ غير مصرح"}
        
        message = """🔄 **إعادة تشغيل البوت**

⚠️ **تحذير:** سيتم إعادة تشغيل البوت خلال 10 ثواني

📝 **ما سيحدث:**
• إيقاف جميع الجلسات النشطة
• قطع الاتصال بالحسابات المساعدة
• إعادة تحميل جميع الإعدادات
• إعادة تشغيل النظام

⏱️ **المدة المتوقعة:** 30-60 ثانية

❓ **هل أنت متأكد؟**"""

        keyboard = [
            [
                {'text': '✅ نعم، أعد التشغيل', 'callback_data': 'confirm_restart'},
                {'text': '❌ إلغاء', 'callback_data': 'owner_main'}
            ]
        ]
        
        return {
            'success': True,
            'message': message,
            'keyboard': keyboard
        }
    
    async def handle_shutdown(self, user_id: int) -> Dict:
        """إيقاف البوت"""
        if user_id != config.OWNER_ID:
            return {'success': False, 'message': "❌ غير مصرح"}
        
        message = """🛑 **إيقاف البوت**

⚠️ **تحذير خطير:** سيتم إيقاف البوت تماماً!

📝 **ما سيحدث:**
• إيقاف جميع الجلسات النشطة
• قطع الاتصال بجميع الحسابات
• إغلاق قاعدة البيانات
• إيقاف البوت نهائياً

🔴 **البوت لن يعمل حتى إعادة تشغيله يدوياً**

❓ **هل أنت متأكد من إيقاف البوت؟**"""

        keyboard = [
            [
                {'text': '🛑 نعم، أوقف البوت', 'callback_data': 'confirm_shutdown'},
                {'text': '❌ إلغاء', 'callback_data': 'owner_main'}
            ]
        ]
        
        return {
            'success': True,
            'message': message,
            'keyboard': keyboard
        }
    
    async def execute_restart(self, user_id: int) -> Dict:
        """تنفيذ إعادة التشغيل"""
        if user_id != config.OWNER_ID:
            return {'success': False, 'message': "❌ غير مصرح"}
        
        try:
            message = "🔄 **جاري إعادة تشغيل البوت...**\n\n⏳ سيتم الانتهاء خلال 30-60 ثانية"
            
            # إرسال رسالة وإغلاق البوت
            asyncio.create_task(self._restart_process())
            
            return {
                'success': True,
                'message': message,
                'keyboard': []
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"❌ فشل في إعادة التشغيل: {str(e)}"
            }
    
    async def execute_shutdown(self, user_id: int) -> Dict:
        """تنفيذ إيقاف البوت"""
        if user_id != config.OWNER_ID:
            return {'success': False, 'message': "❌ غير مصرح"}
        
        try:
            message = "🛑 **جاري إيقاف البوت...**\n\n⚠️ البوت سيتوقف نهائياً"
            
            # إرسال رسالة وإغلاق البوت
            asyncio.create_task(self._shutdown_process())
            
            return {
                'success': True,
                'message': message,
                'keyboard': []
            }
        except Exception as e:
            return {
                'success': False,
                'message': f"❌ فشل في إيقاف البوت: {str(e)}"
            }
    
    async def _restart_process(self):
        """عملية إعادة التشغيل"""
        import os
        import sys
        await asyncio.sleep(3)  # انتظار 3 ثواني
        os.execv(sys.executable, ['python'] + sys.argv)
    
    async def _shutdown_process(self):
        """عملية الإيقاف"""
        import sys
        await asyncio.sleep(3)  # انتظار 3 ثواني
        sys.exit(0)

# إنشاء مثيل عام للوحة التحكم
owner_panel = OwnerPanel()

# معالجات callback للأزرار - سيتم تسجيلها لاحقاً
async def handle_owner_callbacks(event):
    """معالج callbacks أزرار لوحة المطور"""
    try:
        data = event.data.decode('utf-8')
        user_id = event.sender_id
        
        # التحقق من الصلاحيات
        if user_id != config.OWNER_ID:
            await event.answer("❌ هذا الأمر مخصص لمالك البوت فقط", alert=True)
            return
        
        if data == "owner_assistants":
            result = await owner_panel.show_assistants_panel(user_id)
        elif data == "owner_stats":
            result = await owner_panel.show_stats_panel(user_id)
        elif data == "owner_settings":
            result = await owner_panel.show_settings_panel(user_id)
        elif data == "owner_maintenance":
            result = await owner_panel.show_maintenance_panel(user_id)
        elif data == "owner_logs":
            result = await owner_panel.show_logs_panel(user_id)
        elif data == "owner_database":
            result = await owner_panel.show_database_panel(user_id)
        elif data == "owner_main":
            result = await owner_panel.show_main_panel(user_id)
        elif data.startswith("add_assistant"):
            result = await owner_panel.handle_add_assistant(user_id)
        elif data.startswith("remove_assistant_"):
            assistant_id = data.replace("remove_assistant_", "")
            result = await owner_panel.handle_remove_assistant(user_id, assistant_id)
        elif data == "owner_restart":
            result = await owner_panel.handle_restart(user_id)
        elif data == "owner_shutdown":
            result = await owner_panel.handle_shutdown(user_id)
        elif data == "confirm_restart":
            result = await owner_panel.execute_restart(user_id)
        elif data == "confirm_shutdown":
            result = await owner_panel.execute_shutdown(user_id)
        else:
            await event.answer("⚠️ خيار غير معروف")
            return
        
        if result and result.get('success'):
            keyboard_data = result.get('keyboard')
            if keyboard_data:
                # تحويل إلى أزرار Telethon
                from telethon import Button
                buttons = []
                for row in keyboard_data:
                    button_row = []
                    for btn in row:
                        button_row.append(Button.inline(btn['text'], data=btn['callback_data']))
                    buttons.append(button_row)
                
                await event.edit(result['message'], buttons=buttons)
            else:
                await event.edit(result['message'])
        else:
            await event.answer("❌ حدث خطأ في المعالجة")
            
    except Exception as e:
        LOGGER(__name__).error(f"خطأ في معالج callbacks: {e}")
        try:
            await event.answer("❌ حدث خطأ في معالجة الطلب", alert=True)
        except:
            pass