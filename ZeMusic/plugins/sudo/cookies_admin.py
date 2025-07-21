# -*- coding: utf-8 -*-
"""
أوامر إدارة Cookies للمطورين
"""

import os
import time
from datetime import datetime
from pathlib import Path

from ZeMusic.pyrogram_compatibility import filters, Message, InlineKeyboardMarkup, InlineKeyboardButton
from ZeMusic import app
from ZeMusic.misc import SUDOERS
from ZeMusic.utils.decorators.language import language
from ZeMusic.logging import LOGGER

@app.on_message(filters.command(["cookies", "كوكيز"]) & SUDOERS)
@language
async def cookies_admin(client, message: Message, _):
    """عرض إحصائيات cookies"""
    try:
        from ZeMusic.core.cookies_manager import cookies_manager
        
        # تهيئة المدير إذا لم يكن مهيئاً
        if not cookies_manager.available_cookies:
            await cookies_manager.initialize()
        
        stats = await cookies_manager.get_statistics()
        
        text = "🍪 **إحصائيات ملفات Cookies**\n\n"
        text += f"📊 **الإحصائيات العامة:**\n"
        text += f"• إجمالي الملفات: `{stats['total_cookies']}`\n"
        text += f"• الملفات النشطة: `{stats['active_cookies']}`\n"
        text += f"• الملفات المحظورة: `{stats['blocked_cookies']}`\n"
        text += f"• معدل النجاح: `{stats['success_rate']}%`\n\n"
        
        text += f"📈 **إحصائيات الاستخدام:**\n"
        usage = stats['usage_stats']
        text += f"• إجمالي الطلبات: `{usage['total_requests']}`\n"
        text += f"• الطلبات الناجحة: `{usage['successful_requests']}`\n"
        text += f"• الطلبات الفاشلة: `{usage['failed_requests']}`\n"
        text += f"• Cookies محظورة: `{usage['cookies_blocked']}`\n"
        text += f"• Cookies مسترد: `{usage['cookies_recovered']}`\n\n"
        
        if stats['cookies_details']:
            text += f"📝 **تفاصيل الملفات:**\n"
            for cookie in stats['cookies_details'][:10]:  # أول 10 ملفات
                status_icon = "🟢" if cookie['active'] else "🔴"
                blocked_until = cookie.get('blocked_until', 0)
                if blocked_until > int(time.time()):
                    blocked_time = datetime.fromtimestamp(blocked_until).strftime("%H:%M")
                    status_text = f"محظور حتى {blocked_time}"
                else:
                    status_text = "نشط" if cookie['active'] else "معطل"
                
                text += (f"{status_icon} `{cookie['file']}`\n"
                        f"   ├ الحالة: {status_text}\n"
                        f"   ├ النجاح: {cookie['success_count']}\n"
                        f"   ├ الفشل: {cookie['failures']}\n"
                        f"   └ الطلبات: {cookie['total_requests']}\n\n")
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔄 تحديث", callback_data="cookies_refresh"),
                InlineKeyboardButton("🧹 إعادة تعيين", callback_data="cookies_reset")
            ],
            [
                InlineKeyboardButton("📋 التفاصيل", callback_data="cookies_details"),
                InlineKeyboardButton("🗑️ حذف ملف", callback_data="cookies_delete")
            ],
            [
                InlineKeyboardButton("📁 إضافة ملف", callback_data="cookies_add_help"),
                InlineKeyboardButton("🔍 فحص الملفات", callback_data="cookies_scan")
            ],
            [InlineKeyboardButton("❌ إغلاق", callback_data="close")]
        ])
        
        await message.reply_text(text, reply_markup=keyboard)
        
    except ImportError:
        await message.reply_text("❌ مدير Cookies غير متاح")
    except Exception as e:
        LOGGER(__name__).error(f"خطأ في cookies_admin: {e}")
        await message.reply_text(f"❌ حدث خطأ: {str(e)}")

