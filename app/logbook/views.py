# logbook/views.py
from django.shortcuts import redirect, render
from django.views.generic import ListView
from django.utils import timezone
from .models import LogEntry, PROCESS_NAME_CHOICES
from .forms import LogEntryForm


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
