#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎵 ZeMusic Bot v3.0 - Interactive Keyboard System
تاريخ الإنشاء: 2025-01-28

نظام الكيبورد التفاعلي المتقدم
"""

import asyncio
import logging
import random
from typing import Dict, List, Optional, Any
from telethon import events, Button
from telethon.tl.types import KeyboardButtonRow, KeyboardButton, ReplyKeyboardMarkup

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import config
from ..core import TelethonClient, DatabaseManager

logger = logging.getLogger(__name__)

class InteractiveKeyboardPlugin:
    """بلاجين الكيبورد التفاعلي المتقدم"""
    
    def __init__(self, client: TelethonClient, db: DatabaseManager):
        """تهيئة بلاجين الكيبورد التفاعلي"""
        self.client = client
        self.db = db
        
        # محتوى الكيبورد والردود
        self.keyboard_content = {
            'main_keyboard': [
                ["🎵 غنيلي", "🎶 موسيقى عشوائية"],
                ["📸 صور", "🎭 انمي"],
                ["🎬 متحركه", "💭 اقتباسات"],
                ["👨‍💼 افتارات شباب", "👩‍💼 افتار بنات"],
                ["🎨 هيدرات", "📿 قران"],
                ["❌ اخفاء الكيبورد"]
            ],
            'music_keyboard': [
                ["🎵 تشغيل", "⏸️ إيقاف"],
                ["⏭️ التالي", "⏮️ السابق"],
                ["🔀 خلط", "🔁 تكرار"],
                ["🔊 رفع الصوت", "🔉 خفض الصوت"],
                ["📋 القائمة", "🔙 الرئيسية"]
            ],
            'settings_keyboard': [
                ["🌍 تغيير اللغة", "🎧 جودة الصوت"],
                ["🔔 الإشعارات", "🎨 المظهر"],
                ["📊 الإحصائيات", "ℹ️ المساعدة"],
                ["🔙 الرئيسية"]
            ]
        }
        
        # المحتوى المتنوع
        self.content_sources = {
            'quotes': [
                "💭 النجاح هو الانتقال من فشل إلى فشل دون فقدان الحماس",
                "💭 الطريق إلى النجاح دائماً تحت الإنشاء",
                "💭 لا تنتظر الفرصة، بل اصنعها",
                "💭 الأحلام لا تعمل إلا إذا عملت أنت",
                "💭 النجاح يأتي لمن يصبر ويثابر"
            ],
            'anime_facts': [
                "🎭 هل تعلم أن أنمي ناروتو يحتوي على أكثر من 700 حلقة؟",
                "🎭 أول أنمي في التاريخ كان عام 1917 في اليابان",
                "🎭 استوديو جيبلي أنتج أشهر أفلام الأنمي في العالم",
                "🎭 كلمة 'أنمي' مشتقة من الكلمة الإنجليزية 'Animation'",
                "🎭 اليابان تنتج أكثر من 200 أنمي سنوياً"
            ]
        }
        
        # إحصائيات الاستخدام
        self.usage_stats = {
            'keyboard_requests': 0,
            'button_clicks': 0,
            'content_requests': 0,
            'most_used_buttons': {}
        }
        
    async def initialize(self) -> bool:
        """تهيئة بلاجين الكيبورد التفاعلي"""
        try:
            logger.info("⌨️ تهيئة بلاجين الكيبورد التفاعلي...")
            
            # تسجيل معالجات الأحداث
            await self._register_keyboard_handlers()
            
            logger.info("✅ تم تهيئة بلاجين الكيبورد التفاعلي بنجاح")
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في تهيئة بلاجين الكيبورد التفاعلي: {e}")
            return False
    
    async def _register_keyboard_handlers(self):
        """تسجيل معالجات أحداث الكيبورد"""
        try:
            # معالج أمر عرض الكيبورد الرئيسي
            @self.client.client.on(events.NewMessage(pattern=r'^[!/.](?:cmds|keyboard|كيبورد|لوحة المفاتيح)$'))
            async def handle_main_keyboard(event):
                await self._show_main_keyboard(event)
            
            # معالج أزرار الكيبورد الرئيسي
            @self.client.client.on(events.NewMessage(pattern=r'^(🎵 غنيلي|🎶 موسيقى عشوائية|📸 صور|🎭 انمي|🎬 متحركه|💭 اقتباسات|👨‍💼 افتارات شباب|👩‍💼 افتار بنات|🎨 هيدرات|📿 قران|❌ اخفاء الكيبورد)$'))
            async def handle_main_buttons(event):
                await self._handle_main_button_click(event)
            
            # معالج أزرار الموسيقى
            @self.client.client.on(events.NewMessage(pattern=r'^(🎵 تشغيل|⏸️ إيقاف|⏭️ التالي|⏮️ السابق|🔀 خلط|🔁 تكرار|🔊 رفع الصوت|🔉 خفض الصوت|📋 القائمة|🔙 الرئيسية)$'))
            async def handle_music_buttons(event):
                await self._handle_music_button_click(event)
            
            # معالج أزرار الإعدادات
            @self.client.client.on(events.NewMessage(pattern=r'^(🌍 تغيير اللغة|🎧 جودة الصوت|🔔 الإشعارات|🎨 المظهر|📊 الإحصائيات|ℹ️ المساعدة)$'))
            async def handle_settings_buttons(event):
                await self._handle_settings_button_click(event)
            
            # معالج الاستعلامات
            @self.client.client.on(events.CallbackQuery(pattern=b'kb_'))
            async def handle_keyboard_callback(event):
                await self._handle_keyboard_callback(event)
            
            logger.info("📝 تم تسجيل معالجات الكيبورد التفاعلي")
            
        except Exception as e:
            logger.error(f"❌ فشل في تسجيل معالجات الكيبورد: {e}")
    
    async def _show_main_keyboard(self, event):
        """عرض الكيبورد الرئيسي"""
        try:
            user = await event.get_sender()
            user_name = user.first_name or "المستخدم"
            
            message = (
                f"⌨️ **مرحباً {user_name}!**\n\n"
                f"🎵 **أهلاً بك في لوحة التحكم التفاعلية**\n\n"
                f"🔽 **اختر من الأزرار أدناه:**\n"
                f"• 🎵 للموسيقى والتشغيل\n"
                f"• 📸 للصور والمحتوى البصري\n"
                f"• 💭 للاقتباسات والحكم\n"
                f"• 📿 للمحتوى الديني\n\n"
                f"💡 **نصيحة:** يمكنك استخدام الأزرار أو كتابة الأوامر مباشرة"
            )
            
            # إنشاء الكيبورد
            keyboard = self._create_reply_keyboard(self.keyboard_content['main_keyboard'])
            
            await event.reply(message, buttons=keyboard)
            
            # تحديث الإحصائيات
            self.usage_stats['keyboard_requests'] += 1
            
        except Exception as e:
            logger.error(f"❌ خطأ في عرض الكيبورد الرئيسي: {e}")
            await event.reply("❌ حدث خطأ في عرض لوحة المفاتيح")
    
    async def _handle_main_button_click(self, event):
        """معالجة النقر على أزرار الكيبورد الرئيسي"""
        try:
            button_text = event.message.text
            user = await event.get_sender()
            
            # تحديث إحصائيات الاستخدام
            self.usage_stats['button_clicks'] += 1
            if button_text in self.usage_stats['most_used_buttons']:
                self.usage_stats['most_used_buttons'][button_text] += 1
            else:
                self.usage_stats['most_used_buttons'][button_text] = 1
            
            # معالجة كل زر
            if button_text == "🎵 غنيلي":
                await self._handle_music_request(event)
            elif button_text == "🎶 موسيقى عشوائية":
                await self._handle_random_music(event)
            elif button_text == "📸 صور":
                await self._handle_photos_request(event)
            elif button_text == "🎭 انمي":
                await self._handle_anime_request(event)
            elif button_text == "🎬 متحركه":
                await self._handle_gif_request(event)
            elif button_text == "💭 اقتباسات":
                await self._handle_quotes_request(event)
            elif button_text == "👨‍💼 افتارات شباب":
                await self._handle_male_avatars(event)
            elif button_text == "👩‍💼 افتار بنات":
                await self._handle_female_avatars(event)
            elif button_text == "🎨 هيدرات":
                await self._handle_headers_request(event)
            elif button_text == "📿 قران":
                await self._handle_quran_request(event)
            elif button_text == "❌ اخفاء الكيبورد":
                await self._hide_keyboard(event)
                
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة زر الكيبورد الرئيسي: {e}")
            await event.reply("❌ حدث خطأ في معالجة الطلب")
    
    async def _handle_music_button_click(self, event):
        """معالجة أزرار الموسيقى"""
        try:
            button_text = event.message.text
            
            if button_text == "🎵 تشغيل":
                await self._handle_play_command(event)
            elif button_text == "⏸️ إيقاف":
                await self._handle_pause_command(event)
            elif button_text == "⏭️ التالي":
                await self._handle_skip_command(event)
            elif button_text == "⏮️ السابق":
                await self._handle_previous_command(event)
            elif button_text == "🔀 خلط":
                await self._handle_shuffle_command(event)
            elif button_text == "🔁 تكرار":
                await self._handle_loop_command(event)
            elif button_text == "🔊 رفع الصوت":
                await self._handle_volume_up(event)
            elif button_text == "🔉 خفض الصوت":
                await self._handle_volume_down(event)
            elif button_text == "📋 القائمة":
                await self._handle_queue_command(event)
            elif button_text == "🔙 الرئيسية":
                await self._show_main_keyboard(event)
                
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة زر الموسيقى: {e}")
            await event.reply("❌ حدث خطأ في التحكم بالموسيقى")
    
    async def _handle_settings_button_click(self, event):
        """معالجة أزرار الإعدادات"""
        try:
            button_text = event.message.text
            
            if button_text == "🌍 تغيير اللغة":
                await self._handle_language_settings(event)
            elif button_text == "🎧 جودة الصوت":
                await self._handle_audio_quality_settings(event)
            elif button_text == "🔔 الإشعارات":
                await self._handle_notification_settings(event)
            elif button_text == "🎨 المظهر":
                await self._handle_theme_settings(event)
            elif button_text == "📊 الإحصائيات":
                await self._show_user_statistics(event)
            elif button_text == "ℹ️ المساعدة":
                await self._show_help_info(event)
                
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة زر الإعدادات: {e}")
            await event.reply("❌ حدث خطأ في الإعدادات")
    
    async def _handle_keyboard_callback(self, event):
        """معالجة استعلامات الكيبورد"""
        try:
            data = event.data.decode('utf-8')
            
            if data.startswith("kb_show_"):
                keyboard_type = data.replace("kb_show_", "")
                await self._show_specific_keyboard(event, keyboard_type)
            elif data.startswith("kb_content_"):
                content_type = data.replace("kb_content_", "")
                await self._provide_content(event, content_type)
            elif data == "kb_stats":
                await self._show_keyboard_statistics(event)
            elif data == "kb_customize":
                await self._show_customization_options(event)
                
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة استعلام الكيبورد: {e}")
            await event.answer("❌ حدث خطأ في معالجة الطلب", alert=True)
    
    # معالجات المحتوى المختلفة
    async def _handle_music_request(self, event):
        """معالجة طلب الموسيقى"""
        try:
            message = (
                "🎵 **قسم الموسيقى**\n\n"
                "🎶 **اختر نوع الطلب:**\n"
                "• أرسل اسم الأغنية للبحث والتشغيل\n"
                "• استخدم `/play [اسم الأغنية]` للتشغيل المباشر\n"
                "• `/search [كلمة البحث]` للبحث المتقدم\n\n"
                "💡 **أمثلة:**\n"
                "• `فيروز صباح الخير`\n"
                "• `imagine dragons thunder`\n"
                "• `موسيقى هادئة`"
            )
            
            # عرض كيبورد الموسيقى
            keyboard = self._create_reply_keyboard(self.keyboard_content['music_keyboard'])
            
            await event.reply(message, buttons=keyboard)
            
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة طلب الموسيقى: {e}")
            await event.reply("❌ حدث خطأ في قسم الموسيقى")
    
    async def _handle_random_music(self, event):
        """تشغيل موسيقى عشوائية"""
        try:
            # قائمة أغاني شائعة للتشغيل العشوائي
            random_songs = [
                "relaxing music",
                "classical music",
                "jazz music",
                "pop music",
                "rock music",
                "electronic music",
                "ambient music",
                "piano music"
            ]
            
            random_song = random.choice(random_songs)
            
            await event.reply(
                f"🎶 **تشغيل موسيقى عشوائية**\n\n"
                f"🎵 **النوع المختار:** {random_song}\n"
                f"⏳ **جاري البحث والتشغيل...**\n\n"
                f"💡 **استخدم أزرار التحكم أدناه**"
            )
            
            # محاكاة تشغيل الموسيقى (سيتم ربطها بمحرك الموسيقى الفعلي)
            # await self.music_engine.play_random_track(event.chat_id, random_song)
            
        except Exception as e:
            logger.error(f"❌ خطأ في تشغيل الموسيقى العشوائية: {e}")
            await event.reply("❌ حدث خطأ في تشغيل الموسيقى العشوائية")
    
    async def _handle_photos_request(self, event):
        """معالجة طلب الصور"""
        try:
            message = (
                "📸 **قسم الصور**\n\n"
                "🖼️ **أنواع الصور المتاحة:**\n"
                "• صور طبيعية وخلابة\n"
                "• صور فنية وإبداعية\n"
                "• صور حيوانات لطيفة\n"
                "• صور مدن وعمارة\n"
                "• صور فضاء ونجوم\n\n"
                "⏳ **جاري إرسال صورة عشوائية...**"
            )
            
            await event.reply(message)
            
            # محاكاة إرسال صورة (سيتم ربطها بمصدر صور فعلي)
            await asyncio.sleep(1)
            await event.reply("📸 **تم إرسال الصورة!** (محاكاة)")
            
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة طلب الصور: {e}")
            await event.reply("❌ حدث خطأ في قسم الصور")
    
    async def _handle_anime_request(self, event):
        """معالجة طلب الأنمي"""
        try:
            # اختيار معلومة عشوائية عن الأنمي
            anime_fact = random.choice(self.content_sources['anime_facts'])
            
            message = (
                f"🎭 **عالم الأنمي**\n\n"
                f"{anime_fact}\n\n"
                f"🎬 **محتوى الأنمي:**\n"
                f"• صور شخصيات أنمي\n"
                f"• خلفيات أنمي عالية الجودة\n"
                f"• معلومات عن الأنمي الشائع\n"
                f"• توصيات أنمي جديدة\n\n"
                f"⏳ **جاري إرسال محتوى أنمي...**"
            )
            
            await event.reply(message)
            
            # محاكاة إرسال محتوى أنمي
            await asyncio.sleep(1)
            await event.reply("🎭 **تم إرسال محتوى الأنمي!** (محاكاة)")
            
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة طلب الأنمي: {e}")
            await event.reply("❌ حدث خطأ في قسم الأنمي")
    
    async def _handle_quotes_request(self, event):
        """معالجة طلب الاقتباسات"""
        try:
            # اختيار اقتباس عشوائي
            quote = random.choice(self.content_sources['quotes'])
            
            message = (
                f"💭 **اقتباس اليوم**\n\n"
                f"{quote}\n\n"
                f"✨ **المزيد من الاقتباسات:**\n"
                f"• اقتباسات تحفيزية\n"
                f"• حكم وأمثال\n"
                f"• أقوال مأثورة\n"
                f"• اقتباسات أدبية\n\n"
                f"🔄 **اضغط الزر مرة أخرى للمزيد**"
            )
            
            keyboard = [
                [Button.inline("💭 اقتباس آخر", b"kb_content_quote")],
                [Button.inline("🔙 العودة للرئيسية", b"kb_show_main")]
            ]
            
            await event.reply(message, buttons=keyboard)
            
            # تحديث إحصائيات المحتوى
            self.usage_stats['content_requests'] += 1
            
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة طلب الاقتباسات: {e}")
            await event.reply("❌ حدث خطأ في قسم الاقتباسات")
    
    async def _handle_quran_request(self, event):
        """معالجة طلب القرآن"""
        try:
            message = (
                "📿 **القسم الديني**\n\n"
                "🕌 **المحتوى الإسلامي المتاح:**\n"
                "• آيات قرآنية مع التفسير\n"
                "• أحاديث نبوية شريفة\n"
                "• أدعية وأذكار\n"
                "• معلومات إسلامية مفيدة\n"
                "• تلاوات قرآنية مميزة\n\n"
                "🤲 **اللهم بارك لنا فيما رزقتنا**\n\n"
                "⏳ **جاري إرسال محتوى ديني...**"
            )
            
            await event.reply(message)
            
            # محاكاة إرسال محتوى ديني
            await asyncio.sleep(1)
            await event.reply("📿 **تم إرسال المحتوى الديني!** (محاكاة)")
            
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة طلب القرآن: {e}")
            await event.reply("❌ حدث خطأ في القسم الديني")
    
    async def _hide_keyboard(self, event):
        """إخفاء الكيبورد"""
        try:
            from telethon.tl.types import ReplyKeyboardRemove
            
            message = (
                "❌ **تم إخفاء لوحة المفاتيح**\n\n"
                "💡 **لإظهارها مرة أخرى:**\n"
                "• أرسل `/cmds` أو `/keyboard`\n"
                "• أو اكتب `كيبورد` أو `لوحة المفاتيح`\n\n"
                "🎵 **يمكنك الاستمرار في استخدام الأوامر النصية**"
            )
            
            await event.reply(message, buttons=ReplyKeyboardRemove())
            
        except Exception as e:
            logger.error(f"❌ خطأ في إخفاء الكيبورد: {e}")
            await event.reply("❌ حدث خطأ في إخفاء لوحة المفاتيح")
    
    # معالجات أزرار الموسيقى
    async def _handle_play_command(self, event):
        """معالجة أمر التشغيل"""
        await event.reply("🎵 **تم بدء التشغيل** (محاكاة)")
    
    async def _handle_pause_command(self, event):
        """معالجة أمر الإيقاف المؤقت"""
        await event.reply("⏸️ **تم إيقاف التشغيل مؤقتاً** (محاكاة)")
    
    async def _handle_skip_command(self, event):
        """معالجة أمر التخطي"""
        await event.reply("⏭️ **تم تخطي المقطع** (محاكاة)")
    
    async def _handle_previous_command(self, event):
        """معالجة أمر المقطع السابق"""
        await event.reply("⏮️ **تم الانتقال للمقطع السابق** (محاكاة)")
    
    async def _handle_shuffle_command(self, event):
        """معالجة أمر الخلط"""
        await event.reply("🔀 **تم تفعيل نمط الخلط** (محاكاة)")
    
    async def _handle_loop_command(self, event):
        """معالجة أمر التكرار"""
        await event.reply("🔁 **تم تفعيل نمط التكرار** (محاكاة)")
    
    async def _handle_volume_up(self, event):
        """رفع مستوى الصوت"""
        await event.reply("🔊 **تم رفع مستوى الصوت** (محاكاة)")
    
    async def _handle_volume_down(self, event):
        """خفض مستوى الصوت"""
        await event.reply("🔉 **تم خفض مستوى الصوت** (محاكاة)")
    
    async def _handle_queue_command(self, event):
        """عرض قائمة الانتظار"""
        await event.reply("📋 **قائمة الانتظار فارغة** (محاكاة)")
    
    # معالجات الإعدادات
    async def _handle_language_settings(self, event):
        """إعدادات اللغة"""
        keyboard = [
            [Button.inline("🇸🇦 العربية", b"kb_lang_ar")],
            [Button.inline("🇺🇸 English", b"kb_lang_en")],
            [Button.inline("🔙 العودة", b"kb_show_settings")]
        ]
        
        await event.reply(
            "🌍 **إعدادات اللغة**\n\n"
            "اختر اللغة المفضلة:",
            buttons=keyboard
        )
    
    async def _handle_audio_quality_settings(self, event):
        """إعدادات جودة الصوت"""
        keyboard = [
            [Button.inline("🎧 عالية (320kbps)", b"kb_quality_high")],
            [Button.inline("🎵 متوسطة (192kbps)", b"kb_quality_medium")],
            [Button.inline("📻 منخفضة (128kbps)", b"kb_quality_low")],
            [Button.inline("🔙 العودة", b"kb_show_settings")]
        ]
        
        await event.reply(
            "🎧 **إعدادات جودة الصوت**\n\n"
            "اختر الجودة المفضلة:",
            buttons=keyboard
        )
    
    async def _show_user_statistics(self, event):
        """عرض إحصائيات المستخدم"""
        try:
            user = await event.get_sender()
            
            # حساب الإحصائيات
            total_buttons = sum(self.usage_stats['most_used_buttons'].values())
            most_used = max(self.usage_stats['most_used_buttons'].items(), key=lambda x: x[1]) if self.usage_stats['most_used_buttons'] else ("لا يوجد", 0)
            
            message = (
                f"📊 **إحصائيات الاستخدام**\n\n"
                f"👤 **المستخدم:** {user.first_name}\n"
                f"⌨️ **طلبات الكيبورد:** {self.usage_stats['keyboard_requests']:,}\n"
                f"🔘 **نقرات الأزرار:** {self.usage_stats['button_clicks']:,}\n"
                f"📄 **طلبات المحتوى:** {self.usage_stats['content_requests']:,}\n"
                f"⭐ **الزر الأكثر استخداماً:** {most_used[0]} ({most_used[1]} مرة)\n\n"
                f"🎯 **معدل الاستخدام:** {(total_buttons / max(self.usage_stats['keyboard_requests'], 1)):.1f} زر/جلسة"
            )
            
            await event.reply(message)
            
        except Exception as e:
            logger.error(f"❌ خطأ في عرض الإحصائيات: {e}")
            await event.reply("❌ حدث خطأ في جلب الإحصائيات")
    
    # وظائف مساعدة
    def _create_reply_keyboard(self, buttons_layout: List[List[str]]) -> ReplyKeyboardMarkup:
        """إنشاء كيبورد للرد"""
        try:
            keyboard_buttons = []
            
            for row in buttons_layout:
                button_row = []
                for button_text in row:
                    button_row.append(KeyboardButton(button_text))
                keyboard_buttons.append(KeyboardButtonRow(button_row))
            
            return ReplyKeyboardMarkup(
                rows=keyboard_buttons,
                resize=True,
                one_time=False,
                selective=True
            )
            
        except Exception as e:
            logger.error(f"❌ خطأ في إنشاء الكيبورد: {e}")
            return None
    
    async def _show_specific_keyboard(self, event, keyboard_type: str):
        """عرض كيبورد محدد"""
        try:
            if keyboard_type == "main":
                await self._show_main_keyboard(event)
            elif keyboard_type == "music":
                keyboard = self._create_reply_keyboard(self.keyboard_content['music_keyboard'])
                await event.edit("🎵 **كيبورد الموسيقى**", buttons=keyboard)
            elif keyboard_type == "settings":
                keyboard = self._create_reply_keyboard(self.keyboard_content['settings_keyboard'])
                await event.edit("⚙️ **كيبورد الإعدادات**", buttons=keyboard)
                
        except Exception as e:
            logger.error(f"❌ خطأ في عرض الكيبورد المحدد: {e}")
            await event.answer("❌ حدث خطأ في عرض الكيبورد", alert=True)
    
    async def _provide_content(self, event, content_type: str):
        """توفير محتوى محدد"""
        try:
            if content_type == "quote":
                await self._handle_quotes_request(event)
            # يمكن إضافة المزيد من أنواع المحتوى هنا
                
        except Exception as e:
            logger.error(f"❌ خطأ في توفير المحتوى: {e}")
            await event.answer("❌ حدث خطأ في جلب المحتوى", alert=True)
    
    async def get_keyboard_statistics(self) -> Dict[str, Any]:
        """الحصول على إحصائيات الكيبورد"""
        return {
            'keyboard_requests': self.usage_stats['keyboard_requests'],
            'button_clicks': self.usage_stats['button_clicks'],
            'content_requests': self.usage_stats['content_requests'],
            'most_used_buttons': self.usage_stats['most_used_buttons'].copy(),
            'total_interactions': self.usage_stats['keyboard_requests'] + self.usage_stats['button_clicks']
        }

# إنشاء مثيل عام لبلاجين الكيبورد التفاعلي
interactive_keyboard_plugin = None  # سيتم تهيئته في الملف الرئيسي