@app.on_callback_query(filters.regex("cookies_refresh") & SUDOERS)
async def cookies_refresh_callback(client, callback_query):
    """تحديث إحصائيات cookies"""
    try:
        from ZeMusic.core.cookies_manager import cookies_manager
        
        await cookies_manager.initialize()
        stats = await cookies_manager.get_statistics()
        
        text = "🍪 **إحصائيات ملفات Cookies** (محدث)\n\n"
        text += f"📊 **الإحصائيات العامة:**\n"
        text += f"• إجمالي الملفات: `{stats['total_cookies']}`\n"
        text += f"• الملفات النشطة: `{stats['active_cookies']}`\n"
        text += f"• الملفات المحظورة: `{stats['blocked_cookies']}`\n"
        text += f"• معدل النجاح: `{stats['success_rate']}%`\n\n"
        
        text += f"📈 **إحصائيات الاستخدام:**\n"
        usage = stats['usage_stats']
        text += f"• إجمالي الطلبات: `{usage['total_requests']}`\n"
        text += f"• الطلبات الناجحة: `{usage['successful_requests']}`\n"
        text += f"• الطلبات الفاشلة: `{usage['failed_requests']}`\n"
        text += f"• Cookies محظورة: `{usage['cookies_blocked']}`\n"
        text += f"• Cookies مسترد: `{usage['cookies_recovered']}`\n"
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔄 تحديث", callback_data="cookies_refresh"),
                InlineKeyboardButton("🧹 إعادة تعيين", callback_data="cookies_reset")
            ],
            [
                InlineKeyboardButton("📋 التفاصيل", callback_data="cookies_details"),
                InlineKeyboardButton("⚙️ الإعدادات", callback_data="cookies_settings")
            ],
            [InlineKeyboardButton("❌ إغلاق", callback_data="close")]
        ])
        
        await callback_query.edit_message_text(text, reply_markup=keyboard)
        await callback_query.answer("✅ تم التحديث")
        
    except Exception as e:
        await callback_query.answer(f"❌ خطأ: {str(e)}", show_alert=True)

@app.on_callback_query(filters.regex("cookies_reset") & SUDOERS)
async def cookies_reset_callback(client, callback_query):
    """إعادة تعيين جميع cookies"""
    try:
        from ZeMusic.core.cookies_manager import cookies_manager
        
        await cookies_manager.reset_all_cookies()
        await callback_query.answer("✅ تم إعادة تعيين جميع الcookies", show_alert=True)
        
        # تحديث الرسالة
        stats = await cookies_manager.get_statistics()
        text = "🍪 **إحصائيات ملفات Cookies** (تم إعادة التعيين)\n\n"
        text += f"📊 **الإحصائيات العامة:**\n"
        text += f"• إجمالي الملفات: `{stats['total_cookies']}`\n"
        text += f"• الملفات النشطة: `{stats['active_cookies']}`\n"
        text += f"• الملفات المحظورة: `{stats['blocked_cookies']}`\n"
        text += f"• معدل النجاح: `{stats['success_rate']}%`\n"
        
        keyboard = InlineKeyboardMarkup([
            [
                InlineKeyboardButton("🔄 تحديث", callback_data="cookies_refresh"),
                InlineKeyboardButton("🧹 إعادة تعيين", callback_data="cookies_reset")
            ],
            [
                InlineKeyboardButton("📋 التفاصيل", callback_data="cookies_details"),
                InlineKeyboardButton("⚙️ الإعدادات", callback_data="cookies_settings")
            ],
            [InlineKeyboardButton("❌ إغلاق", callback_data="close")]
        ])
        
        await callback_query.edit_message_text(text, reply_markup=keyboard)
        
    except Exception as e:
        await callback_query.answer(f"❌ خطأ: {str(e)}", show_alert=True)

