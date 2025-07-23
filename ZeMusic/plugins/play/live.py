# -*- coding: utf-8 -*-
"""
🔴 نظام البث المباشر المحسن - النسخة المتطورة V3
===============================================
متكامل مع النظام المختلط المحسن والإحصائيات الشاملة
يدعم البث المباشر الذكي مع تتبع الأداء والجودة
"""

import asyncio
import time
from typing import Dict, Optional

# استيراد مكتبات Pyrogram
from ZeMusic.pyrogram_compatibility import filters
from ZeMusic.pyrogram_compatibility import InlineKeyboardMarkup, InlineKeyboardButton

# استيراد إعدادات البوت
from ZeMusic import YouTube, app, LOGGER
from ZeMusic.utils.channelplay import get_channeplayCB
from ZeMusic.utils.decorators.language import languageCB
from ZeMusic.utils.stream.stream import stream
from ZeMusic.pyrogram_compatibility import BANNED_USERS

# استيراد النظام المحسن
from .download import update_performance_stats, log_performance_stats
from .youtube_api_downloader import get_hybrid_stats, search_youtube_hybrid

# إحصائيات البث المباشر
live_stream_stats = {
    'total_live_requests': 0,
    'successful_streams': 0,
    'failed_streams': 0,
    'active_streams': 0,
    'start_time': time.time()
}

def update_live_stats(success: bool, stream_active: bool = False):
    """تحديث إحصائيات البث المباشر"""
    live_stream_stats['total_live_requests'] += 1
    if success:
        live_stream_stats['successful_streams'] += 1
        if stream_active:
            live_stream_stats['active_streams'] += 1
    else:
        live_stream_stats['failed_streams'] += 1

async def get_live_stream_info(video_id: str) -> Optional[Dict]:
    """الحصول على معلومات البث المباشر مع التحقق المحسن"""
    
    start_time = time.time()
    LOGGER.info(f"🔴 جلب معلومات البث المباشر: {video_id}")
    
    try:
        # محاولة 1: استخدام YouTube API المختلط
        try:
            from .youtube_api_downloader import hybrid_downloader
            api_result = await hybrid_downloader.get_video_info(video_id)
            
            if api_result and api_result.get('live_status') == 'is_live':
                LOGGER.info(f"✅ تم التحقق من البث المباشر عبر API: {video_id}")
                return {
                    'title': api_result.get('title', 'بث مباشر'),
                    'channel': api_result.get('uploader', 'قناة غير محددة'),
                    'thumbnail': api_result.get('thumbnail', ''),
                    'url': f"https://www.youtube.com/watch?v={video_id}",
                    'is_live': True,
                    'source': 'youtube_api',
                    'duration_min': None  # البث المباشر لا يحتوي على مدة
                }
        except Exception as api_error:
            LOGGER.warning(f"⚠️ فشل في استخدام YouTube API: {api_error}")
        
        # محاولة 2: استخدام YouTube التقليدي
        try:
            details, track_id = await YouTube.track(video_id, True)
            
            # التحقق من أن هذا بث مباشر
            if not details.get("duration_min"):
                LOGGER.info(f"✅ تم التحقق من البث المباشر عبر YouTube: {video_id}")
                return {
                    'title': details.get('title', 'بث مباشر'),
                    'channel': details.get('channel', 'قناة غير محددة'),
                    'thumbnail': details.get('thumb', ''),
                    'url': details.get('link', f"https://www.youtube.com/watch?v={video_id}"),
                    'is_live': True,
                    'source': 'youtube_traditional',
                    'duration_min': None,
                    'track_id': track_id
                }
            else:
                LOGGER.warning(f"⚠️ الفيديو ليس بث مباشر: {video_id}")
                return None
                
        except Exception as yt_error:
            LOGGER.error(f"❌ خطأ في YouTube التقليدي: {yt_error}")
        
        elapsed = time.time() - start_time
        LOGGER.error(f"❌ فشل في جلب معلومات البث المباشر ({elapsed:.2f}s): {video_id}")
        return None
        
    except Exception as e:
        elapsed = time.time() - start_time
        LOGGER.error(f"❌ خطأ عام في جلب معلومات البث ({elapsed:.2f}s): {e}")
        return None

