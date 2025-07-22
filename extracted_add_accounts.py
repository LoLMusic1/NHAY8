import os
import re
import uuid
import sqlite3
import logging
import asyncio
import random
import time
from datetime import datetime
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import (
    SessionPasswordNeededError, FloodWaitError,
    PhoneNumberInvalidError, PhoneCodeInvalidError,
    PhoneCodeExpiredError, ApiIdInvalidError,
    PhoneNumberBannedError, RPCError
)

# === إعدادات التطبيق ===
API_ID = int(os.getenv('TG_API_ID', '0'))
API_HASH = os.getenv('TG_API_HASH', '')
SESSION_TIMEOUT = 60  # ثانية

# === قائمة أجهزة Android ديناميكية ===
DEVICES = [
    {'device_model': 'Google Pixel 9 Pro', 'system_version': 'Android 15 (SDK 35)', 'app_version': 'Telegram Android 10.9.0', 'lang_code': 'en', 'lang_pack': 'android'},
]

# === دوال مساعدة ===
def get_random_device():
    """الحصول على جهاز عشوائي من القائمة"""
    return random.choice(DEVICES)

def validate_phone(phone: str) -> bool:
    """التحقق من صحة رقم الهاتف"""
    return re.match(r'^\+\d{7,15}$', phone) is not None

def validate_code(code: str) -> bool:
    """التحقق من صحة رمز التحقق"""
    code = code.replace(' ', '').replace(',', '')
    return re.match(r'^\d{5,6}$', code) is not None

def encrypt_session(session_str: str) -> str:
    """تشفير session string (يجب تطبيق تشفير حقيقي)"""
    # هنا يجب استخدام مكتبة تشفير حقيقية
    import base64
    return base64.b64encode(session_str.encode()).decode()

def decrypt_session(encrypted_session: str) -> str:
    """فك تشفير session string"""
    import base64
    return base64.b64decode(encrypted_session.encode()).decode()

async def create_client() -> TelegramClient:
    """إنشاء عميل Telethon مع إعدادات جهاز عشوائي"""
    device = get_random_device()
    client = TelegramClient(
        StringSession(), 
        API_ID, 
        API_HASH,
        device_model=device['device_model'],
        system_version=device['system_version'],
        app_version=device['app_version'],
        lang_code=device['lang_code'],
        system_lang_code=device['lang_code'],
        connection_retries=3,
        timeout=SESSION_TIMEOUT
    )
    client._device_attrs = device
    return client

# === دوال إضافة الحساب بـ Session String ===
async def add_account_with_session(session_str: str, category_name: str = "الحسابات الرئيسية") -> dict:
    """
    إضافة حساب باستخدام session string جاهز
    
    Args:
        session_str: session string الخاص بـ Telethon
        category_name: اسم الفئة لحفظ الحساب فيها
        
    Returns:
        dict: نتيجة العملية مع التفاصيل
    """
    try:
        # التحقق من صحة الجلسة
        client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
        await client.connect()
        me = await client.get_me()
        
        if not me:
            raise ValueError("الجلسة غير صالحة")
        
        phone = me.phone
        username = me.username
        
        # اختيار جهاز عشوائي
        device = get_random_device()
        device_info = {
            'app_name': device.get('app_name', 'Telegram'),
            'app_version': device['app_version'],
            'device_model': device['device_model'],
            'system_version': device['system_version']
        }
        
        # تشفير الجلسة
        encrypted_session = encrypt_session(session_str)
        
        # إنشاء معرف فريد للحساب
        account_id = str(uuid.uuid4())
        category_id = str(uuid.uuid4())
        
        # حفظ في قاعدة البيانات (هنا يجب استخدام قاعدة البيانات الخاصة بك)
        account_data = {
            'id': account_id,
            'category_id': category_id,
            'category_name': category_name,
            'username': username,
            'session_str': encrypted_session,
            'phone': phone,
            'device_info': device_info,
            'created_at': datetime.now().isoformat()
        }
        
        await client.disconnect()
        
        return {
            'success': True,
            'message': f"✅ تم إضافة الحساب بنجاح في فئة '{category_name}'!",
            'account_data': account_data,
            'details': {
                'phone': phone,
                'username': username,
                'category': category_name,
                'device': device_info
            }
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f"❌ فشل إضافة الحساب: {str(e)}",
            'error': str(e)
        }

