"""
Admin Panel Routes
Custom Flask-Admin views for devices and logs
"""

from flask_admin.contrib.sqla import ModelView


class DeviceModelView(ModelView):
    """Custom view for Device model"""
    
    column_list = ['id', 'device_name', 'ip_address', 'last_seen', 'is_active', 'model', 'system_version']
    column_sortable_list = ['id', 'device_name', 'ip_address', 'last_seen']
    column_searchable_list = ['device_name', 'ip_address']
    column_filters = ['device_name', 'ip_address', 'last_seen', 'is_active']
    column_default_sort = ('last_seen', True)
    
    can_create = False
    can_edit = True
    can_delete = True
    can_view_details = True
    
    details_template = 'admin/device_details.html'
    
    column_labels = {
        'device_name': 'Device',
        'ip_address': 'IP Address',
        'last_seen': 'Last Seen',
        'is_active': 'Active',
        'model': 'Model',
        'system_version': 'iOS Version'
    }
    
    column_formatters = {
        'is_active': lambda v, c, m, p: '● Active' if m.is_active else '○ Inactive'
    }


class LogModelView(ModelView):
    """Custom view for Log model"""
    
    column_list = ['id', 'device_id', 'plugin_name', 'data_preview', 'timestamp']
    column_sortable_list = ['id', 'plugin_name', 'timestamp']
    column_searchable_list = ['plugin_name', 'data']
    column_filters = ['plugin_name', 'timestamp']
    column_default_sort = ('timestamp', True)
    
    can_create = False
    can_edit = False
    can_delete = True
    can_view_details = True
    
    column_labels = {
        'plugin_name': 'Plugin',
        'data_preview': 'Data Preview',
        'timestamp': 'Time'
    }
    
    def _data_preview(view, context, model, name):
        if model.data:
            return model.data[:100] + '...' if len(model.data) > 100 else model.data
        return ''
    
    column_formatters = {
        'data_preview': _data_preview
    }