async def enhanced_live_stream_handler(
    callback_query,
    video_id: str,
    user_id: int,
    mode: str,
    chat_id: int,
    channel: str,
    force_play: bool = False
) -> bool:
    """معالج البث المباشر المحسن"""
    
    start_time = time.time()
    user_name = callback_query.from_user.first_name
    video = True if mode == "v" else None
    
    # رسالة الحالة
    mystic = await callback_query.message.reply_text(
        f"🔴 **جاري تحضير البث المباشر...**\n"
        f"📺 **القناة:** `{channel if channel else 'المجموعة'}`\n"
        f"👤 **المستخدم:** `{user_name}`"
    )
    
    try:
        # الحصول على معلومات البث المباشر
        await mystic.edit_text(
            f"🔍 **جاري التحقق من البث المباشر...**\n"
            f"🔗 **معرف الفيديو:** `{video_id}`"
        )
        
        stream_info = await get_live_stream_info(video_id)
        
        if not stream_info:
            update_live_stats(success=False)
            await mystic.edit_text(
                "❌ **خطأ في البث المباشر**\n"
                "• الرابط غير صحيح أو البث غير متاح\n"
                "• تأكد من أن الرابط يحتوي على بث مباشر نشط"
            )
            return False
        
        # تحديث رسالة الحالة
        await mystic.edit_text(
            f"✅ **تم العثور على البث المباشر**\n"
            f"🎵 **العنوان:** `{stream_info['title'][:50]}...`\n"
            f"📺 **القناة:** `{stream_info['channel'][:30]}...`\n"
            f"🔴 **الحالة:** بث مباشر نشط\n"
            f"⚡ **جاري بدء التشغيل...**"
        )
        
        # بدء البث المباشر
        try:
            # تحضير تفاصيل البث للتشغيل
            stream_details = {
                "title": stream_info['title'],
                "duration_min": stream_info['duration_min'],
                "thumb": stream_info['thumbnail'],
                "videoid": video_id,
                "link": stream_info['url'],
                "channel": stream_info['channel'],
                "track": stream_info['url'],
                "view": "بث مباشر",
                "played": 0,
                "source": stream_info['source']
            }
            
            await stream(
                _=None,  # سيتم تمريره من المعالج الأصلي
                mystic=mystic,
                user_id=user_id,
                details=stream_details,
                chat_id=chat_id,
                user_name=user_name,
                message_chat_id=callback_query.message.chat.id,
                video=video,
                streamtype="live",
                forceplay=force_play,
            )
            
            # تحديث الإحصائيات
            elapsed = time.time() - start_time
            update_live_stats(success=True, stream_active=True)
            await update_performance_stats(True, elapsed, False)
            
            LOGGER.info(
                f"✅ تم بدء البث المباشر بنجاح ({elapsed:.2f}s): {stream_info['title']} | "
                f"المصدر: {stream_info['source']} | المستخدم: {user_name}"
            )
            
            # حذف رسالة الحالة
            await mystic.delete()
            return True
            
        except Exception as stream_error:
            update_live_stats(success=False)
            elapsed = time.time() - start_time
            await update_performance_stats(False, elapsed, False)
            
            LOGGER.error(f"❌ خطأ في بدء البث المباشر: {stream_error}")
            
            await mystic.edit_text(
                f"❌ **فشل في بدء البث المباشر**\n"
                f"📋 **السبب:** `{str(stream_error)[:100]}...`\n"
                f"💡 **الحل:** جرب مرة أخرى أو استخدم رابط آخر"
            )
            return False
            
    except Exception as e:
        elapsed = time.time() - start_time
        update_live_stats(success=False)
        await update_performance_stats(False, elapsed, False)
        
        LOGGER.error(f"❌ خطأ عام في معالج البث المباشر ({elapsed:.2f}s): {e}")
        
        try:
            await mystic.edit_text(
                f"❌ **خطأ في معالجة البث المباشر**\n"
                f"📋 **التفاصيل:** `{str(e)[:80]}...`\n"
                f"⏱️ **الوقت:** `{elapsed:.2f}s`"
            )
        except:
            pass
        
        return False

@app.on_callback_query(filters.regex("LiveStream") & ~BANNED_USERS)
@languageCB
async def enhanced_live_stream_callback(client, CallbackQuery, _):
    """معالج callback البث المباشر المحسن"""
    
    start_time = time.time()
    
    try:
        # تحليل البيانات
        callback_data = CallbackQuery.data.strip()
        callback_request = callback_data.split(None, 1)[1]
        vidid, user_id, mode, cplay, fplay = callback_request.split("|")
        
        # التحقق من صلاحية المستخدم
        if CallbackQuery.from_user.id != int(user_id):
            try:
                return await CallbackQuery.answer(
                    "❌ هذا الزر مخصص لمستخدم آخر!", 
                    show_alert=True
                )
            except:
                return
        
        # الحصول على معلومات القناة
        try:
            chat_id, channel = await get_channeplayCB(_, cplay, CallbackQuery)
        except Exception as channel_error:
            LOGGER.error(f"❌ خطأ في الحصول على معلومات القناة: {channel_error}")
            return await CallbackQuery.answer(
                "❌ خطأ في الحصول على معلومات القناة", 
                show_alert=True
            )
        
        # حذف الرسالة الأصلية والرد
        await CallbackQuery.message.delete()
        try:
            await CallbackQuery.answer("🔴 جاري تحضير البث المباشر...")
        except:
            pass
        
        # تحديد الإعدادات
        force_play = True if fplay == "f" else False
        
        # بدء معالجة البث المباشر المحسن
        success = await enhanced_live_stream_handler(
            callback_query=CallbackQuery,
            video_id=vidid,
            user_id=int(user_id),
            mode=mode,
            chat_id=chat_id,
            channel=channel,
            force_play=force_play
        )
        
        elapsed = time.time() - start_time
        
        if success:
            LOGGER.info(f"✅ تم إكمال callback البث المباشر بنجاح ({elapsed:.2f}s)")
        else:
            LOGGER.warning(f"⚠️ فشل في callback البث المباشر ({elapsed:.2f}s)")
            
    except Exception as e:
        elapsed = time.time() - start_time
        LOGGER.error(f"❌ خطأ في callback البث المباشر ({elapsed:.2f}s): {e}")
        
        try:
            await CallbackQuery.answer(
                f"❌ خطأ في معالجة البث المباشر: {str(e)[:50]}...", 
                show_alert=True
            )
        except:
            pass

