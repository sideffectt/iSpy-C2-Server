"""
Rate Limiting Middleware
Prevents brute force attacks
"""

from typing import Optional
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.utils import logger

limiter: Optional[Limiter] = None


def init_limiter(app):
    """Initialize rate limiter with Flask app"""
    
    global limiter
    
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["60 per minute"],
        storage_uri="memory://"  # Use Redis URI (e.g. redis://localhost:6379) in production
    )
    
    # Custom error handler
    @app.errorhandler(429)
    def ratelimit_handler(e):
        logger.warning(f"[RATELIMIT] Too many requests from {get_remote_address()}")
        return {
            'error': 'Rate limit exceeded',
            'message': 'Too many requests. Please try again later.'
        }, 429
    
    return limiter


def get_limiter() -> Optional[Limiter]:
    """Get the limiter instance"""
    return limiter
