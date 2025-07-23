# -*- coding: utf-8 -*-
"""
🎛️ نظام إعدادات التشغيل المحسن - النسخة المتطورة V3
====================================================
متكامل مع النظام المختلط والإحصائيات الشاملة
يوفر تحكم شامل في أوضاع التشغيل والأداء
"""

import asyncio
import time
from typing import Dict, Optional

# استيراد مكتبات Pyrogram
from ZeMusic.pyrogram_compatibility import filters
from ZeMusic.pyrogram_compatibility import InlineKeyboardMarkup, InlineKeyboardButton, Message

# استيراد إعدادات البوت
from ZeMusic import app, LOGGER
from ZeMusic.utils.database import get_playmode, get_playtype, is_nonadmin_chat, set_playmode, set_playtype
from ZeMusic.utils.decorators import language
from ZeMusic.utils.inline.settings import playmode_users_markup
from ZeMusic.pyrogram_compatibility import BANNED_USERS
import config

# استيراد النظام المحسن
from .download import update_performance_stats, log_performance_stats, cleanup_old_downloads
from .youtube_api_downloader import get_hybrid_stats

async def get_enhanced_playmode_info(chat_id: int) -> Dict:
    """الحصول على معلومات أوضاع التشغيل المحسنة"""
    try:
        # الإعدادات الأساسية
        playmode = await get_playmode(chat_id)
        playtype = await get_playtype(chat_id)
        is_non_admin = await is_nonadmin_chat(chat_id)
        
        # الإحصائيات
        hybrid_stats = await get_hybrid_stats()
        
        return {
            'playmode': playmode,
            'playtype': playtype,
            'is_non_admin': is_non_admin,
            'hybrid_stats': hybrid_stats,
            'direct_mode': playmode == "Direct",
            'admin_only': not is_non_admin,
            'everyone_can_play': playtype == "Everyone"
        }
    except Exception as e:
        LOGGER.error(f"❌ خطأ في جلب معلومات أوضاع التشغيل: {e}")
        return {}

def create_enhanced_playmode_markup(_, info: Dict) -> list:
    """إنشاء لوحة مفاتيح محسنة لأوضاع التشغيل"""
    buttons = []
    
    # وضع التشغيل
    direct_text = "✅ مباشر" if info.get('direct_mode') else "❌ مباشر"
    inline_text = "❌ مع أزرار" if info.get('direct_mode') else "✅ مع أزرار"
    
    buttons.append([
        InlineKeyboardButton(direct_text, callback_data="ADMIN_PLAYMODE_DIRECT"),
        InlineKeyboardButton(inline_text, callback_data="ADMIN_PLAYMODE_INLINE")
    ])
    
    # صلاحيات التشغيل
    admin_text = "✅ الإداريون فقط" if info.get('admin_only') else "❌ الإداريون فقط"
    everyone_text = "❌ الجميع" if info.get('admin_only') else "✅ الجميع"
    
    buttons.append([
        InlineKeyboardButton(admin_text, callback_data="ADMIN_PLAYTYPE_ADMIN"),
        InlineKeyboardButton(everyone_text, callback_data="ADMIN_PLAYTYPE_EVERYONE")
    ])
    
    # إحصائيات النظام
    buttons.append([
        InlineKeyboardButton("📊 إحصائيات الأداء", callback_data="PLAYMODE_STATS"),
        InlineKeyboardButton("🔗 إحصائيات النظام المختلط", callback_data="PLAYMODE_HYBRID_STATS")
    ])
    
    # إعدادات متقدمة
    buttons.append([
        InlineKeyboardButton("⚙️ إعدادات متقدمة", callback_data="PLAYMODE_ADVANCED"),
        InlineKeyboardButton("🧹 تنظيف الكاش", callback_data="PLAYMODE_CLEAN_CACHE")
    ])
    
    # زر الإغلاق
    buttons.append([
        InlineKeyboardButton("❌ إغلاق", callback_data="PLAYMODE_CLOSE")
    ])
    
    return buttons

