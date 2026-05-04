import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.utils.text import slugify
from django.utils import timezone
from django.http import JsonResponse
from django.db.models import Count
from django.db.models.functions import TruncMonth
from .models import Event, FormField
from registrations.models import Registration


# ── Role helpers ──────────────────────────────────────────────────────────

def _profile(user):
    """Return AdminProfile or None."""
    return getattr(user, 'admin_profile', None)


def is_admin(user):
    from accounts.god_mode import is_god_mode
    return user.is_authenticated and (
        is_god_mode(user) or user.is_staff or user.is_superuser
        or hasattr(user, 'admin_profile')
    )


def is_superadmin(user):
    from accounts.god_mode import is_god_mode
    if not user.is_authenticated:
        return False
    if is_god_mode(user) or user.is_superuser or user.is_staff:
        return True
    p = _profile(user)
    return p is not None and p.role == 'superadmin'


def is_admin_or_superadmin(user):
    """Superadmin + Admin — can manage events. Moderator excluded."""
    from accounts.god_mode import is_god_mode
    if not user.is_authenticated:
        return False
    if is_god_mode(user) or user.is_superuser or user.is_staff:
        return True
    p = _profile(user)
    return p is not None and p.role in ('superadmin', 'admin')


def get_accessible_events(user):
    from accounts.god_mode import is_god_mode
    if is_god_mode(user) or user.is_superuser or user.is_staff:
        return Event.objects.all()
    p = _profile(user)
    if p:
        return p.get_accessible_events()
    return Event.objects.none()


def can_access_event(user, event):
    from accounts.god_mode import is_god_mode
    if is_god_mode(user) or user.is_superuser or user.is_staff:
        return True
    p = _profile(user)
    return p is not None and p.can_access_event(event)


def can_edit_event(user, event):
    """Moderators cannot edit — only superadmin and admin."""
    from accounts.god_mode import is_god_mode
    if is_god_mode(user) or user.is_superuser or user.is_staff:
        return True
    p = _profile(user)
    return p is not None and p.can_edit_event(event)


def can_delete_event(user, event):
    """Only superadmin can delete."""
    from accounts.god_mode import is_god_mode
    if is_god_mode(user) or user.is_superuser or user.is_staff:
        return True
    p = _profile(user)
    return p is not None and p.can_delete_event(event)


def can_manage_registrations(user, event):
    """Moderators are view-only — cannot add/delete registrations."""
    from accounts.god_mode import is_god_mode
    if is_god_mode(user) or user.is_superuser or user.is_staff:
        return True
    p = _profile(user)
    return p is not None and p.can_manage_registrations(event)


# ── Views ─────────────────────────────────────────────────────────────────

@login_required
@user_passes_test(is_admin)
def dashboard(request):
    accessible_events = get_accessible_events(request.user)
    total_events = accessible_events.count()
    published = accessible_events.filter(status='published').count()
    total_registrations = Registration.objects.filter(
        event__in=accessible_events, status='confirmed'
    ).count()
    upcoming = accessible_events.filter(
        status='published', start_date__gte=timezone.now()
    ).count()
    recent_events = accessible_events.order_by('-created_at')[:5]
    recent_regs = Registration.objects.filter(
        event__in=accessible_events
    ).select_related('event').order_by('-registered_at')[:10]
    events_by_type = accessible_events.values('event_type').annotate(count=Count('id'))
    monthly_regs = (
        Registration.objects
        .filter(event__in=accessible_events, registered_at__year=timezone.now().year)
        .annotate(month=TruncMonth('registered_at'))
        .values('month').annotate(count=Count('id')).order_by('month')
    )
    monthly_regs_data = [
        {'month': e['month'].month, 'count': e['count']}
        for e in monthly_regs if e['month'] is not None
    ]
    p = _profile(request.user)
    context = {
        'total_events': total_events,
        'published_events': published,
        'total_registrations': total_registrations,
        'upcoming_events': upcoming,
        'recent_events': recent_events,
        'recent_registrations': recent_regs,
        'events_by_type': json.dumps(list(events_by_type)),
        'monthly_regs': json.dumps(monthly_regs_data),
        # Pass role flags to template
        'user_is_superadmin': is_superadmin(request.user),
        'user_is_admin_or_super': is_admin_or_superadmin(request.user),
        'user_is_moderator': p is not None and p.is_moderator(),
    }
    return render(request, 'dashboard/index.html', context)


@login_required
@user_passes_test(is_admin)
def event_list(request):
    events = get_accessible_events(request.user).annotate(
        reg_count=Count('registrations')
    ).order_by('-created_at')
    p = _profile(request.user)
    return render(request, 'dashboard/events/list.html', {
        'events': events,
        'can_create': is_admin_or_superadmin(request.user),
        'user_is_moderator': p is not None and p.is_moderator(),
    })


