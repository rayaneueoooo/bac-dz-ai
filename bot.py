
import json
import random
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, ContextTypes, filters

from config import TELEGRAM_TOKEN, BRANCHES, SUBJECTS, YEARS, validate_config
from db import init_db, connect
from ai import answer

def kb(rows):
    return InlineKeyboardMarkup(rows)

def main_menu():
    return kb([
        [InlineKeyboardButton("📚 الدروس والملخصات", callback_data="lessons"),
         InlineKeyboardButton("📝 مواضيع البكالوريا", callback_data="bac")],
        [InlineKeyboardButton("🤖 مساعد الذكاء الاصطناعي", callback_data="ai"),
         InlineKeyboardButton("🧠 اختبرني", callback_data="quiz")],
        [InlineKeyboardButton("🔎 البحث", callback_data="search"),
         InlineKeyboardButton("ℹ️ المساعدة", callback_data="help")],
    ])

def branch_menu(prefix):
    rows=[]
    items=list(BRANCHES.items())
    for i in range(0,len(items),2):
        row=[]
        for key,name in items[i:i+2]:
            row.append(InlineKeyboardButton(name, callback_data=f"{prefix}:branch:{key}"))
        rows.append(row)
    rows.append([InlineKeyboardButton("🏠 الرئيسية", callback_data="home")])
    return kb(rows)

def year_menu(branch, subject):
    rows=[]
    # Show recent years first; older years remain accessible via pagination in a later version.
    for i in range(0, len(YEARS), 3):
        row=[]
        recent_years=list(reversed(YEARS))
        for year in recent_years[i:i+3]:
            row.append(InlineKeyboardButton(str(year), callback_data=f"bacyear:{branch}:{subject}:{year}"))
        rows.append(row)
    rows.append([InlineKeyboardButton("📚 كل السنوات", callback_data=f"bacall:{branch}:{subject}")])
    rows.append([InlineKeyboardButton("🔙 المواد", callback_data="bac")])
    return kb(rows)

def subject_menu(prefix, branch):
    rows=[]
    for i,s in enumerate(SUBJECTS.get(branch, [])):
        rows.append([InlineKeyboardButton("📘 "+s, callback_data=f"{prefix}:subject:{branch}:{i}")])
    rows.append([InlineKeyboardButton("🔙 الشعب", callback_data=prefix)])
    return kb(rows)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    context.user_data.clear()
    await update.message.reply_text(
        "🎓 *مرحباً بك في BAC DZ AI 🇩🇿*\n\n"
        "منصة واحدة للدروس والملخصات ومواضيع البكالوريا والتصحيحات "
        "ومساعد الذكاء الاصطناعي والاختبارات.\n\n"
        "اختر من القائمة:",
        reply_markup=main_menu(), parse_mode="Markdown"
    )

async def render(update, text, markup=None):
    q=update.callback_query
    await q.answer()
    await q.edit_message_text(text, reply_markup=markup, parse_mode="Markdown")

