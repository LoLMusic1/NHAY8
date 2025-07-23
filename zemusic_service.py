#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
🤖 خدمة مراقبة ZeMusic Bot - نظام 30 يوم متطور
================================================
نظام مراقبة ذكي يحافظ على تشغيل البوت بدون انقطاع
مع إعادة تشغيل تلقائية وإحصائيات شاملة
"""

import asyncio
import subprocess
import psutil
import json
import time
import signal
import sys
import os
from datetime import datetime, timedelta
from pathlib import Path
import logging

class ZeMusicMonitor:
    def __init__(self):
        self.bot_command = ["python3", "-m", "ZeMusic"]
        self.workspace_dir = "/workspace"
        self.log_file = "/tmp/zemusic_monitor.log"
        self.stats_file = "/tmp/zemusic_stats.json"
        self.pid_file = "/tmp/zemusic_monitor.pid"
        
        # إعدادات المراقبة
        self.check_interval = 30  # فحص كل 30 ثانية
        self.max_restart_attempts = 5
        self.restart_delay = 10
        self.service_duration = 30 * 24 * 3600  # 30 يوم بالثواني
        
        # متغيرات الحالة
        self.bot_process = None
        self.start_time = datetime.now()
        self.stats = {
            "start_time": self.start_time.isoformat(),
            "total_restarts": 0,
            "successful_restarts": 0,
            "failed_restarts": 0,
            "health_checks": 0,
            "failed_checks": 0,
            "uptime_seconds": 0,
            "last_restart": None,
            "service_status": "starting",
            "monitor_pid": os.getpid()
        }
        
        # إعداد التسجيل
        self.setup_logging()
        
        # حفظ PID للمراقبة
        self.save_pid()
    
    def setup_logging(self):
        """إعداد نظام التسجيل"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler(self.log_file, encoding='utf-8'),
                logging.StreamHandler(sys.stdout)
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def save_pid(self):
        """حفظ PID الخدمة"""
        try:
            with open(self.pid_file, 'w') as f:
                f.write(str(os.getpid()))
            self.logger.info(f"💾 تم حفظ PID: {os.getpid()}")
        except Exception as e:
            self.logger.error(f"❌ خطأ في حفظ PID: {e}")
    
    def update_stats(self, **kwargs):
        """تحديث الإحصائيات"""
        try:
            for key, value in kwargs.items():
                if key in self.stats:
                    if isinstance(value, str) and value == "increment":
                        self.stats[key] += 1
                    else:
                        self.stats[key] = value
            
            # تحديث وقت التشغيل
            self.stats["uptime_seconds"] = int((datetime.now() - self.start_time).total_seconds())
            
            # حفظ الإحصائيات
            with open(self.stats_file, 'w', encoding='utf-8') as f:
                json.dump(self.stats, f, indent=2, ensure_ascii=False)
        
        except Exception as e:
            self.logger.error(f"❌ خطأ في تحديث الإحصائيات: {e}")
    
    def is_bot_running(self):
        """فحص ما إذا كان البوت يعمل"""
        try:
            if self.bot_process and self.bot_process.poll() is None:
                return True
            
            # البحث عن العملية في النظام
            for proc in psutil.process_iter(['pid', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and len(cmdline) >= 2:
                        if 'python3' in cmdline[0] and 'ZeMusic' in ' '.join(cmdline):
                            self.bot_process = subprocess.Popen(['echo'], stdout=subprocess.PIPE)
                            self.bot_process.pid = proc.info['pid']
                            return True
                except (psutil.NoSuchProcess, psutil.AccessDenied):
                    continue
            
            return False
        
        except Exception as e:
            self.logger.error(f"❌ خطأ في فحص حالة البوت: {e}")
            return False
    
    def start_bot(self):
        """بدء تشغيل البوت"""
        try:
            self.logger.info("🚀 بدء تشغيل ZeMusic Bot...")
            
            # الانتقال إلى مجلد العمل
            os.chdir(self.workspace_dir)
            
            # إيقاف أي عملية سابقة
            self.stop_bot()
            time.sleep(3)
            
            # بدء البوت
            log_file_name = f"/tmp/zemusic_service_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
            
            with open(log_file_name, 'w') as log_file:
                self.bot_process = subprocess.Popen(
                    self.bot_command,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    cwd=self.workspace_dir
                )
            
            # انتظار قصير للتأكد من بدء التشغيل
            time.sleep(8)
            
            if self.is_bot_running():
                self.logger.info(f"✅ تم بدء ZeMusic Bot بنجاح (PID: {self.bot_process.pid})")
                self.update_stats(service_status="running")
                return True
            else:
                self.logger.error("❌ فشل في بدء ZeMusic Bot")
                self.update_stats(service_status="failed")
                return False
        
        except Exception as e:
            self.logger.error(f"❌ خطأ في بدء البوت: {e}")
            self.update_stats(service_status="error")
            return False
    
    def stop_bot(self):
        """إيقاف البوت"""
        try:
            # إيقاف العملية المحفوظة
            if self.bot_process:
                try:
                    self.bot_process.terminate()
                    self.bot_process.wait(timeout=10)
                except subprocess.TimeoutExpired:
                    self.bot_process.kill()
                except:
                    pass
            
            # البحث عن وإيقاف جميع عمليات ZeMusic
            for proc in psutil.process_iter(['pid', 'cmdline']):
                try:
                    cmdline = proc.info['cmdline']
                    if cmdline and 'python3' in str(cmdline) and 'ZeMusic' in str(cmdline):
                        proc.terminate()
                        proc.wait(timeout=5)
                except:
                    try:
                        proc.kill()
                    except:
                        pass
            
            self.bot_process = None
            self.logger.info("🛑 تم إيقاف ZeMusic Bot")
        
        except Exception as e:
            self.logger.error(f"❌ خطأ في إيقاف البوت: {e}")
    
    def restart_bot(self, attempt):
        """إعادة تشغيل البوت"""
        self.logger.warning(f"🔄 محاولة إعادة تشغيل ZeMusic Bot (المحاولة {attempt}/{self.max_restart_attempts})")
        
        self.stop_bot()
        time.sleep(self.restart_delay)
        
        if self.start_bot():
            self.update_stats(
                total_restarts="increment",
                successful_restarts="increment",
                last_restart=datetime.now().isoformat()
            )
            self.logger.info("✅ تم إعادة تشغيل ZeMusic Bot بنجاح")
            return True
        else:
            self.update_stats(failed_restarts="increment")
            self.logger.error("❌ فشل في إعادة تشغيل ZeMusic Bot")
            return False
    
    def show_stats(self):
        """عرض الإحصائيات"""
        try:
            uptime_hours = self.stats["uptime_seconds"] / 3600
            success_rate = 0
            
            if self.stats["health_checks"] > 0:
                success_rate = ((self.stats["health_checks"] - self.stats["failed_checks"]) / self.stats["health_checks"]) * 100
            
            stats_text = f"""
📊 إحصائيات خدمة ZeMusic Bot
================================
🕐 وقت البدء: {datetime.fromisoformat(self.stats['start_time']).strftime('%Y-%m-%d %H:%M:%S')}
⏱️  وقت التشغيل: {uptime_hours:.1f} ساعة
🔄 إعادة التشغيل: {self.stats['total_restarts']} مرة
✅ نجح: {self.stats['successful_restarts']} | ❌ فشل: {self.stats['failed_restarts']}
💓 فحوصات الصحة: {self.stats['health_checks']}
❌ فحوصات فاشلة: {self.stats['failed_checks']}
🎯 معدل الاستقرار: {success_rate:.1f}%
📊 حالة الخدمة: {self.stats['service_status']}
"""
            
            if self.stats['last_restart']:
                last_restart = datetime.fromisoformat(self.stats['last_restart'])
                stats_text += f"🕐 آخر إعادة تشغيل: {last_restart.strftime('%Y-%m-%d %H:%M:%S')}\n"
            
            print(stats_text)
            self.logger.info("📊 تم عرض الإحصائيات")
        
        except Exception as e:
            self.logger.error(f"❌ خطأ في عرض الإحصائيات: {e}")
    
    async def monitor_loop(self):
        """حلقة المراقبة الرئيسية"""
        end_time = self.start_time + timedelta(seconds=self.service_duration)
        restart_attempts = 0
        last_stats_show = time.time()
        
        self.logger.info("🎯 بدء مراقبة ZeMusic Bot لمدة 30 يوم")
        self.logger.info(f"🔍 فحص كل {self.check_interval} ثانية")
        self.logger.info(f"📅 انتهاء الخدمة: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        while datetime.now() < end_time:
            try:
                self.update_stats(health_checks="increment")
                
                if self.is_bot_running():
                    # البوت يعمل بشكل طبيعي
                    restart_attempts = 0
                    self.update_stats(service_status="running")
                    
                    # عرض الإحصائيات كل ساعة
                    if time.time() - last_stats_show >= 3600:  # ساعة واحدة
                        uptime_hours = (datetime.now() - self.start_time).total_seconds() / 3600
                        self.logger.info(f"💚 ZeMusic Bot يعمل بشكل طبيعي ({uptime_hours:.1f}h)")
                        self.show_stats()
                        last_stats_show = time.time()
                
                else:
                    # البوت متوقف
                    self.update_stats(failed_checks="increment", service_status="restarting")
                    restart_attempts += 1
                    
                    if restart_attempts <= self.max_restart_attempts:
                        self.logger.warning(f"⚠️  ZeMusic Bot متوقف! محاولة إعادة التشغيل...")
                        
                        if self.restart_bot(restart_attempts):
                            restart_attempts = 0
                        else:
                            await asyncio.sleep(self.restart_delay)
                    else:
                        self.logger.critical(f"🚨 فشل في إعادة تشغيل البوت بعد {self.max_restart_attempts} محاولات")
                        self.logger.critical("🔄 إعادة تعيين العداد والمحاولة مرة أخرى")
                        restart_attempts = 0
                        await asyncio.sleep(self.restart_delay * 2)
                
                # انتظار قبل الفحص التالي
                await asyncio.sleep(self.check_interval)
            
            except Exception as e:
                self.logger.error(f"❌ خطأ في حلقة المراقبة: {e}")
                await asyncio.sleep(self.check_interval)
        
        self.logger.info("⏰ انتهت فترة المراقبة (30 يوم)")
        self.logger.info("🎉 تم إكمال الخدمة بنجاح!")
    
    def cleanup(self):
        """تنظيف الموارد عند الإنهاء"""
        self.logger.info("🛑 إيقاف خدمة المراقبة...")
        self.update_stats(service_status="stopped")
        
        # عرض الإحصائيات النهائية
        self.show_stats()
        
        # حذف ملف PID
        try:
            if os.path.exists(self.pid_file):
                os.remove(self.pid_file)
        except:
            pass
        
        self.logger.info("📋 ملخص الخدمة:")
        self.logger.info(f"   📁 ملف السجل: {self.log_file}")
        self.logger.info(f"   📊 ملف الإحصائيات: {self.stats_file}")
        self.logger.info("   🕐 مدة الخدمة: 30 يوم")
        self.logger.info("✅ تم إنهاء الخدمة بنجاح")
    
    async def run(self):
        """تشغيل الخدمة"""
        try:
            print("🤖 خدمة مراقبة ZeMusic Bot - 30 يوم")
            print("====================================")
            print(f"📅 بدء الخدمة: {self.start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"📅 انتهاء الخدمة: {(self.start_time + timedelta(seconds=self.service_duration)).strftime('%Y-%m-%d %H:%M:%S')}")
            print(f"📁 مجلد العمل: {self.workspace_dir}")
            print(f"📝 ملف السجل: {self.log_file}")
            print(f"📊 ملف الإحصائيات: {self.stats_file}")
            print()
            
            # إعداد معالجات الإشارات
            def signal_handler(signum, frame):
                self.logger.info(f"🔔 تم استلام إشارة {signum}")
                self.cleanup()
                sys.exit(0)
            
            signal.signal(signal.SIGINT, signal_handler)
            signal.signal(signal.SIGTERM, signal_handler)
            
            # بدء البوت إذا لم يكن يعمل
            if not self.is_bot_running():
                self.logger.info("🚀 البوت غير مشغل - بدء التشغيل...")
                self.start_bot()
            else:
                self.logger.info("✅ البوت يعمل بالفعل")
                self.update_stats(service_status="running")
            
            # بدء حلقة المراقبة
            await self.monitor_loop()
            
        except Exception as e:
            self.logger.error(f"❌ خطأ في تشغيل الخدمة: {e}")
        finally:
            self.cleanup()

async def main():
    """الدالة الرئيسية"""
    monitor = ZeMusicMonitor()
    await monitor.run()

if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n🛑 تم إيقاف الخدمة بواسطة المستخدم")
    except Exception as e:
        print(f"❌ خطأ في تشغيل الخدمة: {e}")