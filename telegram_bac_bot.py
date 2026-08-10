
import json
import random

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    ContextTypes,
    filters,
)

from config import TELEGRAM_TOKEN, BRANCHES, SUBJECTS, YEARS, validate_config
from db import init_db, connect
from ai import answer


def kb(rows):
    return InlineKeyboardMarkup(rows)


def main_menu():
    return kb([
        [
            InlineKeyboardButton("📚 الدروس والملخصات", callback_data="lessons"),
            InlineKeyboardButton("📝 مواضيع البكالوريا", callback_data="bac"),
        ],
        [
            InlineKeyboardButton("🤖 مساعد الذكاء الاصطناعي", callback_data="ai"),
            InlineKeyboardButton("🧠 اختبرني", callback_data="quiz"),
        ],
        [
            InlineKeyboardButton("🔎 البحث", callback_data="search"),
            InlineKeyboardButton("ℹ️ المساعدة", callback_data="help"),
        ],
    ])


def branch_menu(prefix):
    rows = []
    items = list(BRANCHES.items())

    for i in range(0, len(items), 2):
        row = []

        for key, name in items[i:i + 2]:
            row.append(
                InlineKeyboardButton(
                    name,
                    callback_data=f"{prefix}:branch:{key}"
                )
            )

        rows.append(row)

    rows.append([
        InlineKeyboardButton("🏠 الرئيسية", callback_data="home")
    ])

    return kb(rows)


def year_menu(branch, subject):
    rows = []
    recent_years = list(reversed(YEARS))

    for i in range(0, len(recent_years), 3):
        row = []

        for year in recent_years[i:i + 3]:
            row.append(
                InlineKeyboardButton(
                    str(year),
                    callback_data=f"bacyear:{branch}:{subject}:{year}"
                )
            )

        rows.append(row)

    rows.append([
        InlineKeyboardButton(
            "📚 كل السنوات",
            callback_data=f"bacall:{branch}:{subject}"
        )
    ])

    rows.append([
        InlineKeyboardButton("🔙 المواد", callback_data="bac")
    ])

    return kb(rows)


def subject_menu(prefix, branch):
    rows = []

    for i, subject in enumerate(SUBJECTS.get(branch, [])):
        rows.append([
            InlineKeyboardButton(
                "📘 " + subject,
                callback_data=f"{prefix}:subject:{branch}:{i}"
            )
        ])

    rows.append([
        InlineKeyboardButton("🔙 الشعب", callback_data=prefix)
    ])

    return kb(rows)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()

    await update.message.reply_text(
        "🎓 مرحباً بك في focus & force bot 🇩🇿\n\n"
        "منصتك التعليمية الذكية للدروس، الملخصات، ومواضيع البكالوريا "
        "مع ميزة التحليل المباشر للمراجع باستخدام الذكاء الاصطناعي.\n\n"
        "اختر من القائمة للبدء:",
        reply_markup=main_menu()
    )


