from django.urls import path
from . import views

app_name = 'checkin'

urlpatterns = [
    # Central overview
    path('', views.event_select, name='event_select'),
    path('overview/', views.overview, name='overview'),
    path('export-all/', views.export_all_checkins, name='export_all'),

    # Per-event online scanner + dashboard
    path('<uuid:event_pk>/scanner/', views.scanner, name='scanner'),
    path('<uuid:event_pk>/scan/', views.process_scan, name='process_scan'),
    path('<uuid:event_pk>/dashboard/', views.dashboard, name='dashboard'),
    path('<uuid:event_pk>/stats/', views.live_stats, name='live_stats'),
    path('<uuid:event_pk>/export/', views.export_checkin, name='export'),
    path('<uuid:event_pk>/manual/<uuid:reg_id>/', views.manual_checkin, name='manual_checkin'),
    path('<uuid:event_pk>/scanner-qr/', views.scanner_url_qr, name='scanner_url_qr'),

    # PWA offline scanner
    path('<uuid:event_pk>/pwa/', views.pwa_scanner, name='pwa_scanner'),
    path('<uuid:event_pk>/offline-registrations/', views.offline_registrations, name='offline_registrations'),
    path('<uuid:event_pk>/sync-offline/', views.sync_offline_checkins, name='sync_offline'),
    path('<uuid:event_pk>/sync-offline-registrations/', views.sync_offline_registrations, name='sync_offline_registrations'),

    # Excel import + manual name check-in
    path('<uuid:event_pk>/import/', views.import_guest_list, name='import_guest_list'),
    path('<uuid:event_pk>/manual-checkin/', views.manual_checkin_list, name='manual_checkin_list'),

    # Offline registration page
    path('<uuid:event_pk>/offline-register/', views.offline_reg_page, name='offline_reg_page'),

    # External QR import
    path('<uuid:event_pk>/external-qr/', views.external_qr_import_page, name='external_qr_import'),
    path('<uuid:event_pk>/external-qr/process/', views.external_qr_import_process, name='external_qr_process'),
    path('<uuid:event_pk>/external-qr/bulk/', views.external_qr_bulk_import, name='external_qr_bulk'),
    path('<uuid:event_pk>/external-qr/preview/', views.external_qr_preview, name='external_qr_preview'),
]
