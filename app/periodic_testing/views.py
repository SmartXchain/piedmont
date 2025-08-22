from django.shortcuts import render, redirect, get_object_or_404
from django.utils import timezone
from .models import FailureLog, DailyTask
from .services import ensure_daily_instances_for
from standard.models import PeriodicTest, PeriodicTestResult
from django.contrib.auth.decorators import login_required
from django import forms


# Landing page redirects to daily by default
def periodic_testing_landing(request):
    tabs = ['Daily', 'Weekly', 'Monthly', 'Semi-Annually', 'Annually', 'Failure Log']
    return render(request, 'periodic_testing/landing.html', {'tabs': tabs})


# WEEKLY
def weekly_view(request):
    return render(request, 'periodic_testing/tabs/weekly.html')


# MONTHLY
def monthly_view(request):
    return render(request, 'periodic_testing/tabs/monthly.html')


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
