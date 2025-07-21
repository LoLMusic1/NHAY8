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
                InlineKeyboardButton("⚙️ الإعدادات", callback_data="cookies_settings")
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

⚙️ **الإعدادات:**
• عدد المحاولات قبل الحظر: `3`
• مدة الحظر: `60 دقيقة`
• تأخير التدوير: `2 ثانية`

📁 **المجلدات:**
• الملفات النشطة: `cookies/`
• النسخ الاحتياطية: `cookies/invalid/`
• ملف الحالة: `cookies/cookies_status.json`

🔧 **الأوامر:**
• `/cookies` - عرض الإحصائيات
• `/scan_cookies` - فحص الملفات
• `/cookies_info` - هذه المعلومات

ℹ️ **ملاحظة:** يتم حفظ الإعدادات تلقائياً"""

    await message.reply_text(text)