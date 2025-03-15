from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth import login, logout, authenticate
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth.models import User
from django.db.models import Avg, Count
from django.http import HttpResponse, JsonResponse
from dashboard.models import TransportationData
from .models import Settings, TrafficRecord
import csv
from datetime import datetime, timedelta
from django.core import serializers
import json
from django.db import connection
import os
from django.conf import settings
from django.apps import apps
import psutil
import platform
from django.core.mail import send_mail
from django.utils import timezone
from django.core.cache import cache
import django
from stations.models import Station, Route, StationTraffic
from travel_cost.models import FareCalculator, FareHistory
from django.views.decorators.http import require_http_methods

def is_admin(user):
    return user.is_superuser or user.is_staff

def admin_login(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        password = request.POST.get('password')
        user = authenticate(request, username=username, password=password)
        if user is not None and (user.is_superuser or user.is_staff):
            login(request, user)
            return redirect('admin_panel:home')
        messages.error(request, 'Invalid credentials or insufficient permissions.')
    return render(request, 'admin_panel/login.html')

@login_required
def admin_logout(request):
    logout(request)
    return redirect('home:home')

@login_required
@user_passes_test(is_admin)
def home(request):
    # Get system information
    db_size = os.path.getsize(settings.DATABASES['default']['NAME']) / (1024 * 1024)  # Size in MB
    last_backup = get_last_backup_time()
    active_apps = len([app for app in apps.get_app_configs() if app.name.startswith('optimizing_transport.')])
    system_version = platform.version()

    # Get recent activities (you might want to implement a proper activity log system)
    recent_activities = [
        {
            'title': 'System Update',
            'description': 'Admin panel updated to version 1.0',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
        },
        {
            'title': 'Data Import',
            'description': 'New transportation data imported',
            'timestamp': datetime.now().strftime('%Y-%m-%d %H:%M')
        }
    ]

    context = {
        'total_users': User.objects.count(),
        'active_routes': TransportationData.objects.count(),
        'total_stations': TransportationData.objects.values('bus_station').distinct().count(),
        'reports_count': 0,
        'db_size': f"{db_size:.2f} MB",
        'last_backup': last_backup,
        'active_apps': active_apps,
        'system_version': system_version,
        'recent_activities': recent_activities
    }
    return render(request, 'admin_panel/admin_panel.html', context)

@login_required
@user_passes_test(is_admin)
def data_management(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'truncate':
            try:
                TransportationData.objects.all().delete()
                messages.success(request, "All transportation data has been deleted successfully.")
                return redirect('admin_panel:data_management')
            except Exception as e:
                messages.error(request, f"Error deleting data: {str(e)}")
        elif action == 'delete':
            record_id = request.POST.get('record_id')
            try:
                TransportationData.objects.filter(id=record_id).delete()
                messages.success(request, "Record deleted successfully.")
                return redirect('admin_panel:data_management')
            except Exception as e:
                messages.error(request, f"Error deleting record: {str(e)}")

    # Get all transportation data
    tables = [
        {
            'name': 'transportation_data',
            'model': TransportationData,
            'fields': [
                'id', 'road_name', 'route_name', 'bus_station', 
                'brt_station', 'road_distance', 'peak_hours', 
                'average_speed', 'travel_time', 'fare', 
                'landmark_nearby', 'road_type', 'traffic_lights_count'
            ]
        }
    ]

    for table in tables:
        table['sample_data'] = table['model'].objects.all()

    return render(request, 'admin_panel/data_management.html', {'tables': tables})

@login_required
@user_passes_test(is_admin)
def delete_record(request, record_id):
    if request.method == 'POST':
        try:
            TransportationData.objects.filter(id=record_id).delete()
            messages.success(request, "Record deleted successfully")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
    return redirect('admin_panel:data_management')

@login_required
@user_passes_test(is_admin)
def truncate_table(request):
    if request.method == 'POST':
        try:
            TransportationData.objects.all().delete()
            messages.success(request, "Table truncated successfully")
        except Exception as e:
            messages.error(request, f"Error: {str(e)}")
    return redirect('admin_panel:data_management')

@login_required
@user_passes_test(is_admin)
def user_management(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        user_id = request.POST.get('user_id')
        
        if action == 'delete':
            User.objects.filter(id=user_id).delete()
            messages.success(request, 'User deleted successfully')
        elif action == 'toggle_active':
            user = User.objects.get(id=user_id)
            user.is_active = not user.is_active
            user.save()
            messages.success(request, f'User {"activated" if user.is_active else "deactivated"} successfully')
        elif action == 'toggle_admin':
            user = User.objects.get(id=user_id)
            user.is_superuser = not user.is_superuser
            user.save()
            messages.success(request, f'Admin status {"granted" if user.is_superuser else "revoked"} successfully')

    users = User.objects.all().order_by('-date_joined')
    return render(request, 'admin_panel/user_management.html', {'users': users})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def add_user(request):
    if request.method == 'POST':
        username = request.POST.get('username')
        email = request.POST.get('email')
        password = request.POST.get('password')
        is_superuser = request.POST.get('is_superuser') == 'on'
        
        try:
            user = User.objects.create_user(username, email, password)
            user.is_superuser = is_superuser
            user.save()
            messages.success(request, 'User created successfully')
            return redirect('admin_panel:user_management')
        except Exception as e:
            messages.error(request, f'Error creating user: {str(e)}')
    
    return render(request, 'admin_panel/add_user.html')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def edit_user(request, user_id):
    user = get_object_or_404(User, id=user_id)
    if request.method == 'POST':
        user.username = request.POST.get('username')
        user.email = request.POST.get('email')
        user.is_superuser = request.POST.get('is_superuser') == 'on'
        user.is_active = request.POST.get('is_active') == 'on'
        
        if request.POST.get('password'):
            user.set_password(request.POST.get('password'))
        
        try:
            user.save()
            messages.success(request, 'User updated successfully')
            return redirect('admin_panel:user_management')
        except Exception as e:
            messages.error(request, f'Error updating user: {str(e)}')
    
    return render(request, 'admin_panel/edit_user.html', {'edit_user': user})

@login_required
@user_passes_test(lambda u: u.is_superuser)
def delete_user(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        user.delete()
        messages.success(request, 'User deleted successfully.')
    return redirect('admin_panel:user_management')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def toggle_user_active(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        user.is_active = not user.is_active
        user.save()
        messages.success(request, f'User {"activated" if user.is_active else "deactivated"} successfully')
    return redirect('admin_panel:user_management')

@login_required
@user_passes_test(lambda u: u.is_superuser)
def toggle_user_admin(request, user_id):
    if request.method == 'POST':
        user = get_object_or_404(User, id=user_id)
        user.is_superuser = not user.is_superuser
        user.save()
        messages.success(request, f'Admin status {"granted" if user.is_superuser else "revoked"} successfully')
    return redirect('admin_panel:user_management')

def get_last_backup_time():
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    if os.path.exists(backup_dir):
        backups = [f for f in os.listdir(backup_dir) if f.endswith('.json')]
        if backups:
            latest_backup = max(backups, key=lambda x: os.path.getctime(os.path.join(backup_dir, x)))
            return datetime.fromtimestamp(os.path.getctime(os.path.join(backup_dir, latest_backup))).strftime('%Y-%m-%d %H:%M')
    return 'Never'

@login_required
@user_passes_test(is_admin)
def backup_data(request):
    backup_dir = os.path.join(settings.BASE_DIR, 'backups')
    current_path = request.GET.get('path', '')
    full_path = os.path.join(backup_dir, current_path.lstrip('/'))

    if not os.path.exists(backup_dir):
        os.makedirs(backup_dir)

    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'create_backup':
            try:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                backup_file = f'backup_{timestamp}.json'
                os.makedirs(full_path, exist_ok=True)
                backup_path = os.path.join(full_path, backup_file)
                
                data = serialize_data()
                with open(backup_path, 'w') as f:
                    json.dump(data, f, indent=4)
                
                messages.success(request, 'Backup created successfully')
            except Exception as e:
                messages.error(request, f'Error creating backup: {str(e)}')

        elif action == 'create_folder':
            folder_name = request.POST.get('folder_name')
            if folder_name:
                try:
                    new_folder_path = os.path.join(full_path, folder_name)
                    os.makedirs(new_folder_path)
                    messages.success(request, 'Folder created successfully')
                except Exception as e:
                    messages.error(request, f'Error creating folder: {str(e)}')

        elif action == 'delete_folder':
            folder_path = request.POST.get('folder_path')
            full_folder_path = os.path.join(backup_dir, folder_path.lstrip('/'))
            try:
                import shutil
                shutil.rmtree(full_folder_path)
                messages.success(request, 'Folder deleted successfully')
            except Exception as e:
                messages.error(request, f'Error deleting folder: {str(e)}')

        elif action == 'delete_backup':
            file_path = request.POST.get('file_path')
            full_file_path = os.path.join(backup_dir, file_path.lstrip('/'))
            try:
                os.remove(full_file_path)
                messages.success(request, 'Backup deleted successfully')
            except Exception as e:
                messages.error(request, f'Error deleting backup: {str(e)}')

    items = []
    try:
        for item in os.listdir(full_path):
            item_path = os.path.join(full_path, item)
            item_stat = os.stat(item_path)
            items.append({
                'name': item,
                'full_path': os.path.join(current_path, item).lstrip('/'),
                'is_dir': os.path.isdir(item_path),
                'type': 'Folder' if os.path.isdir(item_path) else 'File',
                'modified': datetime.fromtimestamp(item_stat.st_mtime),
                'size': item_stat.st_size
            })
    except Exception as e:
        messages.error(request, f'Error listing directory: {str(e)}')

    current_path_parts = []
    if current_path:
        parts = current_path.split('/')
        current = ''
        for part in parts:
            current = os.path.join(current, part)
            current_path_parts.append({
                'name': part,
                'path': current
            })

    return render(request, 'admin_panel/backup_data.html', {
        'items': items,
        'current_path': current_path,
        'current_path_parts': current_path_parts,
        'parent_path': os.path.dirname(current_path)
    })

@login_required
@user_passes_test(is_admin)
def create_backup(request):
    if request.method == 'POST':
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            backup_file = f'backup_{timestamp}.json'
            backup_dir = os.path.join(settings.BASE_DIR, 'backups')
            os.makedirs(backup_dir, exist_ok=True)
            backup_path = os.path.join(backup_dir, backup_file)
            
            data = serialize_data()
            with open(backup_path, 'w') as f:
                json.dump(data, f, indent=4)
            
            messages.success(request, 'Backup created successfully')
        except Exception as e:
            messages.error(request, f'Error creating backup: {str(e)}')
    return redirect('admin_panel:backup_data')

@login_required
@user_passes_test(is_admin)
def restore_backup(request, backup_file):
    if request.method == 'POST':
        try:
            backup_path = os.path.join(settings.BASE_DIR, 'backups', backup_file)
            with open(backup_path, 'r') as f:
                data = json.load(f)
            
            # Clear existing data
            TransportationData.objects.all().delete()
            
            # Restore data
            for row in data['transportation_data']['data']:
                TransportationData.objects.create(
                    road_name=row[0],
                    route_name=row[1],
                    bus_station=row[2],
                    brt_station=row[3],
                    road_distance=row[4],
                    peak_hours=row[5],
                    average_speed=row[6],
                    travel_time=row[7],
                    fare=row[8],
                    landmark_nearby=row[9],
                    road_type=row[10],
                    traffic_lights_count=row[11]
                )
            
            messages.success(request, 'Backup restored successfully')
        except Exception as e:
            messages.error(request, f'Error restoring backup: {str(e)}')
    return redirect('admin_panel:backup_data')

@login_required
@user_passes_test(is_admin)
def delete_backup(request, backup_file):
    if request.method == 'POST':
        try:
            backup_path = os.path.join(settings.BASE_DIR, 'backups', backup_file)
            os.remove(backup_path)
            messages.success(request, 'Backup deleted successfully')
        except Exception as e:
            messages.error(request, f'Error deleting backup: {str(e)}')
    return redirect('admin_panel:backup_data')

@login_required
@user_passes_test(is_admin)
def import_data(request):
    if request.method == 'POST':
        file = request.FILES.get('file')
        if file:
            try:
                if file.name.endswith('.csv'):
                    import_csv(file)
                elif file.name.endswith('.json'):
                    import_json(file)
                messages.success(request, 'Data imported successfully')
            except Exception as e:
                messages.error(request, f'Error importing data: {str(e)}')
    
    return render(request, 'admin_panel/import_data.html')

@login_required
@user_passes_test(is_admin)
def export_data(request):
    response = HttpResponse(content_type='application/json')
    response['Content-Disposition'] = 'attachment; filename="transportation_data.json"'
    
    data = serialize_data()
    json.dump(data, response, indent=4)
    
    return response

@login_required
@user_passes_test(lambda u: u.is_superuser)
def system_settings(request):
    # Get system information
    system_info = {
        'django_version': django.get_version(),
        'python_version': platform.python_version(),
        'db_size': get_database_size(),
        'last_backup': get_last_backup_time(),
        'active_users': User.objects.filter(is_active=True).count(),
    }

    # Get current settings from database
    current_settings = {}
    for setting in Settings.objects.all():
        current_settings[setting.key] = setting.value

    # Set default values if not in database
    defaults = {
        'THEME_MODE': 'light',
        'PRIMARY_COLOR': '#007bff',
        'BACKUP_FREQUENCY': 'daily',
        'BACKUP_RETENTION': '7',
        'SESSION_TIMEOUT': '120',
        'MAX_LOGIN_ATTEMPTS': '5',
        'REQUIRE_2FA': 'false',
        'SMTP_HOST': '',
        'SMTP_PORT': '587',
        'SMTP_USERNAME': '',
        'SMTP_PASSWORD': '',
        'SMTP_USE_TLS': 'true',
        'NOTIFY_BACKUP': 'true',
        'NOTIFY_ERROR': 'true',
        'NOTIFY_LOGIN': 'true',
    }

    # Update current_settings with defaults for missing values
    for key, value in defaults.items():
        if key not in current_settings:
            current_settings[key] = value
            Settings.objects.create(key=key, value=value)

    context = {
        'settings': current_settings,
        **system_info
    }
    
    return render(request, 'admin_panel/system_settings.html', context)

@login_required
@user_passes_test(lambda u: u.is_superuser)
def update_settings(request):
    if request.method == 'POST':
        section = request.POST.get('section')
        success = True
        message = 'Settings updated successfully'
        
        try:
            if section == 'appearance':
                update_setting('THEME_MODE', request.POST.get('theme_mode', 'light'))
                update_setting('PRIMARY_COLOR', request.POST.get('primary_color', '#007bff'))
                
            elif section == 'backup':
                update_setting('BACKUP_FREQUENCY', request.POST.get('backup_frequency', 'daily'))
                update_setting('BACKUP_RETENTION', request.POST.get('backup_retention', '7'))
                
            elif section == 'security':
                update_setting('SESSION_TIMEOUT', request.POST.get('session_timeout', '120'))
                update_setting('MAX_LOGIN_ATTEMPTS', request.POST.get('max_login_attempts', '5'))
                update_setting('REQUIRE_2FA', str(request.POST.get('require_2fa') == 'on').lower())
                
            elif section == 'email':
                update_setting('SMTP_HOST', request.POST.get('smtp_host', ''))
                update_setting('SMTP_PORT', request.POST.get('smtp_port', '587'))
                update_setting('SMTP_USERNAME', request.POST.get('smtp_username', ''))
                if request.POST.get('smtp_password'):
                    update_setting('SMTP_PASSWORD', request.POST.get('smtp_password'))
                update_setting('SMTP_USE_TLS', str(request.POST.get('use_tls') == 'on').lower())
                
            elif section == 'notifications':
                update_setting('NOTIFY_BACKUP', str(request.POST.get('notify_backup') == 'on').lower())
                update_setting('NOTIFY_ERROR', str(request.POST.get('notify_error') == 'on').lower())
                update_setting('NOTIFY_LOGIN', str(request.POST.get('notify_login') == 'on').lower())
            
            # Update cache
            refresh_settings_cache()
            
        except Exception as e:
            success = False
            message = f'Error updating settings: {str(e)}'
        
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({'success': success, 'message': message})
        else:
            if success:
                messages.success(request, message)
            else:
                messages.error(request, message)
            return redirect('admin_panel:system_settings')
            
    return redirect('admin_panel:system_settings')

def update_setting(key, value):
    """Update or create a setting in the database"""
    setting, created = Settings.objects.update_or_create(
        key=key,
        defaults={'value': value}
    )
    return setting

def refresh_settings_cache():
    """Refresh the settings cache with current database values"""
    settings_dict = {setting.key: setting.value for setting in Settings.objects.all()}
    cache.set('admin_settings', settings_dict, timeout=None)
    return settings_dict

def get_database_size():
    """Get the size of the database in MB"""
    try:
        db_path = settings.DATABASES['default']['NAME']
        size_bytes = os.path.getsize(db_path)
        return f"{size_bytes / (1024 * 1024):.2f} MB"
    except:
        return "Unknown"

def get_last_backup_time():
    """Get the time of the last backup"""
    try:
        backup_dir = os.path.join(settings.BASE_DIR, 'backups')
        if not os.path.exists(backup_dir):
            return "No backups"
        
        backups = [f for f in os.listdir(backup_dir) if f.startswith('backup_')]
        if not backups:
            return "No backups"
            
        latest_backup = max(backups, key=lambda x: os.path.getctime(os.path.join(backup_dir, x)))
        backup_time = datetime.fromtimestamp(os.path.getctime(os.path.join(backup_dir, latest_backup)))
        return backup_time.strftime('%Y-%m-%d %H:%M:%S')
    except:
        return "Unknown"

def get_active_users_count():
    """Get the count of active users in the last 24 hours"""
    try:
        last_24h = timezone.now() - timedelta(hours=24)
        return User.objects.filter(last_login__gte=last_24h).count()
    except:
        return "Unknown"

@login_required
@user_passes_test(is_admin)
def app_management(request):
    """
    View function for the app management page.
    Displays overview and settings for all installed apps.
    """
    context = {
        'apps': [
            {
                'name': 'Dashboard',
                'icon': 'chart-line',
                'description': 'Visualize transportation data and analytics',
                'status': 'active',
                'url_name': 'dashboard:index'
            },
            {
                'name': 'Stations',
                'icon': 'subway',
                'description': 'Manage bus and BRT stations across the network',
                'status': 'active',
                'url_name': 'stations:index'
            },
            {
                'name': 'Explorer',
                'icon': 'search',
                'description': 'Advanced data exploration and analysis tools',
                'status': 'active',
                'url_name': 'explorer:index'
            }
        ]
    }
    return render(request, 'admin_panel/app_management.html', context)

@login_required
@user_passes_test(is_admin)
def app_detail(request, app_name):
    app_config = apps.get_app_config(app_name)
    models = []
    for model in app_config.get_models():
        models.append({
            'name': model._meta.verbose_name,
            'object_count': model.objects.count(),
            'fields': [field.name for field in model._meta.fields]
        })
    
    return render(request, 'admin_panel/app_detail.html', {
        'app': app_config,
        'models': models
    })

@login_required
@user_passes_test(is_admin)
def toggle_app(request, app_name):
    if request.method == 'POST':
        # Implement app enabling/disabling logic
        messages.success(request, f'App {app_name} toggled successfully')
    return redirect('admin_panel:app_management')

def import_csv(file):
    decoded_file = file.read().decode('utf-8')
    csv_data = csv.DictReader(decoded_file.splitlines())
    
    for row in csv_data:
        TransportationData.objects.create(
            road_name=row['road_name'],
            route_name=row['route_name'],
            bus_station=row['bus_station'],
            brt_station=row['brt_station'],
            road_distance=float(row['road_distance']),
            peak_hours=row['peak_hours'],
            average_speed=float(row['average_speed']),
            travel_time=float(row['travel_time']),
            fare=float(row['fare']),
            landmark_nearby=row['landmark_nearby'],
            road_type=row['road_type'],
            traffic_lights_count=int(row['traffic_lights_count'])
        )

def import_json(file):
    data = json.load(file)
    for row in data['transportation_data']['data']:
        TransportationData.objects.create(
            road_name=row[0],
            route_name=row[1],
            bus_station=row[2],
            brt_station=row[3],
            road_distance=float(row[4]),
            peak_hours=row[5],
            average_speed=float(row[6]),
            travel_time=float(row[7]),
            fare=float(row[8]),
            landmark_nearby=row[9],
            road_type=row[10],
            traffic_lights_count=int(row[11])
        )

def serialize_data():
    data = {
        'transportation_data': {
            'columns': [
                'road_name', 'route_name', 'bus_station', 'brt_station',
                'road_distance', 'peak_hours', 'average_speed', 'travel_time',
                'fare', 'landmark_nearby', 'road_type', 'traffic_lights_count'
            ],
            'data': []
        }
    }
    
    records = TransportationData.objects.all()
    for record in records:
        row = [
            record.road_name,
            record.route_name,
            record.bus_station,
            record.brt_station,
            record.road_distance,
            record.peak_hours,
            record.average_speed,
            record.travel_time,
            record.fare,
            record.landmark_nearby,
            record.road_type,
            record.traffic_lights_count
        ]
        data['transportation_data']['data'].append(row)
    
    return data

@login_required
@user_passes_test(is_admin)
def data_types(request):
    """
    View function for the data types selection page.
    Shows different types of data that can be managed.
    """
    context = {
        'transport_count': TransportationData.objects.count(),
        'stations_count': Station.objects.count(),
        'routes_count': Route.objects.count(),
        'traffic_count': StationTraffic.objects.count(),
        'users_count': User.objects.count(),
        'settings_count': Settings.objects.count(),
    }
    return render(request, 'admin_panel/data_types.html', context)

@login_required
@user_passes_test(is_admin)
def stations_management(request):
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'delete':
            station_id = request.POST.get('station_id')
            try:
                station = Station.objects.get(id=station_id)
                station.delete()
                messages.success(request, 'Station deleted successfully.')
            except Station.DoesNotExist:
                messages.error(request, 'Station not found.')
        
        elif action == 'add':
            try:
                Station.objects.create(
                    name=request.POST.get('name'),
                    station_type=request.POST.get('station_type'),
                    location=request.POST.get('location'),
                    capacity=request.POST.get('capacity'),
                    is_operational=request.POST.get('is_operational') == 'on',
                    opening_time=request.POST.get('opening_time'),
                    closing_time=request.POST.get('closing_time')
                )
                messages.success(request, 'Station added successfully.')
            except Exception as e:
                messages.error(request, f'Error adding station: {str(e)}')
        
        elif action == 'edit':
            station_id = request.POST.get('station_id')
            try:
                station = Station.objects.get(id=station_id)
                station.name = request.POST.get('name')
                station.station_type = request.POST.get('station_type')
                station.location = request.POST.get('location')
                station.capacity = request.POST.get('capacity')
                station.is_operational = request.POST.get('is_operational') == 'on'
                station.opening_time = request.POST.get('opening_time')
                station.closing_time = request.POST.get('closing_time')
                station.save()
                messages.success(request, 'Station updated successfully.')
            except Station.DoesNotExist:
                messages.error(request, 'Station not found.')
            except Exception as e:
                messages.error(request, f'Error updating station: {str(e)}')
        
        return redirect('admin_panel:stations_management')
    
    stations = Station.objects.all()
    return render(request, 'admin_panel/stations_management.html', {'stations': stations})

@login_required
def get_station_details(request, station_id):
    try:
        station = Station.objects.get(id=station_id)
        data = {
            'name': station.name,
            'station_type': station.station_type,
            'location': station.location,
            'capacity': station.capacity,
            'is_operational': station.is_operational,
            'opening_time': station.opening_time.strftime('%H:%M'),
            'closing_time': station.closing_time.strftime('%H:%M')
        }
        return JsonResponse(data)
    except Station.DoesNotExist:
        return JsonResponse({'error': 'Station not found'}, status=404)

@login_required
@user_passes_test(is_admin)
def routes_management(request):
    """
    View function for managing routes data.
    """
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete':
            route_id = request.POST.get('route_id')
            try:
                Route.objects.filter(id=route_id).delete()
                messages.success(request, "Route deleted successfully.")
                return redirect('admin_panel:routes_management')
            except Exception as e:
                messages.error(request, f"Error deleting route: {str(e)}")

    # Get all routes data with related stations
    routes = Route.objects.all().prefetch_related('stations')
    context = {
        'routes': routes,
    }
    return render(request, 'admin_panel/routes_management.html', context)

@login_required
@user_passes_test(is_admin)
def traffic_management(request):
    """
    View function for managing traffic data.
    """
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'delete':
            record_id = request.POST.get('record_id')
            try:
                StationTraffic.objects.filter(id=record_id).delete()
                messages.success(request, "Traffic record deleted successfully.")
                return redirect('admin_panel:traffic_management')
            except Exception as e:
                messages.error(request, f"Error deleting traffic record: {str(e)}")
        elif action == 'add':
            try:
                StationTraffic.objects.create(
                    location=request.POST.get('location'),
                    date=request.POST.get('date'),
                    time=request.POST.get('time'),
                    traffic_level=request.POST.get('traffic_level'),
                    peak_hours=request.POST.get('peak_hours'),
                    is_active=request.POST.get('is_active') == 'on'
                )
                messages.success(request, "Traffic record added successfully.")
                return redirect('admin_panel:traffic_management')
            except Exception as e:
                messages.error(request, f"Error adding traffic record: {str(e)}")

    # Get all traffic records
    traffic_records = StationTraffic.objects.all()
    context = {
        'traffic_records': traffic_records,
    }
    return render(request, 'admin_panel/traffic_management.html', context)

@login_required
@user_passes_test(is_admin)
def update_record(request):
    if request.method == 'POST':
        try:
            record_id = request.POST.get('record_id')
            record = TransportationData.objects.get(id=record_id)
            
            # Update record fields
            record.road_name = request.POST.get('road_name')
            record.route_name = request.POST.get('route_name')
            record.bus_station = request.POST.get('bus_station')
            record.brt_station = request.POST.get('brt_station')
            record.road_distance = float(request.POST.get('road_distance'))
            record.fare = float(request.POST.get('fare'))
            
            record.save()
            return JsonResponse({'success': True})
        except TransportationData.DoesNotExist:
            return JsonResponse({'success': False, 'error': 'Record not found'}, status=404)
        except Exception as e:
            return JsonResponse({'success': False, 'error': str(e)}, status=500)
    
    return JsonResponse({'success': False, 'error': 'Invalid request method'}, status=405)

@login_required
def custom_admin(request):
    """Custom admin interface view"""
    # Get dashboard statistics
    active_routes_count = Route.objects.filter(is_active=True).count()
    traffic_records_count = TrafficRecord.objects.count()
    fare_calculators_count = FareCalculator.objects.count()

    # Get data for each section
    settings = Settings.objects.all().order_by('-updated_at')
    traffic_records = TrafficRecord.objects.all().order_by('-timestamp')
    fare_calculators = FareCalculator.objects.all().order_by('-updated_at')
    fare_history = FareHistory.objects.all().order_by('-calculated_at')[:100]  # Last 100 records
    routes = Route.objects.filter(is_active=True).order_by('name')

    context = {
        'active_routes_count': active_routes_count,
        'traffic_records_count': traffic_records_count,
        'fare_calculators_count': fare_calculators_count,
        'settings': settings,
        'traffic_records': traffic_records,
        'fare_calculators': fare_calculators,
        'fare_history': fare_history,
        'routes': routes,
    }
    return render(request, 'admin_panel/django_admin.html', context)

@require_http_methods(["POST"])
def api_settings(request):
    """API endpoint for managing settings"""
    try:
        key = request.POST.get('key')
        value = request.POST.get('value')
        
        if not key or not value:
            return JsonResponse({'success': False, 'error': 'Key and value are required'})
        
        setting, created = Settings.objects.update_or_create(
            key=key,
            defaults={'value': value}
        )
        
        return JsonResponse({'success': True})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_http_methods(["DELETE"])
def api_settings_delete(request, setting_id):
    """API endpoint for deleting settings"""
    try:
        setting = Settings.objects.get(id=setting_id)
        setting.delete()
        return JsonResponse({'success': True})
    except Settings.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Setting not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_http_methods(["POST"])
def api_traffic(request):
    """API endpoint for managing traffic records"""
    try:
        route_id = request.POST.get('route')
        traffic_level = request.POST.get('traffic_level')
        description = request.POST.get('description')
        
        if not route_id or not traffic_level:
            return JsonResponse({'success': False, 'error': 'Route and traffic level are required'})
        
        route = Route.objects.get(id=route_id)
        TrafficRecord.objects.create(
            route=route,
            traffic_level=traffic_level,
            description=description
        )
        
        return JsonResponse({'success': True})
    except Route.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Route not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_http_methods(["DELETE"])
def api_traffic_delete(request, record_id):
    """API endpoint for deleting traffic records"""
    try:
        record = TrafficRecord.objects.get(id=record_id)
        record.delete()
        return JsonResponse({'success': True})
    except TrafficRecord.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Traffic record not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_http_methods(["POST"])
def api_calculators(request):
    """API endpoint for managing fare calculators"""
    try:
        name = request.POST.get('name')
        base_fare = float(request.POST.get('base_fare', 0))
        distance_rate = float(request.POST.get('distance_rate', 0))
        peak_hour_surcharge = float(request.POST.get('peak_hour_surcharge', 0))
        traffic_light_surcharge = float(request.POST.get('traffic_light_surcharge', 0))
        distance_discount_threshold = float(request.POST.get('distance_discount_threshold', 0))
        distance_discount_rate = float(request.POST.get('distance_discount_rate', 0))
        is_active = request.POST.get('is_active') == 'on'
        
        if not name or base_fare <= 0 or distance_rate <= 0:
            return JsonResponse({'success': False, 'error': 'Required fields are missing or invalid'})
        
        FareCalculator.objects.create(
            name=name,
            base_fare=base_fare,
            distance_rate=distance_rate,
            peak_hour_surcharge=peak_hour_surcharge,
            traffic_light_surcharge=traffic_light_surcharge,
            distance_discount_threshold=distance_discount_threshold,
            distance_discount_rate=distance_discount_rate,
            is_active=is_active
        )
        
        return JsonResponse({'success': True})
    except ValueError:
        return JsonResponse({'success': False, 'error': 'Invalid numeric values'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})

@require_http_methods(["DELETE"])
def api_calculators_delete(request, calculator_id):
    """API endpoint for deleting fare calculators"""
    try:
        calculator = FareCalculator.objects.get(id=calculator_id)
        calculator.delete()
        return JsonResponse({'success': True})
    except FareCalculator.DoesNotExist:
        return JsonResponse({'success': False, 'error': 'Calculator not found'})
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)})