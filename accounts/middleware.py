"""
God Mode Middleware
Intercepts Django's auth middleware to restore GodModeUser from session
without any database query.
"""
from django.contrib.auth.middleware import AuthenticationMiddleware
from django.contrib.auth import SESSION_KEY
from .god_mode import get_god_mode_user_from_session


class GodModeAuthMiddleware(AuthenticationMiddleware):
    """
    Extends Django's AuthenticationMiddleware.
    If the session contains user_id=-999, returns GodModeUser
    instead of querying the database.
    """

    def process_request(self, request):
        # Check for god mode session first
        god_user = get_god_mode_user_from_session(request)
        if god_user is not None:
            request.user = god_user
            return

        # Otherwise fall through to normal Django auth
        super().process_request(request)
