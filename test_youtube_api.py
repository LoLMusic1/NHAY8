#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🔑 اختبار مفاتيح YouTube Data API
=====================================
"""

import requests
import json
import sys
import time
from datetime import datetime

def test_youtube_api_key(api_key, test_video_id="dQw4w9WgXcQ"):
    """اختبار مفتاح YouTube API واحد"""
    try:
        print(f"🔑 اختبار المفتاح: {api_key[:20]}...")
        
        # اختبار 1: الحصول على معلومات فيديو
        api_url = "https://www.googleapis.com/youtube/v3/videos"
        params = {
            'part': 'snippet,contentDetails,statistics',
            'id': test_video_id,
            'key': api_key
        }
        
        start_time = time.time()
        response = requests.get(api_url, params=params, timeout=10)
        elapsed_time = time.time() - start_time
        
        print(f"⏱️ زمن الاستجابة: {elapsed_time:.2f}s")
        print(f"📊 حالة HTTP: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            
            if 'items' in data and len(data['items']) > 0:
                video = data['items'][0]
                snippet = video['snippet']
                stats = video.get('statistics', {})
                
                print(f"✅ المفتاح يعمل بشكل صحيح!")
                print(f"📹 العنوان: {snippet.get('title', 'غير معروف')}")
                print(f"🎤 القناة: {snippet.get('channelTitle', 'غير معروف')}")
                print(f"📅 تاريخ النشر: {snippet.get('publishedAt', 'غير معروف')}")
                print(f"👁️ المشاهدات: {stats.get('viewCount', 'غير معروف')}")
                print(f"👍 الإعجابات: {stats.get('likeCount', 'غير معروف')}")
                
                return {
                    'success': True,
                    'key': api_key,
                    'response_time': elapsed_time,
                    'video_title': snippet.get('title'),
                    'channel': snippet.get('channelTitle'),
                    'views': stats.get('viewCount')
                }
            else:
                print(f"❌ لم يتم العثور على بيانات الفيديو")
                return {'success': False, 'key': api_key, 'error': 'لا توجد بيانات'}
        
        elif response.status_code == 403:
            error_data = response.json() if response.content else {}
            error_reason = error_data.get('error', {}).get('message', 'غير معروف')
            print(f"❌ المفتاح محظور أو منتهي الصلاحية")
            print(f"🔍 السبب: {error_reason}")
            return {'success': False, 'key': api_key, 'error': f'403: {error_reason}'}
        
        elif response.status_code == 400:
            error_data = response.json() if response.content else {}
            error_reason = error_data.get('error', {}).get('message', 'غير معروف')
            print(f"❌ المفتاح غير صالح")
            print(f"🔍 السبب: {error_reason}")
            return {'success': False, 'key': api_key, 'error': f'400: {error_reason}'}
        
        else:
            print(f"❌ خطأ غير متوقع: {response.status_code}")
            return {'success': False, 'key': api_key, 'error': f'HTTP {response.status_code}'}
            
    except Exception as e:
        print(f"❌ خطأ: {e}")
        return {'success': False, 'key': api_key, 'error': str(e)}

def main():
    """الدالة الرئيسية لاختبار جميع المفاتيح"""
    print("🔑 اختبار مفاتيح YouTube Data API")
    print("=" * 50)
    
    # استيراد المفاتيح من config.py
    try:
        import config
        api_keys = getattr(config, 'YT_API_KEYS', [])
        
        if not api_keys:
            print("❌ لم يتم العثور على مفاتيح API في config.py")
            return
        
        print(f"📊 تم العثور على {len(api_keys)} مفتاح API")
        print()
        
        results = []
        working_keys = 0
        
        for i, api_key in enumerate(api_keys, 1):
            print(f"🔍 اختبار المفتاح #{i}/{len(api_keys)}")
            print("-" * 30)
            
            result = test_youtube_api_key(api_key)
            results.append(result)
            
            if result['success']:
                working_keys += 1
            
            print()
            time.sleep(1)
        
        # ملخص النتائج
        print("📊 ملخص النتائج")
        print("=" * 50)
        print(f"✅ المفاتيح العاملة: {working_keys}/{len(api_keys)}")
        print(f"❌ المفاتيح المعطلة: {len(api_keys) - working_keys}/{len(api_keys)}")
        
        # تفاصيل المفاتيح العاملة
        if working_keys > 0:
            print("\n✅ المفاتيح العاملة:")
            for result in results:
                if result['success']:
                    print(f"   🔑 {result['key'][:20]}... | ⏱️ {result['response_time']:.2f}s")
        
        # تفاصيل المفاتيح المعطلة
        failed_keys = [r for r in results if not r['success']]
        if failed_keys:
            print("\n❌ المفاتيح المعطلة:")
            for result in failed_keys:
                print(f"   🔑 {result['key'][:20]}... | ❌ {result.get('error', 'خطأ غير معروف')}")
        
    except Exception as e:
        print(f"❌ خطأ عام: {e}")

if __name__ == "__main__":
    main()
