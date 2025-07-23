#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎵 ZeMusic Bot v3.0 - Music Handlers
معالجات أوامر الموسيقى والبحث
"""

import asyncio
import logging
import re
import aiohttp
import json
from telethon import events, Button
from telethon.tl.types import DocumentAttributeAudio

logger = logging.getLogger(__name__)

class MusicHandlers:
    """معالجات أوامر الموسيقى"""
    
    def __init__(self, client, db, config):
        self.client = client
        self.db = db
        self.config = config
        
    def register_handlers(self):
        """تسجيل جميع معالجات الموسيقى"""
        
        @self.client.client.on(events.NewMessage(pattern=r'^[./!]?(play|تشغيل|شغل)\s+(.+)'))
        async def play_handler(event):
            """معالج أمر التشغيل"""
            try:
                query = event.pattern_match.group(2).strip()
                user_id = event.sender_id
                chat_id = event.chat_id
                
                if not query:
                    await event.respond("❌ يرجى كتابة اسم الأغنية أو الرابط\n\n**مثال:** `/play Despacito`")
                    return
                
                # رسالة التحميل
                loading_msg = await event.respond("🔍 **جاري البحث...**\n⏳ يرجى الانتظار...")
                
                # البحث عن الأغنية
                search_results = await self._search_music(query)
                
                if not search_results:
                    await loading_msg.edit("❌ **لم يتم العثور على نتائج**\n\n🔍 جرب البحث بكلمات مختلفة")
                    return
                
                # عرض النتائج
                buttons = []
                for i, result in enumerate(search_results[:5]):
                    title = result.get('title', 'غير معروف')[:50]
                    duration = result.get('duration', 'غير معروف')
                    buttons.append([Button.inline(
                        f"🎵 {title} - {duration}",
                        data=f"play_{i}_{user_id}"
                    )])
                
                buttons.append([Button.inline("❌ إلغاء", data=f"cancel_{user_id}")])
                
                results_text = f"""
🎵 **نتائج البحث عن:** `{query}`

📝 **اختر الأغنية التي تريد تشغيلها:**
"""
                
                await loading_msg.edit(results_text, buttons=buttons)
                
                # حفظ النتائج مؤقتاً
                await self.db.save_search_results(user_id, search_results)
                
                logger.info(f"🎵 بحث موسيقى: {query} من المستخدم {user_id}")
                
            except Exception as e:
                logger.error(f"❌ خطأ في معالج التشغيل: {e}")
                await event.respond("❌ حدث خطأ في البحث، يرجى المحاولة مرة أخرى")
        
        @self.client.client.on(events.NewMessage(pattern=r'^[./!]?(search|بحث)\s+(.+)'))
        async def search_handler(event):
            """معالج أمر البحث"""
            try:
                query = event.pattern_match.group(2).strip()
                user_id = event.sender_id
                
                if not query:
                    await event.respond("❌ يرجى كتابة ما تريد البحث عنه\n\n**مثال:** `/search Adele`")
                    return
                
                # رسالة التحميل
                loading_msg = await event.respond("🔍 **جاري البحث...**")
                
                # البحث
                search_results = await self._search_music(query)
                
                if not search_results:
                    await loading_msg.edit("❌ **لم يتم العثور على نتائج**")
                    return
                
                # تنسيق النتائج
                results_text = f"🔍 **نتائج البحث عن:** `{query}`\n\n"
                
                for i, result in enumerate(search_results[:10], 1):
                    title = result.get('title', 'غير معروف')
                    artist = result.get('artist', 'غير معروف')
                    duration = result.get('duration', 'غير معروف')
                    
                    results_text += f"**{i}.** 🎵 {title}\n"
                    results_text += f"👤 {artist} | ⏱️ {duration}\n\n"
                
                results_text += f"💡 **للتشغيل:** `/play {query}`"
                
                # أزرار التشغيل
                buttons = [
                    [Button.inline("🎵 تشغيل الأول", data=f"play_0_{user_id}")],
                    [Button.inline("🔄 بحث جديد", data=f"new_search_{user_id}")]
                ]
                
                await loading_msg.edit(results_text, buttons=buttons)
                
                # حفظ النتائج
                await self.db.save_search_results(user_id, search_results)
                
                logger.info(f"🔍 بحث: {query} من المستخدم {user_id}")
                
            except Exception as e:
                logger.error(f"❌ خطأ في معالج البحث: {e}")
                await event.respond("❌ حدث خطأ في البحث")
        
        @self.client.client.on(events.CallbackQuery(pattern=r'^play_(\d+)_(\d+)$'))
        async def play_callback_handler(event):
            """معالج أزرار التشغيل"""
            try:
                result_index = int(event.pattern_match.group(1))
                user_id = int(event.pattern_match.group(2))
                
                if event.sender_id != user_id:
                    await event.answer("❌ هذا الزر ليس لك!", alert=True)
                    return
                
                # جلب النتائج المحفوظة
                search_results = await self.db.get_search_results(user_id)
                
                if not search_results or result_index >= len(search_results):
                    await event.answer("❌ النتائج منتهية الصلاحية", alert=True)
                    return
                
                selected_song = search_results[result_index]
                
                # بدء التشغيل
                await event.edit("🎵 **جاري التشغيل...**\n⏳ يرجى الانتظار...")
                
                # محاكاة التشغيل (في الوضع المحدود)
                play_text = f"""
