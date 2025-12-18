#!/usr/bin/env python3
"""
iSpy C2 Server
Entry point
"""

from app import create_app, socketio
from app.config import get_config

config = get_config()
app = create_app()


def print_banner():
    """Print startup banner"""
    print("\n" + "=" * 55)
    print("  ██╗███████╗██████╗ ██╗   ██╗     ██████╗██████╗ ")
    print("  ██║██╔════╝██╔══██╗╚██╗ ██╔╝    ██╔════╝╚════██╗")
    print("  ██║███████╗██████╔╝ ╚████╔╝     ██║      █████╔╝")
    print("  ██║╚════██║██╔═══╝   ╚██╔╝      ██║     ██╔═══╝ ")
    print("  ██║███████║██║        ██║       ╚██████╗███████╗")
    print("  ╚═╝╚══════╝╚═╝        ╚═╝        ╚═════╝╚══════╝")
    print("=" * 55)
    print(f"  Admin Panel  : http://localhost:{config.PORT}/admin")
    print(f"  API Endpoint : http://localhost:{config.PORT}/api")
    print(f"  WebSocket    : ws://localhost:{config.PORT}")
    print(f"  Health Check : http://localhost:{config.PORT}/api/health")
    print("=" * 55)
    print(f"  Environment  : {config.FLASK_ENV}")
    print(f"  JWT Expiry   : {config.JWT_EXPIRY_HOURS} hours")
    print(f"  Rate Limit   : {config.RATE_LIMIT_PER_MINUTE}/min")
    print("=" * 55)
    print(f"  Admin: {config.ADMIN_USERNAME} / {config.ADMIN_PASSWORD}")
    print("=" * 55 + "\n")


if __name__ == '__main__':
    print_banner()
    
    socketio.run(
        app,
        host=config.HOST,
        port=config.PORT,
        debug=config.DEBUG,
        allow_unsafe_werkzeug=True
    )
