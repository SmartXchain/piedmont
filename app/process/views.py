# process/views.py
from django.db.models import Q, F
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.text import slugify
from django.views.generic import ListView

from methods.models import Method
from standard.models import Classification
from .models import Process
from .utils import build_process_flowchart_svg


def get_classifications(request):
    standard_id = request.GET.get("standard_id")
    if not standard_id:
        return JsonResponse([], safe=False)

    classifications = Classification.objects.filter(standard_id=standard_id)
    data = [{"id": c.id, "text": str(c)} for c in classifications]
    return JsonResponse(data, safe=False)


def get_method_info(request):
    method_id = request.GET.get("method_id")
    if not method_id:
        return JsonResponse({"error": "No method ID provided"}, status=400)

    method = get_object_or_404(Method, id=method_id)
    return JsonResponse(
        {
            "title": method.title,
            "description": method.description,
            "method_type": method.method_type,
            "chemical": getattr(method, "chemical", None),
            "tank_name": getattr(method, "tank_name", None),
            "is_rectified": getattr(method, "is_rectified", None),
            "is_strike_etch": getattr(method, "is_strike_etch", None),
        }
    )


class ProcessLandingView(ListView):
    """
    Operator-facing landing page:
    - Lists all Processes
    - Search by Standard name, Classification class_name, StandardProcess title, or Process description
    """
    model = Process
    template_name = "process/process_landing.html"
    context_object_name = "processes"
    paginate_by = 25

    def get_queryset(self):
        qs = (
            Process.objects.select_related("standard", "classification", "standard_process")
            .order_by(
                "standard__name",
                F("classification__class_name").asc(nulls_last=True),
                F("standard_process__title").asc(nulls_last=True),
            )
        )

        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(standard__name__icontains=q)
                | Q(classification__class_name__icontains=q)
                | Q(standard_process__title__icontains=q)
                | Q(description__icontains=q)  # <-- Process.description (correct)
            )

        return qs


def process_flowchart_view(request, pk):
    """
    Read-only view that shows a Graphviz SVG flowchart for a Process.
    """
    process = get_object_or_404(
        Process.objects.select_related("standard", "classification", "standard_process")
        .prefetch_related("steps__method"),
        pk=pk,
    )

    svg = build_process_flowchart_svg(process)

    return render(
        request,
        "process/process_flowchart.html",
        {
            "process": process,
            "svg": svg,
        },
    )


def process_flowchart_download_view(request, pk):
    """
    Returns the process flowchart as an SVG file download.
    """
    process = get_object_or_404(
        Process.objects.select_related("standard", "classification", "standard_process")
        .prefetch_related("steps__method"),
        pk=pk,
    )

    svg = build_process_flowchart_svg(process)

    standard_name = process.standard.name if process.standard else "process"
    classification_name = (
        process.classification.class_name
        if process.classification_id
        else "unclassified"
    )
    process_title = (
        process.standard_process.title
        if process.standard_process_id
        else "standard-process"
    )

    base_name = f"{standard_name}-{classification_name}-{process_title}-process-{process.pk}"
    filename = slugify(base_name) + ".svg"

    response = HttpResponse(svg, content_type="image/svg+xml")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