@app.on_callback_query(filters.regex("cookies_details") & SUDOERS)
async def cookies_details_callback(client, callback_query):
    """عرض تفاصيل مفصلة لـ cookies"""
    try:
        from ZeMusic.core.cookies_manager import cookies_manager
        
        stats = await cookies_manager.get_statistics()
        
        text = "📋 **تفاصيل ملفات Cookies**\n\n"
        
        if not stats['cookies_details']:
            text += "لا توجد ملفات cookies"
        else:
            for i, cookie in enumerate(stats['cookies_details'], 1):
                status_icon = "🟢" if cookie['active'] else "🔴"
                blocked_until = cookie.get('blocked_until', 0)
                
                if blocked_until > int(time.time()):
                    blocked_time = datetime.fromtimestamp(blocked_until).strftime("%H:%M:%S")
                    status_text = f"محظور حتى {blocked_time}"
                else:
                    status_text = "نشط" if cookie['active'] else "معطل"
                
                success_rate = 0
                if cookie['total_requests'] > 0:
                    success_rate = (cookie['success_count'] / cookie['total_requests']) * 100
                
                text += (f"{status_icon} **{i}. {cookie['file']}**\n"
                        f"   • الحالة: `{status_text}`\n"
                        f"   • النجاح: `{cookie['success_count']}`\n"
                        f"   • الفشل: `{cookie['failures']}`\n"
                        f"   • إجمالي الطلبات: `{cookie['total_requests']}`\n"
                        f"   • معدل النجاح: `{success_rate:.1f}%`\n\n")
                
                if i >= 15:  # حد أقصى 15 ملف لتجنب الرسائل الطويلة
                    text += f"... وملفات أخرى ({len(stats['cookies_details']) - 15})"
                    break
        
        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 رجوع", callback_data="cookies_refresh")]
        ])
        
        await callback_query.edit_message_text(text, reply_markup=keyboard)
        await callback_query.answer()
        
    except Exception as e:
        await callback_query.answer(f"❌ خطأ: {str(e)}", show_alert=True)

@app.on_message(filters.command(["scan_cookies", "فحص_كوكيز"]) & SUDOERS)
@language
async def scan_cookies_command(client, message: Message, _):
    """فحص وإعادة تحميل ملفات cookies"""
    try:
        from ZeMusic.core.cookies_manager import cookies_manager
        
        await message.reply_text("🔍 بدء فحص ملفات cookies...")
        
        # إعادة تهيئة
        await cookies_manager.initialize()
        
        # فحص المجلد
        cookies_dir = Path("cookies")
        total_files = len(list(cookies_dir.glob("*.txt")))
        
        stats = await cookies_manager.get_statistics()
        
        text = "✅ **تم فحص ملفات Cookies**\n\n"
        text += f"📁 الملفات الموجودة: `{total_files}`\n"
        text += f"✅ الملفات الصالحة: `{stats['active_cookies']}`\n"
        text += f"❌ الملفات المعطلة: `{stats['blocked_cookies']}`\n"
        
        if stats['cookies_details']:
            text += "\n📝 **الملفات المكتشفة:**\n"
            for cookie in stats['cookies_details'][:10]:
                status = "✅" if cookie['active'] else "❌"
                text += f"{status} `{cookie['file']}`\n"
        
        await message.reply_text(text)
        
    except ImportError:
        await message.reply_text("❌ مدير Cookies غير متاح")
    except Exception as e:
        LOGGER(__name__).error(f"خطأ في scan_cookies: {e}")
        await message.reply_text(f"❌ حدث خطأ: {str(e)}")

