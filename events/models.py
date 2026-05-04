import uuid
from django.db import models
from django.contrib.auth.models import User


class Event(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('closed', 'Closed'),
        ('cancelled', 'Cancelled'),
    ]
    EVENT_TYPE_CHOICES = [
        ('concert', 'Concert'),
        ('conference', 'Conference'),
        ('meetup', 'Meetup / Get Together'),
        ('workshop', 'Workshop'),
        ('seminar', 'Seminar'),
        ('party', 'Party'),
        ('sports', 'Sports'),
        ('other', 'Other'),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    title = models.CharField(max_length=255)
    slug = models.SlugField(unique=True, max_length=300)
    description = models.TextField()
    event_type = models.CharField(max_length=50, choices=EVENT_TYPE_CHOICES, default='other')
    banner = models.ImageField(upload_to='event_banners/', blank=True, null=True)
    venue = models.CharField(max_length=500)
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    capacity = models.PositiveIntegerField(default=0, help_text='0 = unlimited')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, related_name='events_created')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    registration_deadline = models.DateTimeField(null=True, blank=True)
    is_featured = models.BooleanField(default=False)
    color_theme = models.CharField(max_length=7, default='#ac2376', help_text='Hex color for event page')

    # ── Access control flags ──────────────────────────────────────────────
    # These only block NEW actions. All existing data (registrations,
    # QR codes, check-in records) is NEVER touched or deleted.
    registration_open = models.BooleanField(
        default=True,
        help_text='When OFF, the public registration form is closed. '
                  'All existing registrations and QR codes remain intact.'
    )
    checkin_open = models.BooleanField(
        default=True,
        help_text='When OFF, the QR scanner will reject new check-ins. '
                  'All previously checked-in records remain intact.'
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return self.title

    @property
    def registration_count(self):
        return self.registrations.filter(status='confirmed').count()

    @property
    def is_full(self):
        if self.capacity == 0:
            return False
        return self.registration_count >= self.capacity

    @property
    def spots_left(self):
        if self.capacity == 0:
            return None
        return max(0, self.capacity - self.registration_count)

    @property
    def can_register(self):
        """True only if the event is published, registration is open, and not full."""
        return (
            self.status == 'published'
            and self.registration_open
            and not self.is_full
        )

    @property
    def can_checkin(self):
        """True only if check-in is open."""
        return self.checkin_open


class FormField(models.Model):
    FIELD_TYPES = [
        ('text', 'Text Input'),
        ('email', 'Email'),
        ('tel', 'Phone Number'),
        ('number', 'Number'),
        ('textarea', 'Text Area'),
        ('select', 'Dropdown Select'),
        ('radio', 'Radio Buttons'),
        ('checkbox', 'Checkbox'),
        ('date', 'Date'),
        ('file', 'File Upload'),
    ]

    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='form_fields')
    label = models.CharField(max_length=255)
    field_type = models.CharField(max_length=20, choices=FIELD_TYPES)
    placeholder = models.CharField(max_length=255, blank=True)
    help_text = models.CharField(max_length=500, blank=True)
    is_required = models.BooleanField(default=True)
    options = models.TextField(blank=True, help_text='Comma-separated options for select/radio/checkbox')
    order = models.PositiveIntegerField(default=0)
    field_key = models.SlugField(max_length=100)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f'{self.event.title} - {self.label}'

    def get_options_list(self):
        if self.options:
            return [o.strip() for o in self.options.split(',') if o.strip()]
        return []
