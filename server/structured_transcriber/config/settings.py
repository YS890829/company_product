"""
統合設定管理
環境変数の読み込みと設定管理

このモジュールは、プロジェクト全体で使用される設定を一元管理します。
"""

import os
from pathlib import Path
from typing import List
from dotenv import load_dotenv

# ==================== プロジェクトパス ====================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
PROCESSED_DATA_DIR = DATA_DIR / "processed"
OUTPUT_DIR = DATA_DIR / "output"
DOWNLOADS_DIR = PROJECT_ROOT / "downloads"

# .envファイルを読み込み
load_dotenv(PROJECT_ROOT / ".env")

# ==================== データベース設定 ====================

# SQLite Database
SQLITE_DB_PATH = os.getenv(
    "SQLITE_DB_PATH",
    str(DATA_DIR / "participants.db")
)

# Vector Database (ChromaDB)
VECTOR_DB_PATH = os.getenv(
    "VECTOR_DB_PATH",
    str(PROJECT_ROOT / "chroma_db")
)

# Vector DB Collection Name
VECTOR_DB_COLLECTION = os.getenv("VECTOR_DB_COLLECTION", "transcripts_unified")

# ==================== API設定 ====================

# CORS Origins (comma-separated list)
CORS_ORIGINS_STR = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:3000,http://localhost:8501"
)
CORS_ORIGINS: List[str] = [origin.strip() for origin in CORS_ORIGINS_STR.split(",")]

# API Server
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8001"))

# ==================== ログ設定 ====================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = PROJECT_ROOT / "logs"

# ==================== Google API設定 ====================

# Gemini API
GEMINI_API_KEY_FREE = os.getenv("GEMINI_API_KEY_FREE")
GEMINI_API_KEY_PAID = os.getenv("GEMINI_API_KEY_PAID")
USE_PAID_TIER = os.getenv("USE_PAID_TIER", "false").lower() == "true"

# Google Drive
GOOGLE_DRIVE_SCOPES = os.getenv(
    "GOOGLE_DRIVE_SCOPES",
    "https://www.googleapis.com/auth/drive,https://www.googleapis.com/auth/calendar"
)
CREDENTIALS_FILE = os.getenv("CREDENTIALS_FILE", str(PROJECT_ROOT / "credentials.json"))
TOKEN_PATH = os.getenv("TOKEN_PATH", str(PROJECT_ROOT / "token.json"))

# Google Calendar
ENABLE_CALENDAR_INTEGRATION = os.getenv("ENABLE_CALENDAR_INTEGRATION", "true").lower() == "true"
CALENDAR_ID = os.getenv("CALENDAR_ID", "primary")

# ==================== 機能フラグ ====================

ENABLE_VECTOR_DB = os.getenv("ENABLE_VECTOR_DB", "true").lower() == "true"
ENABLE_INTEGRATED_PIPELINE = os.getenv("ENABLE_INTEGRATED_PIPELINE", "true").lower() == "true"
ENABLE_ICLOUD_MONITORING = os.getenv("ENABLE_ICLOUD_MONITORING", "true").lower() == "true"
ENABLE_DRIVE_UPLOAD = os.getenv("ENABLE_DRIVE_UPLOAD", "true").lower() == "true"
ENABLE_DOCS_EXPORT = os.getenv("ENABLE_DOCS_EXPORT", "false").lower() == "true"

# ==================== iCloud設定 ====================

ICLOUD_DRIVE_PATH = os.path.expanduser(
    os.getenv(
        "ICLOUD_DRIVE_PATH",
        "~/Library/Group Containers/group.com.apple.VoiceMemos.shared/Recordings"
    )
)
PROCESSED_FILES_REGISTRY = os.getenv(
    "PROCESSED_FILES_REGISTRY",
    str(PROJECT_ROOT / ".processed_files_registry.jsonl")
)
AUTO_DELETE_LOCAL_FILES = os.getenv("AUTO_DELETE_LOCAL_FILES", "false").lower() == "true"

# ==================== ファイル管理 ====================

PROCESSED_FILE = os.getenv("PROCESSED_FILE", str(PROJECT_ROOT / ".processed_drive_files.txt"))
DELETION_LOG_FILE = os.getenv("DELETION_LOG_FILE", str(PROJECT_ROOT / ".deletion_log.jsonl"))
UPLOAD_LOG_FILE = os.getenv("UPLOAD_LOG_FILE", str(PROJECT_ROOT / ".upload_log.jsonl"))
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", str(DOWNLOADS_DIR))

# ==================== Webhook設定 ====================

CHANNEL_EXPIRATION_HOURS = int(os.getenv("CHANNEL_EXPIRATION_HOURS", "24"))

# ==================== 自動リネーム設定 ====================

AUTO_RENAME_FILES = os.getenv("AUTO_RENAME_FILES", "true").lower() == "true"

# ==================== Google Driveアップロード ====================

DRIVE_UPLOAD_FOLDER = os.getenv("DRIVE_UPLOAD_FOLDER", "transcriptions")

# ==================== ユーティリティ関数 ====================

def get_gemini_api_key() -> str:
    """Tierの設定に応じて適切なGemini API Keyを取得"""
    if USE_PAID_TIER and GEMINI_API_KEY_PAID:
        return GEMINI_API_KEY_PAID
    if GEMINI_API_KEY_FREE:
        return GEMINI_API_KEY_FREE
    raise ValueError("Gemini API keyが環境変数に設定されていません")


def ensure_directories():
    """必要なディレクトリが存在することを確認"""
    directories = [
        DATA_DIR,
        RAW_DATA_DIR,
        PROCESSED_DATA_DIR,
        OUTPUT_DIR,
        DOWNLOADS_DIR,
        LOG_DIR,
    ]

    if ENABLE_VECTOR_DB:
        directories.append(Path(VECTOR_DB_PATH).parent)

    for directory in directories:
        if directory:
            directory.mkdir(parents=True, exist_ok=True)