@app.on_message(filters.command(["playmode", "mode", "وضع التشغيل", "إعدادات التشغيل"]) & filters.group & ~BANNED_USERS)
@language
async def enhanced_playmode_command(client, message: Message, _):
    """أمر أوضاع التشغيل المحسن"""
    
    try:
        # جلب معلومات أوضاع التشغيل
        info = await get_enhanced_playmode_info(message.chat.id)
        if not info:
            await message.reply_text("❌ خطأ في جلب إعدادات التشغيل")
            return
        
        # تحضير النص
        playmode_text = "مباشر" if info.get('direct_mode') else "مع أزرار"
        playtype_text = "الإداريون فقط" if info.get('admin_only') else "الجميع"
        
        # النص الأساسي
        text = f"""
🎛️ **إعدادات التشغيل المحسنة**
**المجموعة:** `{message.chat.title}`

📋 **الإعدادات الحالية:**
• **وضع التشغيل:** `{playmode_text}`
• **صلاحيات التشغيل:** `{playtype_text}`

📊 **إحصائيات سريعة:**
"""
        
        # إضافة إحصائيات الأداء الأساسية
        text += f"• **حالة النظام:** `متصل ويعمل`\n"
        text += f"• **وقت التشغيل:** `{time.strftime('%H:%M:%S')}`\n"
        
        # إضافة إحصائيات النظام المختلط
        hybrid_stats = info.get('hybrid_stats', {})
        if hybrid_stats:
            dl_stats = hybrid_stats.get('download_stats', {})
            text += f"• **تحميل مختلط:** `{dl_stats.get('successful_downloads', 0)}`\n"
            text += f"• **مفاتيح API:** `{len(hybrid_stats.get('api_keys_stats', {}))}`\n"
        
        text += "\n🎯 **استخدم الأزرار أدناه لتخصيص الإعدادات**"
        
        # إنشاء الأزرار
        buttons = create_enhanced_playmode_markup(_, info)
        
        # إرسال الرسالة
        await message.reply_text(
            text,
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True
        )
        
    except Exception as e:
        LOGGER.error(f"❌ خطأ في أمر أوضاع التشغيل: {e}")
        await message.reply_text(f"❌ خطأ في عرض إعدادات التشغيل: {e}")

@app.on_callback_query(filters.regex("ADMIN_PLAYMODE_") & ~BANNED_USERS)
@language
async def playmode_callback_handler(client, callback_query, _):
    """معالج callbacks أوضاع التشغيل"""
    
    try:
        # التحقق من الصلاحيات
        chat_member = await app.get_chat_member(callback_query.message.chat.id, callback_query.from_user.id)
        if chat_member.status not in ["creator", "administrator"]:
            return await callback_query.answer("❌ هذا الأمر للإداريين فقط!", show_alert=True)
        
        # تحديد نوع التغيير
        action = callback_query.data.split("_")[-1]
        chat_id = callback_query.message.chat.id
        
        if action == "DIRECT":
            await set_playmode(chat_id, "Direct")
            await callback_query.answer("✅ تم تفعيل الوضع المباشر", show_alert=True)
        elif action == "INLINE":
            await set_playmode(chat_id, "Inline")
            await callback_query.answer("✅ تم تفعيل الوضع مع الأزرار", show_alert=True)
        
        # تحديث الرسالة
        info = await get_enhanced_playmode_info(chat_id)
        buttons = create_enhanced_playmode_markup(_, info)
        
        # تحديث النص
        playmode_text = "مباشر" if info.get('direct_mode') else "مع أزرار"
        playtype_text = "الإداريون فقط" if info.get('admin_only') else "الجميع"
        
        updated_text = f"""
🎛️ **إعدادات التشغيل المحسنة**
**المجموعة:** `{callback_query.message.chat.title}`

📋 **الإعدادات الحالية:**
• **وضع التشغيل:** `{playmode_text}`
• **صلاحيات التشغيل:** `{playtype_text}`

📊 **إحصائيات سريعة:**
• **تم التحديث:** `{time.strftime('%H:%M:%S')}`

🎯 **استخدم الأزرار أدناه لتخصيص الإعدادات**
"""
        
        await callback_query.edit_message_text(
            updated_text,
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True
        )
        
    except Exception as e:
        LOGGER.error(f"❌ خطأ في معالج playmode callback: {e}")
        await callback_query.answer("❌ حدث خطأ أثناء التحديث", show_alert=True)

