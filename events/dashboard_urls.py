from django.urls import path
from . import dashboard_views as views
from registrations import dashboard_views as reg_views

app_name = 'dashboard'

urlpatterns = [
    path('', views.dashboard, name='index'),
    path('events/', views.event_list, name='event_list'),
    path('events/create/', views.event_create, name='event_create'),
    path('events/<uuid:pk>/edit/', views.event_edit, name='event_edit'),
    path('events/<uuid:pk>/delete/', views.event_delete, name='event_delete'),
    path('events/<uuid:pk>/form-builder/', views.form_builder, name='event_form_builder'),
    path('events/<uuid:pk>/form-builder/add-field/', views.add_form_field, name='add_form_field'),
    path('events/<uuid:pk>/form-builder/delete-field/<int:field_id>/', views.delete_form_field, name='delete_form_field'),
    path('events/<uuid:pk>/toggle-status/', views.toggle_event_status, name='toggle_event_status'),
    path('events/<uuid:pk>/toggle-registration/', views.toggle_registration, name='toggle_registration'),
    path('events/<uuid:pk>/toggle-checkin/', views.toggle_checkin, name='toggle_checkin'),
    path('registrations/', reg_views.registrations_list, name='registrations_list'),
    path('registrations/<uuid:event_pk>/', reg_views.event_registrations, name='event_registrations'),
    path('registrations/<uuid:reg_id>/send-qr/', reg_views.send_qr_manual, name='send_qr_manual'),
    path('registrations/<uuid:reg_id>/delete/', reg_views.delete_registration, name='delete_registration'),
    path('registrations/<uuid:event_pk>/export/', reg_views.export_registrations, name='export_registrations'),
    path('registrations/manual-add/<uuid:event_pk>/', reg_views.manual_add_registration, name='manual_add_registration'),
]
