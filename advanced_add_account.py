import os
import re
import uuid
import asyncio
import random
from datetime import datetime
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import (
    SessionPasswordNeededError, PhoneCodeInvalidError, 
    PhoneCodeExpiredError, FloodWaitError
)

# === الإعدادات ===
API_ID = int(os.getenv('TG_API_ID', '26924046'))
API_HASH = os.getenv('TG_API_HASH', '4c6ef4cee5e129b7a674de156e2bcc15')

# قائمة أجهزة للمحاكاة
DEVICES = [
    {
        'device_model': 'Samsung SM-G991B',
        'system_version': 'Android 13 (API 33)',
        'app_version': 'Telegram 10.2.0',
        'lang_code': 'ar'
    },
    {
        'device_model': 'Google Pixel 7',
        'system_version': 'Android 14 (API 34)',
        'app_version': 'Telegram 10.3.0',
        'lang_code': 'en'
    }
]

def get_random_device():
    """اختيار جهاز عشوائي"""
    return random.choice(DEVICES)

def validate_phone_number(phone):
    """التحقق من صحة رقم الهاتف"""
    pattern = r'^\+\d{7,15}$'
    return bool(re.match(pattern, phone))

def validate_verification_code(code):
    """التحقق من صحة رمز التأكيد"""
    clean_code = code.replace(' ', '').replace('-', '')
    return bool(re.match(r'^\d{5,6}$', clean_code))

async def create_telethon_client(session_string=None):
    """إنشاء عميل Telethon مع إعدادات عشوائية"""
    device = get_random_device()
    
    if session_string:
        session = StringSession(session_string)
    else:
        session = StringSession()
    
    client = TelegramClient(
        session,
        API_ID,
        API_HASH,
        device_model=device['device_model'],
        system_version=device['system_version'],
        app_version=device['app_version'],
        lang_code=device['lang_code'],
        system_lang_code=device['lang_code']
    )
    
    return client, device

async def validate_session_string(session_string):
    """
    التحقق من صحة session string
    
    Returns:
        dict: {'valid': bool, 'account_info': dict, 'message': str}
    """
    try:
        client, device = await create_telethon_client(session_string)
        await client.connect()
        
        if not await client.is_user_authorized():
            await client.disconnect()
            return {
                'valid': False,
                'message': '❌ Session string غير صالح أو منتهي الصلاحية'
            }
        
        me = await client.get_me()
        await client.disconnect()
        
        return {
            'valid': True,
            'account_info': {
                'user_id': me.id,
                'phone': me.phone,
                'username': me.username,
                'first_name': me.first_name,
                'last_name': me.last_name,
                'is_premium': me.premium if hasattr(me, 'premium') else False
            },
            'device_info': device,
            'message': '✅ Session string صالح'
        }
        
    except Exception as e:
        return {
            'valid': False,
            'message': f'❌ خطأ في التحقق: {str(e)}'
        }

async def send_verification_code(phone):
    """
    إرسال رمز التحقق لرقم الهاتف
    
    Returns:
        dict: {'success': bool, 'session_data': dict, 'message': str}
    """
    try:
        if not validate_phone_number(phone):
            return {
                'success': False,
                'message': '❌ رقم الهاتف غير صالح. استخدم صيغة دولية (+1234567890)'
            }
        
        client, device = await create_telethon_client()
        await client.connect()
        
        # إرسال رمز التحقق
        sent = await client.send_code_request(phone, force_sms=True)
        
        # حفظ بيانات الجلسة
        session_data = {
            'client_session': client.session.save(),
            'phone': phone,
            'phone_code_hash': sent.phone_code_hash,
            'device_info': device
        }
        
        await client.disconnect()
        
        return {
            'success': True,
            'session_data': session_data,
            'message': '✅ تم إرسال رمز التحقق عبر SMS'
        }
        
    except FloodWaitError as e:
        return {
            'success': False,
            'message': f'❌ يجب الانتظار {e.seconds} ثانية قبل المحاولة مرة أخرى'
        }
    except Exception as e:
        return {
            'success': False,
            'message': f'❌ فشل إرسال رمز التحقق: {str(e)}'
        }

