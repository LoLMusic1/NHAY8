import os
import re
import uuid
import asyncio
from datetime import datetime
from telethon import TelegramClient
from telethon.sessions import StringSession
from telethon.errors import SessionPasswordNeededError, PhoneCodeInvalidError, PhoneCodeExpiredError

# إعدادات أساسية
API_ID = int(os.getenv('TG_API_ID', '0'))
API_HASH = os.getenv('TG_API_HASH', '')

async def add_telegram_account(session_string=None, phone=None):
    """
    دالة مبسطة لإضافة حساب تليجرام
    
    Args:
        session_string: كود الجلسة الجاهز (اختياري)
        phone: رقم الهاتف (اختياري - مطلوب إذا لم يتم توفير session_string)
    
    Returns:
        dict: معلومات الحساب المضاف أو رسالة خطأ
    """
    
    try:
        if session_string:
            # الطريقة الأولى: استخدام session string جاهز
            print("🔄 جاري التحقق من session string...")
            
            client = TelegramClient(StringSession(session_string), API_ID, API_HASH)
            await client.connect()
            
            if not await client.is_user_authorized():
                await client.disconnect()
                return {"success": False, "message": "❌ Session string غير صالح"}
            
            me = await client.get_me()
            await client.disconnect()
            
            return {
                "success": True,
                "message": "✅ تم إضافة الحساب بنجاح!",
                "account_info": {
                    "phone": me.phone,
                    "username": me.username,
                    "user_id": me.id,
                    "first_name": me.first_name,
                    "session_string": session_string
                }
            }
            
        elif phone:
            # الطريقة الثانية: استخدام رقم الهاتف
            print("📱 جاري إرسال رمز التحقق...")
            
            # التحقق من صيغة رقم الهاتف
            if not re.match(r'^\+\d{7,15}$', phone):
                return {"success": False, "message": "❌ رقم الهاتف غير صالح"}
            
            client = TelegramClient(StringSession(), API_ID, API_HASH)
            await client.connect()
            
            # إرسال رمز التحقق
            sent = await client.send_code_request(phone)
            print("✅ تم إرسال رمز التحقق")
            
            # طلب رمز التحقق من المستخدم
            code = input("🔢 أدخل رمز التحقق: ").strip().replace(" ", "")
            
            try:
                # تسجيل الدخول برمز التحقق
                await client.sign_in(phone=phone, code=code, phone_code_hash=sent.phone_code_hash)
                
            except SessionPasswordNeededError:
                # طلب كلمة المرور الثنائية
                password = input("🔒 أدخل كلمة المرور الثنائية: ").strip()
                await client.sign_in(password=password)
                
            except (PhoneCodeInvalidError, PhoneCodeExpiredError):
                await client.disconnect()
                return {"success": False, "message": "❌ رمز التحقق غير صحيح أو منتهي الصلاحية"}
            
            # الحصول على معلومات الحساب
            me = await client.get_me()
            session_str = client.session.save()
            await client.disconnect()
            
            return {
                "success": True,
                "message": "✅ تم إضافة الحساب بنجاح!",
                "account_info": {
                    "phone": me.phone,
                    "username": me.username,
                    "user_id": me.id,
                    "first_name": me.first_name,
                    "session_string": session_str
                }
            }
            
        else:
            return {"success": False, "message": "❌ يجب توفير session_string أو phone"}
            
    except Exception as e:
        return {"success": False, "message": f"❌ حدث خطأ: {str(e)}"}

# مثال على الاستخدام
async def main():
    """مثال على الاستخدام"""
    
    print("=== نظام إضافة حسابات تليجرام ===\n")
    
    choice = input("اختر طريقة الإضافة:\n1. Session String\n2. رقم الهاتف\nاختيارك (1 أو 2): ").strip()
    
    if choice == "1":
        session = input("🔑 أدخل session string: ").strip()
        result = await add_telegram_account(session_string=session)
        
    elif choice == "2":
        phone = input("📱 أدخل رقم الهاتف (مثال: +1234567890): ").strip()
        result = await add_telegram_account(phone=phone)
        
    else:
        print("❌ اختيار غير صالح")
        return
    
    # عرض النتيجة
    print("\n" + "="*50)
    print(result["message"])
    
    if result["success"]:
        info = result["account_info"]
        print(f"\n📋 معلومات الحساب:")
        print(f"📱 الهاتف: {info['phone']}")
        print(f"👤 الاسم: {info['first_name']}")
        print(f"🆔 المعرف: {info['user_id']}")
        print(f"👤 اليوزر: @{info['username'] or 'غير متاح'}")
        print(f"🔑 Session: {info['session_string'][:50]}...")

if __name__ == "__main__":
    asyncio.run(main())