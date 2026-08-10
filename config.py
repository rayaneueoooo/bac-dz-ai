
import os

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
AI_MODEL = "gemini-2.5-flash"
ADMIN_ID = os.getenv("ADMIN_ID")
DB_PATH = os.getenv("DB_PATH", "bac.db")
BRANCHES = {
    "science": "🔬 علوم تجريبية",
    "math": "📐 رياضيات",
    "technical": "⚙️ تقني رياضي",
    "management": "💼 تسيير واقتصاد",
    "philosophy": "📖 آداب وفلسفة",
    "languages": "🌍 لغات أجنبية",
    "other": "🧩 شعب/تخصصات أخرى",
}

SUBJECTS = {
    "science": ["رياضيات", "فيزياء", "علوم الطبيعة والحياة", "لغة عربية", "لغة فرنسية", "لغة إنجليزية", "فلسفة", "تاريخ وجغرافيا", "علوم إسلامية"],
    "math": ["رياضيات", "فيزياء", "لغة عربية", "لغة فرنسية", "لغة إنجليزية", "فلسفة", "تاريخ وجغرافيا", "علوم إسلامية"],
    "technical": ["رياضيات", "فيزياء", "تكنولوجيا", "لغة عربية", "لغة فرنسية", "لغة إنجليزية", "فلسفة", "تاريخ وجغرافيا", "علوم إسلامية"],
    "management": ["تسيير محاسبي ومالي", "اقتصاد ومناجمنت", "قانون", "رياضيات", "لغة عربية", "لغة فرنسية", "لغة إنجليزية", "فلسفة", "تاريخ وجغرافيا"],
    "philosophy": ["فلسفة", "لغة عربية", "لغة فرنسية", "لغة إنجليزية", "تاريخ وجغرافيا", "علوم إسلامية"],
    "languages": ["لغة عربية", "لغة فرنسية", "لغة إنجليزية", "لغة أجنبية ثالثة", "فلسفة", "تاريخ وجغرافيا", "علوم إسلامية"],
    "other": ["رياضيات", "فيزياء", "لغة عربية", "لغة فرنسية", "لغة إنجليزية", "فلسفة", "تاريخ وجغرافيا", "علوم إسلامية"],
}

YEARS = list(range(2008, 2027))

def validate_config():
    missing = []

    if not TELEGRAM_TOKEN:
        missing.append("TELEGRAM_TOKEN")

    if not GEMINI_API_KEY:
        missing.append("GEMINI_API_KEY")

    if missing:
        raise RuntimeError(
            "Missing environment variables: " + ", ".join(missing)
        )