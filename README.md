# iSpy C2 Server

<p align="center">
  <img src="https://img.shields.io/badge/Python-3.9+-blue.svg" alt="Python">
  <img src="https://img.shields.io/badge/Flask-2.3-green.svg" alt="Flask">
  <img src="https://img.shields.io/badge/License-Educational-red.svg" alt="License">
</p>

A modular Command & Control (C2) server built with Flask and Socket.IO for educational purposes in mobile security research.

---

## ⚠️ Disclaimer

**This project is for EDUCATIONAL and AUTHORIZED SECURITY RESEARCH purposes only.**

- ❌ Do NOT use on devices without explicit permission
- ❌ Do NOT use for unauthorized surveillance
- ❌ Do NOT use for any illegal activities

The author assumes NO responsibility for misuse. Use only on devices you own or have written authorization to test.

---

## Features

- 🔐 **JWT Authentication** - Secure token-based device authentication
- 🌐 **WebSocket Communication** - Real-time bidirectional messaging via Socket.IO
- 🛡️ **Rate Limiting** - Protection against brute force attacks
- 📊 **Admin Dashboard** - Flask-Admin panel for device management
- 🔍 **Input Validation** - Sanitization and validation middleware
- 📝 **Security Logging** - Comprehensive event logging
- 🧩 **Modular Architecture** - Clean, maintainable code structure

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                         C2 Server                           │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Auth      │  │   Routes    │  │ Middleware  │         │
│  │  - JWT      │  │  - API      │  │ - Rate Limit│         │
│  │  - Decorators│ │  - WebSocket│  │ - Validator │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐         │
│  │   Models    │  │   Utils     │  │   Config    │         │
│  │  - Device   │  │  - Logger   │  │  - .env     │         │
│  │  - Log      │  │             │  │             │         │
│  └─────────────┘  └─────────────┘  └─────────────┘         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## Project Structure

```
ispy-c2-server/
├── app/
│   ├── __init__.py          # Application factory
│   ├── config.py            # Configuration management
│   ├── auth/
│   │   ├── __init__.py
│   │   ├── jwt_manager.py   # JWT token operations
│   │   └── decorators.py    # Auth decorators
│   ├── models/
│   │   ├── __init__.py
│   │   ├── device.py        # Device model
│   │   └── log.py           # Log model
│   ├── routes/
│   │   ├── __init__.py
│   │   ├── api.py           # REST API endpoints
│   │   ├── admin.py         # Admin panel views
│   │   └── websocket.py     # Socket.IO handlers
│   ├── middleware/
│   │   ├── __init__.py
│   │   ├── rate_limiter.py  # Rate limiting
│   │   └── validator.py     # Input validation
│   ├── utils/
│   │   ├── __init__.py
│   │   └── logger.py        # Logging utilities
│   └── templates/
│       └── admin/
│           └── device_details.html
├── .env.example             # Environment template
├── .gitignore
├── requirements.txt
├── run.py                   # Entry point
├── LICENSE
└── README.md
```

---

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/yourusername/ispy-c2-server.git
cd ispy-c2-server
```

### 2. Create virtual environment

```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment

```bash
cp .env.example .env
# Edit .env with your settings
```

### 5. Run the server

```bash
python run.py
```

---

## Configuration

Create a `.env` file based on `.env.example`:

```env
# Flask
SECRET_KEY=your-secret-key-here
FLASK_ENV=development

# JWT
JWT_SECRET=your-jwt-secret-here
JWT_EXPIRY_HOURS=24

# Device Authentication
DEVICE_SECRET=your-device-secret-here

# Admin Panel
ADMIN_USERNAME=admin
ADMIN_PASSWORD=your-admin-password

# Server
HOST=0.0.0.0
PORT=3000
```

---

## API Endpoints

### Authentication

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/api/auth` | Get JWT token |

**Request:**
```json
{
    "device_id": "device-uuid",
    "secret": "device-secret"
}
```

**Response:**
```json
{
    "token": "eyJhbGciOiJIUzI1NiIs...",
    "device_id": "device-uuid",
    "expires_in": 86400
}
```

### Devices

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/devices` | List connected devices |
| GET | `/api/device/<id>` | Get device details |
| POST | `/api/device/<id>/command` | Send command to device |
| GET | `/api/device/<id>/logs` | Get device logs |

*All device endpoints require JWT authentication via `Authorization: Bearer <token>` header.*

### Health Check

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/health` | Server health status |

---

## WebSocket Events

### Client → Server

| Event | Description |
|-------|-------------|
| `authenticate` | JWT authentication |
| `identify` | Device identification |

### Server → Client

| Event | Description |
|-------|-------------|
| `auth_success` | Authentication successful |
| `auth_error` | Authentication failed |
| `execute_command` | Command to execute |
| `server_message` | Server notification |

---

## Security Features

### JWT Authentication
- Token-based authentication for API and WebSocket
- Configurable expiry time
- Automatic token refresh support

### Rate Limiting
- 5 requests/minute for authentication
- 60 requests/minute for general API
- IP-based tracking

### Input Validation
- Device ID format validation
- Command whitelist
- Data sanitization

### Logging
- Security events logged to file
- Authentication attempts tracked
- Command execution audited

---

## Admin Panel

Access the admin panel at `http://localhost:3000/admin`

Features:
- Device management
- Log viewing
- Real-time device status
- Plugin controls

---

## Tech Stack

- **Backend:** Python 3.9+, Flask
- **WebSocket:** Flask-SocketIO, Socket.IO
- **Database:** SQLite, SQLAlchemy
- **Admin:** Flask-Admin
- **Auth:** PyJWT
- **Security:** Flask-Limiter

---

## Learning Objectives

This project demonstrates:

- 🔐 JWT authentication implementation
- 🌐 WebSocket real-time communication
- 🏗️ Modular Flask application architecture
- 🛡️ Security best practices (rate limiting, input validation)
- 📊 Admin dashboard development
- 🔄 Client-server communication patterns

---

## License

This project is licensed for **educational purposes only**. See [LICENSE](LICENSE) for details.

---

## Author

**sideffect**

- GitHub: [@sideffect](https://github.com/sideffect)

---

## Acknowledgments

- Built for cybersecurity learning and research
- Inspired by mobile security concepts
- Part of iOS security research journey

---

<p align="center">
  <b>⚠️ Remember: Always obtain proper authorization before security testing ⚠️</b>
</p>
