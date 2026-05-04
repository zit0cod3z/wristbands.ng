from django.db import models
from django.contrib.auth.models import User
from events.models import Event


class AdminProfile(models.Model):
    ROLE_CHOICES = [
        ('superadmin', 'Super Admin'),
        ('admin', 'Admin'),
        ('moderator', 'Moderator'),
    ]

    # ── Role definitions ──────────────────────────────────────────────────
    # Super Admin : Full access to ALL events. Can create/manage admins.
    #               Can create/edit/delete events. Can export everything.
    # Admin       : Full access to ASSIGNED events only. Cannot create admins.
    #               Can create/edit events they are assigned to.
    # Moderator   : READ-ONLY access to ASSIGNED events. Cannot create anything.
    #               Cannot manage admins. Cannot create or edit events.
    #               Can only VIEW registrations, check-in data, and exports.

    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='admin_profile')
    role = models.CharField(max_length=20, choices=ROLE_CHOICES, default='admin')
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    phone = models.CharField(max_length=20, blank=True)
    bio = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    assigned_events = models.ManyToManyField(
        Event,
        blank=True,
        related_name='assigned_admins',
        help_text='Superadmins see all events automatically. '
                  'Assign specific events for admin/moderator roles.',
    )

    def __str__(self):
        return f'{self.user.get_full_name() or self.user.username} ({self.get_role_display()})'

    # ── Role checks ───────────────────────────────────────────────────────

    def is_superadmin(self):
        return (
            self.role == 'superadmin'
            or self.user.is_superuser
            or self.user.is_staff
        )

    def is_admin_role(self):
        return self.role == 'admin'

    def is_moderator(self):
        return self.role == 'moderator'

    # ── Event access ──────────────────────────────────────────────────────

    def can_access_event(self, event):
        if self.is_superadmin():
            return True
        return self.assigned_events.filter(pk=event.pk).exists()

    def get_accessible_events(self):
        from events.models import Event as Ev
        if self.is_superadmin():
            return Ev.objects.all()
        return self.assigned_events.all()

    # ── Action permissions ────────────────────────────────────────────────

    def can_create_events(self):
        """Superadmin and Admin can create events. Moderator cannot."""
        return self.role in ('superadmin', 'admin') or self.user.is_superuser or self.user.is_staff

    def can_edit_event(self, event):
        """Superadmin can edit any event. Admin can edit assigned events. Moderator cannot."""
        if self.is_moderator():
            return False
        return self.can_access_event(event)

    def can_delete_event(self, event):
        """Only superadmin can delete events."""
        return self.is_superadmin()

    def can_manage_registrations(self, event):
        """Superadmin and Admin can manage registrations. Moderator view-only."""
        if self.is_moderator():
            return False
        return self.can_access_event(event)

    def can_manage_admins(self):
        """Only superadmin can create/edit/delete other admins."""
        return self.is_superadmin()

    def can_export(self, event):
        """All roles can export data for events they can access."""
        return self.can_access_event(event)