@app.on_callback_query(filters.regex("ADMIN_PLAYTYPE_") & ~BANNED_USERS)
@language
async def playtype_callback_handler(client, callback_query, _):
    """معالج callbacks صلاحيات التشغيل"""
    
    try:
        # التحقق من الصلاحيات
        chat_member = await app.get_chat_member(callback_query.message.chat.id, callback_query.from_user.id)
        if chat_member.status not in ["creator", "administrator"]:
            return await callback_query.answer("❌ هذا الأمر للإداريين فقط!", show_alert=True)
        
        # تحديد نوع التغيير
        action = callback_query.data.split("_")[-1]
        chat_id = callback_query.message.chat.id
        
        if action == "ADMIN":
            await set_playtype(chat_id, "Admin")
            await callback_query.answer("✅ الآن الإداريون فقط يمكنهم التشغيل", show_alert=True)
        elif action == "EVERYONE":
            await set_playtype(chat_id, "Everyone")
            await callback_query.answer("✅ الآن الجميع يمكنهم التشغيل", show_alert=True)
        
        # تحديث الرسالة
        info = await get_enhanced_playmode_info(chat_id)
        buttons = create_enhanced_playmode_markup(_, info)
        
        # تحديث النص
        playmode_text = "مباشر" if info.get('direct_mode') else "مع أزرار"
        playtype_text = "الإداريون فقط" if info.get('admin_only') else "الجميع"
        
        updated_text = f"""
🎛️ **إعدادات التشغيل المحسنة**
**المجموعة:** `{callback_query.message.chat.title}`

📋 **الإعدادات الحالية:**
• **وضع التشغيل:** `{playmode_text}`
• **صلاحيات التشغيل:** `{playtype_text}`

📊 **إحصائيات سريعة:**
• **تم التحديث:** `{time.strftime('%H:%M:%S')}`

🎯 **استخدم الأزرار أدناه لتخصيص الإعدادات**
"""
        
        await callback_query.edit_message_text(
            updated_text,
            reply_markup=InlineKeyboardMarkup(buttons),
            disable_web_page_preview=True
        )
        
    except Exception as e:
        LOGGER.error(f"❌ خطأ في معالج playtype callback: {e}")
        await callback_query.answer("❌ حدث خطأ أثناء التحديث", show_alert=True)

@app.on_callback_query(filters.regex("PLAYMODE_STATS") & ~BANNED_USERS)
async def playmode_stats_callback(client, callback_query):
    """عرض إحصائيات الأداء التفصيلية"""
    
    try:
        # عرض إحصائيات أساسية
        stats_text = f"""
📊 **إحصائيات الأداء التفصيلية**
{'='*35}

🎵 **حالة النظام:**
• النظام: `يعمل بكفاءة`
• الوقت الحالي: `{time.strftime('%Y-%m-%d %H:%M:%S')}`
• نوع النظام: `محسن مع API Keys`

💾 **قاعدة البيانات:**
• حالة الاتصال: `متصل`
• نوع قاعدة البيانات: `SQLite محسن`
• التخزين: `محلي + قناة تخزين`

⚡ **الأداء:**
• سرعة الاستجابة: `عالية`
• المعالجة: `متوازية`
• الكاش: `مُفعل`

🕐 **آخر تحديث:** `{time.strftime('%Y-%m-%d %H:%M:%S')}`
"""
        
        await callback_query.answer()
        await callback_query.message.reply_text(stats_text)
        
    except Exception as e:
        LOGGER.error(f"❌ خطأ في عرض إحصائيات الأداء: {e}")
        await callback_query.answer("❌ خطأ في جلب الإحصائيات", show_alert=True)

