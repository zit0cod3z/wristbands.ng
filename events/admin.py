from django.contrib import admin
from .models import Event, FormField


class FormFieldInline(admin.TabularInline):
    model = FormField
    extra = 0
    fields = ['label', 'field_type', 'is_required', 'order']


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = ['title', 'event_type', 'status', 'start_date', 'registration_count', 'is_featured']
    list_filter = ['status', 'event_type', 'is_featured']
    search_fields = ['title', 'venue', 'city']
    prepopulated_fields = {'slug': ('title',)}
    inlines = [FormFieldInline]
    readonly_fields = ['created_at', 'updated_at']


@admin.register(FormField)
class FormFieldAdmin(admin.ModelAdmin):
    list_display = ['label', 'event', 'field_type', 'is_required', 'order']
    list_filter = ['field_type', 'is_required']
