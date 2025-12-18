"""
Device Model
Represents connected iOS devices
"""

from datetime import datetime


def create_device_model(db):
    """Create Device model with given db instance"""
    
    class Device(db.Model):
        __tablename__ = 'devices'
        
        id = db.Column(db.Integer, primary_key=True)
        device_name = db.Column(db.String(100), unique=True, nullable=False)
        ip_address = db.Column(db.String(50))
        last_seen = db.Column(db.DateTime, default=datetime.utcnow)
        first_seen = db.Column(db.DateTime, default=datetime.utcnow)
        is_active = db.Column(db.Boolean, default=True)
        
        # Device info
        model = db.Column(db.String(50))
        system_name = db.Column(db.String(50))
        system_version = db.Column(db.String(20))
        is_jailbroken = db.Column(db.Boolean, default=False)
        
        # Relationships
        logs = db.relationship('Log', backref='device', lazy='dynamic')
        
        def __repr__(self):
            return f'<Device {self.device_name}>'
        
        def to_dict(self):
            return {
                'id': self.id,
                'device_name': self.device_name,
                'ip_address': self.ip_address,
                'last_seen': self.last_seen.isoformat() if self.last_seen else None,
                'first_seen': self.first_seen.isoformat() if self.first_seen else None,
                'is_active': self.is_active,
                'model': self.model,
                'system_name': self.system_name,
                'system_version': self.system_version,
                'is_jailbroken': self.is_jailbroken
            }
        
        def update_last_seen(self):
            self.last_seen = datetime.utcnow()
        
        def update_info(self, info: dict):
            """Update device info from identify payload"""
            self.model = info.get('model', self.model)
            self.system_name = info.get('system_name', self.system_name)
            self.system_version = info.get('system_version', self.system_version)
            self.is_jailbroken = info.get('is_jailbroken', self.is_jailbroken)
            self.update_last_seen()
    
    return Device