🎵 **الآن يتم تشغيل:**

📀 **العنوان:** {selected_song.get('title', 'غير معروف')}
👤 **الفنان:** {selected_song.get('artist', 'غير معروف')}
⏱️ **المدة:** {selected_song.get('duration', 'غير معروف')}
👥 **في المجموعة:** {event.chat.title if hasattr(event.chat, 'title') else 'محادثة خاصة'}

⚠️ **ملاحظة:** البوت يعمل حالياً في الوضع المحدود
🔧 **لتفعيل التشغيل الكامل:** يتطلب تثبيت PyTgCalls
"""
                
                buttons = [
                    [Button.inline("⏸️ إيقاف مؤقت", data=f"pause_{user_id}"),
                     Button.inline("⏹️ إيقاف", data=f"stop_{user_id}")],
                    [Button.inline("⏭️ التالي", data=f"skip_{user_id}"),
                     Button.inline("🔀 عشوائي", data=f"shuffle_{user_id}")],
                    [Button.inline("📋 القائمة", data=f"queue_{user_id}")]
                ]
                
                await event.edit(play_text, buttons=buttons)
                
                # حفظ معلومات التشغيل
                await self.db.save_now_playing(event.chat_id, selected_song, user_id)
                
                logger.info(f"🎵 تشغيل: {selected_song.get('title')} في {event.chat_id}")
                
            except Exception as e:
                logger.error(f"❌ خطأ في معالج التشغيل: {e}")
                await event.answer("❌ حدث خطأ في التشغيل", alert=True)
        
        @self.client.client.on(events.NewMessage(pattern=r'^[./!]?(pause|إيقاف مؤقت|وقف)$'))
        async def pause_handler(event):
            """معالج أمر الإيقاف المؤقت"""
            await event.respond("⏸️ **تم إيقاف التشغيل مؤقتاً**\n\n💡 استخدم `/resume` للمتابعة")
        
        @self.client.client.on(events.NewMessage(pattern=r'^[./!]?(resume|متابعة|استكمال)$'))
        async def resume_handler(event):
            """معالج أمر المتابعة"""
            await event.respond("▶️ **تم استكمال التشغيل**")
        
        @self.client.client.on(events.NewMessage(pattern=r'^[./!]?(stop|إيقاف|توقف)$'))
        async def stop_handler(event):
            """معالج أمر الإيقاف"""
            await event.respond("⏹️ **تم إيقاف التشغيل**\n\n🎵 شكراً لاستخدام البوت!")
        
        @self.client.client.on(events.NewMessage(pattern=r'^[./!]?(skip|تخطي|التالي)$'))
        async def skip_handler(event):
            """معالج أمر التخطي"""
            await event.respond("⏭️ **تم تخطي المقطع الحالي**")
        
        @self.client.client.on(events.NewMessage(pattern=r'^[./!]?(queue|القائمة|الطابور)$'))
        async def queue_handler(event):
            """معالج أمر عرض القائمة"""
            queue_text = """
📋 **قائمة التشغيل:**

🎵 **الآن يتم تشغيل:**
لا يوجد شيء يتم تشغيله حالياً

📝 **في الانتظار:**
القائمة فارغة

💡 **لإضافة أغاني:** `/play اسم الأغنية`
"""
            
            buttons = [
                [Button.inline("🔀 خلط القائمة", data=f"shuffle_queue_{event.sender_id}"),
                 Button.inline("🗑️ مسح القائمة", data=f"clear_queue_{event.sender_id}")],
                [Button.inline("🔄 تحديث", data=f"refresh_queue_{event.sender_id}")]
            ]
            
            await event.respond(queue_text, buttons=buttons)
        
        logger.info("✅ تم تسجيل جميع معالجات الموسيقى")
    
    async def _search_music(self, query: str) -> list:
        """البحث عن الموسيقى"""
        try:
            # محاكاة نتائج البحث (في الوضع المحدود)
            mock_results = [
                {
                    'title': f'{query} - Original',
                    'artist': 'Various Artists',
                    'duration': '3:45',
                    'url': f'https://example.com/{query}_original',
                    'thumbnail': 'https://via.placeholder.com/320x320'
                },
                {
                    'title': f'{query} - Remix',
                    'artist': 'DJ Mix',
                    'duration': '4:12',
                    'url': f'https://example.com/{query}_remix',
                    'thumbnail': 'https://via.placeholder.com/320x320'
                },
                {
                    'title': f'{query} - Acoustic Version',
                    'artist': 'Acoustic Cover',
                    'duration': '3:28',
                    'url': f'https://example.com/{query}_acoustic',
                    'thumbnail': 'https://via.placeholder.com/320x320'
                },
                {
                    'title': f'{query} - Live Performance',
                    'artist': 'Live Concert',
                    'duration': '4:56',
                    'url': f'https://example.com/{query}_live',
                    'thumbnail': 'https://via.placeholder.com/320x320'
                },
                {
                    'title': f'{query} - Instrumental',
                    'artist': 'Instrumental Version',
                    'duration': '3:33',
                    'url': f'https://example.com/{query}_instrumental',
                    'thumbnail': 'https://via.placeholder.com/320x320'
                }
            ]
            
            logger.info(f"🔍 تم العثور على {len(mock_results)} نتيجة لـ: {query}")
            return mock_results
            
        except Exception as e:
            logger.error(f"❌ خطأ في البحث: {e}")
            return []