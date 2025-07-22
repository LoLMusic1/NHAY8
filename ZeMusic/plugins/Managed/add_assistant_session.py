# -*- coding: utf-8 -*-
"""
معالج إضافة الحساب المساعد عبر Session String
"""

import asyncio
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, ApiIdInvalidError

from ZeMusic import app
from ZeMusic.pyrogram_compatibility import filters, Message
from ZeMusic.core.telethon_client import telethon_manager
from ZeMusic.logging import LOGGER
from ZeMusic.utils.decorators.admins import AdminRightsCheck
import config

# متغير مؤقت لحفظ Session Strings في انتظار المعالجة
pending_sessions = {}

@app.on_message(filters.command(["اضافة_مساعد", "add_assistant"]) & filters.private & filters.user(config.OWNER_ID))
async def start_add_assistant(client, message: Message):
    """بدء عملية إضافة حساب مساعد"""
    
    await message.reply(
        "🤖 **إضافة حساب مساعد جديد**\n\n"
        "📋 **المطلوب:**\n"
        "• كود الجلسة (Session String) للحساب المساعد\n\n"
        "📝 **الطريقة:**\n"
        "• احصل على Session String من [@StringSessionBot](https://t.me/StringSessionBot)\n"
        "• أو من [@StringGenBot](https://t.me/StringGenBot)\n\n"
        "✏️ **أرسل كود الجلسة الآن:**"
    )
    
    # تسجيل المستخدم في انتظار session string
    pending_sessions[message.from_user.id] = {
        'status': 'waiting_session',
        'timestamp': asyncio.get_event_loop().time()
    }

@app.on_message(filters.private & filters.user(config.OWNER_ID) & filters.text)
async def handle_session_input(client, message: Message):
    """معالجة session string المُرسل"""
    
    user_id = message.from_user.id
    text = message.text.strip()
    
    # التحقق من أن المستخدم في انتظار session
    if user_id not in pending_sessions:
        return
    
    # التحقق من أن النص يبدو كـ session string
    if not (len(text) > 100 and text.startswith('1')):
        await message.reply(
            "❌ **كود الجلسة غير صحيح**\n\n"
            "تأكد من أن الكود:\n"
            "• يبدأ بالرقم 1\n"
            "• طوله أكثر من 100 حرف\n"
            "• منسوخ بالكامل بدون أخطاء\n\n"
            "💡 **أرسل كود الجلسة الصحيح:**"
        )
        return
    
    # إرسال رسالة انتظار
    status_msg = await message.reply(
        "⏳ **جاري التحقق من كود الجلسة...**\n"
        "🔍 يتم فحص صحة الكود والاتصال"
    )
    
    try:
        # إضافة الحساب المساعد
        result = await telethon_manager.add_assistant_by_session(text)
        
        if result['success']:
            # نجحت العملية
            user_info = result.get('user_info', {})
            assistant_id = result.get('assistant_id')
            
            success_text = (
                "✅ **تم إضافة الحساب المساعد بنجاح!**\n\n"
                f"🆔 **معرف المساعد:** `{assistant_id}`\n"
                f"👤 **الاسم:** {user_info.get('first_name', 'غير محدد')}\n"
                f"🔗 **اليوزر:** @{user_info.get('username', 'غير محدد')}\n"
                f"📱 **الهاتف:** {user_info.get('phone', 'مخفي')}\n"
                f"🆔 **معرف تيليجرام:** `{user_info.get('id', 'غير محدد')}`\n\n"
                "🎵 **الحساب جاهز للاستخدام في تشغيل الموسيقى**"
            )
            
            await status_msg.edit(success_text)
            
        else:
            # فشلت العملية
            error_msg = result.get('error', 'خطأ غير معروف')
            
            await status_msg.edit(
                f"❌ **فشل في إضافة الحساب المساعد**\n\n"
                f"🚫 **السبب:** {error_msg}\n\n"
                "💡 **الحلول:**\n"
                "• تأكد من صحة كود الجلسة\n"
                "• تأكد من أن الحساب غير محظور\n"
                "• جرب كود جلسة آخر"
            )
    
    except Exception as e:
        LOGGER(__name__).error(f"خطأ في إضافة المساعد: {e}")
        await status_msg.edit(
            f"❌ **حدث خطأ تقني**\n\n"
            f"🔧 **التفاصيل:** `{str(e)}`\n\n"
            "🔄 **حاول مرة أخرى أو تواصل مع المطور**"
        )
    
    finally:
        # إزالة من قائمة الانتظار
        if user_id in pending_sessions:
            del pending_sessions[user_id]

