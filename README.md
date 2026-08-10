# BAC DZ AI

نسخة أولية منظمة لمنصة باكالوريا جزائرية عبر Telegram.

## ما تم بناؤه
- قائمة رئيسية بالأزرار.
- الشعب والمواد.
- مكتبة ملفات PDF/TXT/MD.
- فهرسة المحتوى في SQLite + FTS.
- مساعد AI يبحث في قاعدة المعرفة قبل الإجابة.
- أرشيف البكالوريا حسب السنة/الشعبة/المادة عندما تضع الملفات في مجلداتها.
- نظام اختبارات مبني على JSON/SQLite.
- بحث نصي.

## تثبيت
```cmd
cd C:\Users\rayan\bac-bot
python -m pip install -r requirements.txt
```

## مفاتيح البيئة
لا تضع المفاتيح داخل Python.
```cmd
setx TELEGRAM_TOKEN "NEW_TELEGRAM_TOKEN"
setx ANTHROPIC_API_KEY "NEW_ANTHROPIC_KEY"
setx AI_MODEL "claude-sonnet-5"
```
أغلق CMD وافتح نافذة جديدة بعد setx.

## تنظيم الملفات
ضع ملخصات/دروس:
data\lessons\science\رياضيات\
data\summaries\science\رياضيات\

ضع مواضيع البكالوريا:
data\bac\2025\science\رياضيات\
data\bac\2024\science\رياضيات\

يمكن أن تكون الملفات PDF أو TXT أو MD.

بعد إضافة الملفات:
```cmd
python ingest.py
```

ثم:
```cmd
python seed_questions.py
python bot.py
```

## ملاحظة
هذه النسخة تبني المحرك. محتوى السنوات والملخصات يجب إدخاله من ملفات مرخّصة أو مصادر تسمح بإعادة الاستخدام. لا ننسخ كتبًا أو محتوى محميًا بالكامل إلى البوت دون إذن.

## تشغيل النسخة
من داخل المجلد:
```cmd
python -m pip install -r requirements.txt
python seed_questions.py
python ingest.py
python telegram_bac_bot.py
```

## مهم
- استبدل الملف القديم بنسخة احتياطية أولاً.
- لا ترسل مفاتيح Telegram أو Anthropic لأي شخص.
- إذا كان لديك ملفات PDF للدروس/المواضيع، ضعها في مجلدات data ثم نفّذ `python ingest.py`.
