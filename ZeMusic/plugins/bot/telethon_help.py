# -*- coding: utf-8 -*-
"""
معالج أمر /help مع Telethon
"""

from telethon import events

from ZeMusic.utils.database import get_lang, is_banned_user
from ZeMusic.utils.inline import help_pannel
from config import BANNED_USERS
from strings import get_string


async def handle_help_command(event):
    """معالج أمر /help مع Telethon"""
    try:
        # التحقق من حظر المستخدم
        user_id = event.sender_id
        if user_id in BANNED_USERS:
            return
        
        if await is_banned_user(user_id):
            return
        
        # التحقق من نوع المحادثة
        if event.is_private:
            await handle_private_help(event)
        else:
            await handle_group_help(event)
            
    except Exception as e:
        print(f"خطأ في معالج /help: {e}")


async def handle_private_help(event):
    """معالج /help في المحادثة الخاصة"""
    try:
        user_id = event.sender_id
        
        # الحصول على اللغة
        language = await get_lang(user_id)
        _ = get_string(language)
        
        # إرسال مساعدة مفصلة
        caption = _["help_1"]
        await event.reply(
            caption,
            buttons=help_pannel(_, True),
            link_preview=False
        )
        
    except Exception as e:
        print(f"خطأ في /help خاص: {e}")
        await event.reply("❌ **حدث خطأ في معالجة الأمر**")


async def handle_group_help(event):
    """معالج /help في المجموعات"""
    try:
        chat_id = event.chat_id
        
        # الحصول على اللغة
        language = await get_lang(chat_id)
        _ = get_string(language)
        
        # إرسال رابط المساعدة
        caption = _["help_2"]
        await event.reply(
            caption,
            buttons=help_pannel(_, False),
            link_preview=False
        )
        
    except Exception as e:
        print(f"خطأ في /help مجموعة: {e}")


# معالج callback للمساعدة
async def handle_help_callback(event):
    """معالج callback buttons للمساعدة"""
    try:
        user_id = event.sender_id
        
        # التحقق من حظر المستخدم
        if user_id in BANNED_USERS:
            return await event.answer("❌ أنت محظور من استخدام البوت", alert=True)
        
        if await is_banned_user(user_id):
            return await event.answer("❌ أنت محظور من استخدام البوت", alert=True)
        
        # الحصول على اللغة
        language = await get_lang(user_id)
        _ = get_string(language)
        
        # معالجة البيانات
        callback_data = event.data.decode('utf-8')
        
        if callback_data == "settings_back_helper":
            # العودة للمساعدة الرئيسية
            caption = _["help_1"]
            await event.edit(
                caption,
                buttons=help_pannel(_, True)
            )
        
        elif callback_data == "help_callback":
            # فتح المساعدة من المجموعة
            await event.answer(
                _["help_3"],
                alert=True
            )
        
        else:
            # معالجة callbacks أخرى للمساعدة
            await event.answer("🔄 **جاري المعالجة...**")
            
    except Exception as e:
        print(f"خطأ في help callback: {e}")
        await event.answer("❌ **حدث خطأ**", alert=True)