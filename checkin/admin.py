from django.contrib import admin
from .models import CheckInLog


@admin.register(CheckInLog)
class CheckInLogAdmin(admin.ModelAdmin):
    list_display  = ['scanned_at', 'event', 'registration', 'success', 'message', 'scanned_by']
    list_filter   = ['success', 'event']
    search_fields = ['scanned_code', 'message']
    readonly_fields = ['scanned_at']
