from django.shortcuts import render, get_object_or_404
from .models import Rack, RackPM, PMTask
from datetime import timedelta, date
from django.db.models import Min
from django.utils import timezone


def rack_list(request):
    today = date.today()
    upcoming_days = 10  # Define upcoming threshold (e.g., next 10 days)

    racks = Rack.objects.prefetch_related('pm_plan__task', 'photos').all().order_by('rack_id')

    overdue = []
    upcoming = []

    # Calculate next due date for each rack
    for rack in racks:
        for plan in rack.pm_plan.all():
            last_pm = RackPM.objects.filter(rack=rack, pm_task=plan.task).order_by('-date_performed').first()
            frequency = plan.due_every_days or plan.task.frequency_days

            if last_pm:
                next_due = last_pm.date_performed + timedelta(days=frequency)
            else:
                next_due = rack.in_service_date or today  # fallback to in_service_date or today

            # Categorize
            if next_due < today:
                overdue.append((rack, plan.task.title, next_due))
            elif today <= next_due <= today + timedelta(days=upcoming_days):
                upcoming.append((rack, plan.task.title, next_due))

    context = {
        'racks': racks,
        'overdue': overdue,
        'upcoming': upcoming,
        'stats': {
            'total_racks': racks.count(),
            'total_overdue': len(overdue),
            'total_upcoming': len(upcoming),
        },
    }
    return render(request, 'fixtures/rack_list.html', context)


def rack_detail(request, pk):
    """
    Show the detail view of a specific rack, including:
    - Rack PM plan (prefetched with tasks)
    - Historical PM records
    - Tasks used in the rack's PM history (for instruction tab)
    """
    rack = get_object_or_404(
        Rack.objects.prefetch_related('pm_plan__task', 'photos'),
        pk=pk
    )
    pm_history = RackPM.objects.filter(rack=rack).order_by('-date_performed')
    used_tasks = PMTask.objects.filter(rackpm__rack=rack).distinct()

    context = {
        'rack': rack,
        'pm_history': pm_history,
        'pm_tasks': used_tasks,
    }

    return render(request, 'fixtures/rack_detail.html', context)


def pm_calendar(request):
    today = timezone.now().date()
    events = []

    for rack in Rack.objects.prefetch_related('pm_plan__task'):
        for plan in rack.pm_plan.all():
            last_pm = RackPM.objects.filter(rack=rack, pm_task=plan.task).order_by('-date_performed').first()
            frequency = plan.due_every_days or plan.task.frequency_days

            if last_pm:
                next_due = last_pm.date_performed + timedelta(days=frequency)
            else:
                next_due = rack.in_service_date or today

            events.append({
                "title": f"{rack.rack_id} – {plan.task.title}",
                "start": str(next_due),
                "url": f"/racks/{rack.id}/",
                "color": "#dc3545" if next_due < today else "#ffc107"  # red if overdue, yellow if upcoming
            })

    context = {
        "events": events
    }
    return render(request, 'fixtures/pm_calendar.html', context)