async def callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q=update.callback_query
    data=q.data
    await q.answer()

    if data=="home":
        await q.edit_message_text("🎓 *BAC DZ AI*\n\nاختر الخدمة:", reply_markup=main_menu(), parse_mode="Markdown")
        return

    if data in {"lessons","bac"}:
        title="📚 *الدروس والملخصات*" if data=="lessons" else "📝 *مواضيع البكالوريا*"
        await q.edit_message_text(title+"\n\nاختر شعبتك:", reply_markup=branch_menu(data), parse_mode="Markdown")
        return

    if data=="ai":
        context.user_data["mode"]="ai"
        await q.edit_message_text(
            "🤖 *مساعد BAC DZ AI*\n\nاكتب سؤالك الآن.\n"
            "يمكنك السؤال عن درس، مفهوم، منهجية أو تمرين.",
            reply_markup=kb([[InlineKeyboardButton("🏠 الرئيسية", callback_data="home")]]),
            parse_mode="Markdown"
        )
        return

    if data=="search":
        context.user_data["mode"]="search"
        await q.edit_message_text("🔎 اكتب كلمة أو عبارة للبحث في قاعدة الدروس والمواضيع.")
        return

    if data=="quiz":
        await q.edit_message_text(
            "🧠 *اختبرني*\n\nاختر شعبتك:", reply_markup=branch_menu("quiz"), parse_mode="Markdown"
        )
        return

    if data=="help":
        await q.edit_message_text(
            "ℹ️ *طريقة الاستخدام*\n\n"
            "📚 الدروس: ملفات PDF/TXT/MD التي نضعها في قاعدة المعرفة.\n"
            "📝 البكالوريا: السنوات ثم الشعبة ثم المادة ثم الموضوع/التصحيح.\n"
            "🤖 AI: يبحث أولاً في قاعدة المعرفة ثم يجيب.\n"
            "🧠 الاختبارات: أسئلة JSON قابلة للتوسعة.\n\n"
            "لإضافة محتوى: ضع الملفات في مجلد data ثم شغّل ingest.py.",
            reply_markup=kb([[InlineKeyboardButton("🏠 الرئيسية", callback_data="home")]]),
            parse_mode="Markdown"
        )
        return

    parts=data.split(":")
    if len(parts)>=3 and parts[1]=="branch":
        prefix,_,branch=parts
        if prefix in {"lessons","bac","quiz"}:
            await q.edit_message_text(
                f"{BRANCHES.get(branch,'الشعبة')}\n\nاختر المادة:",
                reply_markup=subject_menu(prefix, branch),
                parse_mode="Markdown"
            )
        return

    if len(parts)>=4 and parts[1]=="subject":
        prefix,_,branch,index=parts
        try:
            subject=SUBJECTS[branch][int(index)]
        except Exception:
            subject="المادة"
        context.user_data.update({"branch":branch,"subject":subject})

        con=connect()
        if prefix=="quiz":
            rows=con.execute(
                "SELECT id,question,choices,answer,explanation FROM quiz_questions WHERE branch=? AND subject=?",
                (branch,subject)
            ).fetchall()
            con.close()
            if not rows:
                await q.edit_message_text(
                    f"🧠 *{subject}*\n\nلا توجد أسئلة اختبار في قاعدة البيانات بعد.",
                    reply_markup=kb([[InlineKeyboardButton("🔙 المواد", callback_data="quiz")]]),
                    parse_mode="Markdown"
                )
                return
            row=random.choice(rows)
            choices=json.loads(row["choices"]) if row["choices"] else []
            context.user_data["quiz"]=dict(row)
            buttons=[[InlineKeyboardButton(c, callback_data=f"quiz_answer:{i}") for i,c in enumerate(choices)]]
            buttons.append([InlineKeyboardButton("🏠 الرئيسية", callback_data="home")])
            await q.edit_message_text(
                "🧠 *اختبار*\n\n"+row["question"],
                reply_markup=kb(buttons), parse_mode="Markdown"
            )
            return

        if prefix=="lessons":
            rows=con.execute(
                "SELECT id,title,kind,year,path FROM documents "
                "WHERE kind IN ('lessons','summaries') AND (branch=? OR branch IS NULL) "
                "AND (subject=? OR subject IS NULL) ORDER BY title",
                (branch,subject)
            ).fetchall()
            con.close()
            if not rows:
                await q.edit_message_text(
                    f"📘 *{subject}*\n\nلا توجد ملفات مفهرسة بعد.\n"
                    "ضع ملفات PDF/TXT/MD في data ثم شغّل:\n`python ingest.py`",
                    reply_markup=kb([[InlineKeyboardButton("🏠 الرئيسية", callback_data="home")]]),
                    parse_mode="Markdown"
                )
                return
            buttons=[[InlineKeyboardButton("📄 "+r["title"][:60], callback_data=f"doc:{r['id']}")] for r in rows[:40]]
            buttons.append([InlineKeyboardButton("🔙 المواد", callback_data="lessons")])
            await q.edit_message_text(
                f"📚 *{subject}*\n\nاختر الدرس أو الملخص:",
                reply_markup=kb(buttons), parse_mode="Markdown"
            )
            return

        # bac: choose year first
        con.close()
        await q.edit_message_text(
            f"📝 *{subject}*\n\nاختر سنة البكالوريا:",
            reply_markup=year_menu(branch, subject),
            parse_mode="Markdown"
        )
        return

    if parts[0]=="bacyear":
        _,branch,subject,year=parts
        year=int(year)
        con=connect()
        rows=con.execute(
            "SELECT id,title,kind,year,path FROM documents "
            "WHERE kind='bac' AND branch=? AND subject=? AND year=? "
            "ORDER BY title",
            (branch,subject,year)
        ).fetchall()
        con.close()
        if not rows:
            await q.edit_message_text(
                f"📝 *بكالوريا {year} — {subject}*\n\n"
                "لا توجد ملفات لهذه السنة في قاعدة البيانات بعد.",
                reply_markup=kb([
                    [InlineKeyboardButton("🔙 السنوات", callback_data=f"bac:subject:{branch}:{SUBJECTS[branch].index(subject)}")],
                    [InlineKeyboardButton("🏠 الرئيسية", callback_data="home")]
                ]),
                parse_mode="Markdown"
            )
            return
        buttons=[[InlineKeyboardButton("📄 "+r["title"][:60], callback_data=f"doc:{r['id']}")] for r in rows]
        buttons.append([InlineKeyboardButton("🔙 السنوات", callback_data=f"bac:subject:{branch}:{SUBJECTS[branch].index(subject)}")])
        await q.edit_message_text(
            f"📝 *بكالوريا {year} — {subject}*\n\nاختر الملف:",
            reply_markup=kb(buttons), parse_mode="Markdown"
        )
        return

    if parts[0]=="bacall":
        _,branch,subject=parts
        con=connect()
        rows=con.execute(
            "SELECT id,title,kind,year,path FROM documents "
            "WHERE kind='bac' AND branch=? AND subject=? ORDER BY year DESC,title",
            (branch,subject)
        ).fetchall()
        con.close()
        if not rows:
            await q.edit_message_text(
                f"📝 *{subject}*\n\nلا توجد مواضيع مفهرسة بعد.",
                reply_markup=kb([[InlineKeyboardButton("🏠 الرئيسية", callback_data="home")]]),
                parse_mode="Markdown"
            )
            return
        buttons=[]
        for r in rows[:60]:
            label=f"{r['year']} — {r['title']}" if r["year"] else r["title"]
            buttons.append([InlineKeyboardButton("📄 "+label[:60], callback_data=f"doc:{r['id']}")])
        buttons.append([InlineKeyboardButton("🔙 السنوات", callback_data=f"bac:subject:{branch}:{SUBJECTS[branch].index(subject)}")])
        await q.edit_message_text(
            f"📝 *{subject}*\n\nكل الملفات المتاحة:",
            reply_markup=kb(buttons), parse_mode="Markdown"
        )
        return

    if parts[0]=="doc":
        from pathlib import Path
        from config import DATA_DIR
        doc_id=int(parts[1])
        con=connect()
        row=con.execute("SELECT * FROM documents WHERE id=?", (doc_id,)).fetchone()
        con.close()
        if not row:
            await q.edit_message_text("❌ الملف غير موجود.", reply_markup=main_menu())
            return
        file_path=DATA_DIR / row["path"]
        if file_path.exists() and file_path.suffix.lower()==".pdf":
            await q.message.reply_document(
                document=str(file_path),
                caption=f"📄 {row['title']}"
            )
            await q.edit_message_text(
                "✅ تم إرسال الملف.",
                reply_markup=kb([[InlineKeyboardButton("🏠 الرئيسية", callback_data="home")]])
            )
        elif file_path.exists() and file_path.suffix.lower() in {".txt",".md"}:
            text=file_path.read_text(encoding="utf-8", errors="ignore")
            text=text[:3800]
            await q.edit_message_text(
                f"📄 *{row['title']}*\n\n{text}",
                reply_markup=kb([[InlineKeyboardButton("🏠 الرئيسية", callback_data="home")]]),
                parse_mode="Markdown"
            )
        else:
            await q.edit_message_text(
                f"📄 *{row['title']}*\n\nالملف غير موجود على القرص.",
                reply_markup=kb([[InlineKeyboardButton("🏠 الرئيسية", callback_data="home")]]),
                parse_mode="Markdown"
            )
        return

    if parts[0]=="quiz_answer":
        saved=context.user_data.get("quiz")
        if not saved:
            await q.edit_message_text("انتهى الاختبار. ابدأ من جديد.", reply_markup=main_menu())
            return
        idx=int(parts[1])
        choices=json.loads(saved["choices"])
        chosen=choices[idx] if idx < len(choices) else ""
        ok=chosen==saved["answer"]
        msg=("✅ *إجابة صحيحة!*\n\n" if ok else f"❌ *إجابة غير صحيحة.*\n\nالإجابة الصحيحة: **{saved['answer']}**\n\n")
        msg += saved["explanation"] or ""
        await q.edit_message_text(msg, reply_markup=kb([
            [InlineKeyboardButton("🔄 سؤال آخر", callback_data=f"quiz:branch:{context.user_data.get('branch','science')}")],
            [InlineKeyboardButton("🏠 الرئيسية", callback_data="home")]
        ]), parse_mode="Markdown")
        return

