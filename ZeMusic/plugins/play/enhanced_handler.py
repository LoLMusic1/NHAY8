# -*- coding: utf-8 -*-
"""
🎵 المعالج المطور للتحميل الذكي مع Telethon
=============================================

يدمج النظام الجديد مع المعالج الحالي
"""

import os
import asyncio
from pathlib import Path
from typing import Optional, Dict
from telethon import events
from telethon.types import Message
from telethon.tl.types import DocumentAttributeAudio

import config
from ZeMusic.core.telethon_client import telethon_manager
from ZeMusic.logging import LOGGER
from ZeMusic.utils.database import is_search_enabled, is_search_enabled1

# استيراد النظام المطور
from ZeMusic.plugins.play.download import (
    downloader
)

async def create_fallback_audio(query: str) -> Optional[Dict]:
    """إنشاء ملف صوتي وهمي للاختبار في حالة الفشل التام"""
    try:
        import os
        import subprocess
        from datetime import datetime
        
        # إنشاء ملف صوتي قصير (5 ثوان صمت) باستخدام ffmpeg
        fallback_id = f"fallback_{int(datetime.now().timestamp())}"
        audio_path = f"downloads/{fallback_id}.mp3"
        
        # إنشاء ملف صمت 5 ثوان
        cmd = [
            'ffmpeg', '-f', 'lavfi', '-i', 'anullsrc=r=44100:cl=stereo', 
            '-t', '5', '-c:a', 'libmp3lame', '-b:a', '128k', 
            audio_path, '-y'
        ]
        
        # محاولة تشغيل ffmpeg
        result = subprocess.run(cmd, capture_output=True, timeout=10)
        
        if result.returncode == 0 and os.path.exists(audio_path):
            return {
                "audio_path": audio_path,
                "title": f"تنبيه: {query[:30]}...",
                "artist": "البوت",
                "duration": 5,
                "file_size": os.path.getsize(audio_path),
                "video_id": fallback_id,
                "source": "fallback_silence",
                "quality": "test",
                "download_time": 0
            }
    
    except Exception as e:
        LOGGER(__name__).warning(f"فشل إنشاء ملف احتياطي: {e}")
    
    return None

