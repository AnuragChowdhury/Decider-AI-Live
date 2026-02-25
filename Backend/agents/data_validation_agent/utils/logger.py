"""
Structured logging with PII masking and JSON formatting.
"""

import logging
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional
import re


class JSONFormatter(logging.Formatter):
    """Custom formatter that outputs logs as JSON."""
    
    def __init__(self, mask_pii: bool = True):
        super().__init__()
        self.mask_pii = mask_pii
    
    def format(self, record: logging.LogRecord) -> str:
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        
        # Add extra fields if present
        if hasattr(record, 'dataset_id'):
            log_data['dataset_id'] = record.dataset_id
        if hasattr(record, 'step'):
            log_data['step'] = record.step
        if hasattr(record, 'metrics'):
            log_data['metrics'] = record.metrics
        
        # Add exception info if present
        if record.exc_info:
            log_data['exception'] = self.formatException(record.exc_info)
        
        # Mask PII if enabled
        if self.mask_pii:
            log_data = self._mask_sensitive_data(log_data)
        
        return json.dumps(log_data)
    
    def _mask_sensitive_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Mask potentially sensitive data in log messages.
        
        This is a simple implementation that masks common PII patterns.
        In production, you might want more sophisticated detection.
        """
        if isinstance(data, dict):
            return {k: self._mask_sensitive_data(v) for k, v in data.items()}
        elif isinstance(data, list):
            return [self._mask_sensitive_data(item) for item in data]
        elif isinstance(data, str):
            # Mask email addresses
            data = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', 
                         '***@***.***', data)
            # Mask phone numbers (simple pattern)
            data = re.sub(r'\b\d{3}[-.]?\d{3}[-.]?\d{4}\b', '***-***-****', data)
            # Mask credit card numbers
            data = re.sub(r'\b\d{4}[-\s]?\d{4}[-\s]?\d{4}[-\s]?\d{4}\b', 
                         '****-****-****-****', data)
        return data


class TextFormatter(logging.Formatter):
    """Standard text formatter with colors for console output."""
    
    COLORS = {
        'DEBUG': '\033[36m',    # Cyan
        'INFO': '\033[32m',     # Green
        'WARNING': '\033[33m',  # Yellow
        'ERROR': '\033[31m',    # Red
        'CRITICAL': '\033[35m', # Magenta
        'RESET': '\033[0m'
    }
    
    def format(self, record: logging.LogRecord) -> str:
        # Add color to level name
        levelname = record.levelname
        if sys.stdout.isatty():  # Only add colors if outputting to terminal
            color = self.COLORS.get(levelname, self.COLORS['RESET'])
            record.levelname = f"{color}{levelname}{self.COLORS['RESET']}"
        
        # Format timestamp
        timestamp = datetime.utcnow().strftime('%Y-%m-%d %H:%M:%S')
        
        # Build message
        msg = f"[{timestamp}] {record.levelname}: {record.getMessage()}"
        
        # Add dataset_id if present
        if hasattr(record, 'dataset_id'):
            msg += f" [dataset_id={record.dataset_id}]"
        
        # Add step if present
        if hasattr(record, 'step'):
            msg += f" [step={record.step}]"
        
        return msg


def setup_logger(
    name: str = "data_validation_agent",
    level: str = "INFO",
    format_type: str = "json",
    mask_pii: bool = True
) -> logging.Logger:
    """
    Set up a logger with the specified configuration.
    
    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Output format ("json" or "text")
        mask_pii: Whether to mask PII in logs
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))
    
    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()
    
    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, level.upper()))
    
    # Set formatter based on format type
    if format_type.lower() == "json":
        formatter = JSONFormatter(mask_pii=mask_pii)
    else:
        formatter = TextFormatter()
    
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return logger


def get_logger(name: str = "data_validation_agent") -> logging.Logger:
    """
    Get an existing logger instance.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    return logging.getLogger(name)


class LoggerAdapter(logging.LoggerAdapter):
    """
    Logger adapter that adds context (dataset_id, step) to all log messages.
    """
    
    def process(self, msg: str, kwargs: Dict[str, Any]) -> tuple:
        """Add extra context to log records."""
        extra = kwargs.get('extra', {})
        extra.update(self.extra)
        kwargs['extra'] = extra
        return msg, kwargs


def get_context_logger(
    dataset_id: Optional[str] = None,
    step: Optional[str] = None,
    logger_name: str = "data_validation_agent"
) -> LoggerAdapter:
    """
    Get a logger with context (dataset_id, step) automatically added.
    
    Args:
        dataset_id: Dataset identifier
        step: Current pipeline step
        logger_name: Base logger name
        
    Returns:
        Logger adapter with context
    """
    logger = get_logger(logger_name)
    context = {}
    if dataset_id:
        context['dataset_id'] = dataset_id
    if step:
        context['step'] = step
    
    return LoggerAdapter(logger, context)
