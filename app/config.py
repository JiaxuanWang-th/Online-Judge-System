"""Application configuration."""

import os
from pathlib import Path

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = Path(os.environ.get("OJ_DATA_DIR", BASE_DIR / "data"))
TEMP_DIR = Path(os.environ.get("OJ_TEMP_DIR", BASE_DIR / "temp"))
BACKUP_DIR = Path(os.environ.get("OJ_BACKUP_DIR", DATA_DIR / "backups"))
FRONTEND_DIR = BASE_DIR / "frontend"

USERS_FILE = DATA_DIR / "users.json"
PROBLEMS_FILE = DATA_DIR / "problems.json"
SUBMISSIONS_FILE = DATA_DIR / "submissions.json"
CASE_LOGS_FILE = DATA_DIR / "case_logs.json"
AUDIT_LOGS_FILE = DATA_DIR / "audit_logs.json"
BACKUPS_META_FILE = DATA_DIR / "backups_meta.json"

SESSION_SECRET = os.environ.get("OJ_SESSION_SECRET", "oj-dev-session-secret-change-me")
SESSION_COOKIE_NAME = "oj_session"
SESSION_MAX_AGE = 60 * 60 * 24 * 7 # 有效期

DEFAULT_ADMIN_USERNAME = "admin"
DEFAULT_ADMIN_PASSWORD = "admin123456"

MAX_SOURCE_CODE_BYTES = 64 * 1024
LOG_TEXT_LIMIT = 4000

PYTHON_EXECUTABLE = os.environ.get("OJ_PYTHON")  # None -> sys.executable


def ensure_directories() -> None:
    # 确保数据相关目录存在
    DATA_DIR.mkdir(parents=True, exist_ok=True)
    TEMP_DIR.mkdir(parents=True, exist_ok=True)
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