async def enhanced_smart_download_handler(event):
    """المعالج المطور للتحميل الذكي مع Telethon"""
    
    # التحقق من أن هذه رسالة وليس callback
    if not hasattr(event, 'message') or not event.message or not event.message.text:
        return
    
    # تجنب معالجة الرسائل القديمة
    if hasattr(event.message, 'date'):
        from datetime import datetime, timezone
        try:
            now = datetime.now(timezone.utc)
            message_date = event.message.date
            if hasattr(message_date, 'replace'):
                if message_date.tzinfo is None:
                    message_date = message_date.replace(tzinfo=timezone.utc)
            
            if (now - message_date).total_seconds() > 30:
                return
        except Exception:
            pass
    
    text = event.message.text.lower().strip()
    
    # فلترة أوامر البحث المحسنة
    is_search_command = False
    search_commands = ["بحث ", "/song ", "song ", "يوت ", config.BOT_NAME + " ابحث"]
    for cmd in search_commands:
        if text.startswith(cmd.lower()):
            is_search_command = True
            break
    
    if " بحث " in text or text == "بحث":
        is_search_command = True
    
    # التوقف هنا إذا لم يكن أمر بحث
    if not is_search_command:
        return
    
    # التحقق من تفعيل الخدمة
    try:
        chat_id = event.chat_id
        user_id = event.sender_id
        
        # فحص نوع المحادثة
        if hasattr(event, 'is_private') and event.is_private:
            # محادثة خاصة
            if not await is_search_enabled1():
                await event.reply("⟡ عذراً عزيزي، اليوتيوب معطل من قبل المطور")
                return
        else:
            # مجموعة أو قناة
            if not await is_search_enabled():
                await event.reply("⟡ عذراً عزيزي، اليوتيوب معطل من قبل المطور")
                return
    except Exception as e:
        LOGGER(__name__).warning(f"فشل فحص تفعيل الخدمة: {e}")
        # المتابعة بدون فحص إذا فشل
    
    # استخراج الاستعلام المحسن
    query = text
    for cmd in search_commands:
        if text.startswith(cmd.lower()):
            query = text[len(cmd):].strip()
            break
    
    # إزالة "بحث" إذا كانت منفصلة
    if " بحث " in query:
        query = query.replace(" بحث ", " ").strip()
    elif query == "بحث":
        query = ""
    
    if not query:
        await event.reply("📝 **الاستخدام:** `بحث اسم الأغنية`")
        return
    
    # رسالة المعالجة المحسنة
    status_msg = await event.reply("⚡ **جاري المعالجة بالنظام الذكي المطور...**\n\n🔍 البحث في التخزين السريع...")
    
    try:
        # التحديد التلقائي للجودة بناء على نوع المحادثة
        quality = "medium"  # افتراضي
        
        # إذا كانت محادثة خاصة، جودة أعلى
        if hasattr(event, 'is_private') and event.is_private:
            quality = "high"
        # إذا كانت مجموعة كبيرة، جودة أقل
        elif hasattr(event, 'is_group') and event.is_group:
            try:
                chat_info = await telethon_manager.bot_client.get_entity(chat_id)
                if hasattr(chat_info, 'participants_count') and chat_info.participants_count > 1000:
                    quality = "low"
            except:
                pass
        
        # تحديث رسالة الحالة
        await status_msg.edit("⚡ **النظام الذكي المطور**\n\n🔍 بحث متقدم في جميع المصادر...")
        
        # التحميل بالنظام الخارق المطور
        result = await downloader.hyper_download(query, quality)
        
        if not result:
            # محاولة أخيرة: إنشاء ملف تنبيه
            fallback_result = await create_fallback_audio(query)
            if fallback_result:
                await status_msg.edit("⚠️ **تم إنشاء ملف تنبيه**\n\n🔊 لم يتم العثور على الملف الصوتي، تم إنشاء ملف تنبيه بدلاً منه")
                result = fallback_result
            else:
                await status_msg.edit("❌ **فشل في العثور على النتائج**\n\n💡 جرب:\n• كلمات مختلفة\n• اسم الفنان\n• عنوان أوضح\n\n🔧 **تفاصيل تقنية:**\n• جميع خوادم التحميل معطلة حالياً\n• يرجى المحاولة لاحقاً")
                return
        
        # التحقق الإضافي من صحة النتيجة
        if not isinstance(result, dict):
            await status_msg.edit("❌ **خطأ في البيانات:** النتيجة غير صحيحة\n\n💡 جرب البحث مرة أخرى")
            LOGGER(__name__).error(f"نتيجة غير صحيحة: {type(result)} - {result}")
            return
        
        # تحديث الرسالة مع معلومات مفصلة
        source_emojis = {
            'cache_direct': '⚡ كاش فوري',
            'cache_fuzzy': '🔍 كاش ذكي',
            'youtube_api': '🔍 YouTube API',
            'invidious_yewtu.be': '🌐 Invidious (YewTu)',
            'invidious_invidious.io': '🌐 Invidious (IO)',
            'ytdlp_cookies': '🍪 تحميل مع كوكيز',
            'ytdlp_no_cookies': '📥 تحميل مباشر',
            'ytdlp_alternative': '🎚️ تحميل بديل',
            'cobalt_api': '🔗 Cobalt API',
            'y2mate_api': '🎵 Y2mate API',
            'savefrom_api': '📁 SaveFrom API',
            'youtube_dl': '📼 YouTube-DL',
            'generic': '🔧 طريقة عامة',
            'local_files': '📁 ملف محلي',
            'fallback_silence': '🔇 ملف تنبيه',
            'youtube_search': '🔎 بحث يوتيوب'
        }
        
        source_text = source_emojis.get(result['source'], result['source'])
        search_method = result.get('search_method', 'unknown')
        total_time = result.get('total_time', 0)
        
        # رسالة بسيطة للتقدم
        progress_text = f"""🎵 **تم العثور على:** {result['title']}
🎤 **{result['artist']}**

⬆️ **جاري إرسال الملف...**"""
        
        await status_msg.edit(progress_text)
        
        # تحديد طريقة الإرسال حسب نوع النتيجة
        if result.get('cached') and result.get('file_id'):
            # إرسال من الكاش
            try:
                # التحقق من صحة file_id
                file_id = result['file_id']
                if file_id and len(str(file_id)) > 10:  # تحقق أساسي من file_id
                    await telethon_manager.bot_client.send_file(
                        entity=event.chat_id,
                        file=file_id,
                        caption=f"💡 **مُحمّل بواسطة:** @{config.BOT_USERNAME}",
                        reply_to=event.message.id,
                        supports_streaming=True
                    )
                    
                    await status_msg.delete()
                    LOGGER(__name__).info(f"✅ تم إرسال من الكاش: {result['title']}")
                    return
                else:
                    LOGGER(__name__).warning(f"file_id غير صحيح: {file_id}")
                    
            except Exception as cache_error:
                LOGGER(__name__).warning(f"فشل إرسال من الكاش: {cache_error}")
                # إعادة التحميل الجديد
                await status_msg.edit(f"{progress_text}\n\n🔄 فشل الكاش، جاري التحميل الجديد...")
                
                # إعادة تحميل بدون استخدام الكاش
                fresh_result = await downloader.download_with_ytdlp(result, quality)
                if not fresh_result or 'audio_path' not in fresh_result:
                    await status_msg.edit("❌ **فشل إعادة التحميل**\n\n💡 جرب البحث مرة أخرى")
                    return
                result = fresh_result
        
        # إذا وصلنا هنا، فالنتيجة يجب أن تحتوي على audio_path
        if 'audio_path' not in result:
            await status_msg.edit("❌ **خطأ:** مشكلة في بيانات التحميل\n\n💡 جرب البحث مرة أخرى")
            LOGGER(__name__).error(f"مفاتيح النتيجة بعد المعالجة: {list(result.keys())}")
            return
        
        # تحميل الصورة المصغرة
        thumb_path = None
        if 'thumb' in result and result['thumb']:
            await status_msg.edit(f"{progress_text}\n\n📸 تحميل الصورة المصغرة...")
            thumb_path = await download_thumbnail(result['thumb'], result['title'])
        
        # تحديث الرسالة قبل الإرسال
        await status_msg.edit(f"{progress_text}\n\n📤 إرسال الملف الصوتي...")
        
        # إرسال الملف الجديد مع Telethon
        try:
                
            audio_path = result['audio_path']
            
            # التأكد من وجود الملف
            if not audio_path or not os.path.exists(audio_path):
                await status_msg.edit("❌ **خطأ:** الملف غير موجود")
                LOGGER(__name__).error(f"مسار الملف غير صحيح: {audio_path}")
                return
            
            # إنشاء DocumentAttributeAudio
            audio_attr = DocumentAttributeAudio(
                duration=result.get('duration', 0),
                title=result['title'],
                performer=result['artist']
            )
            
            # caption بسيط للمستخدم (فقط يوزر البوت)
            caption = f"💡 **مُحمّل بواسطة:** @{config.BOT_USERNAME}"
            
            # إرسال الملف
            with open(audio_path, 'rb') as audio_file:
                await telethon_manager.bot_client.send_file(
                    entity=event.chat_id,
                    file=audio_file,
                    caption=caption,
                    attributes=[audio_attr],
                    thumb=thumb_path,
                    reply_to=event.message.id,
                    supports_streaming=True
                )
            
            # حذف الملفات المؤقتة
            await remove_temp_files(audio_path, thumb_path)
            
            # حذف رسالة المعالجة
            try:
                await status_msg.delete()
            except:
                pass
                
            # تسجيل النجاح
            LOGGER(__name__).info(f"✅ تم إرسال بنجاح: {result['title']} في {total_time:.2f}s")
        
        except Exception as send_error:
            error_msg = str(send_error)
            LOGGER(__name__).error(f"فشل إرسال الملف: {error_msg}")
            
            # رسالة خطأ مفصلة حسب نوع المشكلة
            if 'audio_path' in error_msg:
                await status_msg.edit("❌ **فشل الإرسال:** مشكلة في مسار الملف\n\n💡 جرب البحث مرة أخرى")
            elif 'file not found' in error_msg.lower():
                await status_msg.edit("❌ **فشل الإرسال:** الملف غير موجود\n\n💡 جرب البحث مرة أخرى")
            elif 'permission' in error_msg.lower():
                await status_msg.edit("❌ **فشل الإرسال:** مشكلة في الصلاحيات\n\n💡 تحقق من إعدادات البوت")
            else:
                await status_msg.edit(f"❌ **فشل الإرسال:** خطأ غير متوقع\n\n💡 جرب مرة أخرى\n\n`{error_msg[:100]}...`")
            
            # حذف الملفات المؤقتة حتى لو فشل الإرسال
            try:
                await remove_temp_files(result.get('audio_path'), thumb_path)
            except:
                pass
        
    except Exception as e:
        LOGGER(__name__).error(f"خطأ في المعالج المطور: {e}")
        try:
            await status_msg.edit(f"❌ **خطأ في المعالجة:**\n\n`{str(e)}`\n\n💡 جرب مرة أخرى بعد قليل")
        except:
            pass

