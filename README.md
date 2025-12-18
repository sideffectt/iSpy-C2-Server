# iSpy C2 Server

A simple Command & Control server built with Flask and Socket.IO for learning mobile security.

---

## ⚠️ Disclaimer

**Educational purposes only.** Do not use on devices without permission.

---

## Features

- JWT Authentication
- WebSocket (Socket.IO)
- Rate Limiting
- Admin Dashboard
- Modular Structure

---

## Setup

```bash
# Clone
git clone https://github.com/sideffectt/ispy-c2-server.git
cd ispy-c2-server

# Install
pip install -r requirements.txt

# Configure
cp .env.example .env
# Edit .env with your settings

# Run
python run.py
```

---

## API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth` | POST | Get JWT token |
| `/api/devices` | GET | List devices |
| `/api/health` | GET | Health check |

---

## Structure

```
├── app/
│   ├── auth/        # JWT authentication
│   ├── models/      # Database models
│   ├── routes/      # API & WebSocket
│   ├── middleware/  # Rate limit, validation
│   └── utils/       # Logging
├── run.py
└── .env.example
```

---

## Tech

- Python 3.9+
- Flask
- Socket.IO
- SQLite
- JWT

---

## License

Educational use only. See [LICENSE](LICENSE).
