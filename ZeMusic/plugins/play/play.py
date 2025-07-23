# -*- coding: utf-8 -*-
"""
🎵 نظام التشغيل الذكي المحسن - النسخة المتطورة V3
===================================================
متكامل مع النظام المختلط المحسن (YouTube API + yt-dlp)
يدعم التشغيل المتوازي والذكي مع إحصائيات شاملة
"""

import asyncio
import random
import string
import time
from typing import Dict, Optional, Union

# استيراد مكتبات Pyrogram
from ZeMusic.pyrogram_compatibility import filters
from ZeMusic.pyrogram_compatibility import InlineKeyboardMarkup, InputMediaPhoto, Message
from pytgcalls.exceptions import NoActiveGroupCall

# استيراد إعدادات البوت
import config
from ZeMusic import Apple, Resso, SoundCloud, Spotify, Telegram, YouTube, app, LOGGER
from ZeMusic.core.call import Mody
from ZeMusic.utils import seconds_to_min, time_to_seconds
from ZeMusic.utils.channelplay import get_channeplayCB
from ZeMusic.utils.decorators.language import languageCB
from ZeMusic.utils.decorators.play import PlayWrapper
from ZeMusic.utils.formatters import formats
from ZeMusic.utils.inline import (
    botplaylist_markup,
    livestream_markup,
    playlist_markup,
    slider_markup,
    track_markup,
)
from ZeMusic.utils.logger import play_logs
from ZeMusic.utils.stream.stream import stream
from config import lyrical
from ZeMusic.pyrogram_compatibility import BANNED_USERS

# استيراد النظام المختلط المحسن
from .download import (
    download_song_smart,
    update_performance_stats,
    log_performance_stats,
    cleanup_old_downloads
)
from .youtube_api_downloader import get_hybrid_stats

# متغيرات النظام المحسن
system_stats = {
    'total_play_requests': 0,
    'successful_plays': 0,
    'failed_plays': 0,
    'cache_hits': 0,
    'hybrid_downloads': 0,
    'start_time': time.time()
}

# إحصائيات التشغيل
play_stats = {
    'total_requests': 0,
    'successful_plays': 0,
    'failed_plays': 0,
    'cache_hits': 0,
    'hybrid_downloads': 0,
    'start_time': time.time()
}

def update_play_stats(success: bool, from_cache: bool = False, hybrid_used: bool = False):
    """تحديث إحصائيات التشغيل"""
    play_stats['total_requests'] += 1
    if success:
        play_stats['successful_plays'] += 1
    else:
        play_stats['failed_plays'] += 1
    if from_cache:
        play_stats['cache_hits'] += 1
    if hybrid_used:
        play_stats['hybrid_downloads'] += 1

async def get_play_statistics() -> Dict:
    """الحصول على إحصائيات التشغيل الشاملة"""
    uptime = time.time() - system_stats['start_time']
    hybrid_stats = await get_hybrid_stats()
    
    return {
        'system_stats': system_stats,
        'play_stats': play_stats,
        'uptime_hours': uptime / 3600,
        'success_rate': (play_stats['successful_plays'] / max(1, play_stats['total_requests'])) * 100,
        'cache_hit_rate': (play_stats['cache_hits'] / max(1, play_stats['total_requests'])) * 100,
        'hybrid_stats': hybrid_stats
    }

async def smart_music_search_and_play(
    message: Message,
    query: str,
    chat_id: int,
    user_id: int,
    video: bool = False,
    channel: bool = False
) -> Optional[Dict]:
    """البحث والتشغيل الذكي مع النظام المختلط"""
    
    start_time = time.time()
    LOGGER.info(f"🎵 بدء البحث والتشغيل الذكي: {query}")
    
    try:
        # استخدام نظام التحميل الذكي الموجود
        result = await download_song_smart(message, query)
        
        if not result:
            LOGGER.warning(f"❌ فشل البحث والتحميل: {query}")
            update_play_stats(success=False)
            return None
        
        # تحضير معلومات التشغيل من النتيجة
        track_info = {
            'title': result.get('title', query),
            'duration': result.get('duration', 0),
            'file_path': result.get('file_path', ''),
            'file_id': result.get('file_id', ''),
            'thumbnail': result.get('thumbnail', ''),
            'channel': result.get('uploader', 'قناة غير محددة'),
            'url': result.get('url', ''),
            'video_id': result.get('video_id', ''),
            'source': result.get('source', 'smart_download')
        }
        
        elapsed = time.time() - start_time
        LOGGER.info(f"✅ تم التحضير للتشغيل في {elapsed:.2f}s: {track_info['title']}")
        
        # تحديث الإحصائيات
        from_cache = result.get('source') in ['database', 'storage_channel']
        hybrid_used = result.get('source') == 'hybrid_api_ytdlp'
        
        update_play_stats(
            success=True, 
            from_cache=from_cache, 
            hybrid_used=hybrid_used
        )
        
        return track_info
        
    except Exception as e:
        elapsed = time.time() - start_time
        LOGGER.error(f"❌ خطأ في البحث والتشغيل ({elapsed:.2f}s): {e}")
        update_play_stats(success=False)
        return None

