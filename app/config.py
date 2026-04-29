"""
Configuration management
Loads settings from environment variables
"""

import os
import secrets
from dotenv import load_dotenv

load_dotenv()


def _require_env(key: str, default: str = None) -> str:
    """Return env var value; in production raise if missing."""
    value = os.getenv(key, default)
    if value is None:
        raise EnvironmentError(f"Required environment variable '{key}' is not set.")
    return value


class Config:
    """Base configuration"""

    # Flask
    SECRET_KEY = os.getenv('SECRET_KEY', secrets.token_hex(32))
    FLASK_ENV = os.getenv('FLASK_ENV', 'development')
    DEBUG = os.getenv('FLASK_DEBUG', 'false').lower() == 'true'

    # Database
    SQLALCHEMY_DATABASE_URI = os.getenv('DATABASE_URI', 'sqlite:///c2.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False

    # JWT
    JWT_SECRET = os.getenv('JWT_SECRET', secrets.token_hex(32))
    JWT_ALGORITHM = 'HS256'
    JWT_EXPIRY_HOURS = int(os.getenv('JWT_EXPIRY_HOURS', 24))

    # Device Auth
    DEVICE_SECRET = os.getenv('DEVICE_SECRET', secrets.token_hex(32))

    # Admin — must be overridden via env vars in any real deployment
    ADMIN_USERNAME = os.getenv('ADMIN_USERNAME', 'admin')
    ADMIN_PASSWORD = os.getenv('ADMIN_PASSWORD', 'admin')

    # Server
    HOST = os.getenv('HOST', '127.0.0.1')
    PORT = int(os.getenv('PORT', 3000))

    # Rate Limiting
    RATE_LIMIT_PER_MINUTE = int(os.getenv('RATE_LIMIT_PER_MINUTE', 60))
    AUTH_RATE_LIMIT_PER_MINUTE = int(os.getenv('AUTH_RATE_LIMIT_PER_MINUTE', 5))

    # Security
    # None → same-origin only for WebSocket CORS (browsers); iOS device connections unaffected
    ALLOWED_ORIGINS = os.getenv('ALLOWED_ORIGINS') or None
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    FLASK_ENV = 'development'


class ProductionConfig(Config):
    """Production configuration — all secrets must be set via environment variables"""
    DEBUG = False
    FLASK_ENV = 'production'

    SECRET_KEY = _require_env('SECRET_KEY')
    JWT_SECRET = _require_env('JWT_SECRET')
    DEVICE_SECRET = _require_env('DEVICE_SECRET')
    ADMIN_USERNAME = _require_env('ADMIN_USERNAME')
    ADMIN_PASSWORD = _require_env('ADMIN_PASSWORD')


def get_config():
    """Get config based on environment"""
    env = os.getenv('FLASK_ENV', 'development')

    if env == 'production':
        return ProductionConfig()
    return DevelopmentConfig()
