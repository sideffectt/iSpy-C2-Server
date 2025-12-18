"""
Logging utility
Structured logging for security events
"""

import logging
import os
from datetime import datetime
from functools import wraps


def setup_logger(name: str = 'c2_server') -> logging.Logger:
    """Setup and return a configured logger"""
    
    logger = logging.getLogger(name)
    
    if logger.handlers:
        return logger
    
    log_level = os.getenv('LOG_LEVEL', 'INFO')
    logger.setLevel(getattr(logging, log_level))
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_format = logging.Formatter(
        '[%(asctime)s] %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(console_format)
    logger.addHandler(console_handler)
    
    # File handler (security events)
    os.makedirs('logs', exist_ok=True)
    file_handler = logging.FileHandler('logs/security.log')
    file_format = logging.Formatter(
        '%(asctime)s | %(levelname)s | %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    file_handler.setFormatter(file_format)
    file_handler.setLevel(logging.WARNING)
    logger.addHandler(file_handler)
    
    return logger


# Global logger instance
logger = setup_logger()


def log_security_event(event_type: str, details: dict):
    """Log a security-related event"""
    
    message = f"[SECURITY] {event_type} | {details}"
    logger.warning(message)


def log_auth_attempt(success: bool, device_id: str, ip: str, reason: str = None):
    """Log authentication attempt"""
    
    status = "SUCCESS" if success else "FAILED"
    details = {
        'device_id': device_id,
        'ip': ip,
        'status': status,
        'reason': reason
    }
    log_security_event('AUTH_ATTEMPT', details)


def log_connection(event: str, session_id: str, ip: str, device_id: str = None):
    """Log connection event"""
    
    details = {
        'event': event,
        'session_id': session_id,
        'ip': ip,
        'device_id': device_id
    }
    logger.info(f"[CONNECTION] {event} | {details}")


def log_command(command: str, device_id: str, source: str):
    """Log command execution"""
    
    details = {
        'command': command,
        'device_id': device_id,
        'source': source
    }
    logger.info(f"[COMMAND] {command} | {details}")