async def verify_code_and_login(session_data, verification_code):
    """
    التحقق من رمز التأكيد وتسجيل الدخول
    
    Returns:
        dict: {'success': bool, 'requires_2fa': bool, 'account_info': dict, 'message': str}
    """
    try:
        if not validate_verification_code(verification_code):
            return {
                'success': False,
                'message': '❌ رمز التحقق غير صالح. يجب أن يكون 5-6 أرقام'
            }
        
        # تنظيف الرمز
        clean_code = verification_code.replace(' ', '').replace('-', '')
        
        # استعادة العميل
        client, _ = await create_telethon_client(session_data['client_session'])
        await client.connect()
        
        try:
            # محاولة تسجيل الدخول
            await client.sign_in(
                phone=session_data['phone'],
                code=clean_code,
                phone_code_hash=session_data['phone_code_hash']
            )
            
            # نجح تسجيل الدخول
            me = await client.get_me()
            final_session = client.session.save()
            await client.disconnect()
            
            return {
                'success': True,
                'requires_2fa': False,
                'account_info': {
                    'user_id': me.id,
                    'phone': me.phone,
                    'username': me.username,
                    'first_name': me.first_name,
                    'last_name': me.last_name,
                    'session_string': final_session
                },
                'device_info': session_data['device_info'],
                'message': '✅ تم تسجيل الدخول بنجاح'
            }
            
        except SessionPasswordNeededError:
            # يحتاج كلمة مرور ثنائية
            await client.disconnect()
            return {
                'success': False,
                'requires_2fa': True,
                'session_data': session_data,
                'message': '🔒 هذا الحساب محمي بكلمة مرور ثنائية'
            }
            
        except (PhoneCodeInvalidError, PhoneCodeExpiredError) as e:
            await client.disconnect()
            return {
                'success': False,
                'message': f'❌ {str(e)}'
            }
            
    except Exception as e:
        return {
            'success': False,
            'message': f'❌ فشل التحقق: {str(e)}'
        }

async def verify_2fa_password(session_data, password):
    """
    التحقق من كلمة المرور الثنائية
    
    Returns:
        dict: {'success': bool, 'account_info': dict, 'message': str}
    """
    try:
        # استعادة العميل
        client, _ = await create_telethon_client(session_data['client_session'])
        await client.connect()
        
        # تسجيل الدخول بكلمة المرور
        await client.sign_in(password=password)
        
        # الحصول على معلومات الحساب
        me = await client.get_me()
        final_session = client.session.save()
        await client.disconnect()
        
        return {
            'success': True,
            'account_info': {
                'user_id': me.id,
                'phone': me.phone,
                'username': me.username,
                'first_name': me.first_name,
                'last_name': me.last_name,
                'session_string': final_session
            },
            'device_info': session_data['device_info'],
            'message': '✅ تم تسجيل الدخول بنجاح'
        }
        
    except Exception as e:
        return {
            'success': False,
            'message': f'❌ كلمة المرور غير صحيحة: {str(e)}'
        }

async def add_account_via_session(session_string):
    """
    إضافة حساب باستخدام session string جاهز
    
    Returns:
        dict: معلومات الحساب المضاف
    """
    # التحقق من صحة الجلسة
    validation_result = await validate_session_string(session_string)
    
    if not validation_result['valid']:
        return validation_result
    
    # إنشاء معرف فريد للحساب
    account_id = str(uuid.uuid4())
    timestamp = datetime.now()
    
    account_data = {
        'id': account_id,
        'session_string': session_string,
        'account_info': validation_result['account_info'],
        'device_info': validation_result['device_info'],
        'created_at': timestamp.isoformat(),
        'status': 'active'
    }
    
    return {
        'success': True,
        'account_data': account_data,
        'message': '✅ تم إضافة الحساب بنجاح باستخدام Session String'
    }

