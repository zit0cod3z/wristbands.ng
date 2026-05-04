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

# ── Media file serving ────────────────────────────────────────────────────
# In development: Django serves media directly
# In production on Render: Django also serves media (no Nginx)
# In production on cPanel with Nginx: Nginx serves /media/ directly from disk
# The re_path below ensures media always works regardless of DEBUG setting
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
else:
    # Serve media files even in production (needed for Render)
    # On cPanel with Nginx, Nginx will intercept /media/ before Django sees it
    urlpatterns += [
        re_path(
            r'^media/(?P<path>.*)$',
            serve,
            {'document_root': settings.MEDIA_ROOT, 'show_indexes': False},
        ),
    ]
