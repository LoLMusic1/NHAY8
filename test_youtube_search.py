#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔍 اختبار البحث في YouTube Data API
====================================
"""

import requests
import json
import time
from datetime import datetime

def test_youtube_search(api_key, query="محمد عبده"):
    """اختبار البحث في YouTube API"""
    try:
        print(f"🔍 البحث عن: {query}")
        print(f"�� استخدام المفتاح: {api_key[:20]}...")
        
        # البحث في YouTube
        search_url = "https://www.googleapis.com/youtube/v3/search"
        params = {
            'part': 'snippet',
            'q': query,
            'type': 'video',
            'maxResults': 5,
            'key': api_key,
            'regionCode': 'SA',  # السعودية
            'relevanceLanguage': 'ar'  # العربية
        }
        
        start_time = time.time()
        response = requests.get(search_url, params=params, timeout=15)
        elapsed_time = time.time() - start_time
        
        print(f"⏱️ زمن البحث: {elapsed_time:.2f}s")
        print(f"📊 حالة HTTP: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if 'items' in data and len(data['items']) > 0:
                print(f"✅ تم العثور على {len(data['items'])} نتيجة")
                print()
                
                for i, item in enumerate(data['items'], 1):
                    snippet = item['snippet']
                    video_id = item['id']['videoId']
                    
                    print(f"🎵 {i}. {snippet['title']}")
                    print(f"   🎤 القناة: {snippet['channelTitle']}")
                    print(f"   📅 {snippet['publishedAt'][:10]}")
                    print(f"   🔗 https://youtu.be/{video_id}")
                    print()
                
                # اختبار الحصول على تفاصيل أول فيديو
                first_video_id = data['items'][0]['id']['videoId']
                print(f"🔍 اختبار تفاصيل الفيديو: {first_video_id}")
                
                details_url = "https://www.googleapis.com/youtube/v3/videos"
                details_params = {
                    'part': 'snippet,contentDetails,statistics',
                    'id': first_video_id,
                    'key': api_key
                }
                
                details_response = requests.get(details_url, params=details_params, timeout=10)
                
                if details_response.status_code == 200:
                    details_data = details_response.json()
                    if 'items' in details_data and len(details_data['items']) > 0:
                        video = details_data['items'][0]
                        content_details = video.get('contentDetails', {})
                        stats = video.get('statistics', {})
                        
                        print(f"✅ تفاصيل الفيديو:")
                        print(f"   ⏱️ المدة: {content_details.get('duration', 'غير معروف')}")
                        print(f"   👁️ المشاهدات: {stats.get('viewCount', 'غير معروف')}")
                        print(f"   👍 الإعجابات: {stats.get('likeCount', 'غير معروف')}")
                        print(f"   💬 التعليقات: {stats.get('commentCount', 'غير معروف')}")
                
                return {
                    'success': True,
                    'results_count': len(data['items']),
                    'search_time': elapsed_time,
                    'first_video': {
                        'id': data['items'][0]['id']['videoId'],
                        'title': data['items'][0]['snippet']['title'],
                        'channel': data['items'][0]['snippet']['channelTitle']
                    }
                }
            else:
                print(f"❌ لم يتم العثور على نتائج للبحث")
                return {'success': False, 'error': 'لا توجد نتائج'}
        
        else:
            print(f"❌ فشل البحث: {response.status_code}")
            if response.content:
                error_data = response.json()
                print(f"🔍 السبب: {error_data.get('error', {}).get('message', 'غير معروف')}")
            return {'success': False, 'error': f'HTTP {response.status_code}'}
            
    except Exception as e:
        print(f"❌ خطأ في البحث: {e}")
        return {'success': False, 'error': str(e)}

def main():
    """اختبار البحث مع جميع المفاتيح"""
    print("🔍 اختبار البحث في YouTube Data API")
    print("=" * 50)
    
    try:
        import config
        api_keys = getattr(config, 'YT_API_KEYS', [])
        
        if not api_keys:
            print("❌ لم يتم العثور على مفاتيح API")
            return
        
        # قائمة الاستعلامات للاختبار
        test_queries = [
            "محمد عبده",
            "عمرو دياب",
            "music arabic",
            "أغاني عربية"
        ]
        
        for query in test_queries:
            print(f"\n🎯 اختبار البحث: {query}")
            print("=" * 30)
            
            for i, api_key in enumerate(api_keys, 1):
                print(f"\n📍 المفتاح #{i}:")
                result = test_youtube_search(api_key, query)
                
                if result['success']:
                    print(f"✅ نجح البحث - {result['results_count']} نتيجة في {result['search_time']:.2f}s")
                    break  # استخدم المفتاح الأول الذي يعمل
                else:
                    print(f"❌ فشل البحث: {result.get('error')}")
            
            time.sleep(2)  # انتظار بين الاستعلامات
        
    except Exception as e:
        print(f"❌ خطأ عام: {e}")

if __name__ == "__main__":
    main()
