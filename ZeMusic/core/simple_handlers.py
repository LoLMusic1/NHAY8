# -*- coding: utf-8 -*-
"""
معالجات بسيطة مع Telethon
"""

import asyncio
import re
from typing import Optional, Dict, Any
from telethon import events
from telethon.tl.types import User, Chat

import config
from ZeMusic.logging import LOGGER
from ZeMusic.core.telethon_client import telethon_manager
from ZeMusic.utils.database import add_served_user, add_served_chat, get_lang
from strings import get_string

class TelethonSimpleHandlers:
    """معالجات بسيطة للأوامر الأساسية مع Telethon"""
    
    def __init__(self):
        self.logger = LOGGER(__name__)
    
    async def handle_start(self, event):
        """معالج أمر /start مع Telethon"""
        try:
            user_id = event.sender_id
            chat_id = event.chat_id
            
            # إضافة المستخدم لقاعدة البيانات
            if user_id:
                await add_served_user(user_id)
            
            # إضافة المحادثة لقاعدة البيانات
            if chat_id:
                await add_served_chat(chat_id)
            
            # الحصول على اللغة
            language = await get_lang(chat_id if chat_id < 0 else user_id)
            _ = get_string(language)
            
            if event.is_private:
                # محادثة خاصة
                welcome_text = _["start_2"].format(
                    "المستخدم", 
                    "ZeMusic Bot"
                )
            else:
                # مجموعة أو قناة
                welcome_text = _["start_1"].format(
                    "ZeMusic Bot",
                    "0:00"  # placeholder for uptime
                )
            
            await event.reply(welcome_text)
            
        except Exception as e:
            self.logger.error(f"خطأ في معالج /start: {e}")
            await event.reply("❌ حدث خطأ في معالجة الأمر")
    
    async def handle_help(self, event):
        """معالج أمر /help مع Telethon"""
        try:
            user_id = event.sender_id
            chat_id = event.chat_id
            
            # الحصول على اللغة
            language = await get_lang(chat_id if chat_id < 0 else user_id)
            _ = get_string(language)
            
            help_text = _["help_1"] if hasattr(_, '__getitem__') else """
🎵 **مرحباً بك في ZeMusic Bot**

**الأوامر المتاحة:**
• `بحث [اسم الأغنية]` - البحث عن الموسيقى
• `song [song name]` - تحميل أغنية
• `/start` - بدء البوت
• `/help` - عرض المساعدة

**المطور:** @YourUsername
            """
            
            await event.reply(help_text)
            
        except Exception as e:
            self.logger.error(f"خطأ في معالج /help: {e}")
            await event.reply("❌ حدث خطأ في معالجة الأمر")
    
    async def handle_general_message(self, event):
        """معالج الرسائل العامة مع Telethon"""
        try:
            if not event.message or not event.message.text:
                return
            
            message_text = event.message.text.strip()
            user_id = event.sender_id
            chat_id = event.chat_id
            
            # تجاهل الأوامر
            if message_text.startswith('/'):
                return
            
            # تجاهل أوامر البحث (يتم معالجتها في download.py)
            search_commands = ['بحث', 'song', 'يوت']
            if any(cmd in message_text.lower() for cmd in search_commands):
                return
            
            # رد بسيط للمحادثات الخاصة
            if event.is_private:
                await event.reply(
                    "👋 مرحباً! استخدم `بحث [اسم الأغنية]` للبحث عن الموسيقى\n"
                    "أو `/help` لعرض جميع الأوامر"
                )
            
        except Exception as e:
            self.logger.error(f"خطأ في معالج الرسائل العامة: {e}")
    
    async def handle_callback_query(self, event):
        """معالج الاستعلامات المضمنة (callback queries) مع Telethon"""
        try:
            if not hasattr(event, 'data') or not event.data:
                return
            
            # في Telethon v1.36+، event.data هو نص مباشرة
        callback_data = event.data if isinstance(event.data, str) else event.data.decode('utf-8')
            user_id = event.sender_id
            
            # معالجة بيانات callback مختلفة
            if callback_data == "help":
                await self.handle_help(event)
            elif callback_data == "close":
                try:
                    await event.delete()
                except:
                    await event.answer("❌ لا يمكن حذف الرسالة")
            elif callback_data.startswith("play_"):
                await event.answer("🎵 ميزة التشغيل ستكون متاحة قريباً")
            else:
                await event.answer("🔄 جاري المعالجة...")
            
        except Exception as e:
            self.logger.error(f"خطأ في معالج callback: {e}")
            try:
                await event.answer("❌ حدث خطأ")
            except:
                pass
    
    async def handle_inline_query(self, event):
        """معالج الاستعلامات المضمنة مع Telethon"""
        try:
            query = event.text.strip()
            
            if not query:
                # نتائج افتراضية
                results = []
            else:
                # البحث حسب الاستعلام
                results = []
                # يمكن إضافة منطق البحث هنا لاحقاً
            
            await event.answer(results[:50])  # حد أقصى 50 نتيجة
            
        except Exception as e:
            self.logger.error(f"خطأ في معالج inline query: {e}")

# إنشاء مثيل عام
telethon_simple_handlers = TelethonSimpleHandlers()

# دوال للتوافق مع الكود القديم
async def handle_start(event):
    """دالة للتوافق"""
    return await telethon_simple_handlers.handle_start(event)

async def handle_help(event):
    """دالة للتوافق"""
    return await telethon_simple_handlers.handle_help(event)

async def handle_general_message(event):
    """دالة للتوافق"""
    return await telethon_simple_handlers.handle_general_message(event)

async def handle_callback_query(event):
    """دالة للتوافق"""
    return await telethon_simple_handlers.handle_callback_query(event)

async def handle_inline_query(event):
    """دالة للتوافق"""
    return await telethon_simple_handlers.handle_inline_query(event)