@app.on_message(filters.command(["add_cookie", "اضافة_كوكيز", "اضافه_كوكيز"]) & SUDOERS)
@language
async def add_cookie_command(client, message: Message, _):
    """إضافة ملف cookies جديد"""
    
    # التحقق من وجود ملف مرفق
    if not message.reply_to_message or not message.reply_to_message.document:
        text = """📁 **إضافة ملف Cookies جديد**

🔧 **طريقة الاستخدام:**
1. ارسل أمر `/add_cookie` مع الرد على ملف cookies
2. أو ارسل الملف مع caption يحتوي على `/add_cookie`

📋 **متطلبات الملف:**
• نوع الملف: `.txt`
• تنسيق: Netscape cookies format
• حجم أقل من 10MB
• يحتوي على cookies صالحة

💡 **مثال:**
ارسل ملف `cookies.txt` مع الرد بـ `/add_cookie`"""
        
        await message.reply_text(text)
        return
    
    try:
        document = message.reply_to_message.document
        
        # التحقق من نوع الملف
        if not document.file_name.endswith('.txt'):
            await message.reply_text("❌ يجب أن يكون الملف من نوع .txt")
            return
        
        # التحقق من حجم الملف (أقل من 10MB)
        if document.file_size > 10 * 1024 * 1024:
            await message.reply_text("❌ حجم الملف كبير جداً (أقصى حد 10MB)")
            return
        
        # إنشاء اسم ملف فريد
        import time
        timestamp = int(time.time())
        base_name = document.file_name.replace('.txt', '')
        new_filename = f"cookies_{base_name}_{timestamp}.txt"
        
        await message.reply_text("📥 جاري تحميل ملف cookies...")
        
        # تحميل الملف
        cookies_path = Path("cookies") / new_filename
        await client.download_media(document, str(cookies_path))
        
        # التحقق من صحة محتوى الملف
        if not await validate_cookie_file(cookies_path):
            cookies_path.unlink()  # حذف الملف
            await message.reply_text("❌ ملف cookies غير صالح أو فارغ")
            return
        
        # إعادة فحص النظام
        from ZeMusic.core.cookies_manager import cookies_manager
        scan_result = await cookies_manager._scan_cookies_files()
        await cookies_manager._update_available_cookies()
        await cookies_manager._save_cookies_status()
        
        # الحصول على إحصائيات محدثة
        stats = await cookies_manager.get_statistics()
        
        text = f"""✅ **تم إضافة ملف Cookies بنجاح!**

📁 **معلومات الملف:**
• الاسم: `{new_filename}`
• الحجم: `{document.file_size / 1024:.1f} KB`
• المسار: `cookies/{new_filename}`

📊 **إحصائيات محدثة:**
• إجمالي الملفات: `{stats['total_cookies']}`
• الملفات النشطة: `{stats['active_cookies']}`
• الملفات المحظورة: `{stats['blocked_cookies']}`

🎉 **الملف جاهز للاستخدام فوراً!**"""
        
        await message.reply_text(text)
        LOGGER(__name__).info(f"✅ تم إضافة ملف cookies جديد: {new_filename} بواسطة {message.from_user.id}")
        
    except Exception as e:
        LOGGER(__name__).error(f"خطأ في إضافة cookies: {e}")
        await message.reply_text(f"❌ حدث خطأ في إضافة الملف: {str(e)}")

async def validate_cookie_file(file_path: Path) -> bool:
    """التحقق من صحة ملف cookies"""
    try:
        if not file_path.exists() or file_path.stat().st_size == 0:
            return False
        
        # قراءة الملف والتحقق من المحتوى
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read().strip()
        
        if not content:
            return False
        
        # التحقق من وجود نمط cookies أساسي
        lines = content.split('\n')
        valid_lines = 0
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('#'):
                continue
            
            # تحقق بسيط من تنسيق cookies
            parts = line.split('\t')
            if len(parts) >= 6:  # تنسيق Netscape الأساسي
                valid_lines += 1
        
        # يجب أن يحتوي على 3 cookies صالحة على الأقل
        return valid_lines >= 3
        
    except Exception as e:
        LOGGER(__name__).error(f"خطأ في التحقق من ملف cookies: {e}")
        return False

