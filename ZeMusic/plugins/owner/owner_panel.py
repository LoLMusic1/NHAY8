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
        
        try:
            assistants = await db.get_all_assistants()
            connected_count = 0
            try:
                connected_count = telethon_manager.get_connected_assistants_count()
            except Exception as count_error:
                LOGGER(__name__).error(f"خطأ في عد الحسابات المتصلة: {count_error}")
            
            active_sessions = 0
            try:
                active_sessions = len(music_manager.active_sessions) if hasattr(music_manager, 'active_sessions') else 0
            except Exception as session_error:
                LOGGER(__name__).error(f"خطأ في عد الجلسات النشطة: {session_error}")
            
            # تحديد الحد الأقصى والأدنى
            max_assistants = getattr(config, 'MAX_ASSISTANTS', 10)
            min_assistants = getattr(config, 'MIN_ASSISTANTS', 1)
            
            keyboard = [
                [
                    {'text': '➕ إضافة حساب مساعد', 'callback_data': 'add_assistant'},
                    {'text': '📋 قائمة الحسابات', 'callback_data': 'list_assistants'}
                ],
                [
                    {'text': '🗑️ حذف حساب', 'callback_data': 'remove_assistant_list'},
                    {'text': '🔄 إعادة تشغيل الحسابات', 'callback_data': 'restart_assistants'}
                ],
                [
                    {'text': '📊 إحصائيات مفصلة', 'callback_data': 'assistant_stats'},
                    {'text': '🔍 فحص الحسابات', 'callback_data': 'check_assistants'}
                ],
                [
                    {'text': '⚙️ إعدادات الحسابات', 'callback_data': 'assistant_settings'},
                    {'text': '🧹 تنظيف الحسابات', 'callback_data': 'cleanup_assistants'}
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
                f"🎵 الجلسات النشطة: `{active_sessions}`\n"
                f"📈 الحد الأقصى: `{max_assistants}`\n"
                f"📉 الحد الأدنى: `{min_assistants}`\n\n"
                f"💡 **حالة النظام:** {'✅ مستقر' if connected_count >= min_assistants else '⚠️ يحتاج حسابات'}\n\n"
                "اختر العملية المطلوبة:"
            )
            
            return {
                'success': True,
                'message': message,
                'keyboard': keyboard
            }
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في عرض لوحة الحسابات المساعدة: {e}")
            return {
                'success': False,
                'message': f"❌ خطأ في عرض اللوحة: {str(e)}"
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
    
    async def show_remove_assistant_list(self, user_id: int) -> Dict:
        """عرض قائمة الحسابات للحذف"""
        if user_id != config.OWNER_ID:
            return {'success': False, 'message': "❌ غير مصرح"}
        
        try:
            assistants = await db.get_all_assistants()
            
            if not assistants:
                return {
                    'success': True,
                    'message': "❌ لا توجد حسابات للحذف",
                    'keyboard': [
                        [{'text': '🔙 العودة', 'callback_data': 'owner_assistants'}]
                    ]
                }
            
            keyboard = []
            for assistant in assistants[:10]:  # حد أقصى 10 حسابات في الصفحة
                # التحقق من حالة الاتصال
                is_connected = False
                try:
                    for telethon_assistant in telethon_manager.assistants:
                        if telethon_assistant.assistant_id == assistant['assistant_id']:
                            is_connected = telethon_assistant.is_connected
                            break
                except:
                    pass
                
                status_emoji = "🟢" if is_connected else "🔴"
                button_text = f"{status_emoji} {assistant.get('name', f'حساب {assistant['assistant_id']}')} ({assistant['assistant_id']})"
                keyboard.append([{
                    'text': button_text,
                    'callback_data': f'remove_assistant_{assistant["assistant_id"]}'
                }])
            
            keyboard.append([{'text': '🔙 العودة', 'callback_data': 'owner_assistants'}])
            
            return {
                'success': True,
                'message': "🗑️ **حذف حساب مساعد**\n\n⚠️ اختر الحساب الذي تريد حذفه:\n\n🟢 = متصل | 🔴 = غير متصل",
                'keyboard': keyboard
            }
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في عرض قائمة الحذف: {e}")
            return {
                'success': False,
                'message': f"❌ خطأ في عرض القائمة: {str(e)}"
            }
    
    async def restart_assistants(self, user_id: int) -> Dict:
        """إعادة تشغيل الحسابات المساعدة"""
        if user_id != config.OWNER_ID:
            return {'success': False, 'message': "❌ غير مصرح"}
        
        try:
            # تنظيف الحسابات الفاسدة أولاً
            await telethon_manager.cleanup_idle_assistants()
            
            # إعادة تحميل الحسابات من قاعدة البيانات
            loaded_count = await telethon_manager.load_assistants_from_db()
            
            # الحصول على الإحصائيات
            total_count = telethon_manager.get_assistants_count()
            connected_count = telethon_manager.get_connected_assistants_count()
            
            return {
                'success': True,
                'message': f"✅ **تم إعادة تشغيل الحسابات بنجاح!**\n\n📊 **النتيجة:**\n• تم تحميل: {loaded_count} حساب\n• متصل: {connected_count}\n• المجموع: {total_count}",
                'keyboard': [
                    [{'text': '📋 قائمة الحسابات', 'callback_data': 'list_assistants'}],
                    [{'text': '🔙 العودة', 'callback_data': 'owner_assistants'}]
                ]
            }
                
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في إعادة تشغيل الحسابات: {e}")
            return {
                'success': False,
                'message': f"❌ خطأ في إعادة التشغيل: {str(e)}"
            }
    
    async def fix_inactive_assistants(self, user_id: int) -> Dict:
        """إصلاح الحسابات غير النشطة"""
        if user_id != config.OWNER_ID:
            return {'success': False, 'message': "❌ غير مصرح"}
        
        try:
            # تفعيل جميع الحسابات
            def _fix():
                with db._get_connection() as conn:
                    cursor = conn.cursor()
                    cursor.execute("UPDATE assistants SET is_active = 1")
                    affected_rows = cursor.rowcount
                    conn.commit()
                    return affected_rows
            
            import asyncio
            affected_rows = await asyncio.get_event_loop().run_in_executor(None, _fix)
            
            # إعادة تحميل الحسابات
            loaded_count = await telethon_manager.load_assistants_from_db()
            
            return {
                'success': True,
                'message': f"✅ **تم إصلاح الحسابات بنجاح!**\n\n📊 **النتيجة:**\n• تم تفعيل: {affected_rows} حساب\n• تم تحميل: {loaded_count} حساب\n• متصل: {telethon_manager.get_connected_assistants_count()}",
                'keyboard': [
                    [{'text': '📋 عرض الحسابات', 'callback_data': 'list_assistants'}],
                    [{'text': '🔙 العودة', 'callback_data': 'owner_assistants'}]
                ]
            }
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في إصلاح الحسابات: {e}")
            return {
                'success': False,
                'message': f"❌ خطأ في الإصلاح: {str(e)}"
            }
    
    async def check_assistants(self, user_id: int) -> Dict:
        """فحص حالة الحسابات المساعدة"""
        if user_id != config.OWNER_ID:
            return {'success': False, 'message': "❌ غير مصرح"}
        
        try:
            assistants = await db.get_assistants()  # استخدام get_assistants للحصول على جميع الحسابات
            
            if not assistants:
                return {
                    'success': True,
                    'message': "❌ لا توجد حسابات للفحص",
                    'keyboard': [
                        [{'text': '🔙 العودة', 'callback_data': 'owner_assistants'}]
                    ]
                }
            
            check_results = []
            for assistant in assistants:
                try:
                    assistant_id = assistant['assistant_id']
                    # فحص الحساب باستخدام الدوال الموجودة
                    is_connected = telethon_manager.is_assistant_connected(assistant_id)
                    assistant_info = await telethon_manager.get_assistant_info(assistant_id)
                    
                    if is_connected and assistant_info and assistant_info.get('connected'):
                        result = {'connected': True, 'info': assistant_info}
                    else:
                        error_msg = assistant_info.get('error', 'غير متصل') if assistant_info else 'غير موجود'
                        result = {'connected': False, 'error': error_msg}
                    
                    check_results.append({
                        'id': assistant_id,
                        'name': assistant.get('name', f'Assistant {assistant_id}'),
                        'status': result
                    })
                except Exception as e:
                    check_results.append({
                        'id': assistant.get('assistant_id', 'unknown'),
                        'name': assistant.get('name', f'حساب غير معروف'),
                        'status': {'connected': False, 'error': str(e)}
                    })
            
            # تكوين النتائج
            message_parts = ["🔍 **نتائج فحص الحسابات المساعدة:**\n\n"]
            
            connected_count = 0
            for result in check_results:
                status = result['status']
                if status.get('connected'):
                    emoji = "✅"
                    status_text = "متصل وجاهز"
                    connected_count += 1
                else:
                    emoji = "❌"
                    error = status.get('error', 'غير متصل')
                    status_text = f"خطأ: {error[:50]}"
                
                message_parts.append(
                    f"{emoji} **{result['name']}** (ID: {result['id']})\n"
                    f"   الحالة: {status_text}\n\n"
                )
            
            message_parts.append(f"📊 **الملخص:** {connected_count}/{len(assistants)} حساب متصل")
            
            keyboard = [
                [
                    {'text': '🔄 إعادة الفحص', 'callback_data': 'check_assistants'},
                    {'text': '🔄 إعادة تشغيل', 'callback_data': 'restart_assistants'}
                ],
                [
                    {'text': '🔙 العودة', 'callback_data': 'owner_assistants'}
                ]
            ]
            
            return {
                'success': True,
                'message': ''.join(message_parts),
                'keyboard': keyboard
            }
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في فحص الحسابات: {e}")
            return {
                'success': False,
                'message': f"❌ خطأ في الفحص: {str(e)}"
            }
    
    async def show_assistant_settings(self, user_id: int) -> Dict:
        """عرض إعدادات الحسابات المساعدة"""
        if user_id != config.OWNER_ID:
            return {'success': False, 'message': "❌ غير مصرح"}
        
        try:
            # الحصول على الإعدادات الحالية
            max_assistants = getattr(config, 'MAX_ASSISTANTS', 10)
            min_assistants = getattr(config, 'MIN_ASSISTANTS', 1)
            auto_restart = getattr(config, 'AUTO_RESTART_ASSISTANTS', True)
            
            assistants = await db.get_all_assistants()
            connected_count = telethon_manager.get_connected_assistants_count()
            
            message = (
                "⚙️ **إعدادات الحسابات المساعدة**\n\n"
                f"📊 **الحالة الحالية:**\n"
                f"🤖 إجمالي الحسابات: `{len(assistants)}`\n"
                f"🟢 متصل: `{connected_count}`\n"
                f"🔴 غير متصل: `{len(assistants) - connected_count}`\n\n"
                f"⚙️ **الإعدادات:**\n"
                f"📈 الحد الأقصى: `{max_assistants}`\n"
                f"📉 الحد الأدنى: `{min_assistants}`\n"
                f"🔄 إعادة التشغيل التلقائي: `{'✅ مفعل' if auto_restart else '❌ معطل'}`\n\n"
                "اختر الإعداد الذي تريد تعديله:"
            )
            
            keyboard = [
                [
                    {'text': '📈 تعديل الحد الأقصى', 'callback_data': 'set_max_assistants'},
                    {'text': '📉 تعديل الحد الأدنى', 'callback_data': 'set_min_assistants'}
                ],
                [
                    {'text': '🔄 تبديل إعادة التشغيل التلقائي', 'callback_data': 'toggle_auto_restart'},
                    {'text': '🧹 تنظيف الحسابات الخاملة', 'callback_data': 'cleanup_assistants'}
                ],
                [
                    {'text': '📊 إحصائيات مفصلة', 'callback_data': 'assistant_stats'},
                    {'text': '🔙 العودة', 'callback_data': 'owner_assistants'}
                ]
            ]
            
            return {
                'success': True,
                'message': message,
                'keyboard': keyboard
            }
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في عرض إعدادات الحسابات: {e}")
            return {
                'success': False,
                'message': f"❌ خطأ في عرض الإعدادات: {str(e)}"
            }
    
    async def cleanup_assistants(self, user_id: int) -> Dict:
        """تنظيف الحسابات الخاملة"""
        if user_id != config.OWNER_ID:
            return {'success': False, 'message': "❌ غير مصرح"}
        
        try:
            # فحص الحسابات الخاملة
            assistants = await db.get_all_assistants()
            inactive_assistants = []
            
            for assistant in assistants:
                try:
                    # فحص إذا كان الحساب غير متصل لفترة طويلة
                    is_connected = False
                    for telethon_assistant in telethon_manager.assistants:
                        if telethon_assistant.assistant_id == assistant['assistant_id']:
                            is_connected = telethon_assistant.is_connected
                            break
                    
                    if not is_connected:
                        # محاولة الاتصال للتأكد
                        check_result = await telethon_manager.check_assistant(assistant['assistant_id'])
                        if not check_result.get('connected'):
                            inactive_assistants.append(assistant)
                            
                except Exception:
                    inactive_assistants.append(assistant)
            
            if not inactive_assistants:
                return {
                    'success': True,
                    'message': "✅ **جميع الحسابات نشطة ومتصلة**\n\nلا توجد حسابات خاملة تحتاج للتنظيف.",
                    'keyboard': [
                        [{'text': '🔙 العودة', 'callback_data': 'owner_assistants'}]
                    ]
                }
            
            keyboard = [
                [
                    {'text': f'🗑️ حذف {len(inactive_assistants)} حساب خامل', 'callback_data': 'confirm_cleanup_assistants'},
                    {'text': '🔄 إعادة محاولة الاتصال', 'callback_data': 'retry_inactive_assistants'}
                ],
                [
                    {'text': '❌ إلغاء', 'callback_data': 'owner_assistants'}
                ]
            ]
            
            message_parts = [
                "🧹 **تنظيف الحسابات الخاملة**\n\n"
                f"🔍 تم العثور على **{len(inactive_assistants)}** حساب خامل:\n\n"
            ]
            
            for assistant in inactive_assistants:
                message_parts.append(
                    f"🔴 **{assistant.get('name', f'حساب {assistant['assistant_id']}')}** (ID: {assistant['assistant_id']})\n"
                )
            
            message_parts.append(
                "\n⚠️ **تحذير:** الحسابات المحذوفة لا يمكن استرجاعها!\n"
                "💡 يُنصح بمحاولة إعادة الاتصال أولاً."
            )
            
            return {
                'success': True,
                'message': ''.join(message_parts),
                'keyboard': keyboard
            }
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في تنظيف الحسابات: {e}")
            return {
                'success': False,
                'message': f"❌ خطأ في التنظيف: {str(e)}"
            }
    
    async def _execute_cleanup_assistants(self, user_id: int) -> Dict:
        """تنفيذ حذف الحسابات الخاملة"""
        if user_id != config.OWNER_ID:
            return {'success': False, 'message': "❌ غير مصرح"}
        
        try:
            # الحصول على قائمة الحسابات الخاملة مرة أخرى
            assistants = await db.get_all_assistants()
            inactive_assistants = []
            
            for assistant in assistants:
                try:
                    is_connected = False
                    for telethon_assistant in telethon_manager.assistants:
                        if telethon_assistant.assistant_id == assistant['assistant_id']:
                            is_connected = telethon_assistant.is_connected
                            break
                    
                    if not is_connected:
                        check_result = await telethon_manager.check_assistant(assistant['assistant_id'])
                        if not check_result.get('connected'):
                            inactive_assistants.append(assistant)
                except Exception:
                    inactive_assistants.append(assistant)
            
            # حذف الحسابات الخاملة
            deleted_count = 0
            for assistant in inactive_assistants:
                try:
                    success = await telethon_manager.remove_assistant(assistant['assistant_id'])
                    if success:
                        deleted_count += 1
                except Exception as e:
                    LOGGER(__name__).warning(f"فشل حذف الحساب {assistant['assistant_id']}: {e}")
            
            message = (
                f"🧹 **تم تنظيف الحسابات الخاملة**\n\n"
                f"✅ تم حذف: `{deleted_count}` حساب\n"
                f"❌ فشل الحذف: `{len(inactive_assistants) - deleted_count}` حساب\n"
                f"📊 إجمالي: `{len(inactive_assistants)}` حساب خامل\n\n"
                "✨ تم تحسين أداء النظام!"
            )
            
            return {
                'success': True,
                'message': message,
                'keyboard': [
                    [{'text': '📋 قائمة الحسابات', 'callback_data': 'list_assistants'}],
                    [{'text': '🔙 العودة', 'callback_data': 'owner_assistants'}]
                ]
            }
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في تنفيذ تنظيف الحسابات: {e}")
            return {
                'success': False,
                'message': f"❌ خطأ في تنفيذ التنظيف: {str(e)}"
            }
    
    async def _show_set_max_assistants(self, user_id: int) -> Dict:
        """عرض إعداد الحد الأقصى للحسابات"""
        if user_id != config.OWNER_ID:
            return {'success': False, 'message': "❌ غير مصرح"}
        
        current_max = getattr(config, 'MAX_ASSISTANTS', 10)
        
        keyboard = []
        for value in [5, 10, 15, 20, 25, 30]:
            emoji = "✅" if value == current_max else "⚪"
            keyboard.append([{
                'text': f'{emoji} {value} حساب',
                'callback_data': f'set_max_{value}'
            }])
        
        keyboard.append([{'text': '🔙 العودة', 'callback_data': 'assistant_settings'}])
        
        return {
            'success': True,
            'message': f"📈 **تعديل الحد الأقصى للحسابات المساعدة**\n\nالحد الحالي: `{current_max}` حساب\n\nاختر الحد الجديد:",
            'keyboard': keyboard
        }
    
    async def _show_set_min_assistants(self, user_id: int) -> Dict:
        """عرض إعداد الحد الأدنى للحسابات"""
        if user_id != config.OWNER_ID:
            return {'success': False, 'message': "❌ غير مصرح"}
        
        current_min = getattr(config, 'MIN_ASSISTANTS', 1)
        
        keyboard = []
        for value in [1, 2, 3, 5, 7, 10]:
            emoji = "✅" if value == current_min else "⚪"
            keyboard.append([{
                'text': f'{emoji} {value} حساب',
                'callback_data': f'set_min_{value}'
            }])
        
        keyboard.append([{'text': '🔙 العودة', 'callback_data': 'assistant_settings'}])
        
        return {
            'success': True,
            'message': f"📉 **تعديل الحد الأدنى للحسابات المساعدة**\n\nالحد الحالي: `{current_min}` حساب\n\nاختر الحد الجديد:",
            'keyboard': keyboard
        }
    
    async def _toggle_auto_restart(self, user_id: int) -> Dict:
        """تبديل إعدادات إعادة التشغيل التلقائي"""
        if user_id != config.OWNER_ID:
            return {'success': False, 'message': "❌ غير مصرح"}
        
        try:
            # قراءة الحالة الحالية
            current_state = getattr(config, 'AUTO_RESTART_ASSISTANTS', True)
            new_state = not current_state
            
            # تحديث الإعداد (يجب حفظه في ملف config أو قاعدة البيانات)
            config.AUTO_RESTART_ASSISTANTS = new_state
            
            state_text = "✅ مفعل" if new_state else "❌ معطل"
            
            return {
                'success': True,
                'message': f"🔄 **تم تحديث إعدادات إعادة التشغيل التلقائي**\n\nالحالة الجديدة: `{state_text}`\n\n💡 سيتم تطبيق التغيير فوراً.",
                'keyboard': [
                    [{'text': '⚙️ إعدادات أخرى', 'callback_data': 'assistant_settings'}],
                    [{'text': '🔙 العودة', 'callback_data': 'owner_assistants'}]
                ]
            }
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في تبديل إعادة التشغيل التلقائي: {e}")
            return {
                'success': False,
                'message': f"❌ خطأ في التحديث: {str(e)}"
            }
    
    async def _set_max_assistants(self, user_id: int, value: int) -> Dict:
        """تحديث الحد الأقصى للحسابات"""
        if user_id != config.OWNER_ID:
            return {'success': False, 'message': "❌ غير مصرح"}
        
        try:
            # تحديث القيمة
            config.MAX_ASSISTANTS = value
            
            return {
                'success': True,
                'message': f"✅ **تم تحديث الحد الأقصى للحسابات**\n\nالحد الجديد: `{value}` حساب\n\n💡 سيتم تطبيق التغيير عند إضافة حسابات جديدة.",
                'keyboard': [
                    [{'text': '⚙️ إعدادات أخرى', 'callback_data': 'assistant_settings'}],
                    [{'text': '🔙 العودة', 'callback_data': 'owner_assistants'}]
                ]
            }
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في تحديث الحد الأقصى: {e}")
            return {
                'success': False,
                'message': f"❌ خطأ في التحديث: {str(e)}"
            }
    
    async def _set_min_assistants(self, user_id: int, value: int) -> Dict:
        """تحديث الحد الأدنى للحسابات"""
        if user_id != config.OWNER_ID:
            return {'success': False, 'message': "❌ غير مصرح"}
        
        try:
            # تحديث القيمة
            config.MIN_ASSISTANTS = value
            
            return {
                'success': True,
                'message': f"✅ **تم تحديث الحد الأدنى للحسابات**\n\nالحد الجديد: `{value}` حساب\n\n💡 سيتم تطبيق التغيير عند إدارة الحسابات.",
                'keyboard': [
                    [{'text': '⚙️ إعدادات أخرى', 'callback_data': 'assistant_settings'}],
                    [{'text': '🔙 العودة', 'callback_data': 'owner_assistants'}]
                ]
            }
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في تحديث الحد الأدنى: {e}")
            return {
                'success': False,
                'message': f"❌ خطأ في التحديث: {str(e)}"
            }
    
    async def list_assistants(self, user_id: int) -> Dict:
        """عرض قائمة الحسابات المساعدة"""
        if user_id != config.OWNER_ID:
            return {'success': False, 'message': "❌ غير مصرح"}
        
        try:
            # جلب جميع الحسابات (نشطة وغير نشطة) للتشخيص
            all_assistants = await db.get_assistants()  # جميع الحسابات
            active_assistants = await db.get_all_assistants()  # النشطة فقط
            
            # تشخيص المشكلة
            if all_assistants and not active_assistants:
                # يوجد حسابات لكنها غير نشطة
                debug_message = (
                    f"🔍 **تشخيص المشكلة:**\n\n"
                    f"📊 إجمالي الحسابات: `{len(all_assistants)}`\n"
                    f"✅ الحسابات النشطة: `{len(active_assistants)}`\n\n"
                    f"⚠️ **المشكلة:** يوجد {len(all_assistants)} حساب لكنها غير مفعلة\n\n"
                    f"**الحسابات الموجودة:**\n"
                )
                
                for i, assistant in enumerate(all_assistants[:5]):  # أول 5 حسابات فقط
                    debug_message += (
                        f"{i+1}. ID: `{assistant['assistant_id']}` | "
                        f"نشط: `{'✅' if assistant.get('is_active') else '❌'}` | "
                        f"الاسم: `{assistant.get('name', 'غير محدد')}`\n"
                    )
                
                keyboard = [
                    [{'text': '🔧 إصلاح الحسابات', 'callback_data': 'fix_inactive_assistants'}],
                    [{'text': '➕ إضافة حساب جديد', 'callback_data': 'add_assistant'}],
                    [{'text': '🔙 العودة', 'callback_data': 'owner_assistants'}]
                ]
                
                return {
                    'success': True,
                    'message': debug_message,
                    'keyboard': keyboard
                }
            
            assistants = active_assistants
            
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
                user_info = {}
                
                try:
                    for telethon_assistant in telethon_manager.assistants:
                        if telethon_assistant.assistant_id == assistant['assistant_id']:
                            is_connected = telethon_assistant.is_connected
                            active_calls = getattr(telethon_assistant, 'active_calls_count', 0)
                            user_info = getattr(telethon_assistant, 'user_info', {})
                            break
                except:
                    pass
                
                status_emoji = "🟢" if is_connected else "🔴"
                status_text = "متصل" if is_connected else "غير متصل"
                
                # معلومات إضافية
                phone = user_info.get('phone', 'غير معروف')
                username = user_info.get('username', 'غير متاح')
                
                assistant_info = (
                    f"\n{status_emoji} **الحساب {assistant['assistant_id']}**\n"
                    f"📝 الاسم: `{assistant.get('name', 'غير محدد')}`\n"
                    f"📱 الهاتف: `{phone}`\n"
                    f"👤 اليوزر: `@{username}` " if username != 'غير متاح' else f"👤 اليوزر: `{username}`\n"
                    f"🔌 الحالة: `{status_text}`\n"
                    f"🎵 المكالمات النشطة: `{active_calls}`\n"
                    f"📊 إجمالي الاستخدام: `{assistant.get('total_calls', 0)}`\n"
                    f"🕐 آخر استخدام: `{assistant.get('last_used', 'غير محدد')[:19]}`\n"
                )
                
                message_parts.append(assistant_info)
            
            keyboard = [
                [
                    {'text': '➕ إضافة حساب', 'callback_data': 'add_assistant'},
                    {'text': '🗑️ حذف حساب', 'callback_data': 'remove_assistant_list'}
                ],
                [
                    {'text': '🔄 تحديث القائمة', 'callback_data': 'list_assistants'},
                    {'text': '🔍 فحص الحسابات', 'callback_data': 'check_assistants'}
                ],
                [
                    {'text': '🔙 العودة', 'callback_data': 'owner_assistants'}
                ]
            ]
            
            return {
                'success': True,
                'message': ''.join(message_parts),
                'keyboard': keyboard
            }
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في عرض قائمة الحسابات: {e}")
            return {
                'success': False,
                'message': f"❌ خطأ في عرض القائمة: {str(e)}"
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
            
            # تنظيف session string بشكل شامل
            import string
            allowed_chars = string.ascii_letters + string.digits + '+/=-_'
            session_string = session_string.strip().replace('\n', '').replace('\r', '').replace(' ', '').replace('\t', '')
            # إزالة الأحرف غير المسموحة
            session_string = ''.join(c for c in session_string if c in allowed_chars)
            
            # التحقق الأساسي من صيغة session string
            if not self._validate_session_string(session_string):
                return {
                    'success': False,
                    'message': f"❌ **صيغة session string غير صحيحة**\n\n📏 **الطول الحالي:** {len(session_string)} حرف\n💡 **المطلوب:** أكثر من 100 حرف صالح\n\n🔧 **المشكلة:** قد يحتوي على أحرف غير مدعومة\n\n🔄 **الحل:**\n• انسخ session string كاملاً\n• تأكد من عدم وجود مسافات إضافية\n• استخدم session string من مصدر موثوق"
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
                
                # تجربة عدة طرق للاتصال
                test_client = None
                connection_success = False
                
                # المحاولة 1: الطريقة العادية
                try:
                    test_client = TelegramClient(StringSession(session_string), config.API_ID, config.API_HASH)
                    await test_client.connect()
                    connection_success = True
                except Exception as e1:
                    # المحاولة 2: مع إعدادات مختلفة
                    try:
                        if test_client:
                            await test_client.disconnect()
                        test_client = TelegramClient(StringSession(session_string), config.API_ID, config.API_HASH)
                        test_client.session.timeout = 30
                        await test_client.connect()
                        connection_success = True
                    except Exception as e2:
                        raise e1  # استخدم الخطأ الأول
                
                if not connection_success or not test_client:
                    return {
                        'success': False,
                        'message': "❌ **فشل في الاتصال**\n\n🔧 تحقق من اتصال الإنترنت وأعد المحاولة"
                    }
                
                # التحقق من التفويض
                if not await test_client.is_user_authorized():
                    await test_client.disconnect()
                    return {
                        'success': False,
                        'message': "❌ **session string غير صالح أو منتهي الصلاحية**\n\n🔄 **الحل:**\n• احصل على session string جديد\n• تأكد من عدم تسجيل الخروج من الحساب\n• استخدم نفس API_ID و API_HASH"
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
                result = await telethon_manager.add_assistant_with_session(session_string, auto_name)
                success = result.get('success', False)
                
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
            # إزالة المسافات والسطور الجديدة والأحرف الخاصة
            session_string = session_string.strip().replace('\n', '').replace('\r', '').replace(' ', '').replace('\t', '')
            
            # التحقق من الطول الأدنى
            if len(session_string) < 100:
                return False
            
            # التحقق البسيط: يجب أن يحتوي على أحرف وأرقام بشكل أساسي
            # تساهل أكثر مع الأحرف المسموحة
            import string
            allowed_chars = string.ascii_letters + string.digits + '+/=-_'
            clean_session = ''.join(c for c in session_string if c in allowed_chars)
            
            # إذا كان معظم الـ string صالح، قبله
            if len(clean_session) >= len(session_string) * 0.8:  # 80% من الأحرف صالحة
                return True
            
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
    
    async def fix_inactive_assistants(self, user_id: int) -> Dict:
        """إصلاح الحسابات غير النشطة"""
        if user_id != config.OWNER_ID:
            return {'success': False, 'message': "❌ غير مصرح"}
        
        try:
            # جلب جميع الحسابات
            all_assistants = await db.get_assistants()
            
            if not all_assistants:
                return {
                    'success': True,
                    'message': "❌ لا توجد حسابات لإصلاحها",
                    'keyboard': [[{'text': '🔙 العودة', 'callback_data': 'owner_assistants'}]]
                }
            
            # استخدام دالة الإصلاح من قاعدة البيانات
            fix_result = await db.fix_inactive_assistants()
            fixed_count = fix_result['fixed']
            
            if fixed_count > 0:
                message = (
                    f"✅ **تم إصلاح الحسابات بنجاح!**\n\n"
                    f"🔧 تم تفعيل `{fixed_count}` حساب\n"
                    f"📊 إجمالي الحسابات: `{len(all_assistants)}`\n\n"
                    f"الآن يمكنك عرض قائمة الحسابات بشكل طبيعي."
                )
            else:
                message = "✅ جميع الحسابات مفعلة بالفعل"
            
            keyboard = [
                [{'text': '📋 عرض الحسابات', 'callback_data': 'list_assistants'}],
                [{'text': '🔙 العودة', 'callback_data': 'owner_assistants'}]
            ]
            
            return {
                'success': True,
                'message': message,
                'keyboard': keyboard
            }
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في إصلاح الحسابات: {e}")
            return {
                'success': False,
                'message': f"❌ خطأ في إصلاح الحسابات: {str(e)}"
            }
    
    async def _activate_assistant(self, assistant_id: int):
        """تفعيل حساب مساعد"""
        try:
            # تحديث قاعدة البيانات لتفعيل الحساب
            import sqlite3
            with sqlite3.connect(config.DATABASE_PATH) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute('''
                    UPDATE assistants 
                    SET is_active = 1 
                    WHERE assistant_id = ?
                ''', (assistant_id,))
                conn.commit()
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في تفعيل الحساب {assistant_id}: {e}")

    async def handle_settings_callback(self, user_id: int, data: str) -> Dict:
        """معالج أزرار الإعدادات"""
        if user_id != config.OWNER_ID:
            return {'success': False, 'message': "❌ غير مصرح"}
        
        setting_type = data.replace("settings_", "")
        
        messages = {
            'assistants': "📱 **إعدادات الحسابات المساعدة**\n\n🚧 هذه الميزة قيد التطوير...",
            'music': "🎵 **إعدادات الموسيقى**\n\n🚧 هذه الميزة قيد التطوير...",
            'security': "🛡️ **إعدادات الأمان**\n\n🚧 هذه الميزة قيد التطوير...",
            'general': "🌐 **إعدادات عامة**\n\n🚧 هذه الميزة قيد التطوير..."
        }
        
        return {
            'success': True,
            'message': messages.get(setting_type, "⚠️ إعداد غير معروف"),
            'keyboard': [[{'text': '🔙 العودة للإعدادات', 'callback_data': 'owner_settings'}]]
        }
    
    async def handle_maintenance_callback(self, user_id: int, data: str) -> Dict:
        """معالج أزرار الصيانة"""
        if user_id != config.OWNER_ID:
            return {'success': False, 'message': "❌ غير مصرح"}
        
        maintenance_type = data.replace("maintenance_", "")
        
        messages = {
            'cleanup': "🧹 **تنظيف النظام**\n\n🚧 هذه الميزة قيد التطوير...",
            'update': "🔄 **تحديث النظام**\n\n🚧 هذه الميزة قيد التطوير...",
            'check': "🔍 **فحص النظام**\n\n🚧 هذه الميزة قيد التطوير...",
            'optimize': "⚡ **تحسين الأداء**\n\n🚧 هذه الميزة قيد التطوير..."
        }
        
        return {
            'success': True,
            'message': messages.get(maintenance_type, "⚠️ عملية صيانة غير معروفة"),
            'keyboard': [[{'text': '🔙 العودة للصيانة', 'callback_data': 'owner_maintenance'}]]
        }
    
    async def handle_logs_callback(self, user_id: int, data: str) -> Dict:
        """معالج أزرار السجلات"""
        if user_id != config.OWNER_ID:
            return {'success': False, 'message': "❌ غير مصرح"}
        
        log_type = data.replace("logs_", "")
        
        messages = {
            'full': "📄 **السجل الكامل**\n\n🚧 هذه الميزة قيد التطوير...",
            'errors': "⚠️ **الأخطاء فقط**\n\n🚧 هذه الميزة قيد التطوير...",
            'stats': "📊 **إحصائيات السجل**\n\n🚧 هذه الميزة قيد التطوير...",
            'clear': "🗑️ **مسح السجلات**\n\n🚧 هذه الميزة قيد التطوير..."
        }
        
        return {
            'success': True,
            'message': messages.get(log_type, "⚠️ نوع سجل غير معروف"),
            'keyboard': [[{'text': '🔙 العودة للسجلات', 'callback_data': 'owner_logs'}]]
        }
    
    async def handle_database_callback(self, user_id: int, data: str) -> Dict:
        """معالج أزرار قاعدة البيانات"""
        if user_id != config.OWNER_ID:
            return {'success': False, 'message': "❌ غير مصرح"}
        
        db_type = data.replace("db_", "")
        
        messages = {
            'backup': "💾 **نسخة احتياطية**\n\n🚧 هذه الميزة قيد التطوير...",
            'restore': "📤 **استيراد نسخة**\n\n🚧 هذه الميزة قيد التطوير...",
            'cleanup': "🧹 **تنظيف البيانات**\n\n🚧 هذه الميزة قيد التطوير...",
            'optimize': "🔧 **تحسين قاعدة البيانات**\n\n🚧 هذه الميزة قيد التطوير...",
            'detailed_stats': "📊 **إحصائيات مفصلة**\n\n🚧 هذه الميزة قيد التطوير...",
            'integrity_check': "🔍 **فحص سلامة البيانات**\n\n🚧 هذه الميزة قيد التطوير..."
        }
        
        return {
            'success': True,
            'message': messages.get(db_type, "⚠️ عملية قاعدة بيانات غير معروفة"),
            'keyboard': [[{'text': '🔙 العودة لقاعدة البيانات', 'callback_data': 'owner_database'}]]
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
        # في Telethon v1.36+، event.data هو نص مباشرة
        data = event.data if isinstance(event.data, str) else event.data.decode('utf-8')
        user_id = event.sender_id
        
        # التحقق من الصلاحيات
        if user_id != config.OWNER_ID:
            await event.answer("❌ هذا الأمر مخصص لمالك البوت فقط", alert=True)
            return
        
        # معالجة اللوحات الرئيسية
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
        
        # معالجة الحسابات المساعدة
        elif data == "add_assistant":
            result = await owner_panel.handle_add_assistant(user_id)
        elif data == "list_assistants":
            result = await owner_panel.list_assistants(user_id)
        elif data == "remove_assistant_list":
            result = await owner_panel.show_remove_assistant_list(user_id)
        elif data.startswith("remove_assistant_"):
            assistant_id = data.replace("remove_assistant_", "")
            result = await owner_panel.handle_remove_assistant(user_id, assistant_id)
        elif data == "restart_assistants":
            result = await owner_panel.restart_assistants(user_id)
        
        elif data == "fix_inactive_assistants":
            result = await owner_panel.fix_inactive_assistants(user_id)
        elif data == "check_assistants":
            result = await owner_panel.check_assistants(user_id)
        elif data == "assistant_settings":
            result = await owner_panel.show_assistant_settings(user_id)
        elif data == "cleanup_assistants":
            result = await owner_panel.cleanup_assistants(user_id)
        elif data == "assistant_stats":
            result = await owner_panel.show_detailed_stats(user_id)
        
        # معالجة أوامر إضافية للحسابات
        elif data == "confirm_add_assistant":
            result = await owner_panel.confirm_add_assistant(user_id)
        elif data == "cancel_add_assistant":
            result = await owner_panel.show_assistants_panel(user_id)
        elif data == "confirm_cleanup_assistants":
            # تنفيذ تنظيف الحسابات الخاملة
            result = await owner_panel._execute_cleanup_assistants(user_id)
        elif data == "retry_inactive_assistants":
            # إعادة محاولة اتصال الحسابات الخاملة
            result = await owner_panel.restart_assistants(user_id)
        
        # معالجة الإعدادات
        elif data == "set_max_assistants":
            result = await owner_panel._show_set_max_assistants(user_id)
        elif data == "set_min_assistants":
            result = await owner_panel._show_set_min_assistants(user_id)
        elif data == "toggle_auto_restart":
            result = await owner_panel._toggle_auto_restart(user_id)
        elif data.startswith("set_max_"):
            value = int(data.replace("set_max_", ""))
            result = await owner_panel._set_max_assistants(user_id, value)
        elif data.startswith("set_min_"):
            value = int(data.replace("set_min_", ""))
            result = await owner_panel._set_min_assistants(user_id, value)
        
        # معالجة أوامر النظام
        elif data == "owner_restart":
            result = await owner_panel.handle_restart(user_id)
        elif data == "owner_shutdown":
            result = await owner_panel.handle_shutdown(user_id)
        elif data == "confirm_restart":
            result = await owner_panel.execute_restart(user_id)
        elif data == "confirm_shutdown":
            result = await owner_panel.execute_shutdown(user_id)
        elif data == "fix_inactive_assistants":
            result = await owner_panel.fix_inactive_assistants(user_id)
        
        # معالجة أزرار الإعدادات
        elif data.startswith("settings_"):
            result = await owner_panel.handle_settings_callback(user_id, data)
            
        # معالجة أزرار الصيانة
        elif data.startswith("maintenance_"):
            result = await owner_panel.handle_maintenance_callback(user_id, data)
            
        # معالجة أزرار السجلات
        elif data.startswith("logs_"):
            result = await owner_panel.handle_logs_callback(user_id, data)
            
        # معالجة أزرار قاعدة البيانات
        elif data.startswith("db_"):
            result = await owner_panel.handle_database_callback(user_id, data)
        
        else:
            # رسالة واضحة للأزرار غير المُنفذة
            result = {
                'success': True,
                'message': f"🚧 **{data}**\n\nهذه الميزة قيد التطوير...\n📅 سيتم إضافتها في التحديثات القادمة",
                'keyboard': [[{'text': '🔙 العودة للوحة الرئيسية', 'callback_data': 'owner_main'}]]
            }
        
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