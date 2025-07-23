#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
⬇️ اختبار التحميل باستخدام YouTube Data API
===========================================
"""

import requests
import json
import os
import time
from datetime import datetime

def search_and_download_test(api_key, query="محمد عبده حبيبتي"):
    """البحث والتحميل باستخدام YouTube API"""
    try:
        print(f"🔍 البحث والتحميل: {query}")
        print(f"🔑 استخدام المفتاح: {api_key[:20]}...")
        
        # الخطوة 1: البحث
        search_url = "https://www.googleapis.com/youtube/v3/search"
        search_params = {
            'part': 'snippet',
            'q': query,
            'type': 'video',
            'maxResults': 3,
            'key': api_key,
            'regionCode': 'SA',
            'relevanceLanguage': 'ar'
        }
        
        search_response = requests.get(search_url, params=search_params, timeout=10)
        
        if search_response.status_code != 200:
            print(f"❌ فشل البحث: {search_response.status_code}")
            return False
        
        search_data = search_response.json()
        
        if not search_data.get('items'):
            print(f"❌ لم يتم العثور على نتائج")
            return False
        
        # اختيار أول نتيجة
        first_video = search_data['items'][0]
        video_id = first_video['id']['videoId']
        video_title = first_video['snippet']['title']
        channel_title = first_video['snippet']['channelTitle']
        
        print(f"✅ تم العثور على: {video_title}")
        print(f"🎤 القناة: {channel_title}")
        print(f"🆔 معرف الفيديو: {video_id}")
        
        # الخطوة 2: الحصول على التفاصيل الكاملة
        details_url = "https://www.googleapis.com/youtube/v3/videos"
        details_params = {
            'part': 'snippet,contentDetails,statistics',
            'id': video_id,
            'key': api_key
        }
        
        details_response = requests.get(details_url, params=details_params, timeout=10)
        
        if details_response.status_code == 200:
            details_data = details_response.json()
            if details_data.get('items'):
                video_details = details_data['items'][0]
                content_details = video_details.get('contentDetails', {})
                stats = video_details.get('statistics', {})
                
                print(f"⏱️ المدة: {content_details.get('duration', 'غير معروف')}")
                print(f"👁️ المشاهدات: {stats.get('viewCount', 'غير معروف')}")
                print(f"👍 الإعجابات: {stats.get('likeCount', 'غير معروف')}")
        
        # الخطوة 3: محاولة التحميل باستخدام yt-dlp
        print(f"\n⬇️ محاولة التحميل...")
        
        try:
            import yt_dlp
            
            # إعدادات التحميل
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': f'test_downloads/{video_id}.%(ext)s',
                'quiet': False,
                'no_warnings': False,
            }
            
            # إنشاء مجلد التحميل
            os.makedirs('test_downloads', exist_ok=True)
            
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                print(f"🔄 جاري التحميل...")
                start_time = time.time()
                
                info = ydl.extract_info(f"https://www.youtube.com/watch?v={video_id}", download=True)
                
                download_time = time.time() - start_time
                
                if info:
                    print(f"✅ تم التحميل بنجاح!")
                    print(f"⏱️ وقت التحميل: {download_time:.2f}s")
                    print(f"📁 العنوان الكامل: {info.get('title', 'غير معروف')}")
                    print(f"🎤 الرافع: {info.get('uploader', 'غير معروف')}")
                    print(f"⏳ المدة: {info.get('duration', 0)} ثانية")
                    
                    # البحث عن الملف المحمل
                    import glob
                    downloaded_files = glob.glob(f'test_downloads/{video_id}.*')
                    
                    if downloaded_files:
                        file_path = downloaded_files[0]
                        file_size = os.path.getsize(file_path)
                        
                        print(f"📄 الملف: {os.path.basename(file_path)}")
                        print(f"📊 حجم الملف: {file_size / (1024*1024):.2f} MB")
                        
                        return {
                            'success': True,
                            'video_id': video_id,
                            'title': info.get('title'),
                            'uploader': info.get('uploader'),
                            'duration': info.get('duration'),
                            'file_path': file_path,
                            'file_size': file_size,
                            'download_time': download_time
                        }
                    else:
                        print(f"❌ لم يتم العثور على الملف المحمل")
                        return False
                else:
                    print(f"❌ فشل التحميل - لا توجد معلومات")
                    return False
                    
        except ImportError:
            print(f"❌ yt-dlp غير مثبت")
            return False
        except Exception as e:
            print(f"❌ خطأ في التحميل: {e}")
            return False
            
    except Exception as e:
        print(f"❌ خطأ عام: {e}")
        return False

def main():
    """اختبار التحميل مع مفاتيح API"""
    print("⬇️ اختبار التحميل باستخدام YouTube Data API")
    print("=" * 60)
    
    try:
        import config
        api_keys = getattr(config, 'YT_API_KEYS', [])
        
        if not api_keys:
            print("❌ لم يتم العثور على مفاتيح API")
            return
        
        # قائمة الاستعلامات للاختبار
        test_queries = [
            "محمد عبده حبيبتي",
            "عمرو دياب نور العين",
            "فيروز حبيتك بالصيف"
        ]
        
        successful_downloads = 0
        total_attempts = 0
        
        for query in test_queries:
            print(f"\n🎯 اختبار: {query}")
            print("=" * 40)
            
            # جرب المفتاح الأول
            if api_keys:
                total_attempts += 1
                result = search_and_download_test(api_keys[0], query)
                
                if result:
                    successful_downloads += 1
                    print(f"✅ نجح التحميل!")
                else:
                    print(f"❌ فشل التحميل")
            
            time.sleep(3)  # انتظار بين التحميلات
        
        # ملخص النتائج
        print(f"\n📊 ملخص النتائج")
        print("=" * 30)
        print(f"✅ تحميلات ناجحة: {successful_downloads}/{total_attempts}")
        print(f"❌ تحميلات فاشلة: {total_attempts - successful_downloads}/{total_attempts}")
        
        # عرض الملفات المحملة
        import glob
        downloaded_files = glob.glob('test_downloads/*')
        if downloaded_files:
            print(f"\n📁 الملفات المحملة:")
            for file_path in downloaded_files:
                file_size = os.path.getsize(file_path)
                print(f"   📄 {os.path.basename(file_path)} ({file_size / (1024*1024):.2f} MB)")
        
    except Exception as e:
        print(f"❌ خطأ عام: {e}")

if __name__ == "__main__":
    main()
