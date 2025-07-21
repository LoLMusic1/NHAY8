# -*- coding: utf-8 -*-
"""
معالج أمر /start مع Telethon
"""

import time
from telethon import events
from telethon.tl.types import User

import config
from ZeMusic.core.telethon_client import telethon_manager
from ZeMusic.misc import _boot_
from ZeMusic.utils.database import (
    add_served_chat,
    add_served_user,
    blacklisted_chats,
    get_lang,
    is_banned_user,
    is_on_off,
)
from ZeMusic.utils.formatters import get_readable_time
from ZeMusic.utils.inline import help_pannel, private_panel, start_panel
from config import BANNED_USERS
from strings import get_string


async def handle_start_command(event):
    """معالج أمر /start مع Telethon"""
    try:
        # التحقق من حظر المستخدم
        user_id = event.sender_id
        if user_id in BANNED_USERS:
            return
        
        if await is_banned_user(user_id):
            return
        
        # إضافة المستخدم للقاعدة
        await add_served_user(user_id)
        
        # التحقق من نوع المحادثة
        if event.is_private:
            await handle_private_start(event)
        else:
            await handle_group_start(event)
            
    except Exception as e:
        print(f"خطأ في معالج /start: {e}")


async def handle_private_start(event):
    """معالج /start في المحادثة الخاصة"""
    try:
        user_id = event.sender_id
        
        # الحصول على اللغة
        language = await get_lang(user_id)
        _ = get_string(language)
        
        # التحقق من معاملات الأمر
        command_parts = event.raw_text.split()
        
        # معالجة أوامر /start مع معاملات
        if len(command_parts) > 1:
            parameter = command_parts[1]
            
            if parameter == "help":
                # إرسال مساعدة مفصلة
                caption = _["help_1"]
                await event.reply(
                    caption,
                    buttons=help_pannel(_, True),
                    link_preview=False
                )
                return
            
            elif parameter.startswith("sudolist"):
                # قائمة المديرين
                from ZeMusic.plugins.sudo.sudoers import sudoers_list
                await sudoers_list(event, _)
                return
            
            elif parameter.startswith("info_"):
                # معلومات الأغنية
                video_id = parameter.replace("info_", "")
                # يمكن إضافة معالجة معلومات الفيديو هنا
                await event.reply("📁 **معلومات الأغنية**\n\nهذه الميزة قيد التطوير...")
                return
        
        # رسالة البداية العادية
        user = await event.get_sender()
        username = getattr(user, 'username', None)
        user_mention = f"@{username}" if username else user.first_name
        
        bot_info = await telethon_manager.bot_client.get_me()
        bot_mention = f"@{bot_info.username}" if bot_info.username else "البوت"
        
        caption = _["start_2"].format(user_mention, bot_mention)
        
        await event.reply(
            caption,
            buttons=private_panel(_),
            link_preview=False
        )
        
    except Exception as e:
        print(f"خطأ في /start خاص: {e}")
        await event.reply("❌ **حدث خطأ في معالجة الأمر**")


async def handle_group_start(event):
    """معالج /start في المجموعات"""
    try:
        chat_id = event.chat_id
        
        # إضافة المجموعة للقاعدة
        await add_served_chat(chat_id)
        
        # التحقق من القوائم السوداء
        a = await blacklisted_chats()
        if chat_id in a:
            return await telethon_manager.bot_client.leave_chat(chat_id)
        
        # الحصول على اللغة
        language = await get_lang(chat_id)
        _ = get_string(language)
        
        # حساب وقت التشغيل
        uptime = get_readable_time(int(time.time() - _boot_))
        
        bot_info = await telethon_manager.bot_client.get_me()
        bot_mention = f"@{bot_info.username}" if bot_info.username else "البوت"
        
        caption = _["start_1"].format(bot_mention, uptime)
        
        await event.reply(
            caption,
            buttons=start_panel(_),
            link_preview=False
        )
        
    except Exception as e:
        print(f"خطأ في /start مجموعة: {e}")


# معالج انضمام أعضاء جدد (يمكن تفعيله لاحقاً)
async def handle_new_chat_members(event):
    """معالج انضمام أعضاء جدد"""
    try:
        # التحقق من انضمام البوت نفسه
        bot_info = await telethon_manager.bot_client.get_me()
        
        for user in event.users:
            if user.id == bot_info.id:
                # البوت انضم للمجموعة
                chat_id = event.chat_id
                
                # التحقق من التفعيل العام
                if not await is_on_off(config.LOG):
                    return await telethon_manager.bot_client.leave_chat(chat_id)
                
                # التحقق من القائمة السوداء
                a = await blacklisted_chats()
                if chat_id in a:
                    return await telethon_manager.bot_client.leave_chat(chat_id)
                
                # رسالة ترحيب
                language = await get_lang(chat_id)
                _ = get_string(language)
                
                bot_mention = f"@{bot_info.username}" if bot_info.username else "البوت"
                
                caption = _["start_3"].format(
                    bot_mention,
                    f"https://t.me/{bot_info.username}?start=sudolist",
                    config.SUPPORT_CHAT
                )
                
                await event.reply(caption, link_preview=False)
                
                # إضافة للقاعدة
                await add_served_chat(chat_id)
                
    except Exception as e:
        print(f"خطأ في معالج الأعضاء الجدد: {e}")