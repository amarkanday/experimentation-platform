"""
Logging configuration for the experimentation platform.

This module configures structured JSON logging with proper rotation and context.
"""

import json
import logging
import sys
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger
from typing import Dict, Any, Optional
import uuid
from datetime import datetime

# Configure JSON formatter
class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom JSON formatter that includes additional context."""

    def add_fields(self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]) -> None:
        """Add custom fields to the log record."""
        super(CustomJsonFormatter, self).add_fields(log_record, record, message_dict)

        # Add timestamp in ISO format
        log_record['timestamp'] = datetime.utcnow().isoformat()

        # Add log level
        log_record['level'] = record.levelname

        # Add logger name
        log_record['logger'] = record.name

        # Add file and line number
        log_record['file'] = record.filename
        log_record['line'] = record.lineno

        # Add function name
        log_record['function'] = record.funcName

        # Add process and thread information
        log_record['process'] = record.process
        log_record['thread'] = record.thread

        # Add correlation ID if available
        if hasattr(record, 'correlation_id'):
            log_record['correlation_id'] = record.correlation_id

        # Add user ID if available
        if hasattr(record, 'user_id'):
            log_record['user_id'] = record.user_id

        # Add session ID if available
        if hasattr(record, 'session_id'):
            log_record['session_id'] = record.session_id

def setup_logging(
    log_level: str = "INFO",
    log_file: str = "app.log",
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5
) -> None:
    """
    Set up logging configuration.

    Args:
        log_level: The logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to the log file
        max_bytes: Maximum size of each log file before rotation
        backup_count: Number of backup files to keep
    """
    # Create formatter
    formatter = CustomJsonFormatter(
        '%(timestamp)s %(level)s %(name)s %(message)s'
    )

    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)

    # Create file handler with rotation
    file_handler = RotatingFileHandler(
        log_file,
        maxBytes=max_bytes,
        backupCount=backup_count
    )
    file_handler.setFormatter(formatter)

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Configure third-party loggers
    logging.getLogger("uvicorn").setLevel(log_level)
    logging.getLogger("fastapi").setLevel(log_level)
    logging.getLogger("sqlalchemy.engine").setLevel(log_level)

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance with the given name.

    Args:
        name: The name of the logger

    Returns:
        A configured logger instance
    """
    return logging.getLogger(name)

class LogContext:
    """Context manager for adding context to logs."""

    def __init__(
        self,
        logger: logging.Logger,
        correlation_id: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None
    ):
        self.logger = logger
        self.correlation_id = correlation_id or str(uuid.uuid4())
        self.user_id = user_id
        self.session_id = session_id
        self.old_correlation_id = None
        self.old_user_id = None
        self.old_session_id = None

    def __enter__(self):
        # Store old values
        self.old_correlation_id = getattr(self.logger, 'correlation_id', None)
        self.old_user_id = getattr(self.logger, 'user_id', None)
        self.old_session_id = getattr(self.logger, 'session_id', None)

        # Set new values
        setattr(self.logger, 'correlation_id', self.correlation_id)
        if self.user_id:
            setattr(self.logger, 'user_id', self.user_id)
        if self.session_id:
            setattr(self.logger, 'session_id', self.session_id)

        return self.logger

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Restore old values
        if self.old_correlation_id is not None:
            setattr(self.logger, 'correlation_id', self.old_correlation_id)
        elif hasattr(self.logger, 'correlation_id'):
            delattr(self.logger, 'correlation_id')

        if self.old_user_id is not None:
            setattr(self.logger, 'user_id', self.old_user_id)
        elif hasattr(self.logger, 'user_id'):
            delattr(self.logger, 'user_id')

        if self.old_session_id is not None:
            setattr(self.logger, 'session_id', self.old_session_id)
        elif hasattr(self.logger, 'session_id'):
            delattr(self.logger, 'session_id')