# === دوال إضافة الحساب برقم الهاتف ===
async def add_account_with_phone(phone: str, category_name: str = "الحسابات الرئيسية") -> dict:
    """
    بدء عملية إضافة حساب برقم الهاتف
    
    Args:
        phone: رقم الهاتف بصيغة دولية
        category_name: اسم الفئة لحفظ الحساب فيها
        
    Returns:
        dict: نتيجة إرسال رمز التحقق
    """
    try:
        # التحقق من صحة رقم الهاتف
        if not validate_phone(phone):
            return {
                'success': False,
                'message': "❌ رقم الهاتف غير صالح. استخدم صيغة دولية صحيحة"
            }
        
        # إنشاء عميل مؤقت
        client = await create_client()
        await client.connect()
        
        # إرسال رمز التحقق
        sent = await client.send_code_request(phone, force_sms=True)
        
        # حفظ بيانات الجلسة للاستخدام لاحقاً
        session_data = {
            'client_session': client.session.save(),
            'phone': phone,
            'phone_code_hash': sent.phone_code_hash,
            'category_name': category_name,
            'device_info': getattr(client, '_device_attrs', get_random_device())
        }
        
        await client.disconnect()
        
        return {
            'success': True,
            'message': "✅ تم إرسال رمز التحقق إلى حسابك عبر SMS",
            'session_data': session_data,
            'next_step': 'enter_verification_code'
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f"❌ فشل إرسال رمز التحقق: {str(e)}",
            'error': str(e)
        }

async def verify_phone_code(session_data: dict, verification_code: str) -> dict:
    """
    التحقق من رمز التأكيد وإكمال تسجيل الحساب
    
    Args:
        session_data: بيانات الجلسة من المرحلة السابقة
        verification_code: رمز التحقق المرسل للهاتف
        
    Returns:
        dict: نتيجة العملية
    """
    try:
        # تنظيف رمز التحقق
        code = verification_code.replace(" ", "").replace(",", "")
        
        if not validate_code(code):
            return {
                'success': False,
                'message': "❌ رمز التحقق غير صالح. أدخل رمز مكون من 5-6 أرقام"
            }
        
        # استعادة العميل
        client = TelegramClient(
            StringSession(session_data['client_session']), 
            API_ID, 
            API_HASH
        )
        await client.connect()
        
        phone = session_data['phone']
        phone_code_hash = session_data['phone_code_hash']
        
        try:
            # محاولة تسجيل الدخول
            await client.sign_in(
                phone=phone,
                code=code,
                phone_code_hash=phone_code_hash
            )
            
            # تسجيل الدخول ناجح - إكمال التسجيل
            return await finalize_account_registration(client, session_data)
            
        except SessionPasswordNeededError:
            # الحساب محمي بكلمة مرور ثنائية
            await client.disconnect()
            return {
                'success': False,
                'message': "🔒 هذا الحساب محمي بكلمة مرور ثنائية",
                'session_data': session_data,
                'next_step': 'enter_2fa_password',
                'requires_2fa': True
            }
            
        except (PhoneCodeInvalidError, PhoneCodeExpiredError) as e:
            await client.disconnect()
            return {
                'success': False,
                'message': f"❌ {str(e)}",
                'retry_needed': True
            }
            
    except Exception as e:
        return {
            'success': False,
            'message': f"❌ فشل التحقق: {str(e)}",
            'error': str(e)
        }

async def verify_2fa_password(session_data: dict, password: str) -> dict:
    """
    التحقق من كلمة المرور الثنائية
    
    Args:
        session_data: بيانات الجلسة
        password: كلمة المرور الثنائية
        
    Returns:
        dict: نتيجة العملية
    """
    try:
        # استعادة العميل
        client = TelegramClient(
            StringSession(session_data['client_session']), 
            API_ID, 
            API_HASH
        )
        await client.connect()
        
        # تسجيل الدخول بكلمة المرور
        await client.sign_in(password=password)
        
        # إكمال التسجيل
        return await finalize_account_registration(client, session_data)
        
    except Exception as e:
        return {
            'success': False,
            'message': f"❌ فشل تسجيل الدخول بكلمة المرور: {str(e)}",
            'error': str(e)
        }