@app.on_message(filters.command(["remove_cookie", "حذف_كوكيز"]) & SUDOERS)
@language
async def remove_cookie_command(client, message: Message, _):
    """حذف ملف cookies محدد"""
    
    # التحقق من وجود اسم الملف
    if len(message.command) < 2:
        from ZeMusic.core.cookies_manager import cookies_manager
        stats = await cookies_manager.get_statistics()
        
        if not stats['cookies_details']:
            await message.reply_text("❌ لا توجد ملفات cookies")
            return
        
        text = "🗑️ **حذف ملف Cookies**\n\n"
        text += "📋 **الملفات المتاحة:**\n"
        
        for i, cookie in enumerate(stats['cookies_details'], 1):
            status = "🟢" if cookie['active'] else "🔴"
            text += f"{status} `{i}.` {cookie['file']}\n"
        
        text += f"\n💡 **الاستخدام:**\n`/remove_cookie اسم_الملف`\n\n"
        text += f"📝 **مثال:**\n`/remove_cookie cookies1.txt`"
        
        await message.reply_text(text)
        return
    
    filename = message.command[1]
    
    try:
        # البحث عن الملف
        cookies_path = Path("cookies") / filename
        
        if not cookies_path.exists():
            await message.reply_text(f"❌ الملف `{filename}` غير موجود")
            return
        
        # نقل الملف إلى مجلد المحذوفات بدلاً من حذفه نهائياً
        deleted_dir = Path("cookies") / "deleted"
        deleted_dir.mkdir(exist_ok=True)
        
        import time
        timestamp = int(time.time())
        backup_name = f"{filename.replace('.txt', '')}_{timestamp}.txt"
        backup_path = deleted_dir / backup_name
        
        cookies_path.rename(backup_path)
        
        # إعادة فحص النظام
        from ZeMusic.core.cookies_manager import cookies_manager
        await cookies_manager._scan_cookies_files()
        await cookies_manager._update_available_cookies()
        await cookies_manager._save_cookies_status()
        
        # الحصول على إحصائيات محدثة
        stats = await cookies_manager.get_statistics()
        
        text = f"""✅ **تم حذف ملف Cookies بنجاح!**

🗑️ **معلومات الحذف:**
• الملف المحذوف: `{filename}`
• النسخة الاحتياطية: `deleted/{backup_name}`

📊 **إحصائيات محدثة:**
• إجمالي الملفات: `{stats['total_cookies']}`
• الملفات النشطة: `{stats['active_cookies']}`
• الملفات المحظورة: `{stats['blocked_cookies']}`

ℹ️ **ملاحظة:** تم حفظ نسخة احتياطية في مجلد deleted"""
        
        await message.reply_text(text)
        LOGGER(__name__).info(f"🗑️ تم حذف ملف cookies: {filename} بواسطة {message.from_user.id}")
        
    except Exception as e:
        LOGGER(__name__).error(f"خطأ في حذف cookies: {e}")
        await message.reply_text(f"❌ حدث خطأ في حذف الملف: {str(e)}")

@app.on_message(filters.command(["cookies_info", "معلومات_كوكيز"]) & SUDOERS)
@language  
async def cookies_info_command(client, message: Message, _):
    """معلومات مفصلة عن نظام cookies"""
    text = """🍪 **نظام إدارة Cookies الذكي**

🔥 **المميزات:**
• تدوير تلقائي للcookies
• كشف وحظر الcookies المعطلة
• إحصائيات مفصلة للاستخدام
• استرداد تلقائي للcookies المحظورة
• نسخ احتياطي للملفات المعطلة
• إضافة وحذف ديناميكي للملفات

⚙️ **الإعدادات:**
• عدد المحاولات قبل الحظر: `3`
• مدة الحظر: `60 دقيقة`
• تأخير التدوير: `2 ثانية`

📁 **المجلدات:**
• الملفات النشطة: `cookies/`
• النسخ الاحتياطية: `cookies/invalid/`
• الملفات المحذوفة: `cookies/deleted/`
• ملف الحالة: `cookies/cookies_status.json`

🔧 **الأوامر:**
• `/cookies` - عرض الإحصائيات
• `/scan_cookies` - فحص الملفات
• `/add_cookie` - إضافة ملف جديد
• `/remove_cookie` - حذف ملف محدد
• `/cookies_info` - هذه المعلومات

💡 **إضافة ملف جديد:**
1. ارسل ملف .txt يحتوي على cookies
2. اكتب `/add_cookie` في الرد على الملف

ℹ️ **ملاحظة:** يتم حفظ الإعدادات تلقائياً"""

    await message.reply_text(text)

