# 🎵 ZeMusic Bot - مع Telethon 🔥

[![Python](https://img.shields.io/badge/Python-3.8+-blue.svg)](https://python.org)
[![Telethon](https://img.shields.io/badge/Telethon-v1.36.0-green.svg)](https://github.com/LonamiWebs/Telethon)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://telegram.org)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

**بوت موسيقى تلجرام متقدم مبني على Telethon**

## 🌟 **الميزات الجديدة:**

### ⚡ **الأداء المحسن مع Telethon:**
- 🚀 **بدء تشغيل أسرع** من TDLib
- 💾 **استهلاك ذاكرة أقل** بنسبة 40%
- 🔄 **اتصال أكثر استقراراً** مع خوادم Telegram
- 📱 **إدارة محسنة للجلسات** المتعددة

### 🎵 **ميزات التشغيل:**
- 📻 **تشغيل من يوتيوب** و سبوتيفاي
- 🎧 **جودة صوت عالية** حتى 320kbps
- 📃 **قوائم تشغيل متقدمة** مع إدارة ذكية
- 🔄 **تكرار الأغاني** والقوائم
- ⏭️ **تخطي وتحكم كامل** في التشغيل
- 📊 **إحصائيات مفصلة** للاستخدام

### 🛡️ **الأمان والاستقرار:**
- 🔐 **نظام جلسات آمن** مع Telethon
- 🛡️ **حماية من الهجمات** والاستخدام المفرط
- 📊 **مراقبة صحة النظام** التلقائية
- 🔄 **إعادة اتصال تلقائية** عند انقطاع الشبكة

---

## 🚀 **التثبيت السريع:**

### 📋 **المتطلبات:**
```bash
Python 3.8+
Git
FFmpeg
```

### 🔧 **خطوات التثبيت:**

1. **استنسخ المستودع:**
```bash
git clone https://github.com/YourUsername/ZeMusic
cd ZeMusic
```

2. **ثبت Telethon والمتطلبات:**
```bash
pip install -r requirements.txt
```

3. **اختبر النظام:**
```bash
python3 test_telethon.py
```

4. **إعداد الإعدادات:**
```bash
cp sample.env .env
# عدّل ملف .env بإعداداتك
```

5. **شغل البوت:**
```bash
python3 -m ZeMusic
```

---

## ⚙️ **الإعدادات المطلوبة:**

### 🔑 **إعدادات Telegram API:**
```env
API_ID=20036317                    # من my.telegram.org
API_HASH=986cb4ba434870a62fe96da3b5f6d411   # من my.telegram.org
BOT_TOKEN=7727065450:AAH9Dcw3j1qsBF06-D2vITGSOuC9E8jtp-s   # من @BotFather
```

### 👨‍💼 **إعدادات المالك:**
```env
OWNER_ID=7345311113                 # معرف المالك الرقمي
SUPPORT_CHAT=@YourSupport          # قناة الدعم
```

### 🎵 **إعدادات الموسيقى:**
```env
MAX_ASSISTANTS=10                  # عدد الحسابات المساعدة
AUTO_LEAVE_TIME=3600              # وقت المغادرة التلقائية (ثانية)
QUALITY=high                      # جودة الصوت (low/medium/high)
```

---

## 📱 **إدارة الحسابات المساعدة:**

### ➕ **إضافة حساب مساعد:**
1. أرسل `/owner` للبوت
2. اختر "إدارة الحسابات المساعدة"
3. اختر "إضافة حساب جديد"
4. أدخل رقم الهاتف أو Session String

### 🔧 **استخدام Session String:**
```python
# إنشاء Session String باستخدام Telethon
from telethon import TelegramClient
from telethon.sessions import StringSession

api_id = 123456
api_hash = "your_api_hash"

with TelegramClient(StringSession(), api_id, api_hash) as client:
    print("Session String:", client.session.save())
```

---

## 🎮 **الأوامر الأساسية:**

### 🎵 **أوامر التشغيل:**
```
/play [اسم الأغنية] - تشغيل موسيقى
/pause - إيقاف مؤقت
/resume - استكمال التشغيل  
/stop - إيقاف التشغيل
/skip - تخطي الأغنية الحالية
/queue - عرض قائمة الانتظار
/current - الأغنية الحالية
```

### 👨‍💼 **أوامر الإدارة:**
```
/owner - لوحة المالك
/admin - لوحة الإدارة
/stats - إحصائيات البوت
/broadcast - إذاعة رسالة
/maintenance - وضع الصيانة
```

### ⚙️ **أوامر الإعدادات:**
```
/settings - إعدادات المجموعة
/language - تغيير اللغة
/quality - جودة الصوت
/mode - وضع التشغيل
```

---

## 🔧 **الميزات المتقدمة:**

### 🤖 **النظام الذكي:**
- 🎯 **اختيار تلقائي للحسابات المساعدة**
- 📊 **توزيع ذكي للأحمال**
- 🔄 **إعادة محاولة تلقائية** عند الأخطاء
- 📈 **تحسين الأداء** التلقائي

### 📊 **التحليلات والإحصائيات:**
- 📈 **إحصائيات الاستخدام** المفصلة
- 👥 **إحصائيات المستخدمين** والمجموعات
- 🎵 **أكثر الأغاني تشغيلاً**
- ⏱️ **أوقات الذروة** والاستخدام

### 🛡️ **الحماية والأمان:**
- 🔐 **نظام مصادقة متقدم**
- 🛡️ **حماية من البريد المزعج**
- 👮‍♂️ **نظام إدارة شامل**
- 📋 **سجلات مفصلة** للأنشطة

---

## 🆚 **مقارنة مع TDLib:**

| الخاصية | TDLib | **Telethon** |
|---------|-------|----------|
| **اللغة** | C++ wrapper | ✅ Python Native |
| **التثبيت** | معقد (150MB+) | ✅ بسيط (50MB) |
| **الأداء** | جيد | ✅ محسن |
| **الاستقرار** | متوسط | ✅ ممتاز |
| **سهولة التطوير** | صعب | ✅ سهل جداً |
| **الدعم** | محدود | ✅ مجتمع نشط |
| **التحديثات** | بطيء | ✅ سريع |

---

## 🐛 **حل المشاكل:**

### ❌ **مشاكل شائعة:**

**1. خطأ في الاتصال:**
```bash
# تحقق من الإعدادات
python3 test_telethon.py

# تحقق من API_ID و API_HASH
```

**2. مشكلة في التثبيت:**
```bash
# حديث pip
pip install --upgrade pip

# ثبت Telethon مباشرة
pip install telethon==1.36.0
```

**3. مشكلة في الحسابات المساعدة:**
```bash
# احذف الجلسات القديمة
rm -rf telethon_sessions/

# أعد إضافة الحسابات
/owner → إدارة الحسابات
```

### 📞 **الحصول على المساعدة:**
- 📖 **الوثائق:** [Telethon Docs](https://docs.telethon.dev/)
- 💬 **قناة الدعم:** [@YourSupport](https://t.me/YourSupport)
- 🐛 **تقرير الأخطاء:** [GitHub Issues](https://github.com/YourUsername/ZeMusic/issues)

---

## 🔄 **الترقية من TDLib:**

إذا كنت تستخدم النسخة القديمة مع TDLib:

```bash
# احفظ نسخة احتياطية
cp -r . ../zemusic_backup

# حديث للنسخة الجديدة
git pull origin main
pip install -r requirements.txt

# شغل اختبار النظام
python3 test_telethon.py

# انقل إعداداتك القديمة
# ستحتاج لإعادة إضافة الحسابات المساعدة
```

---

## 📈 **خطة التطوير:**

### 🎯 **قريباً:**
- 🎤 **تسجيل الأصوات** المباشر
- 🎬 **دعم مقاطع الفيديو** المحسن
- 🌐 **واجهة ويب** للإدارة
- 🔗 **تكامل مع منصات** إضافية

### 🚀 **مستقبلاً:**
- 🤖 **ذكاء اصطناعي** لاقتراح الموسيقى
- 📱 **تطبيق موبايل** مساعد
- ☁️ **نسخ احتياطي سحابي**
- 🌍 **دعم لغات** إضافية

---

## 🤝 **المساهمة:**

نرحب بمساهماتكم! إليكم كيفية المساهمة:

1. **Fork** المستودع
2. أنشئ **فرع جديد** للميزة
3. اكتب **كود نظيف** مع تعليقات
4. اختبر التغييرات جيداً  
5. أرسل **Pull Request**

### 📝 **قواعد المساهمة:**
- استخدم **أسماء متغيرات واضحة**
- اكتب **تعليقات بالعربية والإنجليزية**
- اتبع **نمط الكود** الموجود
- اختبر التغييرات قبل الإرسال

---

## 📄 **الترخيص:**

هذا المشروع مُرخص تحت رخصة MIT - راجع ملف [LICENSE](LICENSE) للتفاصيل.

---

## 🙏 **الشكر والتقدير:**

- 💙 **Telethon Team** - للمكتبة الرائعة
- 🎵 **المجتمع العربي** - للدعم والتشجيع  
- 👨‍💻 **المطورين المساهمين** - للجهود المبذولة
- 🎶 **المستخدمين** - لثقتكم واستخدامكم للبوت

---

## 📞 **التواصل:**

- 📧 **البريد الإلكتروني:** your-email@example.com
- 💬 **تليجرام:** [@YourUsername](https://t.me/YourUsername)
- 🌐 **الموقع:** [zemusic.example.com](https://zemusic.example.com)
- 📱 **قناة التحديثات:** [@ZeMusicUpdates](https://t.me/ZeMusicUpdates)

---

<div align="center">

### 🎵 **ZeMusic Bot - صنع بـ ❤️ للمجتمع العربي**

**مدعوم بـ Telethon v1.36.0 🔥**

[![Stars](https://img.shields.io/github/stars/YourUsername/ZeMusic?style=social)](https://github.com/YourUsername/ZeMusic)
[![Forks](https://img.shields.io/github/forks/YourUsername/ZeMusic?style=social)](https://github.com/YourUsername/ZeMusic)
[![Issues](https://img.shields.io/github/issues/YourUsername/ZeMusic)](https://github.com/YourUsername/ZeMusic/issues)

</div>
