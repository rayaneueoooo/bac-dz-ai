
import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent
DATA_DIR = BASE_DIR / "data"
DB_PATH = BASE_DIR / "bac_dz_ai.sqlite3"

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY")
AI_MODEL = os.getenv("AI_MODEL", "claude-sonnet-5")
ADMIN_ID = os.getenv("ADMIN_ID")

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
    if not ANTHROPIC_API_KEY:
        missing.append("ANTHROPIC_API_KEY")
    if missing:
        raise RuntimeError("Missing environment variables: " + ", ".join(missing))
