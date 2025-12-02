# logbook/views.py
from datetime import datetime, time
import csv
import json
from django.db import transaction
from django.db.models import fields as model_fields
from django.http import HttpResponse
from django.shortcuts import redirect, render
from django.utils import timezone
from django.views.generic import ListView, TemplateView

from .forms import (
    LogEntryForm,
    DailyInspectionLogForm,
    ScrubberLogForm
)
from .models import (
    LogEntry,
    PROCESS_NAME_CHOICES,
    DailyInspectionLogEntry,
    ScrubberLog,
)


def operator_env_log_create(request):
    success = False

    if request.method == "POST":
        daily_form = DailyInspectionLogForm(request.POST, prefix="daily")
        scrubber_form = ScrubberLogForm(request.POST, prefix="scrubber")

        try:
            with transaction.atomic():
                daily_valid = daily_form.is_valid()
                scrubber_valid = scrubber_form.is_valid()

                if daily_valid and scrubber_valid:
                    daily_form.save()
                    scrubber_form.save()
                    return redirect("logbook:index")
                else:
                    # Optional: print to console while debugging
                    print("Daily form errors:", daily_form.errors)
                    print("Scrubber form errors:", scrubber_form.errors)
                    success = False

        except Exception as exc:
            print(f"Error during log submission: {exc}")
            success = False
    else:
        daily_form = DailyInspectionLogForm(prefix="daily")
        scrubber_form = ScrubberLogForm(prefix="scrubber")

    context = {
        "daily_form": daily_form,
        "scrubber_form": scrubber_form,
        "success": success,
    }
    return render(request, "logbook/operator_env_log_form.html", context)


class IndexView(TemplateView):
    """ Central Landing Page for Logbook Navigation """
    template_name = 'logbook/index.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['log_creation_url'] = 'logbook:create'
        context['manager_dashboard_url'] = 'logbook:manager_dashboard'
        return context


class ManagerDashboardView(TemplateView):
    template_name = "logbook/manager_dashboard.html"

    # This method fetches the data and puts it into the context for the template
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Data Fetching (Fetch ALL for analysis)
        all_daily_logs = DailyInspectionLogEntry.objects.all().order_by(
            "log_date"
        )
        all_scrubber_logs_qs = ScrubberLog.objects.all().order_by("log_date")

        # Table Display (Last 30)
        context["daily_logs"] = DailyInspectionLogEntry.objects.order_by(
            "-log_date"
        )[:30]
        context["scrubber_logs"] = ScrubberLog.objects.order_by(
            "-log_date"
        )[:30]

        total_daily_logs = all_daily_logs.count()
        total_scrubber_logs = all_scrubber_logs_qs.count()

        # Daily Inspection Summary: Percentage of Fails/Misses
        daily_summary = {
            "total_logs": total_daily_logs,
            "check_percentages": [],
        }

        # Fields to check: The desired behavior (opposite of default) is the "Miss"
        daily_checks = [
            {
                "field": "containment_is_clean",
                "label": "Containment Clean",
                "pass_value": True,
            },
            {
                "field": "system_undamaged",
                "label": "System Undamaged",
                "pass_value": True,
            },
            {
                "field": "pipes_are_secure",
                "label": "Pipes Secure",
                "pass_value": True,
            },
            {
                "field": "tank_lid_closed",
                "label": "Lid Closed",
                "pass_value": True,
            },
            {
                "field": "leaks_present",
                "label": "Leaks Present",
                "pass_value": False,
            },  # True means FAIL/Miss
        ]

        if total_daily_logs > 0:
            for check in daily_checks:
                # Count the logs where the value is the "miss" condition
                # For 'leaks_present', the miss is True. For others, the miss
                # is False.
                if check["field"] == "leaks_present":
                    miss_count = all_daily_logs.filter(leaks_present=True).count()
                else:
                    miss_count = all_daily_logs.filter(
                        **{check["field"]: False}
                    ).count()

                miss_percent = miss_count / total_daily_logs * 100

                daily_summary["check_percentages"].append(
                    {
                        "label": check["label"],
                        "miss_percent": round(miss_percent, 1),
                        "pass_percent": round(100 - miss_percent, 1),
                        "count": miss_count,
                    }
                )

        context["daily_summary"] = daily_summary

        # --- Scrubber Summary & Chart Data ---
        scrubber_miss_count = all_scrubber_logs_qs.filter(
            limits_exceeded=True
        ).count()
        scrubber_miss_percent = (
            scrubber_miss_count / total_scrubber_logs * 100
            if total_scrubber_logs
            else 0
        )

        context["scrubber_summary"] = {
            "total_logs": total_scrubber_logs,
            "miss_percent": round(scrubber_miss_percent, 1),
            "pass_percent": round(100 - scrubber_miss_percent, 1),
        }

        # Prepare Scrubber Chart Data (Time Series, last 30 readings only)
        recent_scrubber_logs = list(
            ScrubberLog.objects.all()
            .order_by("-log_date")[:30]
        )
        # reverse in-place so chart goes oldest -> newest left to right
        recent_scrubber_logs.reverse()

        scrubber_chart_data = {
            "dates": [
                log.log_date.strftime("%Y-%m-%d %H:%M")
                for log in recent_scrubber_logs
            ],
            "stage_1": [
                float(log.stage_one_reading)
                if log.stage_one_reading is not None
                else None
                for log in recent_scrubber_logs
            ],
            "stage_2": [
                float(log.stage_two_reading)
                if log.stage_two_reading is not None
                else None
                for log in recent_scrubber_logs
            ],
            "stage_3": [
                float(log.stage_three_reading)
                if log.stage_three_reading is not None
                else None
                for log in recent_scrubber_logs
            ],
        }
        context["scrubber_chart_data_json"] = json.dumps(scrubber_chart_data)

        return context


