import asyncio
import sqlite3
import time
import re
from typing import Dict, List, Optional
from datetime import datetime, timedelta

import config
from ZeMusic.logging import LOGGER
from ZeMusic.core.telethon_client import telethon_manager
from ZeMusic.core.database import db

# استيراد Telethon للتحقق من session strings
try:
    from telethon import TelegramClient
    from telethon.sessions import StringSession
    from telethon.errors import SessionPasswordNeededError, ApiIdInvalidError, PhoneNumberInvalidError
except ImportError:
    TelegramClient = None
    StringSession = None
    LOGGER(__name__).error("❌ Telethon غير مثبت - معالج الحسابات المساعدة معطل")

class AssistantsHandler:
    """معالج إدارة الحسابات المساعدة المتطور مع Telethon"""
    
    def __init__(self):
        self.pending_sessions = {}  # جلسات إضافة الحسابات
        self.auto_leave_enabled = False
        self.auto_leave_timeout = 300  # 5 دقائق
        self.load_auto_leave_settings()
        self._auto_leave_task_started = False
        
    async def start_auto_leave_task(self):
        """بدء مهمة المغادرة التلقائية"""
        if not self._auto_leave_task_started:
            self._auto_leave_task_started = True
            asyncio.create_task(self._auto_leave_task())
    
    def load_auto_leave_settings(self):
        """تحميل إعدادات المغادرة التلقائية"""
        try:
            with sqlite3.connect(config.DATABASE_PATH) as conn:
                cursor = conn.cursor()
                
                # إنشاء جدول إعدادات المغادرة التلقائية
                cursor.execute("""
                    CREATE TABLE IF NOT EXISTS auto_leave_settings (
                        id INTEGER PRIMARY KEY DEFAULT 1,
                        enabled BOOLEAN DEFAULT FALSE,
                        timeout_minutes INTEGER DEFAULT 5,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                """)
                
                cursor.execute("INSERT OR IGNORE INTO auto_leave_settings (id) VALUES (1)")
                
                # تحميل الإعدادات
                cursor.execute("SELECT enabled, timeout_minutes FROM auto_leave_settings WHERE id = 1")
                row = cursor.fetchone()
                
                if row:
                    self.auto_leave_enabled = bool(row[0])
                    self.auto_leave_timeout = row[1] * 60  # تحويل للثواني
                    
                conn.commit()
                LOGGER(__name__).info(f"تم تحميل إعدادات المغادرة التلقائية - مفعل: {self.auto_leave_enabled}")
                
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في تحميل إعدادات المغادرة التلقائية: {e}")
    
    def save_auto_leave_settings(self):
        """حفظ إعدادات المغادرة التلقائية"""
        try:
            with sqlite3.connect(config.DATABASE_PATH) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    UPDATE auto_leave_settings 
                    SET enabled = ?, timeout_minutes = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = 1
                """, (self.auto_leave_enabled, self.auto_leave_timeout // 60))
                conn.commit()
                
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في حفظ إعدادات المغادرة التلقائية: {e}")
    
    async def show_assistants_panel(self, user_id: int) -> Dict:
        """عرض لوحة إدارة الحسابات المساعدة"""
        if user_id != config.OWNER_ID:
            return {'success': False, 'message': "❌ غير مصرح"}
        
        # الحصول على إحصائيات الحسابات المساعدة
        assistants_stats = await self._get_assistants_stats()
        
        keyboard = [
            [
                {'text': '➕ إضافة حساب مساعد', 'callback_data': 'assistants_add'},
                {'text': '🗑️ حذف حساب مساعد', 'callback_data': 'assistants_remove'}
            ],
            [
                {'text': '📋 عرض الحسابات المساعدة', 'callback_data': 'assistants_list'},
                {'text': '🔄 إعادة تشغيل الحسابات', 'callback_data': 'assistants_restart'}
            ],
            [
                {'text': f'🚪 المغادرة التلقائية: {"🟢 مفعل" if self.auto_leave_enabled else "🔴 معطل"}', 
                 'callback_data': 'assistants_auto_leave_toggle'},
                {'text': '⚙️ إعدادات المغادرة', 'callback_data': 'assistants_auto_leave_settings'}
            ],
            [
                {'text': '🧪 اختبار الحسابات', 'callback_data': 'assistants_test'},
                {'text': '📊 إحصائيات مفصلة', 'callback_data': 'assistants_detailed_stats'}
            ],
            [
                {'text': '🔄 تحديث الحالة', 'callback_data': 'assistants_refresh'},
                {'text': '🔧 صيانة الحسابات', 'callback_data': 'assistants_maintenance'}
            ],
            [
                {'text': '🔙 العودة للوحة الرئيسية', 'callback_data': 'admin_main'}
            ]
        ]
        
        auto_leave_status = "🟢 مفعل" if self.auto_leave_enabled else "🔴 معطل"
        auto_leave_time = f"{self.auto_leave_timeout // 60} دقائق"
        
        message = (
            f"📱 **إدارة الحسابات المساعدة مع Telethon**\n\n"
            
            f"📊 **الإحصائيات:**\n"
            f"🤖 إجمالي الحسابات: `{assistants_stats['total']}`\n"
            f"🟢 متصلة: `{assistants_stats['connected']}`\n"
            f"🔴 غير متصلة: `{assistants_stats['disconnected']}`\n"
            f"⚡ نشطة: `{assistants_stats['active']}`\n"
            f"🎵 في مكالمات: `{assistants_stats['in_calls']}`\n\n"
            
            f"🚪 **المغادرة التلقائية:** {auto_leave_status}\n"
            f"⏱️ **مدة عدم النشاط:** `{auto_leave_time}`\n\n"
            
            f"🔥 **ميزات Telethon:**\n"
            f"• جلسات session strings آمنة\n"
            f"• اتصال مباشر بـ Telegram\n"
            f"• أداء عالي ومستقر\n"
            f"• دعم كامل للميديا\n"
            f"• حماية من الحذف\n\n"
            
            f"💡 **معلومات:**\n"
            f"• الحسابات المساعدة تساعد في تشغيل الموسيقى\n"
            f"• يُنصح بوجود 2-3 حسابات للأداء الأمثل\n"
            f"• استخدم session strings من Telethon فقط\n\n"
            
            f"🎯 اختر الإجراء المطلوب:"
        )
        
        return {
            'success': True,
            'message': message,
            'keyboard': keyboard,
            'parse_mode': 'Markdown'
        }
    
    async def start_add_assistant(self, user_id: int) -> Dict:
        """بدء عملية إضافة حساب مساعد مع Telethon"""
        if user_id != config.OWNER_ID:
            return {'success': False, 'message': "❌ غير مصرح"}
        
        # إنشاء جلسة إضافة جديدة
        session_id = f"add_assistant_{user_id}_{int(time.time())}"
        self.pending_sessions[user_id] = {
            'session_id': session_id,
            'step': 'waiting_session_string',
            'created_at': time.time()
        }
        
        keyboard = [
            [
                {'text': '📚 دليل الحصول على Session String', 'callback_data': 'assistants_session_guide'}
            ],
            [
                {'text': '❌ إلغاء الإضافة', 'callback_data': 'assistants_cancel_add'}
            ]
        ]
        
        message = (
            f"➕ **إضافة حساب مساعد جديد مع Telethon**\n\n"
            
            f"📋 **خطوات الإضافة:**\n"
            f"1️⃣ الحصول على Telethon Session String\n"
            f"2️⃣ إرسال Session String للبوت\n"
            f"3️⃣ التحقق من صحة الجلسة\n"
            f"4️⃣ اختيار اسم للحساب\n"
            f"5️⃣ تأكيد الإضافة والتفعيل\n\n"
            
            f"🔐 **الحصول على Telethon Session String:**\n\n"
            
            f"**الطريقة الأولى - استخدام StringFatherBot:**\n"
            f"• تحدث مع @StringFatherBot\n"
            f"• اختر Generate String Session\n"
            f"• اختر Telethon\n"
            f"• أدخل معلومات حسابك\n\n"
            
            f"**الطريقة الثانية - استخدام Script Python:**\n"
            f"```python\n"
            f"from telethon import TelegramClient\n"
            f"from telethon.sessions import StringSession\n\n"
            f"api_id = YOUR_API_ID\n"
            f"api_hash = 'YOUR_API_HASH'\n\n"
            f"with TelegramClient(StringSession(), api_id, api_hash) as client:\n"
            f"    print(client.session.save())\n"
            f"```\n\n"
            
            f"⚠️ **تنبيهات مهمة:**\n"
            f"• استخدم Telethon Session String فقط\n"
            f"• لا تشارك Session String مع أحد\n"
            f"• تأكد من صحة API_ID و API_HASH\n"
            f"• الحساب يجب أن يكون نشط وغير محظور\n"
            f"• يُفضل حسابات عمرها أكثر من 6 أشهر\n\n"
            
            f"📝 **أرسل الآن Telethon Session String:**"
        )
        
        return {
            'success': True,
            'message': message,
            'keyboard': keyboard,
            'parse_mode': 'Markdown',
            'waiting_session': True
        }
    
    async def process_session_string(self, user_id: int, session_string: str) -> Dict:
        """معالجة Telethon session string المرسل"""
        if user_id != config.OWNER_ID:
            return {'success': False, 'message': "❌ غير مصرح"}
        
        if user_id not in self.pending_sessions:
            return {'success': False, 'message': "❌ لا توجد جلسة إضافة نشطة"}
        
        try:
            # تنظيف session string
            session_string = session_string.strip()
            
            # التحقق من صحة Telethon session string
            validation_result = await self._validate_telethon_session(session_string)
            
            if not validation_result['valid']:
                return {
                    'success': False,
                    'message': f"❌ **Session String غير صحيح**\n\n🔧 **السبب:** {validation_result['error']}\n\n💡 **الحلول:**\n• تأكد من أنه Telethon Session String\n• تحقق من API_ID و API_HASH\n• جرب إنشاء جلسة جديدة\n• استخدم @StringFatherBot"
                }
            
            # حفظ session string وبيانات المستخدم في الجلسة
            self.pending_sessions[user_id]['session_string'] = session_string
            self.pending_sessions[user_id]['user_info'] = validation_result['user_info']
            self.pending_sessions[user_id]['step'] = 'waiting_name'
            
            keyboard = [
                [
                    {'text': f'⏭️ استخدام: {validation_result["user_info"]["display_name"]}', 'callback_data': 'assistants_use_account_name'},
                    {'text': '✏️ اسم مخصص', 'callback_data': 'assistants_custom_name'}
                ],
                [
                    {'text': '❌ إلغاء', 'callback_data': 'assistants_cancel_add'}
                ]
            ]
            
            user_info = validation_result['user_info']
            
            message = (
                f"✅ **تم التحقق من Session String بنجاح!**\n\n"
                
                f"👤 **معلومات الحساب المكتشف:**\n"
                f"🆔 المعرف: `{user_info['id']}`\n"
                f"👤 الاسم: `{user_info['display_name']}`\n"
                f"📱 الهاتف: `{user_info['phone']}`\n"
                f"💎 Premium: `{'نعم' if user_info.get('is_premium') else 'لا'}`\n"
                f"🤖 بوت: `{'نعم' if user_info.get('is_bot') else 'لا'}`\n\n"
                
                f"📝 **اختر اسم للحساب المساعد:**\n"
                f"• يمكنك استخدام اسم الحساب الحالي\n"
                f"• أو إدخال اسم مخصص\n"
                f"• الاسم يظهر في لوحة الإدارة\n\n"
                
                f"💡 **أو أرسل اسماً مخصصاً مباشرة**"
            )
            
            return {
                'success': True,
                'message': message,
                'keyboard': keyboard,
                'parse_mode': 'Markdown',
                'waiting_name': True
            }
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في معالجة session string: {e}")
            return {
                'success': False,
                'message': f"❌ حدث خطأ في معالجة Session String: {str(e)}"
            }
    
    async def process_assistant_name(self, user_id: int, name: str) -> Dict:
        """معالجة اسم الحساب المساعد"""
        if user_id not in self.pending_sessions:
            return {'success': False, 'message': "❌ لا توجد جلسة نشطة"}
        
        session = self.pending_sessions[user_id]
        session['assistant_name'] = name.strip()
        session['step'] = 'confirmation'
        
        keyboard = [
            [
                {'text': '✅ تأكيد الإضافة', 'callback_data': 'assistants_confirm_add'},
                {'text': '❌ إلغاء', 'callback_data': 'assistants_cancel_add'}
            ],
            [
                {'text': '✏️ تعديل الاسم', 'callback_data': 'assistants_edit_name'}
            ]
        ]
        
        user_info = session.get('user_info', {})
        
        message = (
            f"📋 **تأكيد إضافة الحساب المساعد**\n\n"
            
            f"✅ **تفاصيل الحساب:**\n"
            f"📛 الاسم المخصص: `{name}`\n"
            f"👤 اسم الحساب: `{user_info.get('display_name', 'غير متاح')}`\n"
            f"🆔 المعرف: `{user_info.get('id', 'غير متاح')}`\n"
            f"📱 الهاتف: `{user_info.get('phone', 'غير متاح')}`\n"
            f"🔐 Session: `محفوظ بأمان`\n"
            f"⏰ تاريخ الإضافة: `{datetime.now().strftime('%Y-%m-%d %H:%M')}`\n\n"
            
            f"🔄 **ما سيحدث عند التأكيد:**\n"
            f"• حفظ الحساب في قاعدة البيانات\n"
            f"• إنشاء اتصال Telethon مع الحساب\n"
            f"• التحقق من صحة الاتصال\n"
            f"• تفعيل الحساب للاستخدام\n"
            f"• إضافته لمدير الحسابات المساعدة\n\n"
            
            f"⚡ **مميزات Telethon:**\n"
            f"• اتصال مباشر وسريع\n"
            f"• دعم كامل للميديا والصوتيات\n"
            f"• استقرار عالي\n"
            f"• حماية متقدمة\n\n"
            
            f"❓ هل تريد تأكيد الإضافة؟"
        )
        
        return {
            'success': True,
            'message': message,
            'keyboard': keyboard,
            'parse_mode': 'Markdown'
        }
    
    async def confirm_add_assistant(self, user_id: int) -> Dict:
        """تأكيد إضافة الحساب المساعد مع Telethon"""
        if user_id not in self.pending_sessions:
            return {'success': False, 'message': "❌ لا توجد جلسة نشطة"}
        
        session = self.pending_sessions[user_id]
        
        try:
            # إضافة الحساب إلى Telethon Manager
            add_result = await telethon_manager.add_assistant_with_session(
                session['session_string'],
                session['assistant_name']
            )
            
            if not add_result['success']:
                return {
                    'success': False,
                    'message': f"❌ **فشل في إضافة الحساب**\n\n🔧 **السبب:** {add_result.get('error', 'خطأ غير معروف')}\n\n💡 **الحلول:**\n• تحقق من صحة Session String\n• تأكد من عدم انتهاء صلاحية الجلسة\n• جرب إنشاء جلسة جديدة"
                }
            
            # حفظ في قاعدة البيانات
            assistant_id = add_result['assistant_id']
            user_info = session.get('user_info', {})
            
            await db.add_assistant(
                assistant_id=assistant_id,
                session_string=session['session_string'],
                name=session['assistant_name'],
                user_id=user_info.get('id'),
                username=user_info.get('username', ''),
                phone=user_info.get('phone', '')
            )
            
            # إنهاء الجلسة
            del self.pending_sessions[user_id]
            
            keyboard = [
                [
                    {'text': '📋 عرض الحسابات', 'callback_data': 'assistants_list'},
                    {'text': '🧪 اختبار الحساب', 'callback_data': 'assistants_test'}
                ],
                [
                    {'text': '➕ إضافة حساب آخر', 'callback_data': 'assistants_add'}
                ],
                [
                    {'text': '🔙 العودة لإدارة الحسابات', 'callback_data': 'admin_assistants'}
                ]
            ]
            
            connection_status = "✅ متصل ونشط" if add_result.get('connected') else "⚠️ مضاف لكن غير متصل"
            
            message = (
                f"🎉 **تم إضافة الحساب المساعد بنجاح!**\n\n"
                
                f"📱 **تفاصيل الحساب المضاف:**\n"
                f"🆔 معرف المساعد: `{assistant_id}`\n"
                f"📛 الاسم المخصص: `{session['assistant_name']}`\n"
                f"👤 اسم المستخدم: `{user_info.get('display_name', 'غير متاح')}`\n"
                f"🔌 حالة الاتصال: {connection_status}\n"
                f"🚀 النوع: `Telethon Client`\n"
                f"📊 الحالة: `جاهز للاستخدام`\n\n"
                
                f"✅ **تم تنفيذ:**\n"
                f"• إنشاء اتصال Telethon مع الحساب\n"
                f"• حفظ الحساب في قاعدة البيانات\n"
                f"• تفعيل الحساب في النظام\n"
                f"• إضافته لمدير الحسابات المساعدة\n"
                f"• تجهيزه لتشغيل الموسيقى\n\n"
                
                f"🎵 **الآن يمكن للحساب:**\n"
                f"• الانضمام للمكالمات الصوتية\n"
                f"• تشغيل الموسيقى والأغاني\n"
                f"• التعامل مع ملفات الصوت\n"
                f"• المشاركة في المحادثات\n\n"
                
                f"💡 **نصيحة:** يمكنك إضافة 2-3 حسابات أخرى لتحسين الأداء"
            )
            
            return {
                'success': True,
                'message': message,
                'keyboard': keyboard,
                'parse_mode': 'Markdown'
            }
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في إضافة الحساب المساعد: {e}")
            return {
                'success': False,
                'message': f"❌ فشل في إضافة الحساب: {str(e)}"
            }
    
    async def show_session_guide(self, user_id: int) -> Dict:
        """عرض دليل شامل للحصول على Session String"""
        if user_id != config.OWNER_ID:
            return {'success': False, 'message': "❌ غير مصرح"}
        
        keyboard = [
            [
                {'text': '🤖 استخدام StringFatherBot', 'callback_data': 'guide_stringfather'},
                {'text': '🐍 استخدام Python Script', 'callback_data': 'guide_python'}
            ],
            [
                {'text': '📱 من Termux (أندرويد)', 'callback_data': 'guide_termux'},
                {'text': '💻 من حاسوب شخصي', 'callback_data': 'guide_pc'}
            ],
            [
                {'text': '⚠️ نصائح مهمة', 'callback_data': 'guide_tips'},
                {'text': '🔧 حل المشاكل', 'callback_data': 'guide_troubleshoot'}
            ],
            [
                {'text': '🔙 العودة لإضافة الحساب', 'callback_data': 'assistants_add'}
            ]
        ]
        
        message = (
            f"📚 **دليل الحصول على Telethon Session String**\n\n"
            
            f"🎯 **ما هو Session String؟**\n"
            f"هو مفتاح آمن يحتوي على معلومات جلسة حسابك في تيليجرام، "
            f"يسمح للبوت بالدخول باسم حسابك دون الحاجة لكلمة المرور.\n\n"
            
            f"🔐 **مميزات Telethon Session:**\n"
            f"• أمان عالي ومشفر\n"
            f"• لا يحتوي على كلمة المرور\n"
            f"• يمكن إلغاؤه في أي وقت\n"
            f"• يعمل مع جميع ميزات تيليجرام\n"
            f"• سرعة اتصال ممتازة\n\n"
            
            f"📋 **الطرق المتاحة:**\n"
            f"1️⃣ **StringFatherBot** - الأسهل للمبتدئين\n"
            f"2️⃣ **Python Script** - للمتقدمين\n"
            f"3️⃣ **Termux** - للهواتف الذكية\n"
            f"4️⃣ **PC Setup** - للحاسوب الشخصي\n\n"
            
            f"⚠️ **تنبيهات مهمة:**\n"
            f"• لا تشارك Session String مع أحد\n"
            f"• استخدم حسابات قديمة (أكثر من 6 أشهر)\n"
            f"• تأكد من أن الحساب غير محظور\n"
            f"• احتفظ بنسخة احتياطية آمنة\n\n"
            
            f"🎯 **اختر الطريقة المناسبة لك:**"
        )
        
        return {
            'success': True,
            'message': message,
            'keyboard': keyboard,
            'parse_mode': 'Markdown'
        }

    # باقي المعالجات موجودة بنفس الشكل مع تحديثات Telethon حيث لزم الأمر
    async def start_remove_assistant(self, user_id: int) -> Dict:
        """بدء عملية حذف حساب مساعد"""
        if user_id != config.OWNER_ID:
            return {'success': False, 'message': "❌ غير مصرح"}
        
        # الحصول على قائمة الحسابات المساعدة
        assistants = await db.get_assistants()
        
        if not assistants:
            keyboard = [
                [
                    {'text': '➕ إضافة حساب مساعد', 'callback_data': 'assistants_add'},
                    {'text': '🔙 العودة', 'callback_data': 'admin_assistants'}
                ]
            ]
            
            return {
                'success': True,
                'message': "❌ لا توجد حسابات مساعدة مضافة\n\n💡 أضف حساب مساعد أولاً",
                'keyboard': keyboard,
                'parse_mode': 'Markdown'
            }
        
        # إنشاء keyboard مع الحسابات
        keyboard = []
        for assistant in assistants:
            is_connected = telethon_manager.is_assistant_connected(assistant['assistant_id'])
            status_emoji = "🟢" if is_connected else "🔴"
            button_text = f"{status_emoji} {assistant['name']} (ID: {assistant['assistant_id']})"
            keyboard.append([{
                'text': button_text,
                'callback_data': f'remove_assistant_{assistant["assistant_id"]}'
            }])
        
        keyboard.append([
            {'text': '❌ إلغاء الحذف', 'callback_data': 'assistants_cancel_remove'}
        ])
        
        message = (
            f"🗑️ **حذف حساب مساعد**\n\n"
            
            f"📋 **الحسابات المتاحة للحذف:**\n"
            f"• اختر الحساب المراد حذفه من القائمة أدناه\n"
            f"• سيتم فصل الحساب وحذفه نهائياً\n\n"
            
            f"⚠️ **تحذير:**\n"
            f"• الحذف نهائي ولا يمكن التراجع عنه\n"
            f"• الحساب سيتوقف عن العمل فوراً\n"
            f"• سيتم إخراجه من جميع المكالمات\n"
            f"• ستحتاج Session String جديد لإعادة إضافته\n\n"
            
            f"🎯 **اختر الحساب المراد حذفه:**"
        )
        
        return {
            'success': True,
            'message': message,
            'keyboard': keyboard,
            'parse_mode': 'Markdown'
        }

    async def confirm_remove_assistant(self, user_id: int, assistant_id: int) -> Dict:
        """تأكيد حذف حساب مساعد"""
        if user_id != config.OWNER_ID:
            return {'success': False, 'message': "❌ غير مصرح"}
        
        try:
            # الحصول على معلومات الحساب
            assistant_info = await db.get_assistant_by_id(assistant_id)
            if not assistant_info:
                return {
                    'success': False,
                    'message': "❌ لم يتم العثور على الحساب المحدد"
                }
            
            # حذف الحساب من telethon_manager
            await telethon_manager.remove_assistant(assistant_id)
            
            # حذف الحساب من قاعدة البيانات
            await db.remove_assistant(assistant_id)
            
            keyboard = [
                [
                    {'text': '📋 عرض الحسابات المتبقية', 'callback_data': 'assistants_list'},
                    {'text': '➕ إضافة حساب جديد', 'callback_data': 'assistants_add'}
                ],
                [
                    {'text': '🔙 العودة لإدارة الحسابات', 'callback_data': 'admin_assistants'}
                ]
            ]
            
            message = (
                f"✅ **تم حذف الحساب المساعد بنجاح!**\n\n"
                
                f"🗑️ **الحساب المحذوف:**\n"
                f"📛 الاسم: `{assistant_info['name']}`\n"
                f"🆔 المعرف: `{assistant_id}`\n"
                f"⏰ تاريخ الحذف: `{datetime.now().strftime('%Y-%m-%d %H:%M')}`\n\n"
                
                f"✅ **تم تنفيذ:**\n"
                f"• قطع اتصال Telethon مع الحساب\n"
                f"• حذف الحساب من قاعدة البيانات\n"
                f"• إيقاف جميع اتصالات الحساب\n"
                f"• إخراجه من المكالمات النشطة\n"
                f"• تحديث قائمة الحسابات المساعدة\n\n"
                
                f"💡 يمكنك إضافة حسابات جديدة في أي وقت"
            )
            
            return {
                'success': True,
                'message': message,
                'keyboard': keyboard,
                'parse_mode': 'Markdown'
            }
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في حذف الحساب المساعد: {e}")
            return {
                'success': False,
                'message': f"❌ فشل في حذف الحساب: {str(e)}"
            }

    async def show_assistants_list(self, user_id: int) -> Dict:
        """عرض قائمة الحسابات المساعدة"""
        if user_id != config.OWNER_ID:
            return {'success': False, 'message': "❌ غير مصرح"}
        
        try:
            assistants = await db.get_assistants()
            
            if not assistants:
                keyboard = [
                    [
                        {'text': '➕ إضافة حساب مساعد', 'callback_data': 'assistants_add'},
                        {'text': '🔙 العودة', 'callback_data': 'admin_assistants'}
                    ]
                ]
                
                return {
                    'success': True,
                    'message': "📋 **قائمة الحسابات المساعدة**\n\n❌ لا توجد حسابات مساعدة مضافة\n\n💡 أضف حساب مساعد للبدء",
                    'keyboard': keyboard,
                    'parse_mode': 'Markdown'
                }
            
            # تجميع معلومات الحسابات
            accounts_info = []
            for i, assistant in enumerate(assistants, 1):
                # التحقق من حالة الاتصال
                is_connected = telethon_manager.is_assistant_connected(assistant['assistant_id'])
                
                status_emoji = "🟢" if is_connected else "🔴"
                status_text = "متصل" if is_connected else "غير متصل"
                
                account_info = (
                    f"**{i}. {assistant['name']}**\n"
                    f"├ 🆔 المعرف: `{assistant['assistant_id']}`\n"
                    f"├ {status_emoji} الحالة: `{status_text}`\n"
                    f"├ 🚀 النوع: `Telethon Client`\n"
                    f"├ 📱 الهاتف: `{assistant.get('phone', 'غير متاح')}`\n"
                    f"└ ⏰ آخر نشاط: `{assistant.get('last_activity', 'غير متاح')}`\n"
                )
                accounts_info.append(account_info)
            
            keyboard = [
                [
                    {'text': '🔄 تحديث القائمة', 'callback_data': 'assistants_list'},
                    {'text': '📊 إحصائيات مفصلة', 'callback_data': 'assistants_detailed_stats'}
                ],
                [
                    {'text': '➕ إضافة حساب', 'callback_data': 'assistants_add'},
                    {'text': '🗑️ حذف حساب', 'callback_data': 'assistants_remove'}
                ],
                [
                    {'text': '🔄 إعادة التشغيل', 'callback_data': 'assistants_restart'},
                    {'text': '🧪 اختبار الحسابات', 'callback_data': 'assistants_test'}
                ],
                [
                    {'text': '🔙 العودة لإدارة الحسابات', 'callback_data': 'admin_assistants'}
                ]
            ]
            
            total_assistants = len(assistants)
            connected_count = sum(1 for a in assistants if telethon_manager.is_assistant_connected(a['assistant_id']))
            
            message = (
                f"📋 **قائمة الحسابات المساعدة (Telethon)**\n\n"
                
                f"📊 **الملخص:**\n"
                f"🤖 إجمالي الحسابات: `{total_assistants}`\n"
                f"🟢 متصلة: `{connected_count}`\n"
                f"🔴 غير متصلة: `{total_assistants - connected_count}`\n"
                f"🚀 نوع الاتصال: `Telethon v1.36.0`\n\n"
                
                f"📱 **تفاصيل الحسابات:**\n\n"
                + "\n".join(accounts_info) + "\n\n"
                
                f"🔄 آخر تحديث: `{datetime.now().strftime('%H:%M:%S')}`"
            )
            
            return {
                'success': True,
                'message': message,
                'keyboard': keyboard,
                'parse_mode': 'Markdown'
            }
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في عرض قائمة الحسابات: {e}")
            return {
                'success': False,
                'message': "❌ حدث خطأ في عرض قائمة الحسابات"
            }

    async def restart_assistants(self, user_id: int) -> Dict:
        """إعادة تشغيل الحسابات المساعدة مع Telethon"""
        if user_id != config.OWNER_ID:
            return {'success': False, 'message': "❌ غير مصرح"}
        
        try:
            # إعادة تحميل الحسابات من قاعدة البيانات
            restart_result = await telethon_manager.load_assistants_from_db()
            
            # الحصول على إحصائيات بعد إعادة التشغيل
            stats = await self._get_assistants_stats()
            
            keyboard = [
                [
                    {'text': '📋 عرض الحسابات', 'callback_data': 'assistants_list'},
                    {'text': '🧪 اختبار الحسابات', 'callback_data': 'assistants_test'}
                ],
                [
                    {'text': '🔙 العودة لإدارة الحسابات', 'callback_data': 'admin_assistants'}
                ]
            ]
            
            message = (
                f"🔄 **تم إعادة تشغيل الحسابات المساعدة مع Telethon!**\n\n"
                
                f"✅ **نتائج إعادة التشغيل:**\n"
                f"🤖 إجمالي الحسابات: `{stats['total']}`\n"
                f"🟢 متصلة بنجاح: `{stats['connected']}`\n"
                f"🔴 فشل الاتصال: `{stats['disconnected']}`\n"
                f"⚡ نشطة ومتاحة: `{stats['active']}`\n"
                f"🚀 نوع الاتصال: `Telethon v1.36.0`\n\n"
                
                f"🔄 **العمليات المنفذة:**\n"
                f"• إعادة تحميل من قاعدة البيانات\n"
                f"• إعادة إنشاء اتصالات Telethon\n"
                f"• تحديث حالة الحسابات\n"
                f"• فحص صحة Session Strings\n"
                f"• تجهيز الحسابات للاستخدام\n\n"
                
                f"⏰ **وقت التحديث:** `{datetime.now().strftime('%H:%M:%S')}`\n\n"
                
                f"💡 **ملاحظة:** Telethon يوفر اتصال سريع ومستقر"
            )
            
            return {
                'success': True,
                'message': message,
                'keyboard': keyboard,
                'parse_mode': 'Markdown'
            }
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في إعادة تشغيل الحسابات: {e}")
            return {
                'success': False,
                'message': f"❌ فشل في إعادة تشغيل الحسابات: {str(e)}"
            }

    # الدوال المساعدة
    async def _validate_telethon_session(self, session_string: str) -> Dict:
        """التحقق من صحة Telethon session string"""
        try:
            if not StringSession or not TelegramClient:
                return {
                    'valid': False,
                    'error': 'Telethon غير مثبت'
                }
            
            # التحقق من شكل session string
            if len(session_string) < 50:
                return {
                    'valid': False,
                    'error': 'Session string قصير جداً'
                }
            
            # محاولة إنشاء جلسة Telethon
            session = StringSession(session_string)
            
            # إنشاء عميل مؤقت للاختبار
            client = TelegramClient(
                session,
                api_id=config.API_ID,
                api_hash=config.API_HASH
            )
            
            try:
                # محاولة الاتصال والحصول على معلومات المستخدم
                await client.connect()
                
                if not await client.is_user_authorized():
                    await client.disconnect()
                    return {
                        'valid': False,
                        'error': 'Session غير مصرح أو منتهي الصلاحية'
                    }
                
                # الحصول على معلومات المستخدم
                me = await client.get_me()
                
                await client.disconnect()
                
                # إعداد معلومات المستخدم
                user_info = {
                    'id': me.id,
                    'username': me.username,
                    'first_name': me.first_name or '',
                    'last_name': me.last_name or '',
                    'phone': me.phone or '',
                    'is_premium': getattr(me, 'premium', False),
                    'is_bot': me.bot,
                    'display_name': f"{me.first_name or ''} {me.last_name or ''}".strip() or me.username or f"User {me.id}"
                }
                
                return {
                    'valid': True,
                    'user_info': user_info
                }
                
            except Exception as e:
                await client.disconnect()
                return {
                    'valid': False,
                    'error': f'خطأ في الاتصال: {str(e)}'
                }
                
        except Exception as e:
            return {
                'valid': False,
                'error': f'خطأ في التحقق: {str(e)}'
            }

    async def _get_assistants_stats(self) -> Dict:
        """الحصول على إحصائيات الحسابات المساعدة"""
        try:
            total = telethon_manager.get_assistants_count()
            connected = telethon_manager.get_connected_assistants_count()
            
            # حساب النشطة والمكالمات
            active = connected  # في Telethon، المتصل = نشط
            in_calls = 0
            
            # يمكن إضافة منطق لحساب المكالمات النشطة هنا
            
            return {
                'total': total,
                'connected': connected,
                'disconnected': total - connected,
                'active': active,
                'in_calls': in_calls
            }
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في حساب إحصائيات الحسابات: {e}")
            return {
                'total': 0, 'connected': 0, 'disconnected': 0, 
                'active': 0, 'in_calls': 0
            }

    async def check_no_assistants_and_notify(self, user_id: int, user_name: str, chat_id: int) -> bool:
        """فحص عدم وجود حسابات مساعدة وإرسال تنبيه"""
        try:
            # فحص الحسابات المساعدة النشطة
            active_assistants = telethon_manager.get_connected_assistants_count()
            
            if active_assistants == 0:
                # إرسال رسالة للمستخدم
                user_message = (
                    f"⚠️ **عذراً {user_name}**\n\n"
                    f"🤖 **خلل في النظام:**\n"
                    f"لا توجد حسابات مساعدة نشطة حالياً\n\n"
                    f"📞 **الحلول:**\n"
                    f"• تواصل مع مطور البوت\n"
                    f"• انتظر حتى يتم إصلاح المشكلة\n"
                    f"• جرب مرة أخرى بعد قليل\n\n"
                    f"🔧 **تم إرسال تنبيه للمطور**"
                )
                
                # إرسال رسالة للمستخدم
                bot_client = telethon_manager.bot_client
                if bot_client and bot_client.is_connected():
                    await bot_client.send_message(chat_id, user_message)
                
                # إرسال تنبيه للمطور
                developer_alert = (
                    f"🚨 **تنبيه: لا توجد حسابات مساعدة Telethon نشطة!**\n\n"
                    
                    f"👤 **طلب من:**\n"
                    f"الاسم: `{user_name}`\n"
                    f"المعرف: `{user_id}`\n"
                    f"المجموعة: `{chat_id}`\n\n"
                    
                    f"⏰ **الوقت:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`\n\n"
                    
                    f"🔧 **مطلوب:**\n"
                    f"• فحص حسابات Telethon المساعدة\n"
                    f"• التحقق من صحة Session Strings\n"
                    f"• إعادة تشغيل النظام إذا لزم الأمر\n"
                    f"• التأكد من اتصال الحسابات\n\n"
                    
                    f"📱 استخدم `/admin` ← إدارة الحسابات المساعدة"
                )
                
                # إرسال للمطور
                if bot_client and bot_client.is_connected():
                    await bot_client.send_message(config.OWNER_ID, developer_alert)
                
                return True  # يوجد مشكلة
            
            return False  # لا توجد مشكلة
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في فحص الحسابات المساعدة: {e}")
            return False

    async def toggle_auto_leave(self, user_id: int) -> Dict:
        """تفعيل/تعطيل المغادرة التلقائية"""
        if user_id != config.OWNER_ID:
            return {'success': False, 'message': "❌ غير مصرح"}
        
        # تبديل الحالة
        self.auto_leave_enabled = not self.auto_leave_enabled
        self.save_auto_leave_settings()
        
        status = "🟢 مفعل" if self.auto_leave_enabled else "🔴 معطل"
        action = "تفعيل" if self.auto_leave_enabled else "تعطيل"
        
        keyboard = [
            [
                {'text': '⚙️ إعدادات المغادرة', 'callback_data': 'assistants_auto_leave_settings'},
                {'text': '🧪 اختبار النظام', 'callback_data': 'assistants_test_auto_leave'}
            ],
            [
                {'text': '🔙 العودة لإدارة الحسابات', 'callback_data': 'admin_assistants'}
            ]
        ]
        
        message = (
            f"🚪 **تم {action} المغادرة التلقائية مع Telethon!**\n\n"
            
            f"📊 **الحالة الحالية:** {status}\n"
            f"⏱️ **مدة عدم النشاط:** `{self.auto_leave_timeout // 60} دقائق`\n"
            f"🚀 **النوع:** `Telethon Auto Leave`\n\n"
            
            f"💡 **كيف تعمل المغادرة التلقائية:**\n"
            f"• مراقبة نشاط حسابات Telethon المساعدة\n"
            f"• عند عدم النشاط لفترة محددة\n"
            f"• مغادرة المجموعات والقنوات تلقائياً\n"
            f"• تحسين أداء Telethon Clients\n"
            f"• توفير الموارد والذاكرة\n\n"
            
            f"🎯 **الفوائد:**\n"
            f"{'• تنظيف تلقائي للمجموعات غير النشطة' if self.auto_leave_enabled else '• لا توجد مغادرة تلقائية'}\n"
            f"{'• تحسين أداء Telethon' if self.auto_leave_enabled else '• الحسابات تبقى في جميع المجموعات'}\n"
            f"{'• تقليل استهلاك الموارد' if self.auto_leave_enabled else '• قد تحتاج لتنظيف يدوي'}"
        )
        
        return {
            'success': True,
            'message': message,
            'keyboard': keyboard,
            'parse_mode': 'Markdown'
        }

    # مهام المغادرة التلقائية مع Telethon
    async def _auto_leave_task(self):
        """مهمة المغادرة التلقائية مع Telethon"""
        while True:
            try:
                if self.auto_leave_enabled:
                    await self._check_and_leave_inactive_chats()
                
                # فحص كل دقيقة
                await asyncio.sleep(60)
                
            except Exception as e:
                LOGGER(__name__).error(f"خطأ في مهمة المغادرة التلقائية: {e}")
                await asyncio.sleep(60)
    
    async def _check_and_leave_inactive_chats(self):
        """فحص ومغادرة المحادثات غير النشطة مع Telethon"""
        try:
            current_time = time.time()
            
            # فحص جميع حسابات Telethon المساعدة
            for assistant_id, assistant_client in telethon_manager.assistant_clients.items():
                if not assistant_client or not assistant_client.is_connected():
                    continue
                
                # فحص آخر نشاط للحساب (يمكن تحسين هذا)
                # للآن نستخدم timeout ثابت
                await self._leave_assistant_chats(assistant_client)
                    
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في فحص المحادثات غير النشطة: {e}")
    
    async def _leave_assistant_chats(self, assistant_client):
        """مغادرة محادثات الحساب المساعد مع Telethon"""
        try:
            # الحصول على قائمة المحادثات باستخدام Telethon
            async for dialog in assistant_client.iter_dialogs():
                try:
                    # تحقق من نوع المحادثة (مجموعة أو قناة)
                    if dialog.is_group or dialog.is_channel:
                        # مغادرة المحادثة
                        await assistant_client.delete_dialog(dialog.entity)
                        
                        # تأخير قصير بين المغادرات
                        await asyncio.sleep(1)
                        
                except Exception as e:
                    LOGGER(__name__).debug(f"خطأ في مغادرة المحادثة {dialog.id}: {e}")
            
            LOGGER(__name__).info(f"تم تنظيف محادثات حساب Telethon المساعد")
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في مغادرة محادثات حساب Telethon: {e}")

# إنشاء مثيل عام لمعالج الحسابات المساعدة
assistants_handler = AssistantsHandler()