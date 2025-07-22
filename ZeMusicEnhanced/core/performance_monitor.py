#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
🎵 ZeMusic Bot v3.0 - Enhanced Performance Monitor
تاريخ الإنشاء: 2025-01-28

مراقب الأداء المتقدم لمراقبة النظام والموارد
"""

import asyncio
import logging
import psutil
import gc
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from collections import deque

from ..config import config

logger = logging.getLogger(__name__)

@dataclass
class PerformanceMetric:
    """مقياس الأداء"""
    timestamp: datetime
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    disk_usage_percent: float
    network_sent_mb: float
    network_recv_mb: float
    active_connections: int
    response_time_ms: float
    
@dataclass
class SystemAlert:
    """تنبيه النظام"""
    alert_type: str
    severity: str  # low, medium, high, critical
    message: str
    value: float
    threshold: float
    timestamp: datetime

class PerformanceMonitor:
    """مراقب الأداء المتقدم"""
    
    def __init__(self):
        """تهيئة مراقب الأداء"""
        self.metrics_history: deque = deque(maxlen=1000)  # آخر 1000 قياس
        self.alerts: List[SystemAlert] = []
        
        # إعدادات المراقبة
        self.monitoring_interval = config.logging.metrics_interval
        self.is_monitoring = False
        
        # حدود التنبيهات
        self.alert_thresholds = {
            'cpu_high': 80.0,
            'cpu_critical': 95.0,
            'memory_high': 80.0,
            'memory_critical': 95.0,
            'disk_high': 85.0,
            'disk_critical': 95.0,
            'response_time_high': 2000.0,  # 2 ثانية
            'response_time_critical': 5000.0  # 5 ثواني
        }
        
        # معلومات النظام الأساسية
        self.system_info = {}
        self.start_time = datetime.now()
        
        # مهام المراقبة
        self.monitoring_task = None
        self.cleanup_task = None
        self.alert_task = None
        
        # إحصائيات شبكة
        self.network_baseline = None
        
    async def initialize(self) -> bool:
        """تهيئة مراقب الأداء"""
        try:
            logger.info("📈 تهيئة مراقب الأداء...")
            
            # جمع معلومات النظام الأساسية
            await self._collect_system_info()
            
            # تعيين خط أساس الشبكة
            self._set_network_baseline()
            
            logger.info("✅ تم تهيئة مراقب الأداء بنجاح")
            return True
            
        except Exception as e:
            logger.error(f"❌ فشل في تهيئة مراقب الأداء: {e}")
            return False
    
    async def _collect_system_info(self):
        """جمع معلومات النظام الأساسية"""
        try:
            # معلومات المعالج
            self.system_info['cpu_count'] = psutil.cpu_count()
            self.system_info['cpu_freq'] = psutil.cpu_freq()._asdict() if psutil.cpu_freq() else {}
            
            # معلومات الذاكرة
            memory = psutil.virtual_memory()
            self.system_info['total_memory_gb'] = round(memory.total / (1024**3), 2)
            
            # معلومات القرص
            disk = psutil.disk_usage('/')
            self.system_info['total_disk_gb'] = round(disk.total / (1024**3), 2)
            
            # معلومات النظام
            self.system_info['platform'] = psutil.platform
            self.system_info['boot_time'] = datetime.fromtimestamp(psutil.boot_time())
            
            logger.info(f"💻 معلومات النظام: {self.system_info}")
            
        except Exception as e:
            logger.error(f"❌ فشل في جمع معلومات النظام: {e}")
    
    def _set_network_baseline(self):
        """تعيين خط أساس الشبكة"""
        try:
            net_io = psutil.net_io_counters()
            self.network_baseline = {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'timestamp': time.time()
            }
        except Exception as e:
            logger.error(f"❌ فشل في تعيين خط أساس الشبكة: {e}")
    
    async def start_monitoring(self):
        """بدء مراقبة الأداء"""
        try:
            if self.is_monitoring:
                return
            
            self.is_monitoring = True
            
            # بدء مهمة المراقبة الرئيسية
            self.monitoring_task = asyncio.create_task(self._monitoring_loop())
            
            # بدء مهمة تنظيف البيانات القديمة
            self.cleanup_task = asyncio.create_task(self._cleanup_old_data())
            
            # بدء مهمة معالجة التنبيهات
            self.alert_task = asyncio.create_task(self._alert_processing_loop())
            
            logger.info("🚀 تم بدء مراقبة الأداء")
            
        except Exception as e:
            logger.error(f"❌ فشل في بدء مراقبة الأداء: {e}")
    
    async def _monitoring_loop(self):
        """حلقة المراقبة الرئيسية"""
        while self.is_monitoring:
            try:
                # جمع مقاييس الأداء
                metric = await self._collect_metrics()
                
                if metric:
                    self.metrics_history.append(metric)
                    
                    # فحص التنبيهات
                    await self._check_alerts(metric)
                
                # انتظار الفترة المحددة
                await asyncio.sleep(self.monitoring_interval)
                
            except Exception as e:
                logger.error(f"❌ خطأ في حلقة المراقبة: {e}")
                await asyncio.sleep(self.monitoring_interval)
    
    async def _collect_metrics(self) -> Optional[PerformanceMetric]:
        """جمع مقاييس الأداء الحالية"""
        try:
            # قياس وقت الاستجابة
            start_time = time.time()
            
            # معلومات المعالج
            cpu_percent = psutil.cpu_percent(interval=1)
            
            # معلومات الذاكرة
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_mb = round((memory.total - memory.available) / (1024**2), 2)
            
            # معلومات القرص
            disk = psutil.disk_usage('/')
            disk_usage_percent = disk.percent
            
            # معلومات الشبكة
            net_sent_mb, net_recv_mb = self._calculate_network_usage()
            
            # عدد الاتصالات النشطة
            active_connections = len(psutil.net_connections())
            
            # وقت الاستجابة
            response_time_ms = round((time.time() - start_time) * 1000, 2)
            
            return PerformanceMetric(
                timestamp=datetime.now(),
                cpu_percent=cpu_percent,
                memory_percent=memory_percent,
                memory_used_mb=memory_used_mb,
                disk_usage_percent=disk_usage_percent,
                network_sent_mb=net_sent_mb,
                network_recv_mb=net_recv_mb,
                active_connections=active_connections,
                response_time_ms=response_time_ms
            )
            
        except Exception as e:
            logger.error(f"❌ فشل في جمع مقاييس الأداء: {e}")
            return None
    
    def _calculate_network_usage(self) -> tuple:
        """حساب استخدام الشبكة"""
        try:
            if not self.network_baseline:
                return 0.0, 0.0
            
            net_io = psutil.net_io_counters()
            current_time = time.time()
            
            # حساب الفرق منذ آخر قياس
            time_diff = current_time - self.network_baseline['timestamp']
            bytes_sent_diff = net_io.bytes_sent - self.network_baseline['bytes_sent']
            bytes_recv_diff = net_io.bytes_recv - self.network_baseline['bytes_recv']
            
            # تحويل إلى MB/s
            net_sent_mb = round((bytes_sent_diff / (1024**2)) / time_diff, 2) if time_diff > 0 else 0.0
            net_recv_mb = round((bytes_recv_diff / (1024**2)) / time_diff, 2) if time_diff > 0 else 0.0
            
            # تحديث خط الأساس
            self.network_baseline = {
                'bytes_sent': net_io.bytes_sent,
                'bytes_recv': net_io.bytes_recv,
                'timestamp': current_time
            }
            
            return net_sent_mb, net_recv_mb
            
        except Exception as e:
            logger.error(f"❌ فشل في حساب استخدام الشبكة: {e}")
            return 0.0, 0.0
    
    async def _check_alerts(self, metric: PerformanceMetric):
        """فحص التنبيهات"""
        try:
            current_time = datetime.now()
            
            # فحص المعالج
            if metric.cpu_percent >= self.alert_thresholds['cpu_critical']:
                await self._create_alert(
                    'cpu_critical', 'critical',
                    f'استخدام المعالج مرتفع جداً: {metric.cpu_percent}%',
                    metric.cpu_percent, self.alert_thresholds['cpu_critical']
                )
            elif metric.cpu_percent >= self.alert_thresholds['cpu_high']:
                await self._create_alert(
                    'cpu_high', 'high',
                    f'استخدام المعالج مرتفع: {metric.cpu_percent}%',
                    metric.cpu_percent, self.alert_thresholds['cpu_high']
                )
            
            # فحص الذاكرة
            if metric.memory_percent >= self.alert_thresholds['memory_critical']:
                await self._create_alert(
                    'memory_critical', 'critical',
                    f'استخدام الذاكرة مرتفع جداً: {metric.memory_percent}% ({metric.memory_used_mb}MB)',
                    metric.memory_percent, self.alert_thresholds['memory_critical']
                )
            elif metric.memory_percent >= self.alert_thresholds['memory_high']:
                await self._create_alert(
                    'memory_high', 'high',
                    f'استخدام الذاكرة مرتفع: {metric.memory_percent}% ({metric.memory_used_mb}MB)',
                    metric.memory_percent, self.alert_thresholds['memory_high']
                )
            
            # فحص القرص
            if metric.disk_usage_percent >= self.alert_thresholds['disk_critical']:
                await self._create_alert(
                    'disk_critical', 'critical',
                    f'مساحة القرص ممتلئة: {metric.disk_usage_percent}%',
                    metric.disk_usage_percent, self.alert_thresholds['disk_critical']
                )
            elif metric.disk_usage_percent >= self.alert_thresholds['disk_high']:
                await self._create_alert(
                    'disk_high', 'high',
                    f'مساحة القرص منخفضة: {metric.disk_usage_percent}%',
                    metric.disk_usage_percent, self.alert_thresholds['disk_high']
                )
            
            # فحص وقت الاستجابة
            if metric.response_time_ms >= self.alert_thresholds['response_time_critical']:
                await self._create_alert(
                    'response_time_critical', 'critical',
                    f'وقت الاستجابة بطيء جداً: {metric.response_time_ms}ms',
                    metric.response_time_ms, self.alert_thresholds['response_time_critical']
                )
            elif metric.response_time_ms >= self.alert_thresholds['response_time_high']:
                await self._create_alert(
                    'response_time_high', 'high',
                    f'وقت الاستجابة بطيء: {metric.response_time_ms}ms',
                    metric.response_time_ms, self.alert_thresholds['response_time_high']
                )
            
        except Exception as e:
            logger.error(f"❌ فشل في فحص التنبيهات: {e}")
    
    async def _create_alert(self, alert_type: str, severity: str, message: str, 
                           value: float, threshold: float):
        """إنشاء تنبيه"""
        try:
            # تجنب التنبيهات المكررة (خلال آخر 5 دقائق)
            recent_alerts = [
                alert for alert in self.alerts
                if alert.alert_type == alert_type and 
                (datetime.now() - alert.timestamp).seconds < 300
            ]
            
            if recent_alerts:
                return  # تجنب التكرار
            
            alert = SystemAlert(
                alert_type=alert_type,
                severity=severity,
                message=message,
                value=value,
                threshold=threshold,
                timestamp=datetime.now()
            )
            
            self.alerts.append(alert)
            
            # الاحتفاظ بآخر 100 تنبيه فقط
            if len(self.alerts) > 100:
                self.alerts = self.alerts[-100:]
            
            # تسجيل التنبيه
            if severity == 'critical':
                logger.critical(f"🚨 {message}")
            elif severity == 'high':
                logger.error(f"🔴 {message}")
            else:
                logger.warning(f"🟡 {message}")
            
        except Exception as e:
            logger.error(f"❌ فشل في إنشاء التنبيه: {e}")
    
    async def _alert_processing_loop(self):
        """حلقة معالجة التنبيهات"""
        while self.is_monitoring:
            try:
                await asyncio.sleep(60)  # كل دقيقة
                
                # معالجة التنبيهات الحرجة
                await self._process_critical_alerts()
                
            except Exception as e:
                logger.error(f"❌ خطأ في معالجة التنبيهات: {e}")
    
    async def _process_critical_alerts(self):
        """معالجة التنبيهات الحرجة"""
        try:
            recent_critical_alerts = [
                alert for alert in self.alerts
                if alert.severity == 'critical' and 
                (datetime.now() - alert.timestamp).seconds < 300  # آخر 5 دقائق
            ]
            
            if not recent_critical_alerts:
                return
            
            # تنفيذ إجراءات الطوارئ
            for alert in recent_critical_alerts:
                if alert.alert_type == 'memory_critical':
                    await self._emergency_memory_cleanup()
                elif alert.alert_type == 'cpu_critical':
                    await self._emergency_cpu_optimization()
                elif alert.alert_type == 'disk_critical':
                    await self._emergency_disk_cleanup()
            
        except Exception as e:
            logger.error(f"❌ فشل في معالجة التنبيهات الحرجة: {e}")
    
    async def _emergency_memory_cleanup(self):
        """تنظيف الذاكرة في حالات الطوارئ"""
        try:
            logger.warning("🧹 بدء تنظيف الذاكرة الطارئ...")
            
            # تشغيل garbage collector
            collected = gc.collect()
            logger.info(f"♻️ تم تحرير {collected} كائن من الذاكرة")
            
            # تنظيف ذاكرة التخزين المؤقت
            # (سيتم ربطه مع مكونات البوت الأخرى)
            
        except Exception as e:
            logger.error(f"❌ فشل في تنظيف الذاكرة الطارئ: {e}")
    
    async def _emergency_cpu_optimization(self):
        """تحسين المعالج في حالات الطوارئ"""
        try:
            logger.warning("⚡ بدء تحسين المعالج الطارئ...")
            
            # تقليل عدد المهام المتوازية
            # (سيتم ربطه مع مكونات البوت الأخرى)
            
        except Exception as e:
            logger.error(f"❌ فشل في تحسين المعالج الطارئ: {e}")
    
    async def _emergency_disk_cleanup(self):
        """تنظيف القرص في حالات الطوارئ"""
        try:
            logger.warning("💿 بدء تنظيف القرص الطارئ...")
            
            # حذف الملفات المؤقتة القديمة
            import shutil
            from pathlib import Path
            
            temp_dirs = [
                Path(config.music.temp_path),
                Path("logs"),
                Path("downloads")
            ]
            
            for temp_dir in temp_dirs:
                if temp_dir.exists():
                    # حذف الملفات الأقدم من ساعة
                    cutoff_time = datetime.now() - timedelta(hours=1)
                    
                    for file_path in temp_dir.glob("*"):
                        if file_path.is_file():
                            file_time = datetime.fromtimestamp(file_path.stat().st_mtime)
                            if file_time < cutoff_time:
                                try:
                                    file_path.unlink()
                                except:
                                    pass
            
            logger.info("🗑️ تم تنظيف الملفات المؤقتة القديمة")
            
        except Exception as e:
            logger.error(f"❌ فشل في تنظيف القرص الطارئ: {e}")
    
    async def get_performance_stats(self) -> Dict[str, Any]:
        """الحصول على إحصائيات الأداء"""
        try:
            if not self.metrics_history:
                return {}
            
            # آخر قياس
            latest_metric = self.metrics_history[-1]
            
            # متوسط آخر 10 قياسات
            recent_metrics = list(self.metrics_history)[-10:]
            
            avg_cpu = sum(m.cpu_percent for m in recent_metrics) / len(recent_metrics)
            avg_memory = sum(m.memory_percent for m in recent_metrics) / len(recent_metrics)
            avg_response_time = sum(m.response_time_ms for m in recent_metrics) / len(recent_metrics)
            
            # وقت التشغيل
            uptime = datetime.now() - self.start_time
            
            # إحصائيات التنبيهات
            alert_counts = {'low': 0, 'medium': 0, 'high': 0, 'critical': 0}
            for alert in self.alerts:
                alert_counts[alert.severity] += 1
            
            return {
                'current': {
                    'cpu_percent': latest_metric.cpu_percent,
                    'memory_percent': latest_metric.memory_percent,
                    'memory_used_mb': latest_metric.memory_used_mb,
                    'disk_usage_percent': latest_metric.disk_usage_percent,
                    'network_sent_mb': latest_metric.network_sent_mb,
                    'network_recv_mb': latest_metric.network_recv_mb,
                    'active_connections': latest_metric.active_connections,
                    'response_time_ms': latest_metric.response_time_ms
                },
                'averages': {
                    'cpu_percent': round(avg_cpu, 2),
                    'memory_percent': round(avg_memory, 2),
                    'response_time_ms': round(avg_response_time, 2)
                },
                'system_info': self.system_info,
                'uptime': {
                    'days': uptime.days,
                    'hours': uptime.seconds // 3600,
                    'minutes': (uptime.seconds % 3600) // 60,
                    'total_seconds': int(uptime.total_seconds())
                },
                'alerts': {
                    'total_alerts': len(self.alerts),
                    'by_severity': alert_counts,
                    'recent_alerts': [
                        {
                            'type': alert.alert_type,
                            'severity': alert.severity,
                            'message': alert.message,
                            'timestamp': alert.timestamp.isoformat()
                        }
                        for alert in self.alerts[-5:]  # آخر 5 تنبيهات
                    ]
                },
                'monitoring': {
                    'is_active': self.is_monitoring,
                    'interval_seconds': self.monitoring_interval,
                    'metrics_collected': len(self.metrics_history)
                }
            }
            
        except Exception as e:
            logger.error(f"❌ فشل في جلب إحصائيات الأداء: {e}")
            return {}
    
    async def get_historical_data(self, hours: int = 1) -> List[Dict[str, Any]]:
        """الحصول على البيانات التاريخية"""
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            
            historical_data = [
                {
                    'timestamp': metric.timestamp.isoformat(),
                    'cpu_percent': metric.cpu_percent,
                    'memory_percent': metric.memory_percent,
                    'memory_used_mb': metric.memory_used_mb,
                    'disk_usage_percent': metric.disk_usage_percent,
                    'response_time_ms': metric.response_time_ms
                }
                for metric in self.metrics_history
                if metric.timestamp >= cutoff_time
            ]
            
            return historical_data
            
        except Exception as e:
            logger.error(f"❌ فشل في جلب البيانات التاريخية: {e}")
            return []
    
    async def _cleanup_old_data(self):
        """تنظيف البيانات القديمة"""
        while self.is_monitoring:
            try:
                await asyncio.sleep(3600)  # كل ساعة
                
                # تنظيف التنبيهات القديمة (أكثر من 24 ساعة)
                cutoff_time = datetime.now() - timedelta(hours=24)
                self.alerts = [
                    alert for alert in self.alerts
                    if alert.timestamp >= cutoff_time
                ]
                
                logger.info("🧹 تم تنظيف بيانات الأداء القديمة")
                
            except Exception as e:
                logger.error(f"❌ خطأ في تنظيف البيانات القديمة: {e}")
    
    async def shutdown(self):
        """إيقاف مراقب الأداء"""
        try:
            logger.info("🛑 إيقاف مراقب الأداء...")
            
            self.is_monitoring = False
            
            # إيقاف المهام
            if self.monitoring_task:
                self.monitoring_task.cancel()
            
            if self.cleanup_task:
                self.cleanup_task.cancel()
            
            if self.alert_task:
                self.alert_task.cancel()
            
            logger.info("✅ تم إيقاف مراقب الأداء")
            
        except Exception as e:
            logger.error(f"❌ خطأ في إيقاف مراقب الأداء: {e}")

# إنشاء مثيل عام لمراقب الأداء
performance_monitor = PerformanceMonitor()