class LogEntryListView(ListView):
    model = LogEntry
    template_name = "logbook/logentry_list.html"
    context_object_name = "entries"
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset()
        # optional: show only today by default
        today = timezone.localdate()
        return qs.filter(date_of_process=today)
        # to show all, just: return qs


def logentry_create(request):
    if request.method == "POST":
        form = LogEntryForm(request.POST)
        if form.is_valid():
            form.save()
            # after save go back to list
            return redirect("logbook:list")
    else:
        form = LogEntryForm()

    return render(request, "logbook/logentry_form.html", {"form": form})


class LogbookLandingView(ListView):
    model = LogEntry
    template_name = "logbook/logbook_landing.html"
    context_object_name = "entries"
    paginate_by = 25

    def get_queryset(self):
        qs = super().get_queryset()

        # filters
        date_str = self.request.GET.get("date")
        wo = self.request.GET.get("wo")
        part = self.request.GET.get("part")
        proc = self.request.GET.get("process")

        if date_str:
            qs = qs.filter(date_of_process=date_str)
        else:
            qs = qs.filter(date_of_process=timezone.localdate())

        if wo:
            qs = qs.filter(work_order_number__icontains=wo)

        if part:
            qs = qs.filter(part_number__icontains=part)

        if proc:
            qs = qs.filter(process_name=proc)

        return qs

    def get_context_data(self, **kwargs):
        ctx = super().get_context_data(**kwargs)
        ctx["current_date"] = self.request.GET.get("date", timezone.localdate().isoformat())
        ctx["current_wo"] = self.request.GET.get("wo", "")
        ctx["current_part"] = self.request.GET.get("part", "")
        ctx["current_process"] = self.request.GET.get("process", "")
        ctx["process_choices"] = PROCESS_NAME_CHOICES
        return ctx


def download_log_data(request):
    # 1. Get parameters from the request
    log_type = request.GET.get('log_type')
    start_date_str = request.GET.get('start_date')
    end_date_str = request.GET.get('end_date')

    if not all([log_type, start_date_str, end_date_str]):
        # Handle case where dates are missing (shouldn't happen with 'required' in form)
        return HttpResponse("Missing date or log type parameters.", status=400)

    # 2. Determine Model and QuerySet
    if log_type == 'daily':
        Model = DailyInspectionLogEntry
        log_name = 'daily_inspection_logs'
    elif log_type == 'scrubber':
        Model = ScrubberLog
        log_name = 'scrubber_logs'
    else:
        return HttpResponse("Invalid log type specified.", status=400)

    # 3. Parse Dates and Filter QuerySet
    try:
        # Convert start date string to a datetime object at the start of the day (00:00:00)
        start_date = datetime.strptime(start_date_str, '%Y-%m-%d').date()
        start_datetime = datetime.combine(start_date, time.min)

        # Convert end date string to a datetime object at the end of the day (23:59:59)
        end_date = datetime.strptime(end_date_str, '%Y-%m-%d').date()
        end_datetime = datetime.combine(end_date, time.max)
    except ValueError:
        return HttpResponse("Invalid date format.", status=400)

    # Filter data based on the log_date field
    queryset = Model.objects.filter(log_date__range=(start_datetime, end_datetime)).order_by('log_date')

    # 4. Prepare HTTP Response
    filename = f"{log_name}_{start_date_str}_to_{end_date_str}.csv"
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'

    # 5. Write CSV content
    writer = csv.writer(response)

    # Get field names for the CSV header
    # Exclude the primary key 'id' but include all others
    fields = [field for field in Model._meta.fields if field.name != 'id']
    # Create the Header Row using help_text or verbose_name
    header_row = []
    for field in fields:
        # Use help_text if available, otherwise fall back to verbose_name
        # For the Daily Inspection Log, the boolean fields have clear help_text.
        # For the Scrubber Log, stage_one_reading also has help_text.
        title = field.help_text or field.verbose_name.title()
        header_row.append(title)
    # Write Header
    writer.writerow(header_row)

    # Write Data Rows
    for obj in queryset:
        row = []
        for field in fields:
            value = getattr(obj, field.name)

            # Special handling for ForeignKey fields (like 'operator')
            if isinstance(field, model_fields.related.ForeignKey):
                # Use the username or 'N/A' if the operator is None
                value = getattr(value, 'username', 'N/A')

            # Simple conversion for None/Null values
            if value is None:
                value = ''

            row.append(value)
        writer.writerow(row)

    return response
