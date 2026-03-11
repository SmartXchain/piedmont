import logging
from datetime import date, timedelta
from typing import Dict, Any

from django import forms
from django.contrib.auth.decorators import login_required
from django.db import transaction
from django.http import Http404, HttpRequest, HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from standard.models import PeriodicTest, PeriodicTestResult

from .models import DailyTask, DailyTaskTemplate, FailureLog
from .services import ensure_daily_instances_for

logger = logging.getLogger(__name__)


# Landing page redirects to daily by default
def periodic_testing_landing(request):
    tabs = ['Daily', 'Weekly', 'Monthly', 'Semi-Annually', 'Annually', 'Failure Log']
    return render(request, 'periodic_testing/landing.html', {'tabs': tabs})


# WEEKLY
def weekly_view(request):
    return render(request, 'periodic_testing/tabs/weekly.html')


# MONTHLY
def monthly_view(request):
    qs = (
        PeriodicTestResult.objects
        .select_related("test", "test__tank", "test__standard", "reviewed_by")
        .filter(test__frequency="MONTHLY")   # adjust to your field
        .order_by("-performed_on", "-id")
    )

    results = []
    for r in qs:
        results.append({
            "obj": r,
            "yy": f"{r.performed_on:%y}",  # last 2 digits
            "mm": f"{r.performed_on:%m}",  # two digits
        })

    return render(request, "periodic_testing/tabs/monthly.html", {"results": results})


# SEMI-ANNUAL
def semi_annual_view(request):
    return render(request, 'periodic_testing/tabs/semi_annual.html')


# ANNUAL
def annual_view(request):
    tests = (PeriodicTest.objects
             .filter(time_period="yearly")
             .select_related("standard")
             .prefetch_related("results")
             .order_by("standard__name", "name")
             )

    context = {
        "tests": tests,
    }
    return render(request, "periodic_testing/tabs/annual.html", context)


# FAILURE LOG
def failure_log_view(request):
    logs = FailureLog.objects.all()
    return render(request, 'periodic_testing/tabs/failure_log.html', {'logs': logs})


def daily_view(request):
    today = timezone.localdate()
    ensure_daily_instances_for(today)  # make sure rows exist for today
    tasks = (DailyTask.objects
             .select_related("template", "completed_by")
             .filter(scheduled_for=today)
             .order_by("template__name"))
    return render(request, "periodic_testing/tabs/daily.html", {"tasks": tasks, "today": today})


def monthly_tests(request):
    # Get all periodic tests defined as monthly
    tests = (PeriodicTest.objects
             .filter(time_period="monthly")
             .select_related("standard")
             .prefetch_related("results")
             .order_by("standard__name", "name")
             )

    context = {
        "tests": tests,
    }
    return render(request, "periodic_testing/tabs/monthly.html", context)


def _daterange(start: date, end: date):
    cur = start
    while cur <= end:
        yield cur
        cur += timedelta(days=1)


def _ensure_instances_for_range(template: DailyTaskTemplate, start, end) -> None:
    """
    Ensure a DailyTask exists for each date in [start, end] for the given template.
    Creates missing rows so 30-day stats are accurate.
    """
    day = start
    while day <= end:
        DailyTask.objects.get_or_create(template=template, scheduled_for=day)
        day += timedelta(days=1)


def daily_task_summary(request: HttpRequest, template_id: int) -> HttpResponse:
    """
    30-day summary for a DailyTaskTemplate:
      - Performed vs Not Performed counts
      - Latest completed date & operator
      - Table of each day with status/operator
    Ensures one DailyTask per day exists for the window.
    """
    logger.debug("daily_task_summary called for template_id=%s", template_id)
    template_obj = get_object_or_404(DailyTaskTemplate, pk=template_id)
    today = timezone.localdate()
    start = today - timedelta(days=29)
    end = today

    # 1) Ensure rows exist for the window (bulk create missing days)
    existing_dates = set(
        DailyTask.objects.filter(
            template=template_obj,
            scheduled_for__range=(start, end),
        ).values_list("scheduled_for", flat=True)
    )
    to_create = [
        DailyTask(template=template_obj, scheduled_for=dt)
        for dt in _daterange(start, end)
        if dt not in existing_dates
    ]
    if to_create:
        with transaction.atomic():
            DailyTask.objects.bulk_create(to_create, ignore_conflicts=True)

    # 2) Refetch after inserts so we have a complete window
    instances = (
        DailyTask.objects.select_related("completed_by", "template")
        .filter(template=template_obj, scheduled_for__range=(start, end))
        .order_by("-scheduled_for")
    )

    # 3) Stats
    total_days = (end - start).days + 1  # should be 30
    performed_count = instances.filter(completed=True).count()
    not_performed_count = total_days - performed_count

    latest_completed = (
        instances.filter(completed=True)
        .order_by("-scheduled_for", "-completed_at")
        .first()
    )

    context: Dict[str, Any] = {
        "template_obj": template_obj,
        "start": start,
        "end": end,
        "total_days": total_days,
        "performed_count": performed_count,
        "not_performed_count": not_performed_count,
        "latest_completed": latest_completed,
        "instances": instances,  # 30 rows guaranteed
        "today": today,
    }
    return render(
        request,
        "periodic_testing/tabs/daily_summary_page.html",
        context,
    )
