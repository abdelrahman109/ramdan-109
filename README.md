## 📦 **محتوى ملف `README.md` لمشروعك على GitHub**

```markdown
# نظام حفل إفطار أسر شهداء الدفعة 109 🎟️

نظام متكامل لإدارة حجوزات وتذاكر حفل الإفطار، يشمل بوت تليجرام للحجز، لوحة تحكم ويب للإدارة، ونظام QR Code للدخول.

---

## ✨ المميزات

### 🤖 بوت تليجرام
- حجز التذاكر (حضور / مساهمة)
- اختيار عدد الأفراد الإضافيين
- اختيار بروش + ميدالية
- دفع عبر InstaPay أو محفظة إلكترونية
- رفع صورة إيصال الدفع
- استلام تذكرة QR بعد القبول

### 🖥️ لوحة التحكم (Web Dashboard)
- مراجعة طلبات الدفع (قبول / رفض)
- إحصائيات حية (إجمالي الحجوزات، الإيرادات، المتبقي)
- إحصائيات الضيوف والبروش
- إرسال رسائل جماعية
- تقارير CSV

### 📱 نظام الدخول (QR Scanner)
- مسح QR Code للدخول
- إحصائيات لحظية (عدد الداخلين، المتبقي)
- أصوات تنبيه لكل حالة (نجاح - تحذير - خطأ)
- إدخال يدوي للكود
- تسجيل كل عمليات المسح

---

## 🛠️ التقنيات المستخدمة

- **اللغة:** Python 3.10+
- **الإطار:** Flask (Web) + pyTelegramBotAPI (Bot)
- **قاعدة البيانات:** SQLite
- **السيرفر:** Ubuntu على AWS Lightsail
- **الـ QR:** html5-qrcode
- **الخطوط:** Arial Bold

---

## 📁 هيكل المشروع

```
ramdan-109/
├── app/
│   ├── __init__.py
│   ├── analytics.py      # إحصائيات
│   ├── config.py          # الإعدادات
│   ├── constants.py       # الثوابت
│   ├── db.py              # قاعدة البيانات
│   ├── notifications.py   # إشعارات تليجرام
│   ├── reports.py         # تقارير
│   ├── services.py        # منطق الأعمال
│   ├── storage.py         # تخزين الملفات
│   ├── tickets.py         # إنشاء التذاكر
│   └── utils.py           # دوال مساعدة
├── assets/                # الصور (لوجو، قالب التذكرة)
├── static/                # CSS, JS
├── templates/             # قوالب HTML
│   ├── admin/             # صفحات الإدارة
│   ├── public/            # صفحات عامة
│   └── scan/              # صفحة الماسح
├── uploads/               # صور إثبات الدفع
├── generated/             # التذاكر والـ QR
├── bot.py                 # ملف البوت
├── webapp.py              # ملف الويب
├── .env                   # متغيرات البيئة
└── requirements.txt       # المكتبات المطلوبة
```

---

## 🚀 طريقة التشغيل

### 1️⃣ تنزيل المشروع
```bash
git clone https://github.com/USERNAME/ramdan-109.git
cd ramdan-109
```

### 2️⃣ إعداد البيئة
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 3️⃣ إعداد ملف `.env`
```env
TELEGRAM_BOT_TOKEN=你的_بوت_توكين
ADMIN_CHAT_IDS=123456789
ADMIN_PASSWORD=admin123
BASE_URL=http://your-server-ip:5000

# بيانات الحدث
EVENT_NAME=حفل إفطار أسر شهداء الدفعة ١٠٩
EVENT_TIME=5:30 مساءً
EVENT_LOCATION=دار الأسلحة والذخيرة
EVENT_MAP=https://maps.app.goo.gl/xxx
EVENT_CAPACITY=400

# بيانات الدفع
ACCOUNT_NAME_AR=جمال الدين أحمد جمال الدين الجاويش
ACCOUNT_NAME_EN=GAMAL EL-DIN AHMED GAMAL EL-DIN EL-GAWISH
INSTAPAY_PHONE=01020877259
WALLET_PHONE=01020877259
INSTAPAY_LINK=https://ipn.eg/S/gawish92/instapay/2dPqBf
```

### 4️⃣ تشغيل البوت والويب
```bash
# تشغيل البوت
tmux new -d -s bot "source venv/bin/activate && python3 bot.py"

# تشغيل الويب
tmux new -d -s web "source venv/bin/activate && python3 webapp.py"
```

---

## 📱 واجهات المستخدم

### **بوت تليجرام**
ابحث عن البوت: `@YourBotUsername`

### **لوحة الإدارة**
```
https://your-server-ip:5000/admin/login
```
كلمة المرور: `admin123` (قابلة للتغيير في `.env`)

### **صفحة الماسح**
```
https://your-server-ip:5000/scan
```

---

## 📊 الإحصائيات المتوفرة

- ✅ إجمالي الحجوزات
- ✅ عدد المدفوع / المعلق
- ✅ عدد الحضور / المساهمين
- ✅ إجمالي الإيرادات
- ✅ إجمالي الضيوف (أساسي + إضافيين)
- ✅ عدد البروشات المسلمة / المتبقية
- ✅ إحصائيات طرق الدفع (InstaPay / محفظة)

---

## 🔒 الأمان

- جميع المدفوعات تمر بمراجعة يدوية
- التذاكر تستخدم مرة واحدة فقط
- QR Code مشفر وغير قابل للتكرار
- جلسات الأدمن محمية بكلمة مرور

---

## 📝 الترخيص

هذا المشروع مخصص للاستخدام الشخصي والتطوير.

---

## 👤 المطور

- **الاسم:** [اسمك هنا]
- **للتواصل:** [بريدك الإلكتروني أو تليجرام]

---

## 🙏 شكر خاص

- لشهداء مصر الأبرار 🇪🇬
- لكل من ساهم في هذا العمل

---

⭐ **إذا أعجبك المشروع، لا تنسى تضع نجمة على GitHub!** ⭐
```

---

## 📦 **ملف `requirements.txt`**

```txt
Flask==3.1.0
pyTelegramBotAPI==4.24.0
python-dotenv==1.0.1
qrcode==8.0
Pillow==11.0.0
openpyxl==3.1.5
```

---

## 🚀 **أوامر رفع المشروع على GitHub**

```bash
# 1. أنشئ مستودع جديد على GitHub
#    - روح https://github.com/new
#    - اسم المستودع: ramdan-109
#    - لا تختار Initialize with README

# 2. في السيرفر، نفذ:
cd ~/ramdan-109
git init
git add .
git commit -m "Initial commit - Ramadan 109 Event System"
git branch -M main
git remote add origin https://github.com/USERNAME/ramdan-109.git
git push -u origin main
```

---

## ⚠️ **مهم جداً: ملف `.gitignore`**

أنشئ ملف `.gitignore`:

```bash
nano .gitignore
```

الصق ده:

```
# Python
__pycache__/
*.py[cod]
*.log
*.db
*.sqlite
instance/
venv/
.env

# المشروع
uploads/
generated/
*.log
*.pid
*.pot

# IDE
.vscode/
.idea/
*.swp
*.swo
*~
.DS_Store
```

---

كده كل حاجة جاهزة للرفع على GitHub! 🎉💪