async def text_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    mode = context.user_data.get("mode")
    text = update.message.text.strip()

    if mode == "ai":
        msg = await update.message.reply_text("🤔 أبحث في قاعدة المعرفة وأجيب...")
        try:
            ans, n = answer(
                text,
                context.user_data.get("branch"),
                context.user_data.get("subject")
            )

            await msg.delete()

            await update.message.reply_text(
                "🤖 *BAC DZ AI*\n\n" + ans,
                parse_mode="Markdown"
            )

        except Exception as e:
            await msg.edit_text("❌ حدث خطأ:\n" + str(e))

        return
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
            (f"%{text}%", f"%{text}%")
        ).fetchall()

        con.close()

        if not rows:
            await update.message.reply_text(
                "🔎 لم أجد نتائج. جرّب كلمة أخرى.",
                reply_markup=main_menu()
            )
            return

        lines = ["🔎 *نتائج البحث:*"]

        for r in rows:
            y = f"{r['year']} - " if r["year"] else ""
            lines.append(f"- {y}{r['title']} ({r['kind']})")

        await update.message.reply_text(
            "\n".join(lines),
            parse_mode="Markdown",
            reply_markup=main_menu()
        )

        return

    await update.message.reply_text(
        "اختر خدمة من /start",
        reply_markup=main_menu()
    )
        except Exception as e:
            await msg.edit_text("❌ حدث خطأ:\n"+str(e))
        return
    if mode=="search":
        con=connect()
        rows=con.execute(
            "SELECT id,title,kind,year,path FROM documents WHERE title LIKE ? OR content LIKE ? ORDER BY year DESC LIMIT 20",
            (f"%{text}%",f"%{text}%")
        ).fetchall()
        con.close()
        if not rows:
            await update.message.reply_text("🔎 لم أجد نتائج. جرّب كلمة أخرى.", reply_markup=main_menu())
            return
        lines=["🔎 *نتائج البحث:*",""]
        for r in rows:
            y=f"{r['year']} - " if r["year"] else ""
            lines.append(f"• {y}{r['title']} ({r['kind']})")
        await update.message.reply_text("\n".join(lines), parse_mode="Markdown", reply_markup=main_menu())
        return
    await update.message.reply_text("اختر خدمة من /start", reply_markup=main_menu())

def main():
    validate_config()
    init_db()
    app=Application.builder().token(TELEGRAM_TOKEN).build()
    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(callbacks))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, text_handler))
    print("✅ BAC DZ AI يعمل")
    app.run_polling()

if __name__=="__main__":
    main()