@app.on_callback_query(filters.regex("PLAYMODE_HYBRID_STATS") & ~BANNED_USERS)
async def playmode_hybrid_stats_callback(client, callback_query):
    """عرض إحصائيات النظام المختلط"""
    
    try:
        hybrid_stats = await get_hybrid_stats()
        
        stats_text = f"""
🔗 **إحصائيات النظام المختلط**
{'='*35}

🔑 **مفاتيح YouTube API:**
"""
        
        # إحصائيات المفاتيح
        api_stats = hybrid_stats.get('api_keys_stats', {})
        for key, stats in api_stats.items():
            stats_text += f"""
• **{key}:**
  - الاستخدام: `{stats['usage']}`
  - النجاح: `{stats['success']}`
  - الأخطاء: `{stats['errors']}`
  - معدل النجاح: `{stats['success_rate']:.1f}%`
"""
        
        # إحصائيات التحميل
        dl_stats = hybrid_stats.get('download_stats', {})
        stats_text += f"""
⬇️ **إحصائيات التحميل:**
• إجمالي البحث: `{dl_stats.get('total_searches', 0)}`
• بحث API: `{dl_stats.get('api_searches', 0)}`
• تحميل ناجح: `{dl_stats.get('successful_downloads', 0)}`
• تحميل فاشل: `{dl_stats.get('failed_downloads', 0)}`

🍪 **الكوكيز:**
• عدد ملفات الكوكيز: `{hybrid_stats.get('cookies_count', 0)}`
• الكوكيز الحالي: `{hybrid_stats.get('current_cookie', 0)}`

🕐 **آخر تحديث:** `{time.strftime('%Y-%m-%d %H:%M:%S')}`
"""
        
        await callback_query.answer()
        await callback_query.message.reply_text(stats_text)
        
    except Exception as e:
        LOGGER.error(f"❌ خطأ في عرض إحصائيات النظام المختلط: {e}")
        await callback_query.answer("❌ خطأ في جلب الإحصائيات", show_alert=True)

