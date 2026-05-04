from django.db import models
from django.contrib.auth.models import User
from registrations.models import Registration
from events.models import Event


class CheckInLog(models.Model):
    """Every scan attempt is logged — success or failure."""
    registration = models.ForeignKey(
        Registration, on_delete=models.CASCADE,
        related_name='checkin_logs', null=True, blank=True
    )
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='checkin_logs')
    scanned_code = models.CharField(max_length=500)          # raw QR payload
    scanned_by = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True
    )
    scanned_at = models.DateTimeField(auto_now_add=True)
    success = models.BooleanField(default=False)
    message = models.CharField(max_length=255, blank=True)   # e.g. "Already checked in"
    device_info = models.CharField(max_length=255, blank=True)

    class Meta:
        ordering = ['-scanned_at']

    def __str__(self):
        status = 'OK' if self.success else 'FAIL'
        return f'[{status}] {self.scanned_code[:30]} @ {self.scanned_at:%Y-%m-%d %H:%M}'
