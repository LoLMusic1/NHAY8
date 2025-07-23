#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎵 ZeMusic Bot v3.0 - Enhanced Live Stream Plugin
تاريخ الإنشاء: 2025-01-28

بلاجين البث المباشر المحسن
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any
from telethon import events, Button

import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).parent.parent))
from config import config
from ..core import MusicEngine
from ..platforms import PlatformManager

logger = logging.getLogger(__name__)

class LiveStreamPlugin:
    """بلاجين البث المباشر"""
    
    def __init__(self, client, music_engine: MusicEngine, platform_manager: PlatformManager):
        """تهيئة بلاجين البث المباشر"""
        self.client = client
        self.music_engine = music_engine
        self.platform_manager = platform_manager
        
        # قائمة البثوث المباشرة النشطة
        self.active_streams: Dict[int, Dict[str, Any]] = {}
        
    async def initialize(self) -> bool:
        """تهيئة البلاجين"""
        try:
            logger.info("📺 تهيئة بلاجين البث المباشر...")
            
            # تسجيل معالجات البث المباشر
            await self._register_handlers()
            
            logger.info("✅ تم تهيئة بلاجين البث المباشر بنجاح")
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في تهيئة بلاجين البث المباشر: {e}")
            return False
    
    async def _register_handlers(self):
        """تسجيل معالجات البث المباشر"""
        try:
            # معالج أمر البث المباشر
            @self.client.client.on(events.NewMessage(pattern=r'^[!/.]live'))
            async def handle_live_command(event):
                await self._handle_live_command(event)
            
            # معالج استعلام البث المباشر
            @self.client.client.on(events.CallbackQuery(pattern=b'LiveStream'))
            async def handle_live_callback(event):
                await self._handle_live_callback(event)
            
            logger.info("📝 تم تسجيل معالجات البث المباشر")
            
        except Exception as e:
            logger.error(f"❌ فشل في تسجيل معالجات البث المباشر: {e}")
    
    async def _handle_live_command(self, event):
        """معالجة أمر البث المباشر"""
        try:
            args = event.message.text.split()[1:] if len(event.message.text.split()) > 1 else []
            
            if not args:
                await event.reply(
                    "📺 **البث المباشر**\n\n"
                    "🔍 **الاستخدام:**\n"
                    "• `/live [رابط البث]` - تشغيل بث مباشر\n"
                    "• `/live youtube [كلمة البحث]` - البحث عن بث مباشر في YouTube\n"
                    "• `/live stop` - إيقاف البث المباشر\n\n"
                    "📋 **أمثلة:**\n"
                    "• `/live https://youtube.com/watch?v=...`\n"
                    "• `/live youtube news`"
                )
                return
            
            if args[0].lower() == "stop":
                await self._stop_live_stream(event)
            elif args[0].lower() == "youtube":
                search_query = " ".join(args[1:])
                await self._search_live_youtube(event, search_query)
            elif args[0].startswith(('http://', 'https://')):
                await self._play_live_url(event, args[0])
            else:
                # البحث العام
                search_query = " ".join(args)
                await self._search_live_streams(event, search_query)
                
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة أمر البث المباشر: {e}")
            await event.reply("❌ حدث خطأ في معالجة أمر البث المباشر")
    
    async def _handle_live_callback(self, event):
        """معالجة استعلام البث المباشر"""
        try:
            data = event.data.decode('utf-8')
            parts = data.split('|')
            
            if len(parts) < 5:
                await event.answer("❌ بيانات غير صحيحة", alert=True)
                return
            
            video_id = parts[0].replace('LiveStream ', '')
            user_id = int(parts[1])
            mode = parts[2]  # 'v' للفيديو، 'a' للصوت
            channel_play = parts[3]
            force_play = parts[4]
            
            # التحقق من المستخدم
            if event.sender_id != user_id:
                await event.answer("❌ هذا الزر ليس لك", alert=True)
                return
            
            # تشغيل البث المباشر
            await self._start_live_stream(event, video_id, mode == 'v', force_play == 'f')
            
        except Exception as e:
            logger.error(f"❌ خطأ في معالجة استعلام البث المباشر: {e}")
            await event.answer("❌ حدث خطأ في تشغيل البث المباشر", alert=True)
    
    async def _search_live_youtube(self, event, query: str):
        """البحث عن بث مباشر في YouTube"""
        try:
            if not query:
                await event.reply("❌ يرجى كتابة كلمة البحث")
                return
            
            search_msg = await event.reply("🔍 جاري البحث عن البثوث المباشرة...")
            
            # البحث في YouTube عن البثوث المباشرة
            search_results = await self.platform_manager.search_platform(
                'youtube', f"{query} live stream", 10
            )
            
            if not search_results:
                await search_msg.edit("❌ لم يتم العثور على بثوث مباشرة")
                return
            
            # فلترة البثوث المباشرة فقط
            live_results = []
            for result in search_results:
                if result.get('duration', 0) == 0 or 'live' in result.get('title', '').lower():
                    live_results.append(result)
            
            if not live_results:
                await search_msg.edit("❌ لم يتم العثور على بثوث مباشرة نشطة")
                return
            
            # إنشاء لوحة مفاتيح للنتائج
            keyboard = []
            for i, result in enumerate(live_results[:5]):
                title = result['title'][:50] + "..." if len(result['title']) > 50 else result['title']
                
                callback_data = f"LiveStream {result['id']}|{event.sender_id}|v||f"
                keyboard.append([Button.inline(f"📺 {title}", callback_data.encode())])
            
            keyboard.append([Button.inline("❌ إلغاء", b"close")])
            
            message = (
                "📺 **نتائج البحث - البثوث المباشرة**\n\n"
                f"🔍 **البحث عن:** {query}\n"
                f"📊 **النتائج:** {len(live_results)} بث مباشر\n\n"
                "اختر بثاً مباشراً للتشغيل:"
            )
            
            await search_msg.edit(message, buttons=keyboard)
            
        except Exception as e:
            logger.error(f"❌ خطأ في البحث عن البثوث المباشرة: {e}")
            await event.reply("❌ حدث خطأ في البحث")
    
    async def _play_live_url(self, event, url: str):
        """تشغيل بث مباشر من رابط"""
        try:
            play_msg = await event.reply("📺 جاري تحضير البث المباشر...")
            
            # التحقق من أن الرابط صالح
            if not self._is_valid_stream_url(url):
                await play_msg.edit("❌ رابط البث غير صالح")
                return
            
            # الحصول على معلومات البث
            stream_info = await self._get_stream_info(url)
            
            if not stream_info:
                await play_msg.edit("❌ لا يمكن الحصول على معلومات البث")
                return
            
            # تشغيل البث المباشر
            from ..core.music_engine import TrackInfo
            track = TrackInfo(
                title=stream_info.get('title', 'بث مباشر'),
                url=url,
                duration=0,  # البث المباشر لا يحتوي على مدة
                platform='live_stream',
                thumbnail=stream_info.get('thumbnail', ''),
                artist=stream_info.get('uploader', 'قناة غير معروفة'),
                requested_by=event.sender_id,
                stream_url=stream_info.get('stream_url', url)
            )
            
            result = await self.music_engine.play_track(event.chat_id, track, event.sender_id)
            
            if result['success']:
                # تسجيل البث النشط
                self.active_streams[event.chat_id] = {
                    'title': track.title,
                    'url': url,
                    'started_by': event.sender_id,
                    'started_at': asyncio.get_event_loop().time()
                }
                
                message = (
                    f"📺 **{result['message']}**\n\n"
                    f"📡 **العنوان:** {track.title}\n"
                    f"📺 **القناة:** {track.artist}\n"
                    f"🌐 **المنصة:** بث مباشر\n"
                    f"👨‍💻 **طلبه:** {event.sender.first_name}\n\n"
                    f"⚠️ **ملاحظة:** البثوث المباشرة قد تتوقف تلقائياً إذا انتهت"
                )
                
                keyboard = [
                    [
                        Button.inline("⏸️ إيقاف مؤقت", b"play_pause"),
                        Button.inline("⏹️ إيقاف", b"play_stop")
                    ],
                    [Button.inline("❌ إغلاق", b"close")]
                ]
                
                await play_msg.edit(message, buttons=keyboard)
            else:
                await play_msg.edit(f"❌ {result['message']}")
                
        except Exception as e:
            logger.error(f"❌ خطأ في تشغيل البث المباشر: {e}")
            await event.reply("❌ حدث خطأ في تشغيل البث المباشر")
    
    async def _start_live_stream(self, event, video_id: str, is_video: bool = False, force_play: bool = False):
        """بدء تشغيل البث المباشر"""
        try:
            await event.message.delete()
            
            play_msg = await event.respond("📺 جاري تشغيل البث المباشر...")
            
            # الحصول على معلومات الفيديو
            track_info = await self.platform_manager.get_track_info('youtube', video_id)
            
            if not track_info:
                await play_msg.edit("❌ لم يتم العثور على البث")
                return
            
            # التحقق من أنه بث مباشر
            if track_info.get('duration', 0) > 0:
                await play_msg.edit("❌ هذا ليس بث مباشر")
                return
            
            # تحضير معلومات المقطع
            from ..core.music_engine import TrackInfo
            track = TrackInfo(
                title=track_info['title'],
                url=track_info['url'],
                duration=0,
                platform='youtube',
                thumbnail=track_info.get('thumbnail', ''),
                artist=track_info.get('artist', ''),
                requested_by=event.sender_id
            )
            
            # تشغيل البث
            result = await self.music_engine.play_track(event.chat_id, track, event.sender_id)
            
            if result['success']:
                # تسجيل البث النشط
                self.active_streams[event.chat_id] = {
                    'video_id': video_id,
                    'title': track.title,
                    'started_by': event.sender_id,
                    'started_at': asyncio.get_event_loop().time(),
                    'is_video': is_video
                }
                
                await play_msg.edit(f"📺 **تم بدء البث المباشر**\n\n{track.title}")
            else:
                await play_msg.edit(f"❌ {result['message']}")
                
        except Exception as e:
            logger.error(f"❌ خطأ في بدء البث المباشر: {e}")
            try:
                await event.respond("❌ حدث خطأ في تشغيل البث المباشر")
            except:
                pass
    
    async def _stop_live_stream(self, event):
        """إيقاف البث المباشر"""
        try:
            chat_id = event.chat_id
            
            if chat_id not in self.active_streams:
                await event.reply("❌ لا يوجد بث مباشر نشط")
                return
            
            # إيقاف التشغيل
            result = await self.music_engine.stop_playback(chat_id)
            
            # إزالة من القائمة النشطة
            if chat_id in self.active_streams:
                del self.active_streams[chat_id]
            
            await event.reply(f"📺 {result['message']}")
            
        except Exception as e:
            logger.error(f"❌ خطأ في إيقاف البث المباشر: {e}")
            await event.reply("❌ حدث خطأ في إيقاف البث المباشر")
    
    def _is_valid_stream_url(self, url: str) -> bool:
        """التحقق من صحة رابط البث"""
        try:
            valid_domains = [
                'youtube.com', 'youtu.be', 'twitch.tv', 
                'facebook.com', 'instagram.com', 'tiktok.com'
            ]
            
            from urllib.parse import urlparse
            parsed = urlparse(url)
            
            return any(domain in parsed.netloc for domain in valid_domains)
            
        except Exception:
            return False
    
    async def _get_stream_info(self, url: str) -> Optional[Dict[str, Any]]:
        """الحصول على معلومات البث"""
        try:
            # استخدام yt-dlp للحصول على معلومات البث
            import yt_dlp
            
            ydl_opts = {
                'quiet': True,
                'no_warnings': True,
                'extract_flat': False
            }
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)
                
                return {
                    'title': info.get('title', 'بث مباشر'),
                    'uploader': info.get('uploader', 'قناة غير معروفة'),
                    'thumbnail': info.get('thumbnail', ''),
                    'stream_url': info.get('url', url)
                }
                
        except Exception as e:
            logger.error(f"❌ خطأ في الحصول على معلومات البث: {e}")
            return None
    
    async def get_active_streams(self) -> Dict[int, Dict[str, Any]]:
        """الحصول على البثوث النشطة"""
        return self.active_streams.copy()
    
    async def cleanup_inactive_streams(self):
        """تنظيف البثوث غير النشطة"""
        try:
            current_time = asyncio.get_event_loop().time()
            inactive_chats = []
            
            for chat_id, stream_info in self.active_streams.items():
                # إذا مر أكثر من 6 ساعات على البث
                if current_time - stream_info['started_at'] > 21600:
                    inactive_chats.append(chat_id)
            
            for chat_id in inactive_chats:
                # محاولة إيقاف البث
                try:
                    await self.music_engine.stop_playback(chat_id)
                except:
                    pass
                
                # إزالة من القائمة
                if chat_id in self.active_streams:
                    del self.active_streams[chat_id]
                
                logger.info(f"🧹 تم تنظيف البث غير النشط: {chat_id}")
                
        except Exception as e:
            logger.error(f"❌ خطأ في تنظيف البثوث غير النشطة: {e}")

# إنشاء مثيل عام للبلاجين
live_stream_plugin = None  # سيتم تهيئته في الملف الرئيسي