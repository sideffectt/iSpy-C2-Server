"""
Rate Limiting Middleware
Prevents brute force attacks
"""

from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from app.utils import logger

limiter = None


def init_limiter(app):
    """Initialize rate limiter with Flask app"""
    
    global limiter
    
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=["60 per minute"],
        storage_uri="memory://"
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


def get_limiter():
    """Get the limiter instance"""
    return limiter