# أمر لعرض إحصائيات البث المباشر
@app.on_message(filters.command(["livestats", "إحصائيات البث المباشر"]) & ~BANNED_USERS)
async def live_stream_statistics(client, message):
    """عرض إحصائيات البث المباشر"""
    
    try:
        # حساب الإحصائيات
        uptime = time.time() - live_stream_stats['start_time']
        success_rate = (
            live_stream_stats['successful_streams'] / 
            max(1, live_stream_stats['total_live_requests'])
        ) * 100
        
        # الحصول على إحصائيات النظام المختلط
        hybrid_stats = await get_hybrid_stats()
        
        stats_text = f"""
🔴 **إحصائيات البث المباشر**
{'='*35}

📊 **إحصائيات عامة:**
• إجمالي الطلبات: `{live_stream_stats['total_live_requests']}`
• بث ناجح: `{live_stream_stats['successful_streams']}`
• بث فاشل: `{live_stream_stats['failed_streams']}`
• معدل النجاح: `{success_rate:.1f}%`

🔴 **البث النشط:**
• عدد البث النشط: `{live_stream_stats['active_streams']}`
• وقت التشغيل: `{uptime / 3600:.1f}` ساعة

🔗 **النظام المختلط:**
• مفاتيح API: `{len(hybrid_stats.get('api_keys_stats', {}))}`
• الكوكيز المتاح: `{hybrid_stats.get('cookies_count', 0)}`

⏱️ **معلومات النظام:**
• متوسط الطلبات/ساعة: `{live_stream_stats['total_live_requests'] / max(0.1, uptime / 3600):.1f}`
• آخر تحديث: `{time.strftime('%H:%M:%S')}`

🚀 **النظام يعمل بكفاءة عالية!**
"""
        
        await message.reply_text(stats_text)
        
    except Exception as e:
        LOGGER.error(f"❌ خطأ في عرض إحصائيات البث المباشر: {e}")
        await message.reply_text(f"❌ خطأ في جلب الإحصائيات: {e}")

# أمر لاختبار البث المباشر
@app.on_message(filters.command(["testlive", "اختبار البث المباشر"]) & ~BANNED_USERS)
async def test_live_stream(client, message):
    """اختبار البث المباشر"""
    
    try:
        if len(message.command) < 2:
            await message.reply_text(
                "📝 **كيفية الاستخدام:**\n"
                "`/testlive [معرف الفيديو أو الرابط]`\n\n"
                "**مثال:**\n"
                "`/testlive dQw4w9WgXcQ`"
            )
            return
        
        video_input = message.command[1]
        
        # استخراج معرف الفيديو من الرابط إذا لزم الأمر
        if "youtube.com/watch?v=" in video_input:
            video_id = video_input.split("v=")[1].split("&")[0]
        elif "youtu.be/" in video_input:
            video_id = video_input.split("/")[-1].split("?")[0]
        else:
            video_id = video_input
        
        status_msg = await message.reply_text(
            f"🔍 **جاري اختبار البث المباشر...**\n"
            f"🔗 **معرف الفيديو:** `{video_id}`"
        )
        
        # اختبار الحصول على معلومات البث
        stream_info = await get_live_stream_info(video_id)
        
        if stream_info:
            await status_msg.edit_text(
                f"✅ **نتيجة الاختبار: نجح**\n\n"
                f"🎵 **العنوان:** `{stream_info['title'][:50]}...`\n"
                f"📺 **القناة:** `{stream_info['channel'][:30]}...`\n"
                f"🔴 **الحالة:** بث مباشر نشط\n"
                f"🔗 **المصدر:** `{stream_info['source']}`\n"
                f"📱 **الرابط:** `{stream_info['url'][:50]}...`\n\n"
                f"🎯 **البث جاهز للتشغيل!**"
            )
        else:
            await status_msg.edit_text(
                f"❌ **نتيجة الاختبار: فشل**\n\n"
                f"🔗 **معرف الفيديو:** `{video_id}`\n"
                f"📋 **السبب:** البث غير متاح أو الرابط غير صحيح\n\n"
                f"💡 **اقتراحات:**\n"
                f"• تأكد من أن الرابط صحيح\n"
                f"• تأكد من أن البث مباشر ونشط\n"
                f"• جرب رابط آخر"
            )
        
    except Exception as e:
        LOGGER.error(f"❌ خطأ في اختبار البث المباشر: {e}")
        await message.reply_text(f"❌ خطأ في الاختبار: {e}")

LOGGER.info("✅ تم تحميل نظام البث المباشر المحسن بنجاح!")
