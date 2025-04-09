"""
Logging configuration for the experimentation platform.

This module configures structured JSON logging with proper rotation and context.
"""

import json
import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pythonjsonlogger import jsonlogger
from typing import Dict, Any, Optional, Union
import uuid
from datetime import datetime
import watchtower
import boto3
from pythonjsonlogger.jsonlogger import JsonFormatter
import socket

class CustomJsonFormatter(JsonFormatter):
    """Custom JSON formatter that adds additional fields to log records."""

    def __init__(self):
        """Initialize the formatter with default format and style."""
        fmt = '%(asctime)s %(name)s %(levelname)s %(message)s'
        self._fmt = fmt  # Explicitly set _fmt before the super call
        self._style = logging.PercentStyle(fmt)  # Initialize style before super().__init__()
        super().__init__(
            fmt=fmt,
            style='%',  # Use % style formatting
            datefmt=None,
            json_default=str,
            json_encoder=None,
            reserved_attrs=[]
        )

    def add_fields(self, log_record, record, message_dict):
        """Add custom fields to the log record."""
        super().add_fields(log_record, record, message_dict)

        # Add standard fields
        log_record['logger'] = record.name
        log_record['level'] = record.levelname

        # Add context fields if they exist
        for field in ['correlation_id', 'user_id', 'session_id']:
            if hasattr(record, field):
                log_record[field] = getattr(record, field)

def setup_logging(
    level: int = logging.INFO,
    format: Optional[str] = None,
    log_file: Optional[str] = None,
    max_bytes: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    enable_cloudwatch: bool = False
) -> logging.Logger:
    """Set up logging configuration."""
    logger = logging.getLogger()
    logger.setLevel(level)

    # Remove existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create and configure handler
    if log_file:
        handler = RotatingFileHandler(log_file, maxBytes=max_bytes, backupCount=backup_count)
    else:
        handler = logging.StreamHandler()

    handler.setLevel(level)

    # Use standard formatter for tests, JSON formatter for production
    if format:
        formatter = logging.Formatter(format)
    else:
        # Use CustomJsonFormatter by default
        formatter = CustomJsonFormatter()

    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Add CloudWatch handler if enabled
    if enable_cloudwatch:
        try:
            # Check if AWS credentials are available
            if not os.getenv('AWS_ACCESS_KEY_ID'):
                logger.warning("AWS credentials not found, CloudWatch logging disabled")
                return logger

            aws_client = boto3.client('logs')
            app_env = os.getenv('APP_ENV', 'dev')
            log_group = f"/experimentation-platform/{app_env}"
            stream_name = f"{socket.gethostname()}-{datetime.now().strftime('%Y-%m-%d-%H-%M-%S')}"

            cloudwatch_handler = watchtower.CloudWatchLogHandler(
                log_group=log_group,
                stream_name=stream_name,
                boto3_client=aws_client,
                batch_count=100,
                batch_timeout=5,
                create_log_group=True
            )
            cloudwatch_handler.setLevel(level)  # Set the same level as root logger
            cloudwatch_handler.setFormatter(formatter)
            logger.addHandler(cloudwatch_handler)

            # This log message should trigger an emit call
            logger.info("CloudWatch logging enabled")
        except Exception as e:
            logger.warning(f"Failed to initialize CloudWatch logging: {e}")

    return logger

# Configure root logger
logger = setup_logging()

def get_logger(name: str) -> logging.Logger:
    """
    Get a logger with the specified name.

    Args:
        name: The name of the logger.

    Returns:
        A logger instance.
    """
    try:
        return logging.getLogger(name)
    except Exception:
        # If there's an error getting the logger, create a new one
        logger = logging.Logger(name)
        logger.setLevel(logging.INFO)
        return logger

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

        return self

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

    def info(self, msg: str, *args, **kwargs):
        """Log an info message with context."""
        extra = kwargs.get('extra', {})
        extra.update({
            'correlation_id': self.correlation_id,
            'user_id': self.user_id,
            'session_id': self.session_id
        })
        kwargs['extra'] = extra
        self.logger.info(msg, *args, **kwargs)

    def error(self, msg: str, *args, **kwargs):
        """Log an error message with context."""
        extra = kwargs.get('extra', {})
        extra.update({
            'correlation_id': self.correlation_id,
            'user_id': self.user_id,
            'session_id': self.session_id
        })
        kwargs['extra'] = extra
        self.logger.error(msg, *args, **kwargs)

    def warning(self, msg: str, *args, **kwargs):
        """Log a warning message with context."""
        extra = kwargs.get('extra', {})
        extra.update({
            'correlation_id': self.correlation_id,
            'user_id': self.user_id,
            'session_id': self.session_id
        })
        kwargs['extra'] = extra
        self.logger.warning(msg, *args, **kwargs)

    def debug(self, msg: str, *args, **kwargs):
        """Log a debug message with context."""
        extra = kwargs.get('extra', {})
        extra.update({
            'correlation_id': self.correlation_id,
            'user_id': self.user_id,
            'session_id': self.session_id
        })
        kwargs['extra'] = extra
        self.logger.debug(msg, *args, **kwargs)
