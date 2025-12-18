"""
Log Model
Stores plugin output and events from devices
"""

from datetime import datetime


def create_log_model(db):
    """Create Log model with given db instance"""
    
    class Log(db.Model):
        __tablename__ = 'logs'
        
        id = db.Column(db.Integer, primary_key=True)
        device_id = db.Column(db.Integer, db.ForeignKey('devices.id'), nullable=False)
        plugin_name = db.Column(db.String(100), nullable=False)
        data = db.Column(db.Text)
        timestamp = db.Column(db.DateTime, default=datetime.utcnow)
        
        # Additional metadata
        is_error = db.Column(db.Boolean, default=False)
        data_size = db.Column(db.Integer, default=0)
        
        def __repr__(self):
            return f'<Log {self.plugin_name} @ {self.timestamp}>'
        
        def to_dict(self):
            return {
                'id': self.id,
                'device_id': self.device_id,
                'plugin_name': self.plugin_name,
                'data': self.data,
                'timestamp': self.timestamp.isoformat() if self.timestamp else None,
                'is_error': self.is_error,
                'data_size': self.data_size
            }
    
    return Log
