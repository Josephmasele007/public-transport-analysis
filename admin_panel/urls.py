from django.urls import path
from . import views

app_name = 'admin_panel'

urlpatterns = [
    # Authentication
    path('login/', views.admin_login, name='login'),
    path('logout/', views.admin_logout, name='logout'),
    
    # Dashboard
    path('', views.home, name='home'),
    
    # Data Management
    path('data/', views.data_types, name='data_types'),
    path('data/transportation/', views.data_management, name='data_management'),
    path('data/transportation/update/', views.update_record, name='update_record'),
    path('data/stations/', views.stations_management, name='stations_management'),
    path('data/stations/<int:station_id>/', views.get_station_details, name='get_station_details'),
    path('data/routes/', views.routes_management, name='routes_management'),
    path('data/traffic/', views.traffic_management, name='traffic_management'),
    path('data/transportation/delete/<int:record_id>/', views.delete_record, name='delete_record'),
    path('data/transportation/truncate/', views.truncate_table, name='truncate_table'),
    
    # User Management
    path('users/', views.user_management, name='user_management'),
    path('users/add/', views.add_user, name='add_user'),
    path('users/edit/<int:user_id>/', views.edit_user, name='edit_user'),
    path('users/delete/<int:user_id>/', views.delete_user, name='delete_user'),
    path('users/toggle-active/<int:user_id>/', views.toggle_user_active, name='toggle_user_active'),
    path('users/toggle-admin/<int:user_id>/', views.toggle_user_admin, name='toggle_user_admin'),
    
    # Backup & Restore
    path('backup/', views.backup_data, name='backup_data'),
    path('backup/create/', views.create_backup, name='create_backup'),
    path('backup/restore/<str:backup_file>/', views.restore_backup, name='restore_backup'),
    path('backup/delete/<str:backup_file>/', views.delete_backup, name='delete_backup'),
    
    # Import/Export
    path('import/', views.import_data, name='import_data'),
    path('export/', views.export_data, name='export_data'),
    
    # System Settings
    path('settings/', views.system_settings, name='system_settings'),
    path('settings/update/', views.update_settings, name='update_settings'),
    
    # App Management
    path('apps/', views.app_management, name='app_management'),
    path('apps/<str:app_name>/', views.app_detail, name='app_detail'),
    path('apps/<str:app_name>/toggle/', views.toggle_app, name='toggle_app'),
    
    # Custom admin interface
    path('custom-admin/', views.custom_admin, name='custom_admin'),
    
    # API endpoints
    path('api/settings/', views.api_settings, name='api_settings'),
    path('api/settings/<int:setting_id>/', views.api_settings_delete, name='api_settings_delete'),
    path('api/traffic/', views.api_traffic, name='api_traffic'),
    path('api/traffic/<int:record_id>/', views.api_traffic_delete, name='api_traffic_delete'),
    path('api/calculators/', views.api_calculators, name='api_calculators'),
    path('api/calculators/<int:calculator_id>/', views.api_calculators_delete, name='api_calculators_delete'),
]
