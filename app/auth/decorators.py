"""
Authentication Decorators
Use these to protect routes and socket events
"""

from functools import wraps
from flask import request, jsonify
from app.auth.jwt_manager import verify_token
from app.utils import logger


def require_jwt(f):
    """
    Decorator for HTTP routes requiring JWT authentication
    
    Usage:
        @app.route('/api/protected')
        @require_jwt
        def protected_route():
            device_id = request.jwt_payload['device_id']
            return jsonify({'message': 'Hello ' + device_id})
    """
    
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization')
        
        # Check header exists
        if not auth_header:
            logger.warning(f"[AUTH] Missing auth header from {request.remote_addr}")
            return jsonify({'error': 'Missing Authorization header'}), 401
        
        # Check format
        if not auth_header.startswith('Bearer '):
            logger.warning(f"[AUTH] Invalid auth format from {request.remote_addr}")
            return jsonify({'error': 'Invalid Authorization format. Use: Bearer <token>'}), 401
        
        # Extract and verify token
        token = auth_header.split(' ')[1]
        payload = verify_token(token)
        
        if not payload:
            logger.warning(f"[AUTH] Invalid token from {request.remote_addr}")
            return jsonify({'error': 'Invalid or expired token'}), 401
        
        # Attach payload to request
        request.jwt_payload = payload
        
        return f(*args, **kwargs)
    
    return decorated


def require_admin(f):
    """
    Decorator for admin-only routes (Basic Auth)
    
    Usage:
        @app.route('/admin/action')
        @require_admin
        def admin_action():
            return jsonify({'message': 'Admin only'})
    """
    
    @wraps(f)
    def decorated(*args, **kwargs):
        from app.config import get_config
        import base64
        
        config = get_config()
        auth_header = request.headers.get('Authorization')
        
        if not auth_header or not auth_header.startswith('Basic '):
            return jsonify({'error': 'Admin authentication required'}), 401
        
        try:
            credentials = base64.b64decode(auth_header[6:]).decode('utf-8')
            username, password = credentials.split(':', 1)
            
            if username != config.ADMIN_USERNAME or password != config.ADMIN_PASSWORD:
                logger.warning(f"[ADMIN] Invalid credentials from {request.remote_addr}")
                return jsonify({'error': 'Invalid credentials'}), 401
                
        except Exception as e:
            logger.warning(f"[ADMIN] Auth error from {request.remote_addr}: {e}")
            return jsonify({'error': 'Invalid credentials'}), 401
        
        return f(*args, **kwargs)
    
    return decorated


# Socket authentication state
authenticated_sessions = set()


def socket_authenticated(session_id: str) -> bool:
    """Check if a socket session is authenticated"""
    return session_id in authenticated_sessions


def add_authenticated_session(session_id: str):
    """Mark a session as authenticated"""
    authenticated_sessions.add(session_id)


def remove_authenticated_session(session_id: str):
    """Remove a session from authenticated set"""
    authenticated_sessions.discard(session_id)


def require_socket_auth(f):
    """
    Decorator for socket events requiring authentication
    
    Usage:
        @socketio.on('some_event')
        @require_socket_auth
        def handle_event(data):
            pass
    """
    
    @wraps(f)
    def decorated(*args, **kwargs):
        from flask import request
        from flask_socketio import emit, disconnect
        
        session_id = request.sid
        
        if not socket_authenticated(session_id):
            logger.warning(f"[SOCKET] Unauthenticated request from {session_id}")
            emit('auth_error', {'error': 'Not authenticated'})
            return
        
        return f(*args, **kwargs)
    
    return decorated
