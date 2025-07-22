#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎵 ZeMusic Bot v3.0 - Enhanced Platform Manager
تاريخ الإنشاء: 2025-01-28

مدير المنصات الموسيقية الشامل مع دعم جميع المنصات الرئيسية
"""

import asyncio
import logging
from typing import Dict, List, Optional, Any, Union
from abc import ABC, abstractmethod

from ..config import config

logger = logging.getLogger(__name__)

class BasePlatform(ABC):
    """الكلاس الأساسي للمنصات الموسيقية"""
    
    def __init__(self, name: str):
        self.name = name
        self.is_available = False
        self.search_limit = 10
    
    @abstractmethod
    async def initialize(self) -> bool:
        """تهيئة المنصة"""
        pass
    
    @abstractmethod
    async def search(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """البحث في المنصة"""
        pass
    
    @abstractmethod
    async def get_stream_url(self, track_id: str) -> Optional[str]:
        """الحصول على رابط التشغيل"""
        pass
    
    @abstractmethod
    async def get_track_info(self, track_id: str) -> Optional[Dict[str, Any]]:
        """الحصول على معلومات المقطع"""
        pass

class PlatformManager:
    """مدير المنصات الموسيقية"""
    
    def __init__(self):
        """تهيئة مدير المنصات"""
        self.platforms: Dict[str, BasePlatform] = {}
        self.is_initialized = False
        
        # أولويات البحث
        self.search_priority = [
            'youtube',
            'spotify', 
            'soundcloud',
            'apple_music',
            'resso',
            'carbon',
            'telegram'
        ]
    
    async def initialize(self) -> bool:
        """تهيئة جميع المنصات"""
        try:
            logger.info("🎵 تهيئة مدير المنصات الموسيقية...")
            
            # تحميل المنصات المتاحة
            await self._load_platforms()
            
            # تهيئة كل منصة
            for platform_name, platform in self.platforms.items():
                try:
                    success = await platform.initialize()
                    if success:
                        logger.info(f"✅ تم تهيئة منصة {platform_name} بنجاح")
                    else:
                        logger.warning(f"⚠️ فشل في تهيئة منصة {platform_name}")
                except Exception as e:
                    logger.error(f"❌ خطأ في تهيئة منصة {platform_name}: {e}")
            
            self.is_initialized = True
            available_platforms = [name for name, platform in self.platforms.items() if platform.is_available]
            logger.info(f"🎵 تم تهيئة مدير المنصات - المنصات المتاحة: {', '.join(available_platforms)}")
            
            return len(available_platforms) > 0
            
        except Exception as e:
            logger.error(f"❌ فشل في تهيئة مدير المنصات: {e}")
            return False
    
    async def _load_platforms(self):
        """تحميل المنصات المتاحة"""
        try:
            # YouTube - الأولوية الأولى
            if config.api_keys.youtube_api_key:
                from .youtube import YouTubePlatform
                self.platforms['youtube'] = YouTubePlatform()
            
            # Spotify
            if config.api_keys.spotify_client_id and config.api_keys.spotify_client_secret:
                from .spotify import SpotifyPlatform
                self.platforms['spotify'] = SpotifyPlatform()
            
            # SoundCloud
            if config.api_keys.soundcloud_client_id:
                from .soundcloud import SoundCloudPlatform
                self.platforms['soundcloud'] = SoundCloudPlatform()
            
            # Apple Music
            if config.api_keys.apple_music_key:
                from .apple_music import AppleMusicPlatform
                self.platforms['apple_music'] = AppleMusicPlatform()
            
            # Resso (سيتم التنفيذ لاحقاً)
            # if config.api_keys.resso_api_key:
            #     from .resso import RessoPlatform
            #     self.platforms['resso'] = RessoPlatform()
            
            # Carbon (سيتم التنفيذ لاحقاً)
            # if config.api_keys.carbon_api_key:
            #     from .carbon import CarbonPlatform
            #     self.platforms['carbon'] = CarbonPlatform()
            
            # Telegram (للملفات المرفوعة)
            from .telegram import TelegramPlatform
            self.platforms['telegram'] = TelegramPlatform()
            
            logger.info(f"📚 تم تحميل {len(self.platforms)} منصة")
            
        except Exception as e:
            logger.error(f"❌ فشل في تحميل المنصات: {e}")
    
    async def search_all_platforms(self, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """البحث في جميع المنصات المتاحة"""
        try:
            all_results = []
            
            # البحث حسب الأولوية
            for platform_name in self.search_priority:
                if platform_name in self.platforms and self.platforms[platform_name].is_available:
                    try:
                        platform_results = await self.platforms[platform_name].search(query, limit)
                        
                        # إضافة معلومات المنصة لكل نتيجة
                        for result in platform_results:
                            result['platform'] = platform_name
                            result['platform_display'] = self._get_platform_display_name(platform_name)
                        
                        all_results.extend(platform_results)
                        
                        # إذا وجدنا نتائج كافية، نتوقف
                        if len(all_results) >= limit:
                            break
                            
                    except Exception as e:
                        logger.error(f"❌ خطأ في البحث في منصة {platform_name}: {e}")
                        continue
            
            # ترتيب النتائج حسب الجودة والشعبية
            sorted_results = await self._sort_search_results(all_results)
            
            return sorted_results[:limit]
            
        except Exception as e:
            logger.error(f"❌ فشل في البحث في المنصات: {e}")
            return []
    
    async def search_platform(self, platform_name: str, query: str, limit: int = 10) -> List[Dict[str, Any]]:
        """البحث في منصة محددة"""
        try:
            if platform_name not in self.platforms:
                logger.warning(f"⚠️ المنصة {platform_name} غير متاحة")
                return []
            
            platform = self.platforms[platform_name]
            if not platform.is_available:
                logger.warning(f"⚠️ المنصة {platform_name} غير مفعلة")
                return []
            
            results = await platform.search(query, limit)
            
            # إضافة معلومات المنصة
            for result in results:
                result['platform'] = platform_name
                result['platform_display'] = self._get_platform_display_name(platform_name)
            
            return results
            
        except Exception as e:
            logger.error(f"❌ فشل في البحث في منصة {platform_name}: {e}")
            return []
    
    async def get_stream_url(self, platform_name: str, track_id: str) -> Optional[str]:
        """الحصول على رابط التشغيل من منصة محددة"""
        try:
            if platform_name not in self.platforms:
                return None
            
            platform = self.platforms[platform_name]
            if not platform.is_available:
                return None
            
            return await platform.get_stream_url(track_id)
            
        except Exception as e:
            logger.error(f"❌ فشل في الحصول على رابط التشغيل من {platform_name}: {e}")
            return None
    
    async def get_track_info(self, platform_name: str, track_id: str) -> Optional[Dict[str, Any]]:
        """الحصول على معلومات المقطع من منصة محددة"""
        try:
            if platform_name not in self.platforms:
                return None
            
            platform = self.platforms[platform_name]
            if not platform.is_available:
                return None
            
            track_info = await platform.get_track_info(track_id)
            if track_info:
                track_info['platform'] = platform_name
                track_info['platform_display'] = self._get_platform_display_name(platform_name)
            
            return track_info
            
        except Exception as e:
            logger.error(f"❌ فشل في الحصول على معلومات المقطع من {platform_name}: {e}")
            return None
    
    async def _sort_search_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """ترتيب نتائج البحث حسب الجودة"""
        try:
            # نظام تسجيل النقاط
            def calculate_score(result: Dict[str, Any]) -> float:
                score = 0.0
                
                # نقاط المنصة (حسب الجودة والموثوقية)
                platform_scores = {
                    'youtube': 10.0,
                    'spotify': 9.0,
                    'soundcloud': 8.0,
                    'apple_music': 9.5,
                    'resso': 7.0,
                    'carbon': 6.0,
                    'telegram': 5.0
                }
                
                score += platform_scores.get(result.get('platform', ''), 0.0)
                
                # نقاط الجودة الصوتية
                quality = result.get('quality', 'medium')
                quality_scores = {
                    'high': 5.0,
                    'medium': 3.0,
                    'low': 1.0
                }
                score += quality_scores.get(quality, 0.0)
                
                # نقاط المدة (تفضيل المقاطع ذات المدة المعقولة)
                duration = result.get('duration', 0)
                if 30 <= duration <= 600:  # 30 ثانية إلى 10 دقائق
                    score += 2.0
                elif duration > 600:
                    score -= 1.0
                
                # نقاط المشاهدات/الاستماعات
                views = result.get('views', 0)
                if views > 1000000:  # أكثر من مليون
                    score += 3.0
                elif views > 100000:  # أكثر من 100 ألف
                    score += 2.0
                elif views > 10000:  # أكثر من 10 آلاف
                    score += 1.0
                
                return score
            
            # ترتيب النتائج
            sorted_results = sorted(results, key=calculate_score, reverse=True)
            return sorted_results
            
        except Exception as e:
            logger.error(f"❌ فشل في ترتيب نتائج البحث: {e}")
            return results
    
    def _get_platform_display_name(self, platform_name: str) -> str:
        """الحصول على الاسم المعروض للمنصة"""
        display_names = {
            'youtube': 'YouTube',
            'spotify': 'Spotify',
            'soundcloud': 'SoundCloud',
            'apple_music': 'Apple Music',
            'resso': 'Resso',
            'carbon': 'Carbon',
            'telegram': 'Telegram'
        }
        
        return display_names.get(platform_name, platform_name.title())
    
    def get_available_platforms(self) -> List[str]:
        """الحصول على قائمة المنصات المتاحة"""
        return [name for name, platform in self.platforms.items() if platform.is_available]
    
    def get_platform_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات المنصات"""
        try:
            stats = {
                'total_platforms': len(self.platforms),
                'available_platforms': len(self.get_available_platforms()),
                'platforms_status': {}
            }
            
            for name, platform in self.platforms.items():
                stats['platforms_status'][name] = {
                    'available': platform.is_available,
                    'display_name': self._get_platform_display_name(name)
                }
            
            return stats
            
        except Exception as e:
            logger.error(f"❌ فشل في جلب إحصائيات المنصات: {e}")
            return {}
    
    async def test_platform(self, platform_name: str) -> Dict[str, Any]:
        """اختبار منصة محددة"""
        try:
            if platform_name not in self.platforms:
                return {
                    'success': False,
                    'message': f'المنصة {platform_name} غير موجودة'
                }
            
            platform = self.platforms[platform_name]
            
            # اختبار البحث
            test_query = "test music"
            start_time = asyncio.get_event_loop().time()
            
            try:
                results = await platform.search(test_query, 1)
                end_time = asyncio.get_event_loop().time()
                response_time = round((end_time - start_time) * 1000, 2)
                
                return {
                    'success': True,
                    'platform': platform_name,
                    'available': platform.is_available,
                    'response_time_ms': response_time,
                    'test_results_count': len(results),
                    'message': f'المنصة {platform_name} تعمل بشكل طبيعي'
                }
                
            except Exception as e:
                return {
                    'success': False,
                    'platform': platform_name,
                    'available': False,
                    'error': str(e),
                    'message': f'المنصة {platform_name} لا تعمل: {str(e)}'
                }
                
        except Exception as e:
            logger.error(f"❌ فشل في اختبار المنصة {platform_name}: {e}")
            return {
                'success': False,
                'message': f'خطأ في اختبار المنصة: {str(e)}'
            }
    
    async def test_all_platforms(self) -> Dict[str, Any]:
        """اختبار جميع المنصات"""
        try:
            results = {}
            
            for platform_name in self.platforms.keys():
                results[platform_name] = await self.test_platform(platform_name)
            
            # إحصائيات عامة
            working_platforms = sum(1 for result in results.values() if result['success'])
            total_platforms = len(results)
            
            return {
                'total_platforms': total_platforms,
                'working_platforms': working_platforms,
                'success_rate': round((working_platforms / total_platforms) * 100, 1) if total_platforms > 0 else 0,
                'platforms': results
            }
            
        except Exception as e:
            logger.error(f"❌ فشل في اختبار المنصات: {e}")
            return {}

# إنشاء مثيل عام لمدير المنصات
platform_manager = PlatformManager()