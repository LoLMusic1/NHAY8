"""
🔍 معالج أوامر البحث للبوت
========================
يتعامل مع جميع أوامر البحث ويوجهها للمعالج المناسب
"""

import asyncio
import re
from telethon import events, Button
from ZeMusic import bot, LOGGER

# قائمة أوامر البحث المدعومة
SEARCH_COMMANDS = [
    "بحث", "search", "song", "يوت", "اغنية", "تحميل", 
    "ابحث", "يوتيوب", "موسيقى", "اغاني", "نغمة"
]

@bot.on(events.NewMessage(pattern=r'^/?(بحث|search|song|يوت|اغنية|تحميل|ابحث|يوتيوب|موسيقى|اغاني|نغمة)(\s+(.+))?$'))
async def handle_search_command(event):
    """معالج أوامر البحث الرئيسي"""
    try:
        # التحقق من أن الرسالة من مستخدم وليس بوت
        if event.sender.bot:
            return
            
        # استخراج النص والاستعلام
        text = event.raw_text
        match = event.pattern_match
        command = match.group(1) if match.group(1) else ""
        query = match.group(3) if match.group(3) else ""
        
        if not query:
            await event.reply(
                "📝 **الاستخدام:**\n"
                f"• `/{command} اسم الأغنية`\n"
                f"• `{command} اسم الفنان - اسم الأغنية`\n\n"
                "**مثال:**\n"
                f"`/{command} عمرو دياب نور العين`"
            )
            return
        
        # رسالة الحالة
        status_msg = await event.reply("⚡ **جاري البحث...**")
        
        # استيراد وتشغيل المعالج
        try:
            from ZeMusic.plugins.play.download_enhanced import download_enhanced_song
            await download_enhanced_song(event, query)
            LOGGER(__name__).info(f"✅ تم تشغيل البحث المحسن: {query}")
        except ImportError:
            try:
                from ZeMusic.plugins.play.download import download_song_smart
                await download_song_smart(event, query)
                LOGGER(__name__).info(f"✅ تم تشغيل البحث الأساسي: {query}")
            except ImportError:
                await status_msg.edit(
                    "❌ **خطأ في النظام**\n\n"
                    "المعالجات غير متاحة حالياً\n"
                    "يرجى المحاولة لاحقاً"
                )
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في تشغيل المعالج: {e}")
            await status_msg.edit(
                "❌ **خطأ في البحث**\n\n"
                "حدث خطأ أثناء معالجة طلبك\n"
                "يرجى المحاولة مرة أخرى"
            )
            
    except Exception as e:
        LOGGER(__name__).error(f"خطأ في معالج البحث: {e}")
        await event.reply(
            "❌ **خطأ في البحث**\n\n"
            "حدث خطأ أثناء معالجة طلبك\n"
            "يرجى المحاولة مرة أخرى"
        )

# معالج إضافي للرسائل النصية البسيطة
@bot.on(events.NewMessage(pattern=r'^(بحث|search|song|يوت|اغنية|تحميل|ابحث|يوتيوب|موسيقى|اغاني|نغمة)\s+(.+)$'))
async def handle_simple_text_search(event):
    """معالج للرسائل النصية البسيطة التي تحتوي على أوامر البحث"""
    try:
        if event.sender.bot:
            return
            
        match = event.pattern_match
        command = match.group(1) if match.group(1) else ""
        query = match.group(2) if match.group(2) else ""
        
        if query:
            # رسالة الحالة
            status_msg = await event.reply("⚡ **جاري البحث...**")
            
            try:
                from ZeMusic.plugins.play.download_enhanced import download_enhanced_song
                await download_enhanced_song(event, query)
                LOGGER(__name__).info(f"✅ تم تشغيل البحث النصي المحسن: {query}")
            except Exception as e:
                LOGGER(__name__).error(f"خطأ في تشغيل المعالج النصي: {e}")
                await status_msg.edit(
                    "❌ **خطأ في البحث**\n\n"
                    "حدث خطأ أثناء معالجة طلبك\n"
                    "يرجى المحاولة مرة أخرى"
                )
                    
    except Exception as e:
        LOGGER(__name__).error(f"خطأ في معالج البحث النصي: {e}")

LOGGER(__name__).info("✅ تم تحميل معالج أوامر البحث")
