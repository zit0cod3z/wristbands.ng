from django.contrib import admin
from .models import Registration, RegistrationData


class RegistrationDataInline(admin.TabularInline):
    model = RegistrationData
    extra = 0
    readonly_fields = ['field_key', 'field_label', 'value']


@admin.register(Registration)
class RegistrationAdmin(admin.ModelAdmin):
    list_display = ['registration_code', 'name', 'email', 'event', 'status', 'registered_at', 'email_sent']
    list_filter = ['status', 'email_sent', 'checked_in', 'event']
    search_fields = ['name', 'email', 'registration_code']
    readonly_fields = ['id', 'registration_code', 'registered_at', 'qr_code']
    inlines = [RegistrationDataInline]
