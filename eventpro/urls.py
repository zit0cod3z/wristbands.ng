from django.contrib import admin
from django.urls import path, include, re_path
from django.conf import settings
from django.conf.urls.static import static
from django.views.static import serve
from checkin.views import service_worker, pwa_manifest

urlpatterns = [
    path('django-admin/', admin.site.urls),
    path('', include('events.urls')),
    path('accounts/', include('accounts.urls')),
    path('dashboard/', include('events.dashboard_urls')),
    path('registrations/', include('registrations.urls')),
    path('checkin/', include('checkin.urls')),
    # PWA files must be served from root
    path('sw.js', service_worker, name='service_worker'),
    path('manifest.json', pwa_manifest, name='pwa_manifest'),
]

if settings.DEBUG:
    # Development: Django serves both static and media directly
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # Production (Render / any host without Nginx in front of Django):
    # Serve static files from STATIC_ROOT (populated by collectstatic)
    # Serve media files from MEDIA_ROOT
    # On cPanel with Nginx, Nginx intercepts these paths before Django sees them
    urlpatterns += [
        re_path(
            r'^static/(?P<path>.*)$',
            serve,
            {'document_root': settings.STATIC_ROOT, 'show_indexes': False},
        ),
        re_path(
            r'^media/(?P<path>.*)$',
            serve,
            {'document_root': settings.MEDIA_ROOT, 'show_indexes': False},
        ),
    ]
