from django.shortcuts import render, get_object_or_404
from .models import Rack, RackPM, PMTask, RackPMPlan
from datetime import timedelta, date
from django.db.models import Min, Prefetch
from django.utils import timezone


def rack_list(request):
    today = date.today()
    upcoming_days = 10

    racks = Rack.objects.prefetch_related(
        'pm_plan__task',
        'photos',
        Prefetch(
            'rackpm_set',
            queryset=RackPM.objects.order_by('-date_performed'),
            to_attr='prefetched_pms',
        ),
    ).order_by('rack_id')

    overdue = []
    upcoming = []

    for rack in racks:
        # Build task_id -> most-recent RackPM from prefetched data (no extra queries)
        last_pm_by_task = {}
        for pm in rack.prefetched_pms:
            if pm.pm_task_id not in last_pm_by_task:
                last_pm_by_task[pm.pm_task_id] = pm

        for plan in rack.pm_plan.all():
            last_pm = last_pm_by_task.get(plan.task_id)
            frequency = plan.due_every_days or plan.task.frequency_days

            if last_pm:
                next_due = last_pm.date_performed + timedelta(days=frequency)
            else:
                next_due = rack.in_service_date or today

            if next_due < today:
                overdue.append((rack, plan.task.title, next_due))
            elif today <= next_due <= today + timedelta(days=upcoming_days):
                upcoming.append((rack, plan.task.title, next_due))

    context = {
        'racks': racks,
        'overdue': overdue,
        'upcoming': upcoming,
        'stats': {
            'total_racks': len(racks),  # queryset already evaluated above
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

    racks = Rack.objects.prefetch_related(
        'pm_plan__task',
        Prefetch(
            'rackpm_set',
            queryset=RackPM.objects.order_by('-date_performed'),
            to_attr='prefetched_pms',
        ),
    )

    for rack in racks:
        last_pm_by_task = {}
        for pm in rack.prefetched_pms:
            if pm.pm_task_id not in last_pm_by_task:
                last_pm_by_task[pm.pm_task_id] = pm

        for plan in rack.pm_plan.all():
            last_pm = last_pm_by_task.get(plan.task_id)
            frequency = plan.due_every_days or plan.task.frequency_days

            if last_pm:
                next_due = last_pm.date_performed + timedelta(days=frequency)
            else:
                next_due = rack.in_service_date or today

            events.append({
                "title": f"{rack.rack_id} – {plan.task.title}",
                "start": str(next_due),
                "url": f"/racks/{rack.id}/",
                "color": "#dc3545" if next_due < today else "#ffc107"
            })

    context = {
        "events": events
    }
    return render(request, 'fixtures/pm_calendar.html', context)