async def add_account_via_phone(phone):
    """
    إضافة حساب باستخدام رقم الهاتف (عملية تفاعلية)
    
    Returns:
        dict: معلومات الحساب المضاف أو خطأ
    """
    # المرحلة 1: إرسال رمز التحقق
    sms_result = await send_verification_code(phone)
    if not sms_result['success']:
        return sms_result
    
    print(sms_result['message'])
    
    # المرحلة 2: طلب رمز التحقق
    verification_code = input("🔢 أدخل رمز التحقق: ").strip()
    
    verify_result = await verify_code_and_login(sms_result['session_data'], verification_code)
    
    # المرحلة 3: التحقق من الحاجة لكلمة مرور ثنائية
    if verify_result.get('requires_2fa'):
        print(verify_result['message'])
        password = input("🔒 أدخل كلمة المرور الثنائية: ").strip()
        verify_result = await verify_2fa_password(sms_result['session_data'], password)
    
    if not verify_result['success']:
        return verify_result
    
    # إنشاء بيانات الحساب
    account_id = str(uuid.uuid4())
    timestamp = datetime.now()
    
    account_data = {
        'id': account_id,
        'session_string': verify_result['account_info']['session_string'],
        'account_info': {k: v for k, v in verify_result['account_info'].items() if k != 'session_string'},
        'device_info': verify_result['device_info'],
        'created_at': timestamp.isoformat(),
        'status': 'active'
    }
    
    return {
        'success': True,
        'account_data': account_data,
        'message': '✅ تم إضافة الحساب بنجاح باستخدام رقم الهاتف'
    }

# === مثال على الاستخدام ===
async def interactive_example():
    """مثال تفاعلي على الاستخدام"""
    
    print("🔹" * 30)
    print("    نظام إضافة حسابات Telegram")
    print("🔹" * 30)
    
    while True:
        print("\nاختر طريقة الإضافة:")
        print("1️⃣ Session String جاهز")
        print("2️⃣ رقم الهاتف")
        print("3️⃣ اختبار session string")
        print("0️⃣ خروج")
        
        choice = input("\n👈 اختيارك: ").strip()
        
        if choice == "1":
            session = input("🔑 أدخل Session String: ").strip()
            result = await add_account_via_session(session)
            
        elif choice == "2":
            phone = input("📱 أدخل رقم الهاتف (+1234567890): ").strip()
            result = await add_account_via_phone(phone)
            
        elif choice == "3":
            session = input("🔍 أدخل Session String للاختبار: ").strip()
            result = await validate_session_string(session)
            
        elif choice == "0":
            print("👋 مع السلامة!")
            break
            
        else:
            print("❌ اختيار غير صالح")
            continue
        
        # عرض النتيجة
        print("\n" + "="*50)
        print(result.get('message', ''))
        
        if result.get('success') and 'account_data' in result:
            info = result['account_data']['account_info']
            device = result['account_data']['device_info']
            
            print("\n📋 تفاصيل الحساب:")
            print(f"👤 الاسم: {info.get('first_name', 'غير متاح')}")
            print(f"📱 الهاتف: {info.get('phone', 'غير متاح')}")
            print(f"🆔 المعرف: {info.get('user_id', 'غير متاح')}")
            print(f"👤 اليوزر: @{info.get('username') or 'غير متاح'}")
            print(f"📱 الجهاز: {device.get('device_model', 'غير متاح')}")
            print(f"💎 Premium: {'نعم' if info.get('is_premium') else 'لا'}")
            
        elif result.get('valid') and 'account_info' in result:
            info = result['account_info']
            print(f"\n✅ Session صالح:")
            print(f"👤 الاسم: {info.get('first_name', 'غير متاح')}")
            print(f"📱 الهاتف: {info.get('phone', 'غير متاح')}")
            print(f"🆔 المعرف: {info.get('user_id', 'غير متاح')}")

if __name__ == "__main__":
    asyncio.run(interactive_example())