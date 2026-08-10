
import json
from db import init_db, connect

QUESTIONS=[
    {
        "branch":"science","subject":"رياضيات",
        "question":"إذا كانت f(x)=x²، فما مشتقتها؟",
        "choices":["x","2x","x²","2"],
        "answer":"2x",
        "explanation":"قاعدة اشتقاق x^n هي n*x^(n-1)، وبالتالي مشتقة x² هي 2x."
    },
    {
        "branch":"science","subject":"فيزياء",
        "question":"ما الوحدة الدولية للقوة؟",
        "choices":["جول","نيوتن","واط","باسكال"],
        "answer":"نيوتن",
        "explanation":"الوحدة الدولية للقوة هي النيوتن (N)."
    },
]

init_db()
con=connect()
con.execute("DELETE FROM quiz_questions")
con.executemany(
    "INSERT INTO quiz_questions(branch,subject,question,choices,answer,explanation) VALUES(?,?,?,?,?,?)",
    [(q["branch"],q["subject"],q["question"],json.dumps(q["choices"],ensure_ascii=False),q["answer"],q["explanation"]) for q in QUESTIONS]
)
con.commit(); con.close()
print("Seeded",len(QUESTIONS),"questions.")
