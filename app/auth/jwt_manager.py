"""
JWT Token Management
Handles token generation and verification
"""

import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict
from app.config import get_config
from app.utils import logger, log_auth_attempt

config = get_config()


def generate_token(device_id: str) -> str:
    """
    Generate a new JWT token for a device
    
    Args:
        device_id: Unique device identifier
        
    Returns:
        JWT token string
    """
    
    payload = {
        'device_id': device_id,
        'iat': datetime.utcnow(),
        'exp': datetime.utcnow() + timedelta(hours=config.JWT_EXPIRY_HOURS)
    }
    
    token = jwt.encode(
        payload,
        config.JWT_SECRET,
        algorithm=config.JWT_ALGORITHM
    )
    
    logger.info(f"[JWT] Token generated for device: {device_id}")
    return token


def verify_token(token: str) -> Optional[Dict]:
    """
    Verify and decode a JWT token
    
    Args:
        token: JWT token string
        
    Returns:
        Decoded payload dict if valid, None otherwise
    """
    
    try:
        payload = jwt.decode(
            token,
            config.JWT_SECRET,
            algorithms=[config.JWT_ALGORITHM]
        )
        return payload
        
    except jwt.ExpiredSignatureError:
        logger.warning("[JWT] Token expired")
        return None
        
    except jwt.InvalidTokenError as e:
        logger.warning(f"[JWT] Invalid token: {e}")
        return None


def get_token_expiry() -> int:
    """Get token expiry time in seconds"""
    return config.JWT_EXPIRY_HOURS * 3600


def refresh_token(old_token: str) -> Optional[str]:
    """
    Refresh an existing token (if still valid)
    
    Args:
        old_token: Current JWT token
        
    Returns:
        New JWT token if old one is valid, None otherwise
    """
    
    payload = verify_token(old_token)
    
    if payload:
        device_id = payload.get('device_id')
        return generate_token(device_id)
    
    return None