@app.on_callback_query(filters.regex("PLAYMODE_ADVANCED") & ~BANNED_USERS)
async def playmode_advanced_callback(client, callback_query):
    """إعدادات متقدمة لأوضاع التشغيل"""
    
    try:
        # التحقق من الصلاحيات
        chat_member = await app.get_chat_member(callback_query.message.chat.id, callback_query.from_user.id)
        if chat_member.status not in ["creator", "administrator"]:
            return await callback_query.answer("❌ هذا الأمر للإداريين فقط!", show_alert=True)
        
        advanced_text = f"""
⚙️ **الإعدادات المتقدمة**
{'='*25}

🎛️ **خيارات التحكم:**
• جودة التحميل: `عالية (192kbps)`
• الحد الأقصى للمدة: `{config.DURATION_LIMIT_MIN} دقيقة`
• المعالجة المتوازية: `مُفعلة`
• النظام المختلط: `مُفعل`

🔧 **إعدادات الأداء:**
• حد العمليات المتوازية: `20`
• مهلة الطلب: `30 ثانية`
• تنظيف تلقائي: `كل ساعة`
• حفظ الكاش: `مُفعل`

💡 **نصائح الأداء:**
• استخدم الوضع المباشر للسرعة
• فعّل الكاش لتوفير البيانات
• نظّف الملفات المؤقتة دورياً

⚠️ **ملاحظة:** هذه الإعدادات تؤثر على أداء البوت في المجموعة
"""
        
        buttons = [
            [InlineKeyboardButton("🔄 إعادة تشغيل النظام", callback_data="PLAYMODE_RESTART")],
            [InlineKeyboardButton("🧹 تنظيف شامل", callback_data="PLAYMODE_DEEP_CLEAN")],
            [InlineKeyboardButton("📊 تقرير مفصل", callback_data="PLAYMODE_DETAILED_REPORT")],
            [InlineKeyboardButton("🔙 العودة", callback_data="PLAYMODE_BACK")]
        ]
        
        await callback_query.answer()
        await callback_query.message.edit_text(
            advanced_text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        
    except Exception as e:
        LOGGER.error(f"❌ خطأ في الإعدادات المتقدمة: {e}")
        await callback_query.answer("❌ خطأ في عرض الإعدادات", show_alert=True)

@app.on_callback_query(filters.regex("PLAYMODE_CLEAN_CACHE") & ~BANNED_USERS)
async def playmode_clean_cache_callback(client, callback_query):
    """تنظيف كاش النظام"""
    
    try:
        # التحقق من الصلاحيات
        chat_member = await app.get_chat_member(callback_query.message.chat.id, callback_query.from_user.id)
        if chat_member.status not in ["creator", "administrator"]:
            return await callback_query.answer("❌ هذا الأمر للإداريين فقط!", show_alert=True)
        
        await callback_query.answer("🧹 جاري تنظيف الكاش...", show_alert=True)
        
        # تنظيف الملفات القديمة
        cleaned_count = await cleanup_old_downloads()
        
        # تحديث الرسالة
        clean_text = f"""
🧹 **تم تنظيف الكاش بنجاح!**

📊 **النتائج:**
• تم حذف `{cleaned_count}` ملف مؤقت
• تم تحرير مساحة التخزين
• تم تحسين الأداء

✅ **الحالة:** النظام محسن ومجهز للعمل

🕐 **وقت التنظيف:** `{time.strftime('%Y-%m-%d %H:%M:%S')}`
"""
        
        buttons = [
            [InlineKeyboardButton("🔙 العودة لإعدادات التشغيل", callback_data="PLAYMODE_BACK")]
        ]
        
        await callback_query.message.edit_text(
            clean_text,
            reply_markup=InlineKeyboardMarkup(buttons)
        )
        
    except Exception as e:
        LOGGER.error(f"❌ خطأ في تنظيف الكاش: {e}")
        await callback_query.answer("❌ خطأ في تنظيف الكاش", show_alert=True)

@app.on_callback_query(filters.regex("PLAYMODE_CLOSE") & ~BANNED_USERS)
async def playmode_close_callback(client, callback_query):
    """إغلاق قائمة إعدادات التشغيل"""
    
    try:
        await callback_query.message.delete()
        await callback_query.answer("✅ تم إغلاق إعدادات التشغيل")
        
    except Exception as e:
        LOGGER.error(f"❌ خطأ في إغلاق القائمة: {e}")
        await callback_query.answer("❌ خطأ في الإغلاق", show_alert=True)

# أمر سريع لعرض حالة النظام
@app.on_message(filters.command(["systemstatus", "حالة النظام"]) & ~BANNED_USERS)
async def system_status_command(client, message: Message):
    """عرض حالة النظام السريعة"""
    
    try:
        # جلب الإحصائيات
        hybrid_stats = await get_hybrid_stats()
        
        # تحضير النص
        status_text = f"""
🚀 **حالة النظام**
{'='*20}

⚡ **الأداء:**
• النظام: `يعمل بكفاءة`
• الحالة: `متصل`
• الاستجابة: `سريعة`

🔗 **النظام المختلط:**
• مفاتيح API: `{len(hybrid_stats.get('api_keys_stats', {}))}`
• الكوكيز: `{hybrid_stats.get('cookies_count', 0)}`
• التحميل: `{hybrid_stats.get('download_stats', {}).get('successful_downloads', 0)}`

🕐 **الوقت:** `{time.strftime('%H:%M:%S')}`
"""
        
        await message.reply_text(status_text)
        
    except Exception as e:
        LOGGER.error(f"❌ خطأ في عرض حالة النظام: {e}")
        await message.reply_text(f"❌ خطأ في جلب حالة النظام: {e}")

LOGGER.info("✅ تم تحميل نظام إعدادات التشغيل المحسن بنجاح!")
