import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'eventpro.settings')

# Django setup must happen before any app imports
import django
django.setup()

from django.core.asgi import get_asgi_application
from django.conf import settings
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from whitenoise import WhiteNoise
from checkin.routing import websocket_urlpatterns

# Bare Django ASGI app (handles HTTP requests through Django middleware stack)
django_asgi_app = get_asgi_application()

# Wrap with WhiteNoise for static file serving under Daphne/ASGI.
# The MIDDLEWARE-based WhiteNoise only works with WSGI (gunicorn).
# Under Daphne, HTTP requests go through ProtocolTypeRouter → we must wrap
# the Django app here so WhiteNoise intercepts /static/ before Django sees it.
_whitenoise_app = WhiteNoise(
    django_asgi_app,
    root=str(settings.STATIC_ROOT),
    prefix=settings.STATIC_URL.strip('/'),
)

application = ProtocolTypeRouter({
    'http': _whitenoise_app,
    'websocket': AuthMiddlewareStack(
        URLRouter(websocket_urlpatterns)
    ),
})
