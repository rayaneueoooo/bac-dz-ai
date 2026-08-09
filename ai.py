
import anthropic
from config import ANTHROPIC_API_KEY, AI_MODEL
from db import search_chunks

client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)

SYSTEM = """
أنت BAC DZ AI، مساعد تعليمي مخصص لتلاميذ البكالوريا الجزائرية.
أجب بالعربية الواضحة، ويمكن استعمال مصطلحات فرنسية/إنجليزية عند الحاجة.
عندما توجد مصادر في السياق، اعتمد عليها أولاً ولا تخترع معلومات من خارجها.
إذا لم تجد المعلومة في المصادر، قل بوضوح إن قاعدة المعرفة الحالية لا تحتوي عليها،
ثم قدم شرحاً عاماً فقط إذا كان ذلك مفيداً.
عند حل التمارين: اشرح المنهجية والخطوات، ثم النتيجة.
عند الأسئلة النظرية: قدم تعريفاً، شرحاً، مثالاً، ثم ملاحظة للبكالوريا عند الحاجة.
لا تدّع أن ملفاً أو موضوعاً موجود إذا لم يكن مفهرساً.
"""

def answer(question, branch=None, subject=None, year=None):
    # SQLite FTS query can be too strict with Arabic; use a few keywords.
    terms = " ".join(question.split()[:12])
    rows = search_chunks(terms, limit=8, branch=branch, subject=subject, year=year)
    context=[]
    for r in rows:
        context.append(
            f"[{r['title']} | {r['kind']} | {r['year'] or ''}]\n{r['text']}"
        )
    source_text="\n\n---\n\n".join(context)
    if not source_text:
        source_text="لا توجد مصادر مطابقة في قاعدة المعرفة الحالية."

    prompt=f"""
سؤال الطالب:
{question}

المصادر المسترجعة من قاعدة BAC DZ AI:
{source_text}

اكتب الإجابة بشكل منظم ومناسب للبكالوريا.
"""
    response=client.messages.create(
        model=AI_MODEL,
        max_tokens=2500,
        system=SYSTEM,
        messages=[{"role":"user","content":prompt}],
    )
    return response.content[0].text, len(rows)
