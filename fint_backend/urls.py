"""
URL configuration for fint_backend project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from .views import health_check

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/health', health_check, name='health_check'),
    path('api/auth/', include('apps.users.urls')),
    path('api/receipts/', include('apps.receipts.urls')),
    path('api/stats/', include('apps.receipts.stats_urls')),
    path('api/categories', include('apps.categories.urls')),
    path('api/users/', include('apps.users.profile_urls')),
]

# Serve uploaded files in development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
