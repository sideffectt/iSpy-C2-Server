from .device import create_device_model
from .log import create_log_model


def init_models(db):
    """Initialize all models and return them"""
    
    Device = create_device_model(db)
    Log = create_log_model(db)
    
    return {
        'Device': Device,
        'Log': Log
    }
