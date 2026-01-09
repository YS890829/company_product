"""
Unified Configuration Management

This module provides centralized configuration for database paths,
API keys, and other environment variables used across the project.
"""

import os
from pathlib import Path
from typing import List

# ==================== Project Paths ====================

PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DOWNLOADS_DIR = PROJECT_ROOT / "downloads"

# ==================== Database Configuration ====================

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

# ==================== API Configuration ====================

# CORS Origins (comma-separated list)
CORS_ORIGINS_STR = os.getenv(
    "CORS_ORIGINS",
    "http://localhost:5173,http://localhost:3000"
)
CORS_ORIGINS: List[str] = [origin.strip() for origin in CORS_ORIGINS_STR.split(",")]

# API Server
API_HOST = os.getenv("API_HOST", "0.0.0.0")
API_PORT = int(os.getenv("API_PORT", "8001"))

# ==================== Logging Configuration ====================

LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")
LOG_DIR = PROJECT_ROOT / "logs"

# ==================== Google API Configuration ====================

# Gemini API
GEMINI_API_KEY_FREE = os.getenv("GEMINI_API_KEY_FREE")
GEMINI_API_KEY_PAID = os.getenv("GEMINI_API_KEY_PAID")
USE_PAID_TIER = os.getenv("USE_PAID_TIER", "false").lower() == "true"

# Google Drive
GOOGLE_DRIVE_SCOPES = os.getenv(
    "GOOGLE_DRIVE_SCOPES",
    "https://www.googleapis.com/auth/drive"
)
CREDENTIALS_FILE = os.getenv("CREDENTIALS_FILE", "credentials.json")
TOKEN_PATH = os.getenv("TOKEN_PATH", "token.json")

# Google Calendar
ENABLE_CALENDAR_INTEGRATION = os.getenv("ENABLE_CALENDAR_INTEGRATION", "true").lower() == "true"
CALENDAR_ID = os.getenv("CALENDAR_ID", "primary")

# ==================== Feature Flags ====================

ENABLE_VECTOR_DB = os.getenv("ENABLE_VECTOR_DB", "true").lower() == "true"
ENABLE_INTEGRATED_PIPELINE = os.getenv("ENABLE_INTEGRATED_PIPELINE", "true").lower() == "true"
ENABLE_ICLOUD_MONITORING = os.getenv("ENABLE_ICLOUD_MONITORING", "true").lower() == "true"
ENABLE_DRIVE_UPLOAD = os.getenv("ENABLE_DRIVE_UPLOAD", "true").lower() == "true"
ENABLE_DOCS_EXPORT = os.getenv("ENABLE_DOCS_EXPORT", "true").lower() == "true"

# ==================== iCloud Configuration ====================

ICLOUD_DRIVE_PATH = os.path.expanduser(
    os.getenv(
        "ICLOUD_DRIVE_PATH",
        "~/Library/Group Containers/group.com.apple.VoiceMemos.shared/Recordings"
    )
)
PROCESSED_FILES_REGISTRY = os.getenv("PROCESSED_FILES_REGISTRY", ".processed_files_registry.jsonl")
AUTO_DELETE_LOCAL_FILES = os.getenv("AUTO_DELETE_LOCAL_FILES", "false").lower() == "true"

# ==================== File Management ====================

PROCESSED_FILE = os.getenv("PROCESSED_FILE", ".processed_drive_files.txt")
DELETION_LOG_FILE = os.getenv("DELETION_LOG_FILE", ".deletion_log.jsonl")
UPLOAD_LOG_FILE = os.getenv("UPLOAD_LOG_FILE", ".upload_log.jsonl")
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "downloads")

# ==================== Webhook Configuration ====================

CHANNEL_EXPIRATION_HOURS = int(os.getenv("CHANNEL_EXPIRATION_HOURS", "24"))

# ==================== Auto Rename Configuration ====================

AUTO_RENAME_FILES = os.getenv("AUTO_RENAME_FILES", "true").lower() == "true"

# ==================== Google Drive Upload ====================

DRIVE_UPLOAD_FOLDER = os.getenv("DRIVE_UPLOAD_FOLDER", "transcriptions")


# ==================== Utility Functions ====================

def get_gemini_api_key() -> str:
    """Get the appropriate Gemini API key based on tier setting"""
    if USE_PAID_TIER and GEMINI_API_KEY_PAID:
        return GEMINI_API_KEY_PAID
    if GEMINI_API_KEY_FREE:
        return GEMINI_API_KEY_FREE
    raise ValueError("No Gemini API key found in environment variables")


def ensure_directories():
    """Ensure all required directories exist"""
    directories = [
        DATA_DIR,
        DOWNLOADS_DIR,
        LOG_DIR,
        Path(VECTOR_DB_PATH).parent if ENABLE_VECTOR_DB else None,
    ]
    for directory in directories:
        if directory:
            directory.mkdir(parents=True, exist_ok=True)
