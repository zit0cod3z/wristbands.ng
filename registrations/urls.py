from django.urls import path
from . import views

urlpatterns = [
    path('<slug:slug>/', views.register, name='register'),
    path('success/<uuid:reg_id>/', views.registration_success, name='registration_success'),
]
