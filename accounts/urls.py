from django.urls import path
from . import views

app_name = 'accounts'

urlpatterns = [
    path('login/',   views.login_view,   name='login'),
    path('logout/',  views.logout_view,  name='logout'),
    path('profile/', views.profile,      name='profile'),

    # Admin user management (superadmin only)
    path('admins/',              views.admin_list,    name='admin_list'),
    path('admins/create/',       views.admin_create,  name='admin_create'),
    path('admins/<int:pk>/edit/', views.admin_edit,   name='admin_edit'),
    path('admins/<int:pk>/delete/', views.admin_delete, name='admin_delete'),
]
