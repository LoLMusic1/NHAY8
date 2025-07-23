"""
أمر عرض إحصائيات مفاتيح YouTube API
"""

from telethon import events
from ZeMusic.core.telethon_client import telethon_manager
from ZeMusic import LOGGER
import config

@telethon_manager.on(events.NewMessage(pattern=r'^[/!]youtube_stats$'))
async def youtube_api_stats_handler(event):
    """عرض إحصائيات مفاتيح YouTube API"""
    try:
        # التحقق من الصلاحيات
        if event.sender_id != config.OWNER_ID:
            await event.reply("❌ هذا الأمر مخصص للمطور فقط")
            return
        
        # الحصول على الإحصائيات
        try:
            from ZeMusic.plugins.play.youtube_api_downloader import get_downloader_stats
            stats = await get_downloader_stats()
        except ImportError:
            await event.reply("❌ نظام YouTube API غير متاح")
            return
        
        if stats.get('status') == 'no_keys':
            stats_text = "📊 **إحصائيات YouTube API**\n\n"
            stats_text += "❌ **لا توجد مفاتيح API محددة**\n\n"
            stats_text += "💡 **لإضافة مفاتيح:**\n"
            stats_text += "1. احصل على مفاتيح من Google Cloud Console\n"
            stats_text += "2. أضفها في ملف config.py\n"
            stats_text += "3. أعد تشغيل البوت"
            
        elif stats.get('status') == 'not_initialized':
            stats_text = "📊 **إحصائيات YouTube API**\n\n"
            stats_text += "⚠️ **النظام غير مُفعل بعد**\n\n"
            stats_text += "💡 استخدم أمر بحث لتفعيل النظام"
            
        else:
            stats_text = "📊 **إحصائيات YouTube API**\n\n"
            stats_text += f"🔑 **عدد المفاتيح:** {stats['total_keys']}\n"
            stats_text += f"🎯 **المفتاح الحالي:** {stats['current_key']}\n"
            stats_text += f"🍪 **ملفات الكوكيز:** {stats['cookies_available']}\n\n"
            
            stats_text += "📈 **إحصائيات الاستخدام:**\n"
            for key, usage_count in stats['usage_stats'].items():
                error_count = stats['error_stats'].get(key, 0)
                success_rate = ((usage_count - error_count) / usage_count * 100) if usage_count > 0 else 0
                stats_text += f"   • {key}: {usage_count} استخدام ({success_rate:.1f}% نجح)\n"
            
            if any(stats['error_stats'].values()):
                stats_text += "\n⚠️ **الأخطاء:**\n"
                for key, error_count in stats['error_stats'].items():
                    if error_count > 0:
                        stats_text += f"   • {key}: {error_count} خطأ\n"
        
        # عرض معلومات إضافية
        stats_text += f"\n🔧 **الإعدادات:**\n"
        stats_text += f"   • مفاتيح في التكوين: {len(config.YT_API_KEYS)}\n"
        stats_text += f"   • ملفات كوكيز: {len(config.COOKIES_FILES)}\n"
        
        await event.reply(stats_text)
        
    except Exception as e:
        LOGGER(__name__).error(f"❌ خطأ في عرض إحصائيات YouTube: {e}")
        await event.reply(f"❌ خطأ في عرض الإحصائيات: {str(e)}")

@telethon_manager.on(events.NewMessage(pattern=r'^[/!]test_youtube_api (.+)'))
async def test_youtube_api_handler(event):
    """اختبار البحث بـ YouTube API"""
    try:
        # التحقق من الصلاحيات
        if event.sender_id != config.OWNER_ID:
            await event.reply("❌ هذا الأمر مخصص للمطور فقط")
            return
        
        query = event.pattern_match.group(1).strip()
        if not query:
            await event.reply("❌ يرجى إدخال كلمة البحث")
            return
        
        status_msg = await event.reply(f"🔍 **اختبار البحث بـ YouTube API:**\n`{query}`")
        
        try:
            from ZeMusic.plugins.play.youtube_api_downloader import get_hybrid_downloader
            downloader = await get_hybrid_downloader()
            
            # البحث فقط (بدون تحميل)
            search_results = await downloader.search_with_api(query, max_results=3)
            
            if search_results and 'items' in search_results:
                results_text = f"✅ **نتائج البحث لـ:** `{query}`\n\n"
                
                for i, item in enumerate(search_results['items'], 1):
                    title = item['snippet']['title']
                    channel = item['snippet']['channelTitle']
                    video_id = item['id']['videoId']
                    
                    results_text += f"**{i}.** {title[:50]}{'...' if len(title) > 50 else ''}\n"
                    results_text += f"   📺 **القناة:** {channel}\n"
                    results_text += f"   🆔 **المعرف:** `{video_id}`\n\n"
                
                # إضافة إحصائيات المفاتيح
                stats = downloader.get_api_stats()
                results_text += f"🔑 **المفتاح المستخدم:** {stats['current_key']}\n"
                
                await status_msg.edit(results_text)
            else:
                await status_msg.edit(f"❌ **لم يتم العثور على نتائج لـ:** `{query}`")
                
        except Exception as api_error:
            await status_msg.edit(f"❌ **خطأ في اختبار API:**\n`{str(api_error)}`")
            
    except Exception as e:
        LOGGER(__name__).error(f"❌ خطأ في اختبار YouTube API: {e}")
        await event.reply(f"❌ خطأ في الاختبار: {str(e)}")

# تسجيل المعالجات
LOGGER(__name__).info("✅ تم تحميل معالجات إحصائيات YouTube API")