async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    data = q.data

    # تغليف الإجابة لتجنب خطأ انتهاء وقت الاستجابة الافتراضي
    try:
        await q.answer()
    except Exception:
        pass
    # الرئيسية
    if data == "home":
        context.user_data.pop("mode", None)

        await q.edit_message_text(
            "🎓 focus & force bot\n\nاختر الخدمة من القائمة:",
            reply_markup=main_menu()
        )
        return

    # الدروس / البكالوريا
    if data in {"lessons", "bac"}:
        title = (
            "📚 الدروس والملخصات"
            if data == "lessons"
            else "📝 مواضيع البكالوريا"
        )

        await q.edit_message_text(
            title + "\n\nاختر شعبتك الآن:",
            reply_markup=branch_menu(data)
        )
        return

    # AI
    if data == "ai":
        context.user_data["mode"] = "ai"

        await q.edit_message_text(
            "🤖 مساعد الذكاء الاصطناعي الذكي\n\n"
            "اكتب سؤالك أو طلبك الآن (مثال: اشرح لي درس الدوال).\n"
            "سأقوم تلقائياً بالبحث في كتبك وملخصاتك المرفوعة والإجابة منها!",
            reply_markup=kb([
                [
                    InlineKeyboardButton(
                        "🏠 الرئيسية",
                        callback_data="home"
                    )
                ]
            ])
        )
        return

    # البحث
    if data == "search":
        context.user_data["mode"] = "search"

        await q.edit_message_text(
            "🔎 اكتب كلمة أو عبارة للبحث في قاعدة الدروس والمواضيع المتاحة."
        )
        return

    # الاختبار
    if data == "quiz":
        await q.edit_message_text(
            "🧠 اختبر نفسك\n\nاختر شعبتك أولاً:",
            reply_markup=branch_menu("quiz")
        )
        return

    # المساعدة
    if data == "help":
        await q.edit_message_text(
            "ℹ️ دليل استخدام focus & force bot\n\n"
            "📚 الدروس: استعراض الملفات التعليمية والملخصات المفهرسة.\n"
            "📝 البكالوريا: أرشيف شامل للمواضيع الرسمية مع التصحيح النموذجي.\n"
            "🤖 AI: مساعد ذكي يقرأ ويحلل كتبك وملخصاتك الملقمة يدوياً في النظام.\n"
            "🧠 الاختبارات: أسئلة تفاعلية لتقييم مستواك.\n\n"
            "لتغذية البوت بكتب جديدة: ضع ملفات الـ PDF داخل مجلد books الخاص بمادتك.",
            reply_markup=kb([
                [
                    InlineKeyboardButton(
                        "🏠 الرئيسية",
                        callback_data="home"
                    )
                ]
            ])
        )
        return

    # اختيار الشعبة
    parts = data.split(":")

    if len(parts) >= 3 and parts[1] == "branch":
        prefix, _, branch = parts

        if prefix in {"lessons", "bac", "quiz"}:
            await q.edit_message_text(
                f"شعبة: {BRANCHES.get(branch, 'الشعبة')}\n\nاختر المادة الدراسية:",
                reply_markup=subject_menu(prefix, branch)
            )

        return

    # اختيار المادة
    if len(parts) >= 4 and parts[1] == "subject":
        prefix, _, branch, index = parts

        try:
            subject = SUBJECTS[branch][int(index)]
        except Exception:
            subject = "المادة"

        context.user_data.update({
            "branch": branch,
            "subject": subject,
        })

        con = connect()

        # Quiz
        if prefix == "quiz":
            rows = con.execute(
                """
                SELECT id, question, choices, answer, explanation
                FROM quiz_questions
                WHERE branch = ? AND subject = ?
                """,
                (branch, subject),
            ).fetchall()

            con.close()

            if not rows:
                await q.edit_message_text(
                    f"🧠 اختبار {subject}\n\n"
                    "لا توجد أسئلة اختبار متوفرة لهذه المادة حالياً.",
                    reply_markup=kb([
                        [
                            InlineKeyboardButton(
                                "🔙 المواد",
                                callback_data="quiz"
                            )
                        ]
                    ])
                )
                return

            row = random.choice(rows)

            choices = (
                json.loads(row["choices"])
                if row["choices"]
                else []
            )

            context.user_data["quiz"] = dict(row)

            buttons = [
                [
                    InlineKeyboardButton(
                        choice,
                        callback_data=f"quiz_answer:{i}"
                    )
                    for i, choice in enumerate(choices)
                ]
            ]

            buttons.append([
                InlineKeyboardButton(
                    "🏠 الرئيسية",
                    callback_data="home"
                )
            ])

            await q.edit_message_text(
                f"🧠 اختبار المادة:\n\n" + row["question"],
                reply_markup=kb(buttons)
            )
            return

        # الدروس
        if prefix == "lessons":
            rows = con.execute(
                """
                SELECT id, title, kind, year, path
                FROM documents
                WHERE kind IN ('lessons', 'summaries')
                AND (branch = ? OR branch IS NULL)
                AND (subject = ? OR subject IS NULL)
                ORDER BY title
                """,
                (branch, subject),
            ).fetchall()

            con.close()

            if not rows:
                await q.edit_message_text(
                    f"📘 مادة {subject}\n\n"
                    "لا توجد مستندات مرفوعة بعد في هذا القسم.",
                    reply_markup=kb([
                        [
                            InlineKeyboardButton(
                                "🏠 الرئيسية",
                                callback_data="home"
                            )
                        ]
                    ])
                )
                return

            buttons = [
                [
                    InlineKeyboardButton(
                        "📄 " + r["title"][:60],
                        callback_data=f"doc:{r['id']}"
                    )
                ]
                for r in rows[:40]
            ]

            buttons.append([
                InlineKeyboardButton(
                    "🔙 المواد",
                    callback_data="lessons"
                )
            ])

            await q.edit_message_text(
                f"📚 مراجع {subject}\n\nاختر الملف المُراد تحميله أو عرضه:",
                reply_markup=kb(buttons)
            )
            return

        # البكالوريا
        con.close()

        await q.edit_message_text(
            f"📝 بكالوريا {subject}\n\nاختر السنة المطلوبة:",
            reply_markup=year_menu(branch, subject)
        )
        return

    # سنة البكالوريا
    if parts[0] == "bacyear":
        _, branch, subject, year = parts
        year = int(year)

        con = connect()

        rows = con.execute(
            """
            SELECT id, title, kind, year, path
            FROM documents
            WHERE kind = 'bac'
            AND branch = ?
            AND subject = ?
            AND year = ?
            ORDER BY title
            """,
            (branch, subject, year),
        ).fetchall()

        con.close()

        if not rows:
            await q.edit_message_text(
                f"📝 بكالوريا {year} — {subject}\n\n"
                "المواضيع غير متوفرة بعد لهذه السنة.",
                reply_markup=kb([
                    [
                        InlineKeyboardButton(
                            "🔙 السنوات",
                            callback_data=(
                                f"bac:subject:{branch}:"
                                f"{SUBJECTS[branch].index(subject)}"
                            ),
                        )
                    ],
                    [
                        InlineKeyboardButton(
                            "🏠 الرئيسية",
                            callback_data="home"
                        )
                    ],
                ])
            )
            return

        buttons = [
            [
                InlineKeyboardButton(
                    "📄 " + r["title"][:60],
                    callback_data=f"doc:{r['id']}"
                )
            ]
            for r in rows
        ]

        buttons.append([
            InlineKeyboardButton(
                "🔙 السنوات",
                callback_data=(
                    f"bac:subject:{branch}:"
                    f"{SUBJECTS[branch].index(subject)}"
                ),
            )
        ])

        await q.edit_message_text(
            f"📝 دورة {year} — {subject}\n\nاختر المستند المتوفر:",
            reply_markup=kb(buttons)
        )
        return

    # كل سنوات البكالوريا
    if parts[0] == "bacall":
        _, branch, subject = parts

        con = connect()

        rows = con.execute(
            """
            SELECT id, title, kind, year, path
            FROM documents
            WHERE kind = 'bac'
            AND branch = ?
            AND subject = ?
            ORDER BY year DESC, title
            """,
            (branch, subject),
        ).fetchall()

        con.close()

        if not rows:
            await q.edit_message_text(
                f"📝 أرشيف {subject}\n\nلا توجد مواضيع مضافة حالياً.",
                reply_markup=kb([
                    [
                        InlineKeyboardButton(
                            "🏠 الرئيسية",
                            callback_data="home"
                        )
                    ]
                ])
            )
            return

        buttons = []

        for r in rows[:60]:
            label = (
                f"{r['year']} — {r['title']}"
                if r["year"]
                else r["title"]
            )

            buttons.append([
                InlineKeyboardButton(
                    "📄 " + label[:60],
                    callback_data=f"doc:{r['id']}"
                )
            ])

        buttons.append([
            InlineKeyboardButton(
                "🔙 السنوات",
                callback_data=(
                    f"bac:subject:{branch}:"
                    f"{SUBJECTS[branch].index(subject)}"
                ),
            )
        ])

        await q.edit_message_text(
            f"📝 كل مواضيع {subject} المتوفرة:",
            reply_markup=kb(buttons)
        )
        return

    # فتح وثيقة
    if parts[0] == "doc":
        from pathlib import Path
        from config import DATA_DIR

        doc_id = int(parts[1])

        con = connect()
        row = con.execute(
            "SELECT * FROM documents WHERE id = ?",
            (doc_id,),
        ).fetchone()
        con.close()

        if not row:
            await q.edit_message_text(
                "❌ نعتذر، هذا الملف لم يعد متاحاً.",
                reply_markup=main_menu(),
            )
            return

        file_path = DATA_DIR / row["path"]

        if file_path.exists() and file_path.suffix.lower() == ".pdf":
            await q.message.reply_document(
                document=str(file_path),
                caption=f"📄 {row['title']}",
            )

            await q.edit_message_text(
                "✅ تم إرسال كتابك/ملفك بنجاح كوثيقة مباشرة.",
                reply_markup=kb([
                    [
                        InlineKeyboardButton(
                            "🏠 الرئيسية",
                            callback_data="home"
                        )
                    ]
                ]),
            )

        elif file_path.exists() and file_path.suffix.lower() in {".txt", ".md"}:
            text = file_path.read_text(
                encoding="utf-8",
                errors="ignore",
            )

            text = text[:3800]

            await q.edit_message_text(
                f"📄 {row['title']}\n\n{text}",
                reply_markup=kb([
                    [
                        InlineKeyboardButton(
                            "🏠 الرئيسية",
                            callback_data="home"
                        )
                    ]
                ])
            )

        else:
            await q.edit_message_text(
                f"❌ المستند [{row['title']}] غير متوفر حالياً في خادم التخزين الخاص بالبوت.",
                reply_markup=kb([
                    [
                        InlineKeyboardButton(
                            "🏠 الرئيسية",
                            callback_data="home"
                        )
                    ]
                ])
            )

        return

    # جواب الاختبار
    if parts[0] == "quiz_answer":
        saved = context.user_data.get("quiz")

        if not saved:
            await q.edit_message_text(
                "انتهت جلسة الاختبار الحالية، يرجى البدء مجدداً.",
                reply_markup=main_menu(),
            )
            return

        idx = int(parts[1])
        choices = json.loads(saved["choices"])

        chosen = choices[idx] if idx < len(choices) else ""
        ok = chosen == saved["answer"]

        if ok:
            msg = "✅ إجابة صحيحة وممتازة!\n\n"
        else:
            msg = (
                "❌ إجابة خاطئة.\n\n"
                f"الإجابة الصحيحة هي: {saved['answer']}\n\n"
            )

        msg += saved["explanation"] or ""

        await q.edit_message_text(
            msg,
            reply_markup=kb([
                [
                    InlineKeyboardButton(
                        "🔄 سؤال آخر",
                        callback_data=(
                            "quiz:branch:"
                            f"{context.user_data.get('branch', 'science')}"
                        ),
                    )
                ],
                [
                    InlineKeyboardButton(
                        "🏠 الرئيسية",
                        callback_data="home"
                    )
                ],
            ])
        )
        return


