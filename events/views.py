from django.shortcuts import render, get_object_or_404
from django.utils import timezone
from .models import Event


def home(request):
    featured = Event.objects.filter(status='published', is_featured=True, end_date__gte=timezone.now())[:3]
    upcoming = Event.objects.filter(status='published', end_date__gte=timezone.now()).order_by('start_date')[:9]
    event_types = Event.EVENT_TYPE_CHOICES
    context = {
        'featured_events': featured,
        'upcoming_events': upcoming,
        'event_types': event_types,
        'total_events': Event.objects.filter(status='published').count(),
    }
    return render(request, 'home.html', context)


def event_detail(request, slug):
    event = get_object_or_404(Event, slug=slug, status='published')
    return render(request, 'events/event_detail.html', {'event': event})


def events_list(request):
    events = Event.objects.filter(status='published', end_date__gte=timezone.now())
    event_type = request.GET.get('type')
    search = request.GET.get('q')
    if event_type:
        events = events.filter(event_type=event_type)
    if search:
        events = events.filter(title__icontains=search)
    return render(request, 'events/events_list.html', {
        'events': events,
        'event_types': Event.EVENT_TYPE_CHOICES,
        'selected_type': event_type,
        'search': search,
    })