# اسم البوت للأوامر
Nem = config.BOT_NAME + " شغل"

@app.on_message(
    filters.command([
        "play", "تشغيل", "شغل", Nem, "vplay", "cplay", "cvplay",
        "playforce", "vplayforce", "cplayforce", "cvplayforce",
    ]) & ~BANNED_USERS
)
@PlayWrapper
async def enhanced_play_command(
    client,
    message: Message,
    _,
    chat_id,
    video,
    channel,
    playmode,
    url,
    fplay,
):
    """أمر التشغيل المحسن مع النظام المختلط"""
    
    start_time = time.time()
    
    # رسالة الحالة الأولية
    mystic = await message.reply_text(
        _["play_2"], disable_web_page_preview=True
    )
    
    try:
        # التحقق من وجود استعلام
        if not message.command or len(message.command) < 2:
            await mystic.edit_text(_["play_3"])
            return
        
        query = " ".join(message.command[1:]).strip()
        if not query:
            await mystic.edit_text(_["play_3"])
            return
        
        LOGGER.info(f"🎵 طلب تشغيل جديد: {query} | المستخدم: {message.from_user.id}")
        
        # تحديث رسالة الحالة
        await mystic.edit_text(_["play_1"])
        
        # البحث والتحميل الذكي
        track_info = await smart_music_search_and_play(
            message=message,
            query=query,
            chat_id=chat_id,
            user_id=message.from_user.id,
            video=video,
            channel=channel
        )
        
        if not track_info:
            await mystic.edit_text(_["play_4"])
            return
        
        # تحديث رسالة الحالة
        await mystic.edit_text(_["play_5"])
        
        # تحضير مصدر التشغيل
        if track_info.get('file_id'):
            # التشغيل من file_id
            source = track_info['file_id']
            source_type = "telegram"
        elif track_info.get('file_path'):
            # التشغيل من ملف محلي
            source = track_info['file_path']
            source_type = "local"
        elif track_info.get('url'):
            # التشغيل من URL
            source = track_info['url']
            source_type = "url"
        else:
            await mystic.edit_text("❌ لا يمكن العثور على مصدر للتشغيل")
            return
        
        # معلومات المسار للتشغيل
        track_details = {
            "title": track_info['title'],
            "duration_min": seconds_to_min(track_info.get('duration', 0)),
            "duration_sec": track_info.get('duration', 0),
            "videoid": track_info.get('video_id', 'unknown'),
            "track": source,
            "view": "غير محدد",
            "played": 0,
            "channel": track_info.get('channel', 'غير محدد'),
            "thumb": track_info.get('thumbnail', ''),
            "source_type": source_type,
            "hybrid_source": track_info.get('source', 'unknown')
        }
        
        # بدء التشغيل
        try:
            await stream(
                _,
                mystic,
                message.from_user.id,
                track_details,
                chat_id,
                message.from_user.first_name,
                message.chat.id,
                video,
                streamtype="youtube" if source_type == "url" else "telegram",
            )
            
            # تسجيل نجاح التشغيل
            elapsed = time.time() - start_time
            LOGGER.info(
                f"✅ تم بدء التشغيل بنجاح ({elapsed:.2f}s): {track_info['title']} | "
                f"المصدر: {track_info.get('source', 'unknown')} | "
                f"النوع: {source_type}"
            )
            
            # تسجيل إحصائيات التشغيل
            await play_logs(message, streamtype="Smart Enhanced")
            
        except NoActiveGroupCall:
            await mystic.edit_text(
                "❌ لا يوجد مكالمة صوتية نشطة في هذه المجموعة.\n"
                "يرجى بدء مكالمة صوتية أولاً."
            )
            
        except Exception as stream_error:
            LOGGER.error(f"❌ خطأ في بدء التشغيل: {stream_error}")
            await mystic.edit_text(f"❌ خطأ في بدء التشغيل: {stream_error}")
            
    except Exception as e:
        elapsed = time.time() - start_time
        LOGGER.error(f"❌ خطأ في أمر التشغيل ({elapsed:.2f}s): {e}")
        
        try:
            await mystic.edit_text(
                f"❌ حدث خطأ أثناء معالجة طلبك:\n`{str(e)[:100]}...`"
            )
        except:
            pass

