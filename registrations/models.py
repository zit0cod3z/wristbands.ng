import uuid
from django.db import models
from events.models import Event


class Registration(models.Model):
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
        ('attended', 'Attended'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    registration_code = models.CharField(max_length=20, unique=True, editable=False)
    name = models.CharField(max_length=255)
    email = models.EmailField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')
    qr_code = models.ImageField(upload_to='qrcodes/', blank=True, null=True)
    registered_at = models.DateTimeField(auto_now_add=True)
    email_sent = models.BooleanField(default=False)
    checked_in = models.BooleanField(default=False)
    checked_in_at = models.DateTimeField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    # External QR ID — stores the ID from an external ticketing/registration system.
    # When this is set, scanning the external QR code will check in this guest
    # without needing a WristbandsNG QR code.
    # The external QR payload is stored here and matched during scanning.
    external_qr_id = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        db_index=True,
        help_text='External QR code ID from another system (Eventbrite, Google Forms, etc.)'
    )

    class Meta:
        ordering = ['-registered_at']
        unique_together = ['event', 'email']

    def __str__(self):
        return f'{self.name} - {self.event.title}'

    def save(self, *args, **kwargs):
        if not self.registration_code:
            if self.external_qr_id:
                # External import: registration_code = EXT-<the_actual_qr_id>
                # This makes it human-readable and directly matches the imported ID.
                # Uniqueness is guaranteed because external_qr_id is unique per event.
                clean_id = str(self.external_qr_id).strip()[:50]
                self.registration_code = f'EXT-{clean_id}'
                # If somehow a collision exists (same ID across events), append short suffix
                if Registration.objects.filter(registration_code=self.registration_code).exists():
                    import uuid as _uuid
                    suffix = str(_uuid.uuid4()).replace('-', '')[:4].upper()
                    self.registration_code = f'EXT-{clean_id}-{suffix}'
            else:
                self.registration_code = self._generate_code()
        super().save(*args, **kwargs)

    def _generate_code(self):
        import random, string
        prefix = self.event.title[:3].upper() if self.event else 'EVT'
        suffix = ''.join(random.choices(string.ascii_uppercase + string.digits, k=7))
        return f'{prefix}-{suffix}'


class RegistrationData(models.Model):
    registration = models.ForeignKey(Registration, on_delete=models.CASCADE, related_name='field_data')
    field_key = models.CharField(max_length=100)
    field_label = models.CharField(max_length=255)
    value = models.TextField(blank=True)

    class Meta:
        ordering = ['field_key']

    def __str__(self):
        return f'{self.registration.registration_code} - {self.field_label}'