@app.on_message(filters.command(["المساعدين", "assistants"]) & filters.private & filters.user(config.OWNER_ID))
async def list_assistants(client, message: Message):
    """عرض قائمة الحسابات المساعدة"""
    
    try:
        # الحصول على الحسابات من قاعدة البيانات
        assistants = await telethon_manager.load_assistants_from_db()
        total_assistants = telethon_manager.get_assistants_count()
        connected_assistants = telethon_manager.get_connected_assistants_count()
        
        if total_assistants == 0:
            await message.reply(
                "📝 **لا توجد حسابات مساعدة**\n\n"
                "➕ لإضافة حساب مساعد:\n"
                "`/اضافة_مساعد`"
            )
            return
        
        # إنشاء النص
        text = (
            f"🤖 **الحسابات المساعدة ({total_assistants})**\n"
            f"✅ **متصل:** {connected_assistants}\n"
            f"❌ **غير متصل:** {total_assistants - connected_assistants}\n\n"
        )
        
        # الحصول على تفاصيل كل حساب
        from ZeMusic.core.database import db
        assistants_data = await db.get_assistants()
        
        for i, assistant in enumerate(assistants_data, 1):
            assistant_id = assistant.get('id')
            is_connected = telethon_manager.is_assistant_connected(assistant_id)
            status_emoji = "🟢" if is_connected else "🔴"
            
            text += (
                f"{status_emoji} **المساعد {i}**\n"
                f"├ 🆔 **المعرف:** `{assistant_id}`\n"
                f"├ 👤 **الاسم:** {assistant.get('name', 'غير محدد')}\n"
                f"├ 🔗 **اليوزر:** @{assistant.get('username', 'غير محدد')}\n"
                f"└ 📅 **مُضاف:** {assistant.get('created_at', 'غير محدد')[:10]}\n\n"
            )
        
        text += (
            "⚙️ **الأوامر المتاحة:**\n"
            "• `/اضافة_مساعد` - إضافة حساب جديد\n"
            "• `/حذف_مساعد [معرف]` - حذف حساب\n"
            "• `/اعادة_تحميل_المساعدين` - إعادة تحميل الحسابات"
        )
        
        await message.reply(text)
        
    except Exception as e:
        LOGGER(__name__).error(f"خطأ في عرض المساعدين: {e}")
        await message.reply(f"❌ خطأ في عرض القائمة: {str(e)}")

@app.on_message(filters.command(["حذف_مساعد", "remove_assistant"]) & filters.private & filters.user(config.OWNER_ID))
async def remove_assistant_command(client, message: Message):
    """حذف حساب مساعد"""
    
    try:
        # التحقق من وجود معرف
        if len(message.command) < 2:
            await message.reply(
                "❌ **يجب تحديد معرف الحساب المساعد**\n\n"
                "📝 **الاستخدام:**\n"
                "`/حذف_مساعد [معرف_المساعد]`\n\n"
                "💡 **للحصول على قائمة المساعدين:**\n"
                "`/المساعدين`"
            )
            return
        
        assistant_id = int(message.command[1])
        
        # التحقق من وجود المساعد
        if not telethon_manager.is_assistant_connected(assistant_id):
            await message.reply(f"❌ **الحساب المساعد {assistant_id} غير موجود أو غير متصل**")
            return
        
        # حذف المساعد
        success = await telethon_manager.remove_assistant(assistant_id)
        
        if success:
            # حذف من قاعدة البيانات
            from ZeMusic.core.database import db
            await db.remove_assistant(assistant_id)
            
            await message.reply(
                f"✅ **تم حذف الحساب المساعد {assistant_id} بنجاح**\n\n"
                "🔄 **تم قطع الاتصال وحذف البيانات**"
            )
        else:
            await message.reply(f"❌ **فشل في حذف الحساب المساعد {assistant_id}**")
    
    except ValueError:
        await message.reply("❌ **معرف المساعد يجب أن يكون رقماً**")
    except Exception as e:
        LOGGER(__name__).error(f"خطأ في حذف المساعد: {e}")
        await message.reply(f"❌ **خطأ في الحذف:** {str(e)}")

@app.on_message(filters.command(["اعادة_تحميل_المساعدين", "reload_assistants"]) & filters.private & filters.user(config.OWNER_ID))
async def reload_assistants_command(client, message: Message):
    """إعادة تحميل الحسابات المساعدة"""
    
    status_msg = await message.reply("🔄 **جاري إعادة تحميل الحسابات المساعدة...**")
    
    try:
        # إعادة تحميل المساعدين
        loaded_count = await telethon_manager.load_assistants_from_db()
        
        await status_msg.edit(
            f"✅ **تم إعادة تحميل الحسابات بنجاح**\n\n"
            f"📊 **تم تحميل:** {loaded_count} حساب\n"
            f"🟢 **متصل:** {telethon_manager.get_connected_assistants_count()}\n"
            f"📱 **المجموع:** {telethon_manager.get_assistants_count()}"
        )
        
    except Exception as e:
        LOGGER(__name__).error(f"خطأ في إعادة تحميل المساعدين: {e}")
        await status_msg.edit(f"❌ **خطأ في إعادة التحميل:** {str(e)}")

# تنظيف جلسات الانتظار المنتهية الصلاحية (كل 5 دقائق)
async def cleanup_pending_sessions():
    """تنظيف الجلسات المعلقة"""
    while True:
        try:
            current_time = asyncio.get_event_loop().time()
            expired_users = []
            
            for user_id, data in pending_sessions.items():
                if current_time - data['timestamp'] > 300:  # 5 دقائق
                    expired_users.append(user_id)
            
            for user_id in expired_users:
                del pending_sessions[user_id]
                
            await asyncio.sleep(300)  # فحص كل 5 دقائق
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في تنظيف الجلسات: {e}")
            await asyncio.sleep(60)

# بدء مهمة التنظيف
asyncio.create_task(cleanup_pending_sessions())