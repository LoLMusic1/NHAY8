"""
🔍 معالج أوامر البحث للبوت
========================
يتعامل مع جميع أوامر البحث ويوجهها للمعالج المناسب
"""

import asyncio
import re
from telethon import events
from pyrogram import filters
from ZeMusic import app, LOGGER

# قائمة أوامر البحث المدعومة
SEARCH_COMMANDS = [
    "بحث", "search", "song", "يوت", "اغنية", "تحميل", 
    "ابحث", "يوتيوب", "موسيقى", "اغاني", "نغمة"
]

@app.on_message(filters.command(SEARCH_COMMANDS) & ~filters.bot)
async def handle_search_command(client, message):
    """معالج أوامر البحث الرئيسي"""
    try:
        # استخراج النص
        command = message.command[0] if message.command else ""
        query = " ".join(message.command[1:]) if len(message.command) > 1 else ""
        
        # إذا لم يكن هناك استعلام، استخدم النص بعد الأمر
        if not query and message.text:
            text_parts = message.text.split(maxsplit=1)
            query = text_parts[1] if len(text_parts) > 1 else ""
        
        if not query:
            await message.reply_text(
                "📝 **الاستخدام:**\n"
                f"• `/{command} اسم الأغنية`\n"
                f"• `{command} اسم الفنان - اسم الأغنية`\n\n"
                "**مثال:**\n"
                f"`/{command} عمرو دياب نور العين`"
            )
            return
        
        # استيراد وتشغيل المعالج المحسن
        try:
            from ZeMusic.plugins.play.download_enhanced import download_enhanced_song
            await download_enhanced_song(message, query)
            LOGGER(__name__).info(f"✅ تم تشغيل البحث المحسن: {query}")
        except ImportError:
            try:
                from ZeMusic.plugins.play.download import download_song_smart
                await download_song_smart(message, query)
                LOGGER(__name__).info(f"✅ تم تشغيل البحث الأساسي: {query}")
            except ImportError:
                await message.reply_text(
                    "❌ **خطأ في النظام**\n\n"
                    "المعالجات غير متاحة حالياً\n"
                    "يرجى المحاولة لاحقاً"
                )
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في تشغيل المعالج: {e}")
            await message.reply_text(
                "❌ **خطأ في البحث**\n\n"
                "حدث خطأ أثناء معالجة طلبك\n"
                "يرجى المحاولة مرة أخرى"
            )
            
    except Exception as e:
        LOGGER(__name__).error(f"خطأ في معالج البحث: {e}")
        await message.reply_text(
            "❌ **خطأ في البحث**\n\n"
            "حدث خطأ أثناء معالجة طلبك\n"
            "يرجى المحاولة مرة أخرى"
        )

# معالج للرسائل العادية التي تبدأ بكلمات البحث
@app.on_message(filters.text & ~filters.command(SEARCH_COMMANDS) & ~filters.bot)
async def handle_text_search(client, message):
    """معالج للرسائل النصية التي تحتوي على أوامر البحث"""
    try:
        if not message.text:
            return
            
        text = message.text.strip()
        text_lower = text.lower()
        
        # فحص إذا كانت الرسالة تبدأ بكلمة بحث
        for cmd in SEARCH_COMMANDS:
            if text_lower.startswith(cmd.lower() + " "):
                query = text[len(cmd):].strip()
                
                if query:
                    # استيراد وتشغيل المعالج المحسن
                    try:
                        from ZeMusic.plugins.play.download_enhanced import download_enhanced_song
                        await download_enhanced_song(message, query)
                        LOGGER(__name__).info(f"✅ تم تشغيل البحث النصي المحسن: {query}")
                    except ImportError:
                        try:
                            from ZeMusic.plugins.play.download import download_song_smart
                            await download_song_smart(message, query)
                            LOGGER(__name__).info(f"✅ تم تشغيل البحث النصي الأساسي: {query}")
                        except ImportError:
                            await message.reply_text(
                                "❌ **خطأ في النظام**\n\n"
                                "المعالجات غير متاحة حالياً\n"
                                "يرجى المحاولة لاحقاً"
                            )
                    except Exception as e:
                        LOGGER(__name__).error(f"خطأ في تشغيل المعالج النصي: {e}")
                        await message.reply_text(
                            "❌ **خطأ في البحث**\n\n"
                            "حدث خطأ أثناء معالجة طلبك\n"
                            "يرجى المحاولة مرة أخرى"
                        )
                    return
                    
    except Exception as e:
        LOGGER(__name__).error(f"خطأ في معالج البحث النصي: {e}")

LOGGER(__name__).info("✅ تم تحميل معالج أوامر البحث")
