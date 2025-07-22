# -*- coding: utf-8 -*-
"""
معالج البحث المخصص - يتعامل مع أوامر البحث مباشرة
"""

import asyncio
from telethon import events
from ZeMusic.logging import LOGGER
from ZeMusic.utils.database import is_search_enabled, is_search_enabled1
from ZeMusic.plugins.play.enhanced_handler import enhanced_smart_download_handler
import config

async def search_command_handler(event):
    """معالج أوامر البحث المباشر"""
    
    # التحقق من أن هذه رسالة نصية
    if not event.message or not event.message.text:
        return
    
    text = event.message.text.strip()
    LOGGER(__name__).info(f"🔍 تم استلام رسالة: {text[:50]}...")
    
    # قائمة أوامر البحث
    search_commands = [
        "بحث ",
        "/song ",
        "song ",
        "يوت ",
        "/search ",
        "search ",
        f"{config.BOT_NAME} ابحث ",
        "تحميل ",
        "download ",
        "ابحث ",
        "غنيلي ",
    ]
    
    # فحص إذا كانت الرسالة تحتوي على أمر بحث
    is_search = False
    for cmd in search_commands:
        if text.lower().startswith(cmd.lower()):
            is_search = True
            break
    
    # أو إذا كانت الرسالة فقط "بحث"
    if text.lower() in ["بحث", "/song", "song", "search", "/search", "تحميل", "download"]:
        is_search = True
    
    if not is_search:
        return
    
    LOGGER(__name__).info(f"✅ تم التعرف على أمر بحث: {text[:50]}...")
    
    # التحقق من تفعيل الخدمة
    try:
        chat_id = event.chat_id
        if hasattr(event, 'is_private') and event.is_private:
            if not await is_search_enabled1():
                await event.reply("⚠️ عذراً، خدمة البحث معطلة في المحادثات الخاصة")
                return
        else:
            if not await is_search_enabled(chat_id):
                await event.reply("⚠️ عذراً، خدمة البحث معطلة في المجموعات")
                return
        LOGGER(__name__).info(f"✅ خدمة البحث مفعلة للمحادثة: {chat_id}")
    except Exception as e:
        LOGGER(__name__).error(f"خطأ في فحص تفعيل الخدمة: {e}")
        return
    
    # إذا كانت الرسالة فقط الأمر بدون نص
    if text.lower().strip() in ["بحث", "/song", "song", "search", "/search", "تحميل", "download"]:
        await event.reply(
            "🔍 **استخدام أمر البحث:**\n\n"
            "• `بحث اسم الأغنية`\n"
            "• `تحميل اسم الأغنية`\n"
            "• `/song اسم الأغنية`\n\n"
            "**مثال:**\n"
            "`بحث فيروز يا أم العيون الناعسة`"
        )
        return
    
    # استخراج نص البحث
    search_text = ""
    for cmd in search_commands:
        if text.lower().startswith(cmd.lower()):
            search_text = text[len(cmd):].strip()
            break
    
    if not search_text:
        await event.reply("❌ لم تكتب اسم الأغنية للبحث عنها")
        return
    
    # إرسال رسالة انتظار
    status_msg = await event.reply(f"🔍 جاري البحث عن: **{search_text}**...")
    
    try:
        LOGGER(__name__).info(f"🎵 بدء البحث عن: {search_text}")
        
        # تمرير الحدث للمعالج المحسن
        # إنشاء نسخة معدلة من النص للمعالج
        original_text = event.message.text
        event.message.text = f"بحث {search_text}"
        
        # استدعاء المعالج المحسن
        LOGGER(__name__).info("📡 استدعاء enhanced_smart_download_handler...")
        await enhanced_smart_download_handler(event)
        LOGGER(__name__).info("✅ تم الانتهاء من المعالج المحسن")
        
        # استعادة النص الأصلي
        event.message.text = original_text
        
        # حذف رسالة الانتظار
        try:
            await status_msg.delete()
        except:
            pass
            
    except Exception as e:
        LOGGER(__name__).error(f"خطأ في معالج البحث: {e}")
        try:
            await status_msg.edit(f"❌ حدث خطأ أثناء البحث: {str(e)}")
        except:
            await event.reply(f"❌ حدث خطأ أثناء البحث: {str(e)}")

# تم نقل التسجيل إلى handlers_registry.py