# --- أوامر إحصائيات وإدارة محسنة ---
async def enhanced_cache_stats_handler(event):
    """عرض إحصائيات محسنة للتخزين الذكي"""
    try:
        # فحص الصلاحيات
        user_id = event.sender_id
        if user_id != config.OWNER_ID:
            await event.reply("❌ هذا الأمر للمطور فقط")
            return
        
        import sqlite3
        from ZeMusic.plugins.play.download import DB_FILE
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # إحصائيات عامة
        cursor.execute("SELECT COUNT(*) FROM audio_cache")
        total_cached = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(access_count) FROM channel_index")
        total_hits = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT SUM(file_size) FROM channel_index")
        total_size = cursor.fetchone()[0] or 0
        
        cursor.execute("SELECT AVG(download_time) FROM channel_index WHERE download_time > 0")
        avg_download_time = cursor.fetchone()[0] or 0
        
        # أفضل الأغاني
        cursor.execute("""
            SELECT original_title, original_artist, access_count, download_source 
            FROM channel_index 
            ORDER BY access_count DESC 
            LIMIT 5
        """)
        top_songs = cursor.fetchall()
        
        # إحصائيات الأداء
        cursor.execute("""
            SELECT method_name, success_count, failure_count, avg_response_time 
            FROM performance_stats 
            ORDER BY success_count DESC
        """)
        performance_stats = cursor.fetchall()
        
        conn.close()
        
        # إعداد النص
        efficiency = (total_hits / max(1, total_cached)) * 100
        
        stats_text = f"""📊 **إحصائيات التخزين الذكي المطور**

💾 **المحفوظ:** {total_cached:,} ملف
⚡ **مرات الاستخدام:** {total_hits:,}
📈 **كفاءة الكاش:** {efficiency:.1f}%
💽 **الحجم الإجمالي:** {format_file_size(total_size)}
⏱️ **متوسط وقت التحميل:** {avg_download_time:.2f}s

🎵 **الأكثر طلباً:**"""
        
        for i, (title, artist, count, source) in enumerate(top_songs, 1):
            stats_text += f"\n{i}. {title[:25]}... - {artist[:15]} ({count} مرة)"
        
        stats_text += f"\n\n📈 **أداء الطرق:**"
        
        for method, success, failure, avg_time in performance_stats:
            total_attempts = success + failure
            success_rate = (success / max(1, total_attempts)) * 100
            stats_text += f"\n• **{method}:** {success_rate:.1f}% ({avg_time:.2f}s)"
        
        await event.reply(stats_text)
        
    except Exception as e:
        await event.reply(f"❌ خطأ في الإحصائيات: {e}")

