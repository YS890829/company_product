"""
Structured Logging Configuration

This module provides centralized logging configuration with:
- Structured logging (JSON format for production)
- Log rotation
- Different log levels for different environments
- Separate loggers for different components

Based on 2025 FastAPI logging best practices.
"""

import logging
import logging.handlers
import json
from pathlib import Path
from typing import Optional
from datetime import datetime

from . import config


# ==================== Custom Formatter ====================

class StructuredFormatter(logging.Formatter):
    """
    JSON formatter for structured logging.

    Outputs logs in JSON format for easier parsing and analysis.
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.

        Args:
            record: LogRecord to format

        Returns:
            JSON string
        """
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add custom fields if present
        if hasattr(record, "extra_data"):
            log_data.update(record.extra_data)

        return json.dumps(log_data, ensure_ascii=False)


class ColoredFormatter(logging.Formatter):
    """
    Colored formatter for console output in development.
    """

    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
        'RESET': '\033[0m'       # Reset
    }

    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record with colors.

        Args:
            record: LogRecord to format

        Returns:
            Colored log string
        """
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        reset = self.COLORS['RESET']

        # Format timestamp
        timestamp = datetime.fromtimestamp(record.created).strftime('%Y-%m-%d %H:%M:%S')

        # Format message
        log_message = (
            f"{color}[{record.levelname}]{reset} "
            f"{timestamp} "
            f"{record.name} "
            f"- {record.getMessage()}"
        )

        # Add exception if present
        if record.exc_info:
            log_message += f"\n{self.formatException(record.exc_info)}"

        return log_message


# ==================== Logger Setup ====================

def setup_logging(
    log_level: str = "INFO",
    log_dir: Optional[Path] = None,
    log_file: str = "app.log",
    use_json: bool = False,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> logging.Logger:
    """
    Set up application logging with rotation.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_dir: Directory for log files (default: config.LOG_DIR)
        log_file: Log file name
        use_json: Use JSON formatter (for production)
        max_bytes: Maximum size of each log file before rotation
        backup_count: Number of backup files to keep

    Returns:
        Configured root logger

    Example:
        logger = setup_logging(log_level="INFO", use_json=True)
        logger.info("Application started")
    """
    # Ensure log directory exists
    if log_dir is None:
        log_dir = config.LOG_DIR
    log_dir.mkdir(parents=True, exist_ok=True)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, log_level.upper()))

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler (always colored in development)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(getattr(logging, log_level.upper()))

    if use_json:
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler.setFormatter(ColoredFormatter())

    root_logger.addHandler(console_handler)

    # File handler with rotation
    log_file_path = log_dir / log_file
    file_handler = logging.handlers.RotatingFileHandler(
        log_file_path,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding='utf-8'
    )
    file_handler.setLevel(getattr(logging, log_level.upper()))

    if use_json:
        file_handler.setFormatter(StructuredFormatter())
    else:
        file_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        )

    root_logger.addHandler(file_handler)

    return root_logger


def get_logger(name: str, log_level: Optional[str] = None) -> logging.Logger:
    """
    Get a logger with the specified name.

    Args:
        name: Logger name (usually __name__)
        log_level: Optional log level override

    Returns:
        Configured logger

    Example:
        logger = get_logger(__name__)
        logger.info("Processing started")
    """
    logger = logging.getLogger(name)

    if log_level:
        logger.setLevel(getattr(logging, log_level.upper()))

    return logger


# ==================== Component-Specific Loggers ====================

def setup_api_logger() -> logging.Logger:
    """
    Set up logger for API server.

    Returns:
        Configured API logger
    """
    logger = get_logger("api_server")
    logger.setLevel(logging.INFO)
    return logger


def setup_gemini_logger() -> logging.Logger:
    """
    Set up logger for Gemini API calls.

    Returns:
        Configured Gemini logger
    """
    logger = get_logger("gemini_api")
    logger.setLevel(logging.INFO)
    return logger


def setup_vector_db_logger() -> logging.Logger:
    """
    Set up logger for Vector DB operations.

    Returns:
        Configured Vector DB logger
    """
    logger = get_logger("vector_db")
    logger.setLevel(logging.INFO)
    return logger


def setup_sqlite_logger() -> logging.Logger:
    """
    Set up logger for SQLite operations.

    Returns:
        Configured SQLite logger
    """
    logger = get_logger("sqlite_db")
    logger.setLevel(logging.INFO)
    return logger


# ==================== Log Filtering ====================

class SensitiveDataFilter(logging.Filter):
    """
    Filter to remove sensitive data from logs.

    Prevents API keys, tokens, and other sensitive data from being logged.
    """

    SENSITIVE_PATTERNS = [
        'api_key',
        'apikey',
        'token',
        'password',
        'secret',
        'authorization',
    ]

    def filter(self, record: logging.LogRecord) -> bool:
        """
        Filter log record to remove sensitive data.

        Args:
            record: LogRecord to filter

        Returns:
            True to include record, False to exclude
        """
        # Check message for sensitive patterns
        message = record.getMessage().lower()

        for pattern in self.SENSITIVE_PATTERNS:
            if pattern in message:
                # Replace the message with redacted version
                record.msg = "[REDACTED - Sensitive data removed]"
                record.args = ()
                break

        return True


# ==================== Initialization ====================

def init_logging(environment: str = "development"):
    """
    Initialize logging for the application.

    Args:
        environment: Environment name ("development", "production", "testing")

    Example:
        init_logging(environment="production")
    """
    # Determine log level and format based on environment
    if environment == "production":
        log_level = "INFO"
        use_json = True
    elif environment == "development":
        log_level = config.LOG_LEVEL
        use_json = False
    else:  # testing
        log_level = "WARNING"
        use_json = False

    # Set up root logger
    root_logger = setup_logging(
        log_level=log_level,
        log_dir=config.LOG_DIR,
        log_file=f"{environment}.log",
        use_json=use_json
    )

    # Add sensitive data filter
    sensitive_filter = SensitiveDataFilter()
    root_logger.addFilter(sensitive_filter)

    # Set up component loggers
    setup_api_logger()
    setup_gemini_logger()
    setup_vector_db_logger()
    setup_sqlite_logger()

    logging.info(f"Logging initialized for {environment} environment")


# ==================== Usage Example ====================

if __name__ == "__main__":
    # Initialize logging
    init_logging(environment="development")

    # Get logger
    logger = get_logger(__name__)

    # Log messages
    logger.debug("This is a debug message")
    logger.info("This is an info message")
    logger.warning("This is a warning message")
    logger.error("This is an error message")

    # Log with exception
    try:
        raise ValueError("Example error")
    except Exception:
        logger.exception("An exception occurred")

    # Test sensitive data filtering
    logger.info("API key: sk-12345")  # Should be redacted