async def finalize_account_registration(client: TelegramClient, session_data: dict) -> dict:
    """
    إكمال عملية تسجيل الحساب وحفظه
    
    Args:
        client: عميل Telethon المتصل
        session_data: بيانات الجلسة
        
    Returns:
        dict: نتيجة العملية النهائية
    """
    try:
        # الحصول على معلومات الحساب
        me = await client.get_me()
        phone = session_data['phone']
        category_name = session_data['category_name']
        device_info = session_data['device_info']
        
        # حفظ جلسة Telethon مشفّرة
        session_str = client.session.save()
        encrypted_session = encrypt_session(session_str)
        
        # إنشاء معرفات فريدة
        account_id = str(uuid.uuid4())
        category_id = str(uuid.uuid4())
        
        # تحضير بيانات الحساب
        account_data = {
            'id': account_id,
            'category_id': category_id,
            'category_name': category_name,
            'username': me.username,
            'session_str': encrypted_session,
            'phone': phone,
            'device_info': device_info,
            'created_at': datetime.now().isoformat(),
            'user_id': me.id,
            'first_name': me.first_name,
            'last_name': me.last_name
        }
        
        await client.disconnect()
        
        return {
            'success': True,
            'message': f"✅ تم تسجيل الحساب بنجاح في فئة '{category_name}'!",
            'account_data': account_data,
            'details': {
                'phone': phone,
                'username': me.username,
                'user_id': me.id,
                'first_name': me.first_name,
                'category': category_name,
                'device': device_info
            }
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f"❌ فشل حفظ الحساب: {str(e)}",
            'error': str(e)
        }

# === دالة التحقق من صحة Session String ===
async def validate_session_string(session_str: str) -> dict:
    """
    التحقق من صحة session string
    
    Args:
        session_str: session string للتحقق منه
        
    Returns:
        dict: نتيجة التحقق مع تفاصيل الحساب إن كان صالحاً
    """
    try:
        client = TelegramClient(StringSession(session_str), API_ID, API_HASH)
        await client.connect()
        
        if not await client.is_user_authorized():
            await client.disconnect()
            return {
                'valid': False,
                'message': "❌ Session string غير صالح أو منتهي الصلاحية"
            }
        
        me = await client.get_me()
        await client.disconnect()
        
        return {
            'valid': True,
            'message': "✅ Session string صالح",
            'account_info': {
                'user_id': me.id,
                'phone': me.phone,
                'username': me.username,
                'first_name': me.first_name,
                'last_name': me.last_name
            }
        }
        
    except Exception as e:
        return {
            'valid': False,
            'message': f"❌ خطأ في التحقق: {str(e)}",
            'error': str(e)
        }

# === مثال على الاستخدام ===
async def main_example():
    """مثال على كيفية استخدام الدوال"""
    
    # مثال 1: إضافة حساب بـ session string
    session_string = "YOUR_SESSION_STRING_HERE"
    result = await add_account_with_session(session_string, "فئة الاختبار")
    print("نتيجة إضافة الحساب بـ session:", result)
    
    # مثال 2: إضافة حساب برقم الهاتف
    phone = "+1234567890"
    result = await add_account_with_phone(phone, "فئة الاختبار")
    
    if result['success']:
        print("تم إرسال رمز التحقق")
        
        # محاكاة إدخال رمز التحقق
        verification_code = input("أدخل رمز التحقق: ")
        
        result = await verify_phone_code(result['session_data'], verification_code)
        
        if result.get('requires_2fa'):
            # محاكاة إدخال كلمة المرور الثنائية
            password = input("أدخل كلمة المرور الثنائية: ")
            result = await verify_2fa_password(result['session_data'], password)
        
        print("النتيجة النهائية:", result)

if __name__ == "__main__":
    # تشغيل المثال
    asyncio.run(main_example())