"""
API Routes
HTTP endpoints for device management
"""

from flask import Blueprint, request, jsonify
from app.auth import require_jwt, generate_token, get_token_expiry
from app.middleware import validate_auth_request, get_limiter
from app.utils import logger, log_auth_attempt
from app.config import get_config

api_bp = Blueprint('api', __name__, url_prefix='/api')
config = get_config()


@api_bp.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    from app import get_connected_devices
    from datetime import datetime
    
    return jsonify({
        'status': 'healthy',
        'connected_devices': len(get_connected_devices()),
        'timestamp': datetime.now().isoformat()
    })


@api_bp.route('/auth', methods=['POST'])
def authenticate():
    """
    Device authentication endpoint
    
    Request:
        {
            "device_id": "UUID",
            "secret": "device-secret"
        }
    
    Response:
        {
            "token": "jwt-token",
            "device_id": "UUID",
            "expires_in": 86400
        }
    """
    
    data = request.get_json()
    client_ip = request.remote_addr
    
    # Validate request
    is_valid, error = validate_auth_request(data)
    if not is_valid:
        log_auth_attempt(False, data.get('device_id', 'unknown'), client_ip, error)
        return jsonify({'error': error}), 400
    
    device_id = data.get('device_id')
    secret = data.get('secret')
    
    # Verify secret
    if secret != config.DEVICE_SECRET:
        log_auth_attempt(False, device_id, client_ip, 'Invalid secret')
        return jsonify({'error': 'Invalid secret'}), 401
    
    # Generate token
    token = generate_token(device_id)
    log_auth_attempt(True, device_id, client_ip)
    
    return jsonify({
        'token': token,
        'device_id': device_id,
        'expires_in': get_token_expiry()
    })


@api_bp.route('/devices', methods=['GET'])
@require_jwt
def list_devices():
    """List all connected devices"""
    from app import get_connected_devices
    
    devices = get_connected_devices()
    
    return jsonify({
        'devices': list(devices.values()),
        'count': len(devices)
    })


@api_bp.route('/device/<device_id>', methods=['GET'])
@require_jwt
def get_device(device_id):
    """Get device details"""
    from app import get_connected_devices, db, Device
    
    # Check if online
    connected = get_connected_devices()
    is_online = any(d.get('device_id') == device_id for d in connected.values())
    
    # Get from database
    device = db.session.query(Device).filter_by(device_name=device_id).first()
    
    if not device:
        return jsonify({'error': 'Device not found'}), 404
    
    device_data = device.to_dict()
    device_data['is_online'] = is_online
    
    return jsonify(device_data)


@api_bp.route('/device/<device_id>/command', methods=['POST'])
@require_jwt
def send_command(device_id):
    """Send command to device"""
    from app import send_command_to_device
    from app.middleware import validate_command
    from app.utils import log_command
    
    data = request.get_json()
    command = data.get('command')
    params = data.get('params', {})
    
    if not command:
        return jsonify({'error': 'Command is required'}), 400
    
    if not validate_command(command):
        return jsonify({'error': f'Invalid command: {command}'}), 400
    
    success = send_command_to_device(device_id, command, params)
    log_command(command, device_id, 'api')
    
    return jsonify({
        'success': success,
        'device_id': device_id,
        'command': command
    })


@api_bp.route('/device/<device_id>/logs', methods=['GET'])
@require_jwt
def get_device_logs(device_id):
    """Get device logs"""
    from app import db, Device, Log
    
    device = db.session.query(Device).filter_by(device_name=device_id).first()
    
    if not device:
        return jsonify({'error': 'Device not found'}), 404
    
    # Pagination
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 50, type=int)
    per_page = min(per_page, 100)  # Max 100
    
    logs = db.session.query(Log)\
        .filter_by(device_id=device.id)\
        .order_by(Log.timestamp.desc())\
        .paginate(page=page, per_page=per_page)
    
    return jsonify({
        'device_id': device_id,
        'logs': [log.to_dict() for log in logs.items],
        'page': page,
        'per_page': per_page,
        'total': logs.total,
        'pages': logs.pages
    })
