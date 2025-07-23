#!/usr/bin/env python3
"""
سكريبت فحص المشروع - ZeMusic Bot
يقوم بفحص شامل للمشروع واكتشاف المشاكل
"""

import os
import sys
import py_compile
import json
import subprocess
from pathlib import Path

class ProjectChecker:
    def __init__(self):
        self.errors = []
        self.warnings = []
        self.success_count = 0
        
    def log_error(self, message):
        self.errors.append(f"❌ {message}")
        print(f"❌ {message}")
        
    def log_warning(self, message):
        self.warnings.append(f"⚠️ {message}")
        print(f"⚠️ {message}")
        
    def log_success(self, message):
        self.success_count += 1
        print(f"✅ {message}")
    
    def check_python_files(self):
        """فحص جميع ملفات Python للأخطاء التركيبية"""
        print("\n🔍 فحص ملفات Python...")
        
        python_files = list(Path('.').rglob('*.py'))
        for py_file in python_files:
            try:
                py_compile.compile(str(py_file), doraise=True)
                self.log_success(f"ملف Python سليم: {py_file}")
            except py_compile.PyCompileError as e:
                self.log_error(f"خطأ تركيبي في {py_file}: {e}")
    
    def check_json_files(self):
        """فحص جميع ملفات JSON"""
        print("\n🔍 فحص ملفات JSON...")
        
        json_files = list(Path('.').rglob('*.json'))
        for json_file in json_files:
            try:
                with open(json_file, 'r', encoding='utf-8') as f:
                    json.load(f)
                self.log_success(f"ملف JSON سليم: {json_file}")
            except json.JSONDecodeError as e:
                self.log_error(f"خطأ في JSON {json_file}: {e}")
            except Exception as e:
                self.log_error(f"خطأ في قراءة {json_file}: {e}")
    
    def check_requirements(self):
        """فحص ملف المتطلبات"""
        print("\n🔍 فحص متطلبات المشروع...")
        
        if not os.path.exists('requirements.txt'):
            self.log_error("ملف requirements.txt غير موجود")
            return
            
        self.log_success("ملف requirements.txt موجود")
        
        # فحص Python version
        try:
            result = subprocess.run([sys.executable, '--version'], 
                                  capture_output=True, text=True)
            current_version = result.stdout.strip()
            self.log_success(f"إصدار Python الحالي: {current_version}")
            
            if os.path.exists('runtime.txt'):
                with open('runtime.txt', 'r') as f:
                    required_version = f.read().strip()
                if required_version not in current_version:
                    self.log_warning(f"إصدار Python مختلف. المطلوب: {required_version}")
                else:
                    self.log_success("إصدار Python متطابق")
        except Exception as e:
            self.log_warning(f"تعذر فحص إصدار Python: {e}")
    
    def check_config_files(self):
        """فحص ملفات الإعدادات"""
        print("\n🔍 فحص ملفات الإعدادات...")
        
        config_files = ['config.py', 'app.json', 'Dockerfile', 'Procfile']
        for config_file in config_files:
            if os.path.exists(config_file):
                self.log_success(f"ملف الإعداد موجود: {config_file}")
            else:
                self.log_warning(f"ملف الإعداد مفقود: {config_file}")
        
        # فحص ملف البيئة
        if os.path.exists('.env'):
            self.log_success("ملف .env موجود")
        elif os.path.exists('sample.env'):
            self.log_warning("ملف .env مفقود، لكن sample.env موجود")
        else:
            self.log_warning("لا يوجد ملف .env أو sample.env")
    
    def check_project_structure(self):
        """فحص بنية المشروع"""
        print("\n🔍 فحص بنية المشروع...")
        
        required_dirs = ['ZeMusic', 'ZeMusic/core', 'ZeMusic/plugins', 'strings']
        for dir_name in required_dirs:
            if os.path.exists(dir_name):
                self.log_success(f"مجلد موجود: {dir_name}")
            else:
                self.log_error(f"مجلد مفقود: {dir_name}")
        
        # فحص الملفات الأساسية
        required_files = [
            'ZeMusic/__init__.py',
            'ZeMusic/__main__.py', 
            'config.py'
        ]
        for file_name in required_files:
            if os.path.exists(file_name):
                self.log_success(f"ملف أساسي موجود: {file_name}")
            else:
                self.log_error(f"ملف أساسي مفقود: {file_name}")
    
    def check_imports(self):
        """فحص الاستيرادات الأساسية"""
        print("\n🔍 فحص الاستيرادات الأساسية...")
        
        try:
            import config
            self.log_success("تم استيراد config بنجاح")
        except Exception as e:
            self.log_error(f"خطأ في استيراد config: {e}")
        
        try:
            import ZeMusic
            self.log_success("تم استيراد ZeMusic بنجاح")
        except Exception as e:
            self.log_warning(f"خطأ في استيراد ZeMusic (قد يكون بسبب المتطلبات): {e}")
    
    def generate_report(self):
        """إنشاء التقرير النهائي"""
        print("\n" + "="*60)
        print("📊 تقرير الفحص النهائي")
        print("="*60)
        
        print(f"✅ العناصر السليمة: {self.success_count}")
        print(f"⚠️ التحذيرات: {len(self.warnings)}")
        print(f"❌ الأخطاء: {len(self.errors)}")
        
        if self.errors:
            print("\n❌ الأخطاء المكتشفة:")
            for error in self.errors:
                print(f"  {error}")
        
        if self.warnings:
            print("\n⚠️ التحذيرات:")
            for warning in self.warnings:
                print(f"  {warning}")
        
        # حالة المشروع العامة
        if not self.errors:
            if not self.warnings:
                print("\n🎉 حالة المشروع: ممتاز - جاهز للإنتاج")
            else:
                print("\n👍 حالة المشروع: جيد - يحتاج بعض التحسينات")
        else:
            print("\n🔧 حالة المشروع: يحتاج إصلاح")
        
        print("="*60)

def main():
    print("🔍 بدء فحص شامل لمشروع ZeMusic Bot")
    print("="*60)
    
    checker = ProjectChecker()
    
    # تشغيل جميع الفحوصات
    checker.check_project_structure()
    checker.check_python_files()
    checker.check_json_files()
    checker.check_requirements()
    checker.check_config_files()
    checker.check_imports()
    
    # إنشاء التقرير
    checker.generate_report()
    
    # إرجاع كود الخروج
    return 1 if checker.errors else 0

if __name__ == "__main__":
    sys.exit(main())