@login_required
@user_passes_test(is_admin_or_superadmin)   # Moderators blocked here
def event_create(request):
    if request.method == 'POST':
        data = request.POST
        slug_base = slugify(data.get('title', ''))
        slug = slug_base
        counter = 1
        while Event.objects.filter(slug=slug).exists():
            slug = f'{slug_base}-{counter}'
            counter += 1
        event = Event.objects.create(
            title=data['title'],
            slug=slug,
            description=data['description'],
            event_type=data['event_type'],
            venue=data['venue'],
            address=data.get('address', ''),
            city=data.get('city', ''),
            country=data.get('country', ''),
            start_date=data['start_date'],
            end_date=data['end_date'],
            capacity=int(data.get('capacity', 0)),
            status=data.get('status', 'draft'),
            registration_deadline=data.get('registration_deadline') or None,
            is_featured='is_featured' in data,
            color_theme=data.get('color_theme', '#ac2376'),
            # God mode user is not a real DB User — store None safely
            created_by=request.user if hasattr(request.user, '_meta') and request.user.pk != -999 else None,
        )
        if 'banner' in request.FILES:
            event.banner = request.FILES['banner']
            event.save()
        # Auto-assign event to admin who created it
        p = _profile(request.user)
        if p and p.role == 'admin':
            p.assigned_events.add(event)
        messages.success(request, f'Event "{event.title}" created successfully!')
        return redirect('dashboard:event_form_builder', pk=event.pk)
    return render(request, 'dashboard/events/create.html', {
        'event_types': Event.EVENT_TYPE_CHOICES,
    })


@login_required
@user_passes_test(is_admin)
def event_edit(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if not can_edit_event(request.user, event):
        messages.error(request, 'You do not have permission to edit this event.')
        return redirect('dashboard:event_list')
    if request.method == 'POST':
        data = request.POST
        event.title = data['title']
        event.description = data['description']
        event.event_type = data['event_type']
        event.venue = data['venue']
        event.address = data.get('address', '')
        event.city = data.get('city', '')
        event.country = data.get('country', '')
        event.start_date = data['start_date']
        event.end_date = data['end_date']
        event.capacity = int(data.get('capacity', 0))
        event.status = data.get('status', 'draft')
        event.registration_deadline = data.get('registration_deadline') or None
        event.is_featured = 'is_featured' in data
        event.color_theme = data.get('color_theme', '#ac2376')
        if 'banner' in request.FILES:
            event.banner = request.FILES['banner']
        event.save()
        messages.success(request, 'Event updated successfully!')
        return redirect('dashboard:event_list')
    return render(request, 'dashboard/events/edit.html', {
        'event': event,
        'event_types': Event.EVENT_TYPE_CHOICES,
    })


@login_required
@user_passes_test(is_superadmin)   # Only superadmin can delete
def event_delete(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if not can_delete_event(request.user, event):
        messages.error(request, 'Only Super Admins can delete events.')
        return redirect('dashboard:event_list')
    if request.method == 'POST':
        title = event.title
        event.delete()
        messages.success(request, f'Event "{title}" deleted.')
        return redirect('dashboard:event_list')
    return render(request, 'dashboard/events/confirm_delete.html', {'event': event})


@login_required
@user_passes_test(is_admin)
def form_builder(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if not can_access_event(request.user, event):
        messages.error(request, 'You do not have permission to access this event.')
        return redirect('dashboard:event_list')
    # Moderators can view form builder but not add/remove fields
    p = _profile(request.user)
    read_only = p is not None and p.is_moderator()
    fields = event.form_fields.all()
    return render(request, 'dashboard/events/form_builder.html', {
        'event': event,
        'fields': fields,
        'field_types': FormField.FIELD_TYPES,
        'read_only': read_only,
    })


@login_required
@user_passes_test(is_admin_or_superadmin)   # Moderators blocked
def add_form_field(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if not can_edit_event(request.user, event):
        messages.error(request, 'Permission denied.')
        return redirect('dashboard:event_form_builder', pk=pk)
    if request.method == 'POST':
        data = request.POST
        label = data['label']
        field_key = slugify(label).replace('-', '_')
        counter = 1
        base_key = field_key
        while event.form_fields.filter(field_key=field_key).exists():
            field_key = f'{base_key}_{counter}'
            counter += 1
        FormField.objects.create(
            event=event,
            label=label,
            field_type=data['field_type'],
            placeholder=data.get('placeholder', ''),
            help_text=data.get('help_text', ''),
            is_required='is_required' in data,
            options=data.get('options', ''),
            order=event.form_fields.count(),
            field_key=field_key,
        )
        messages.success(request, 'Field added.')
    return redirect('dashboard:event_form_builder', pk=pk)


@login_required
@user_passes_test(is_admin_or_superadmin)   # Moderators blocked
def delete_form_field(request, pk, field_id):
    field = get_object_or_404(FormField, pk=field_id, event__pk=pk)
    if not can_edit_event(request.user, field.event):
        messages.error(request, 'Permission denied.')
        return redirect('dashboard:event_form_builder', pk=pk)
    field.delete()
    messages.success(request, 'Field removed.')
    return redirect('dashboard:event_form_builder', pk=pk)


@login_required
@user_passes_test(is_admin_or_superadmin)   # Moderators cannot toggle status
def toggle_event_status(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if not can_edit_event(request.user, event):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    event.status = 'draft' if event.status == 'published' else 'published'
    event.save()
    return JsonResponse({'status': event.status})


@login_required
@user_passes_test(is_admin_or_superadmin)
def toggle_registration(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if not can_edit_event(request.user, event):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    event.registration_open = not event.registration_open
    event.save(update_fields=['registration_open'])
    return JsonResponse({
        'registration_open': event.registration_open,
        'label': 'Open' if event.registration_open else 'Closed',
    })


@login_required
@user_passes_test(is_admin_or_superadmin)
def toggle_checkin(request, pk):
    event = get_object_or_404(Event, pk=pk)
    if not can_edit_event(request.user, event):
        return JsonResponse({'error': 'Permission denied'}, status=403)
    event.checkin_open = not event.checkin_open
    event.save(update_fields=['checkin_open'])
    return JsonResponse({
        'checkin_open': event.checkin_open,
        'label': 'Open' if event.checkin_open else 'Closed',
    })