@app.on_message(filters.command(["playstats", "إحصائيات التشغيل"]) & ~BANNED_USERS)
async def play_statistics_command(client, message: Message):
    """عرض إحصائيات التشغيل الشاملة"""
    
    try:
        stats = await get_play_statistics()
        
        # تنسيق الإحصائيات
        play_data = stats['play_stats']
        uptime_hours = stats['uptime_hours']
        success_rate = stats['success_rate']
        cache_hit_rate = stats['cache_hit_rate']
        
        stats_text = f"""
📊 **إحصائيات التشغيل الشاملة**
{'='*35}

🎵 **إحصائيات التشغيل:**
• إجمالي الطلبات: `{play_data['total_requests']}`
• تشغيل ناجح: `{play_data['successful_plays']}`
• تشغيل فاشل: `{play_data['failed_plays']}`
• معدل النجاح: `{success_rate:.1f}%`

💾 **إحصائيات الكاش:**
• إصابات الكاش: `{play_data['cache_hits']}`
• معدل الكاش: `{cache_hit_rate:.1f}%`
• تحميل مختلط: `{play_data['hybrid_downloads']}`

⏱️ **معلومات النظام:**
• وقت التشغيل: `{uptime_hours:.1f}` ساعة
• متوسط الطلبات/ساعة: `{play_data['total_requests'] / max(0.1, uptime_hours):.1f}`

🔗 **النظام المختلط:**
"""
        
        # إضافة إحصائيات النظام المختلط
        hybrid_data = stats.get('hybrid_stats', {})
        if hybrid_data:
            dl_stats = hybrid_data.get('download_stats', {})
            stats_text += f"""• بحث API: `{dl_stats.get('api_searches', 0)}`
• تحميل ناجح: `{dl_stats.get('successful_downloads', 0)}`
• تحميل فاشل: `{dl_stats.get('failed_downloads', 0)}`
• عدد الكوكيز: `{hybrid_data.get('cookies_count', 0)}`"""
        
        stats_text += f"\n\n🚀 **النظام يعمل بكفاءة عالية!**"
        
        await message.reply_text(stats_text)
        
    except Exception as e:
        LOGGER.error(f"❌ خطأ في عرض الإحصائيات: {e}")
        await message.reply_text(f"❌ خطأ في جلب الإحصائيات: {e}")

@app.on_message(filters.command(["cleantemp", "تنظيف الملفات"]) & filters.user(config.OWNER_ID))
async def clean_temp_files_command(client, message: Message):
    """تنظيف الملفات المؤقتة (للمطور فقط)"""
    
    try:
        status_msg = await message.reply_text("🧹 جاري تنظيف الملفات المؤقتة...")
        
        # تنظيف الملفات القديمة
        cleaned_count = await cleanup_old_downloads()
        
        await status_msg.edit_text(
            f"✅ تم تنظيف الملفات القديمة وحذف `{cleaned_count}` ملف!"
        )
        
    except Exception as e:
        LOGGER.error(f"❌ خطأ في تنظيف الملفات: {e}")
        await message.reply_text(f"❌ خطأ في التنظيف: {e}")

# إضافة تنظيف دوري للملفات المؤقتة
async def periodic_cleanup():
    """تنظيف دوري للملفات المؤقتة"""
    while True:
        try:
            await asyncio.sleep(3600)  # كل ساعة
            cleaned = await cleanup_old_downloads()
            if cleaned > 0:
                LOGGER.info(f"🧹 تم تنظيف {cleaned} ملف قديم تلقائياً")
        except Exception as e:
            LOGGER.error(f"❌ خطأ في التنظيف الدوري: {e}")

# بدء التنظيف الدوري
asyncio.create_task(periodic_cleanup())

LOGGER.info("✅ تم تحميل نظام التشغيل الذكي المحسن بنجاح!")
