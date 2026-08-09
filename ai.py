from google import genai
from config import GEMINI_API_KEY, AI_MODEL
from db import search_chunks

if not GEMINI_API_KEY:
    raise RuntimeError("Missing GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

SYSTEM = """
أنت BAC DZ AI، مساعد تعليمي متخصص لتلاميذ البكالوريا الجزائرية.

أجب بالعربية الواضحة والمبسطة، ويمكن استعمال المصطلحات الفرنسية أو الإنجليزية عند الحاجة.

عندما توجد مصادر في السياق، اعتمد عليها أولاً ولا تخترع معلومات من خارجها.
إذا لم تجد المعلومة في المصادر، قل بوضوح إن المصادر المتاحة لا تحتوي عليها.

عند حل التمارين:
- اشرح المنهجية والخطوات.
- لا تعط النتيجة فقط.
- اجعل الشرح مناسباً لمستوى البكالوريا.

عند السؤال النظري:
- قدم تعريفاً واضحاً.
- ثم شرحاً مختصراً ومنظماً.
- ثم مثالاً عند الحاجة.

لا تدّع أن معلومة موجودة في المصادر إذا لم تكن موجودة فعلاً.
"""

def answer(question, branch=None, subject=None, year=None):
    terms = " ".join(question.split()[:12])

    rows = search_chunks(
        terms,
        limit=8,
        branch=branch,
        subject=subject,
        year=year
    )

    context = []

    for r in rows:
        context.append(
            f"[{r['title']}] | {r['kind']} | {r['year'] or ''}\n"
            f"{r['text']}"
        )

    source_text = "\n\n---\n\n".join(context)

    if not source_text:
        source_text = "لا توجد مصادر مطابقة في قاعدة المعرفة الحالية."

    prompt = f"""
سؤال الطالب:
{question}

المصادر الموجودة في قاعدة BAC DZ AI:
{source_text}

أجب بشكل منظم ومناسب لتلميذ البكالوريا الجزائرية.
"""

    response = client.models.generate_content(
        model=AI_MODEL or "gemini-2.5-flash",
        contents=prompt,
        config={
            "system_instruction": SYSTEM,
            "max_output_tokens": 1500,
        }
    )

    text = response.text

    return text, len(rows)