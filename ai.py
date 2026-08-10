import os
from groq import Groq

# قراءة المفتاح بأمان من إعدادات السيرفر دون كتابته علناً
GROQ_API_KEY = os.environ.get("GROQ_API_KEY")

def answer(question, branch="", subject=""):
    if not GROQ_API_KEY:
        return "❌ خطأ: لم يتم ضبط مفتاح GROQ_API_KEY في إعدادات السيرفر (Environment Variables).", 0
        
    try:
        client = Groq(api_key=GROQ_API_KEY)
        
        # هنا يتم صياغة الطلب للذكاء الاصطناعي مع مراعاة المادة والشعبة
        prompt = f"أنت مساعد تعليمي لتلاميذ البكالوريا في الجزائر. الشعبة: {branch}، المادة: {subject}.\nالسؤال: {question}"
        
        chat_completion = client.chat.completions.create(
            messages=[
                {
                    "role": "user",
                    "content": prompt,
                }
            ],
            model="llama3-8b-8192",
        )
        
        reply = chat_completion.choices[0].message.content
        return reply, len(reply)
        
    except Exception as e:
        return f"❌ حدث خطأ أثناء الاتصال بالذكاء الاصطناعي: {str(e)}", 0