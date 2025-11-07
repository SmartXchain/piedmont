from django.views.generic import ListView
from .models import ProcessRun


class ProcessRunListView(ListView):
    model = ProcessRun
    template_name = "logbook/processrun_list.html"  # adjust to your app/templates path
    context_object_name = "runs"
    paginate_by = 25  # change as needed
    ordering = ['-date_of_process', '-plating_end_time']

    def get_queryset(self):
        qs = super().get_queryset()
        # later you can add filters/search here
        return qs

