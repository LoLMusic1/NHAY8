"""
🔍 معالج البحث المبسط والسريع
===========================
معالج بحث مباشر وسريع للأغاني مع Telethon
"""

import asyncio
import os
import re
from telethon import events, Button
from ZeMusic import bot, LOGGER

@bot.on(events.NewMessage(pattern=r'^/?(بحث|search|song|يوت|اغنية|تحميل|ابحث|يوتيوب|موسيقى|اغاني|نغمة)(\s+(.+))?$'))
async def quick_search_handler(event):
    """معالج البحث السريع والمباشر"""
    try:
        # التحقق من أن المرسل ليس بوت
        if event.sender.bot:
            return
            
        # استخراج الاستعلام
        match = event.pattern_match
        command = match.group(1) if match.group(1) else ""
        query = match.group(3) if match.group(3) else ""
        
        if not query:
            await event.reply(
                f"📝 **الاستخدام:**\n\n"
                f"• `/{command} اسم الأغنية`\n"
                f"• `{command} اسم الفنان - اسم الأغنية`\n\n"
                f"**مثال:**\n"
                f"`{command} عمرو دياب نور العين`"
            )
            return
            
        # رسالة الحالة
        status_msg = await event.reply(
            f"🔍 **البحث عن:** `{query}`\n\n"
            f"⏳ جاري البحث في جميع المصادر..."
        )
        
        LOGGER(__name__).info(f"🔍 تم استقبال طلب بحث: {query} من المستخدم {event.sender_id}")
        
        # محاولة البحث والتحميل
        try:
            # استيراد وتشغيل نظام البحث
            await search_and_download(event, query, status_msg)
            
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في البحث: {e}")
            await status_msg.edit(
                f"❌ **فشل في البحث**\n\n"
                f"**الاستعلام:** `{query}`\n"
                f"**الخطأ:** {str(e)[:100]}...\n\n"
                f"💡 جرب البحث بطريقة أخرى أو أعد المحاولة"
            )
            
    except Exception as e:
        LOGGER(__name__).error(f"خطأ في معالج البحث: {e}")
        try:
            await event.reply(
                "❌ **خطأ في النظام**\n\n"
                "حدث خطأ غير متوقع\n"
                "يرجى المحاولة مرة أخرى"
            )
        except:
            pass

async def search_and_download(event, query: str, status_msg):
    """دالة البحث والتحميل الرئيسية"""
    try:
        # تحديث الحالة
        await status_msg.edit(
            f"🔍 **البحث عن:** `{query}`\n\n"
            f"🎵 جاري البحث في يوتيوب..."
        )
        
        # البحث في يوتيوب
        try:
            from youtubesearchpython import VideosSearch
            
            search = VideosSearch(query, limit=1)
            results = search.result()
            
            if not results.get('result'):
                await status_msg.edit(
                    f"❌ **لم يتم العثور على نتائج**\n\n"
                    f"**الاستعلام:** `{query}`\n\n"
                    f"💡 جرب البحث بكلمات أخرى"
                )
                return
                
            video = results['result'][0]
            video_url = video['link']
            title = video['title']
            duration = video.get('duration', 'غير محدد')
            
            # تحديث الحالة
            await status_msg.edit(
                f"✅ **تم العثور على الأغنية!**\n\n"
                f"🎵 **العنوان:** {title[:50]}...\n"
                f"⏱️ **المدة:** {duration}\n\n"
                f"📥 جاري التحميل..."
            )
            
            LOGGER(__name__).info(f"✅ تم العثور على: {title}")
            
            # تحميل الملف
            await download_audio(event, video_url, title, status_msg)
            
        except ImportError:
            await status_msg.edit(
                "❌ **خطأ في النظام**\n\n"
                "مكتبة البحث غير متاحة\n"
                "يرجى المحاولة لاحقاً"
            )
        except Exception as e:
            LOGGER(__name__).error(f"خطأ في البحث: {e}")
            await status_msg.edit(
                f"❌ **خطأ في البحث**\n\n"
                f"**الخطأ:** {str(e)[:100]}...\n\n"
                f"💡 جرب البحث بطريقة أخرى"
            )
            
    except Exception as e:
        LOGGER(__name__).error(f"خطأ في دالة البحث: {e}")
        raise

async def download_audio(event, video_url: str, title: str, status_msg):
    """تحميل الملف الصوتي"""
    try:
        # محاولة رسالة بسيطة أولاً
        await status_msg.edit(
            f"✅ **تم العثور على الأغنية!**\n\n"
            f"🎵 **العنوان:** {title[:50]}...\n\n"
            f"🔗 **الرابط:** {video_url}\n\n"
            f"📥 يمكنك تحميلها يدوياً من الرابط أعلاه"
        )
        
        LOGGER(__name__).info(f"✅ تم إرسال رابط الأغنية: {title}")
            
    except Exception as e:
        LOGGER(__name__).error(f"خطأ في دالة التحميل: {e}")
        raise

LOGGER(__name__).info("✅ تم تحميل معالج البحث المبسط والسريع")