# معالج إضافة cookies عند إرسال ملف مع caption
@app.on_message(filters.document() & SUDOERS)
async def handle_document_upload(client, message: Message):
    """معالج تلقائي لملفات cookies المرسلة مع caption"""
    
    # التحقق من وجود ملف مرفق
    if not message.document:
        return
    
    # التحقق من وجود caption يحتوي على أمر إضافة cookies
    if not message.caption:
        return
    
    caption_lower = message.caption.lower()
    if not any(cmd in caption_lower for cmd in ['/add_cookie', 'اضافة_كوكيز', 'اضافه_كوكيز']):
        return
    
    try:
        document = message.document
        
        # التحقق من نوع الملف
        if not document.file_name.endswith('.txt'):
            await message.reply_text("❌ يجب أن يكون الملف من نوع .txt")
            return
        
        # التحقق من حجم الملف (أقل من 10MB)
        if document.file_size > 10 * 1024 * 1024:
            await message.reply_text("❌ حجم الملف كبير جداً (أقصى حد 10MB)")
            return
        
        # إنشاء اسم ملف فريد
        import time
        timestamp = int(time.time())
        base_name = document.file_name.replace('.txt', '')
        new_filename = f"cookies_{base_name}_{timestamp}.txt"
        
        # رسالة التحميل
        loading_msg = await message.reply_text("📥 جاري تحميل ملف cookies...")
        
        # تحميل الملف
        cookies_path = Path("cookies") / new_filename
        await client.download_media(document, str(cookies_path))
        
        # التحقق من صحة محتوى الملف
        if not await validate_cookie_file(cookies_path):
            cookies_path.unlink()  # حذف الملف
            await loading_msg.edit_text("❌ ملف cookies غير صالح أو فارغ")
            return
        
        # إعادة فحص النظام
        from ZeMusic.core.cookies_manager import cookies_manager
        await cookies_manager._scan_cookies_files()
        await cookies_manager._update_available_cookies()
        await cookies_manager._save_cookies_status()
        
        # الحصول على إحصائيات محدثة
        stats = await cookies_manager.get_statistics()
        
        text = f"""✅ **تم إضافة ملف Cookies بنجاح!**

📁 **معلومات الملف:**
• الاسم: `{new_filename}`
• الحجم: `{document.file_size / 1024:.1f} KB`
• المسار: `cookies/{new_filename}`

📊 **إحصائيات محدثة:**
• إجمالي الملفات: `{stats['total_cookies']}`
• الملفات النشطة: `{stats['active_cookies']}`
• الملفات المحظورة: `{stats['blocked_cookies']}`

🎉 **الملف جاهز للاستخدام فوراً!**"""
        
        await loading_msg.edit_text(text)
        LOGGER(__name__).info(f"✅ تم إضافة ملف cookies جديد عبر caption: {new_filename} بواسطة {message.from_user.id}")
        
    except Exception as e:
        LOGGER(__name__).error(f"خطأ في إضافة cookies عبر caption: {e}")
        await message.reply_text(f"❌ حدث خطأ في إضافة الملف: {str(e)}")

