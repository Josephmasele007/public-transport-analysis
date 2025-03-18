from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path('admin/', admin.site.urls),
    path('explorer/', include('explorer.urls')),
    path('', include('core.urls')),
] 