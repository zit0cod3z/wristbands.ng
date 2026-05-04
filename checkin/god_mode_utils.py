"""
Utility helpers for God Mode compatibility.
God Mode user is not a real DB User — any ForeignKey to User must use None.
"""


def safe_user(request_user):
    """
    Returns the real Django User for FK fields, or None for God Mode.
    Usage: scanned_by=safe_user(request.user)
    """
    if getattr(request_user, 'pk', None) == -999:
        return None
    return request_user
