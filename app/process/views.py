# process/views.py
from django.http import JsonResponse
from standard.models import Classification
from methods.models import Method
from django.shortcuts import get_object_or_404, render
from .models import Process
from .utils import build_process_flowchart_svg
from django.views.generic import ListView
from django.db.models import Q
from django.utils.text import slugify
from django.http import HttpResponse


def get_classifications(request):
    standard_id = request.GET.get('standard_id')
    if not standard_id:
        return JsonResponse([], safe=False)

    classifications = Classification.objects.filter(standard_id=standard_id)
    data = [{'id': c.id, 'text': str(c)} for c in classifications]
    return JsonResponse(data, safe=False)


def get_method_info(request):
    method_id = request.GET.get('method_id')
    if not method_id:
        return JsonResponse({'error': 'No method ID provided'}, status=400)

    try:
        method = Method.objects.get(id=method_id)
        return JsonResponse({
            'title': method.title,
            'description': method.description,
            'method_type': method.method_type,
            'chemical': method.chemical,
            'tank_name': method.tank_name,
            'is_rectified': method.is_rectified,
            'is_strike_etch': method.is_strike_etch,
        })
    except Method.DoesNotExist:
        return JsonResponse({'error': 'Method not found'}, status=404)


class ProcessLandingView(ListView):
    """
    Operator-facing landing page:
    - Lists all Processes
    - Simple search by Standard, Classification, or StandardProcess
    """
    model = Process
    template_name = "process/process_landing.html"
    context_object_name = "processes"
    paginate_by = 25

    def get_queryset(self):
        qs = (
            Process.objects
            .select_related("standard", "classification", "standard_process")
            .order_by("standard__name", "classification__class_name")
        )

        q = self.request.GET.get("q", "").strip()
        if q:
            qs = qs.filter(
                Q(standard__name__icontains=q) |
                Q(classification__class_name__icontains=q) |
                Q(standard_process__name__icontains=q)
            )

        # Optional: hide template processes or show only them
        # show_templates = self.request.GET.get("templates") == "1"
        # if not show_templates:
        #     qs = qs.filter(is_template=False)

        return qs


def process_flowchart_view(request, pk):
    """
    Read-only view that shows a Graphviz SVG flowchart for a Process.
    """
    process = get_object_or_404(
        Process.objects.select_related("standard", "classification")
                       .prefetch_related("steps__method"),
        pk=pk
    )

    svg = build_process_flowchart_svg(process)

    context = {
        "process": process,
        "svg": svg,
    }
    return render(request, "process/process_flowchart.html", context)


def process_flowchart_download_view(request, pk):
    """
    Returns the process flowchart as an SVG file download.
    """
    process = get_object_or_404(
        Process.objects.select_related("standard", "classification")
                       .prefetch_related("steps__method"),
        pk=pk
    )

    svg = build_process_flowchart_svg(process)

    # Build a nice filename, e.g. "ams-2410-class-1a-process-42.svg"
    standard_name = process.standard.name if process.standard else "process"
    classification_name = (
        process.classification.class_name
        if getattr(process, "classification", None)
        else "unclassified"
    )

    base_name = f"{standard_name}-{classification_name}-process-{process.pk}"
    filename = slugify(base_name) + ".svg"

    response = HttpResponse(svg, content_type="image/svg+xml")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