# معالجات callbacks إضافية
@app.on_callback_query(filters.regex("cookies_add_help") & SUDOERS)
async def cookies_add_help_callback(client, callback_query):
    """شرح كيفية إضافة ملف cookies"""
    text = """📁 **إضافة ملف Cookies جديد**

🔧 **طريقتان للإضافة:**

**1️⃣ الطريقة الأولى:**
• ارسل أمر `/add_cookie`
• اتبع التعليمات لإرفاق الملف

**2️⃣ الطريقة الثانية (سهلة):**
• ارسل ملف .txt مباشرة
• اكتب في caption: `/add_cookie`

📋 **متطلبات الملف:**
• نوع الملف: `.txt`
• تنسيق: Netscape cookies
• حجم: أقل من 10MB
• يحتوي على 3 cookies صالحة على الأقل

✅ **مثال صحيح:**
```
# ملف cookies.txt
.youtube.com	TRUE	/	FALSE	1735689600	session_token	abc123
.youtube.com	TRUE	/	FALSE	1735689600	user_pref	xyz789
```

🎉 **سيتم إضافة الملف فوراً وجاهز للاستخدام!**"""

    keyboard = InlineKeyboardMarkup([
        [InlineKeyboardButton("🔙 رجوع", callback_data="cookies_refresh")]
    ])
    
    try:
        await callback_query.edit_message_text(text, reply_markup=keyboard)
        await callback_query.answer()
    except Exception as e:
        await callback_query.answer(f"❌ خطأ: {str(e)}", show_alert=True)

@app.on_callback_query(filters.regex("cookies_delete") & SUDOERS)
async def cookies_delete_callback(client, callback_query):
    """عرض قائمة الملفات للحذف"""
    try:
        from ZeMusic.core.cookies_manager import cookies_manager
        stats = await cookies_manager.get_statistics()
        
        if not stats['cookies_details']:
            await callback_query.answer("❌ لا توجد ملفات cookies", show_alert=True)
            return
        
        text = "🗑️ **حذف ملف Cookies**\n\n"
        text += "📋 **اختر الملف المراد حذفه:**\n\n"
        
        buttons = []
        for i, cookie in enumerate(stats['cookies_details'][:10], 1):  # أول 10 ملفات
            status = "🟢" if cookie['active'] else "🔴"
            button_text = f"{status} {cookie['file']}"
            callback_data = f"delete_file_{cookie['file']}"
            buttons.append([InlineKeyboardButton(button_text, callback_data=callback_data)])
        
        buttons.append([InlineKeyboardButton("🔙 رجوع", callback_data="cookies_refresh")])
        keyboard = InlineKeyboardMarkup(buttons)
        
        await callback_query.edit_message_text(text, reply_markup=keyboard)
        await callback_query.answer()
        
    except Exception as e:
        await callback_query.answer(f"❌ خطأ: {str(e)}", show_alert=True)

@app.on_callback_query(filters.regex("cookies_scan") & SUDOERS)
async def cookies_scan_callback(client, callback_query):
    """فحص ملفات cookies عبر الواجهة"""
    try:
        await callback_query.answer("🔍 جاري فحص الملفات...")
        
        from ZeMusic.core.cookies_manager import cookies_manager
        
        # إعادة فحص الملفات
        scan_result = await cookies_manager._scan_cookies_files()
        await cookies_manager._update_available_cookies()
        
        # الحصول على إحصائيات محدثة
        stats = await cookies_manager.get_statistics()
        
        text = f"""🔍 **تم فحص مجلد Cookies**

📊 **الوضع الحالي:**
• إجمالي الملفات: `{stats['total_cookies']}`
• الملفات النشطة: `{stats['active_cookies']}`
• الملفات المحظورة: `{stats['blocked_cookies']}`
• معدل النجاح: `{stats['success_rate']}%`

✅ **تم تحديث النظام بنجاح**"""

        keyboard = InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 رجوع", callback_data="cookies_refresh")]
        ])
        
        await callback_query.edit_message_text(text, reply_markup=keyboard)
        
    except Exception as e:
        await callback_query.answer(f"❌ خطأ: {str(e)}", show_alert=True)