async def enhanced_cache_clear_handler(event):
    """مسح محسن للكاش"""
    try:
        # فحص الصلاحيات
        user_id = event.sender_id
        if user_id != config.OWNER_ID:
            await event.reply("❌ هذا الأمر للمطور فقط")
            return
        
        import sqlite3
        from ZeMusic.plugins.play.download import DB_FILE
        
        conn = sqlite3.connect(DB_FILE)
        cursor = conn.cursor()
        
        # عد الملفات قبل المسح
        cursor.execute("SELECT COUNT(*) FROM audio_cache")
        total_before = cursor.fetchone()[0]
        
        cursor.execute("SELECT SUM(file_size) FROM channel_index")
        size_before = cursor.fetchone()[0] or 0
        
        # مسح البيانات
        cursor.execute("DELETE FROM channel_index")
        cursor.execute("UPDATE performance_stats SET success_count = 0, failure_count = 0")
        
        conn.commit()
        conn.close()
        
        await event.reply(f"""🧹 **تم مسح الكاش بنجاح!**

📊 **المحذوف:** {total_before:,} ملف
💽 **المساحة المحررة:** {format_file_size(size_before)}
🔄 **إحصائيات الأداء:** تم إعادة تعيينها

⚡ سيتم إعادة بناء الكاش تلقائياً مع الاستخدام""")
        
    except Exception as e:
        await event.reply(f"❌ خطأ في مسح الكاش: {e}")

LOGGER(__name__).info("🚀 تم تحميل المعالج المطور للتحميل الذكي")