async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get("mode")
    text = update.message.text.strip()

    # AI
    if mode == "ai":
    msg = await update.message.reply_text("معليش تصبر شوي لعزيز (ة)")
        try:
            # تمرير المادة والشعبة الحالية المحددة لمساعدة دالة القراءة الذكية
            ans, n = answer(
                text,
                context.user_data.get("branch", ""),
                context.user_data.get("subject", ""),
            )

            await msg.delete()

            # تعطيل الـ parse_mode نهائياً لمنع تعليق الرسالة بسبب رموز الرياضيات والرموز البرمجية
            await update.message.reply_text(
                f"🤖 focus & force bot\n\n{ans}"
            )

        except Exception as e:
            await msg.edit_text(
                "❌ واجه الذكاء الاصطناعي مشكلة أثناء تحليل البيانات:\n" + str(e)
            )

        return

    # Search
    if mode == "search":
        con = connect()

        rows = con.execute(
            """
            SELECT id, title, kind, year, path
            FROM documents
            WHERE title LIKE ? OR content LIKE ?
            ORDER BY year DESC
            LIMIT 20
            """,
            (f"%{text}%", f"%{text}%"),
        ).fetchall()

        con.close()

        if not rows:
            await update.message.reply_text(
                "🔎 لم يتم العثور على أي ملفات مطابقة لكلمة البحث. جرب كلمات أخرى.",
                reply_markup=main_menu(),
            )
            return

        lines = [
            "🔎 نتائج البحث المطابقة للمستندات:",
            "",
        ]

        for r in rows:
            y = f"{r['year']} - " if r["year"] else ""
            lines.append(f"• {y}{r['title']} ({r['kind']})")

        await update.message.reply_text(
            "\n".join(lines),
            reply_markup=main_menu(),
        )
        return

    await update.message.reply_text(
        "يرجى اختيار خدمة من القائمة الأساسية لبدء التصفح.",
        reply_markup=main_menu(),
    )


def main():
    validate_config()
    init_db()

    app = Application.builder().token(TELEGRAM_TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callbacks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))

    print("✅ focus & force bot يعمل بنجاح الآن")

    app.run_polling()


if __name__ == "__main__":
    main()