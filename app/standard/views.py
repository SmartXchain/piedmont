from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Max, OuterRef, Subquery, F, Count
from collections import OrderedDict
from .models import (
    Standard,
    StandardRevisionNotification,
    PeriodicTest,
    InspectionRequirement,
    Classification,
    StandardProcess,
)


# 📌 List all standards (Read-only, latest revision only)
def standard_list_view(request):
    """
    Show only the most recent revision of each standard.name (by updated_at),
    and group for display.
    """
    # NOTE: PROCESS_CHOICES must be defined on StandardProcess model or imported globally.
    process_choices = getattr(StandardProcess, "PROCESS_CHOICES", [])
    selected_process = request.GET.get('process')

    # For each standard name, get the most recent updated_at timestamp
    latest_update_subq = (
        Standard.objects
        .filter(name=OuterRef('name'))
        .values('name')
        .annotate(latest_updated_at=Max('updated_at'))
        .values('latest_updated_at')[:1]
    )

    # Keep only the rows that match that most recent updated_at and are released
    latest_standards = (
        Standard.objects
        .annotate(latest_for_name=Subquery(latest_update_subq))
        .filter(updated_at=F('latest_for_name'))
        .exclude(requires_process_review=True)
        .order_by('name')
        .prefetch_related("standard_processes")
    )

    # REMOVED FILTERING BY THE LEGACY 'process' FIELD
    # if selected_process:
    #     latest_standards = latest_standards.filter(process=selected_process)

    # Check if any standards still need review
    if selected_process:
        latest_standards = latest_standards.filter(
            standard_processes__process_type=selected_process
        ).distinct()

    process_label_map = dict(process_choices)

    for std in latest_standards:
        raw_types = {sp.process_type for sp in std.standard_processes.all()}
        std.process_badges = [
            {
                "value": pt,
                "label": process_label_map.get(pt, pt.title()),
            }
            for pt in sorted(raw_types)
        ]

    pending_reviews = Standard.objects.filter(requires_process_review=True)
    requires_review = pending_reviews.exists()

    # Group by author (stable order, deterministic)
    standards_by_author = OrderedDict()
    sorted_standards = sorted(latest_standards, key=lambda s: (s.author.lower(), s.name.lower()))
    for std in sorted_standards:
        standards_by_author.setdefault(std.author, [])
        standards_by_author[std.author].append(std)

    context = {
        'standards_by_author': standards_by_author,
        'pending_reviews': pending_reviews,
        'requires_review': requires_review,
        'selected_process': selected_process,
        'process_choices': process_choices,
    }

    return render(request, 'standard/standard_list.html', context)


# 📌 Read-only operator view for one Standard
def standard_detail_view(request, standard_id):
    standard = get_object_or_404(Standard, id=standard_id)

    # Fetch all process blocks for this standard, and prefetch related data
    process_blocks = (
        StandardProcess.objects
        .filter(standard=standard)
        .order_by('title')
        .prefetch_related(
            'inspections',
            'classifications',
        )
    )

    process_data = []
    for block in process_blocks:
        block_inspections = block.inspections.order_by('name')
        block_classifications = block.classifications.order_by('class_name', 'type')

        process_data.append({
            "process": block,
            "inspections": block_inspections,
            "classifications": block_classifications,
        })

    # Build a human-readable list of process types for the header
    process_label_map = dict(StandardProcess.PROCESS_CHOICES)
    distinct_types = sorted({pb.process_type for pb in process_blocks})
    if distinct_types:
        primary_processes = ", ".join(
            process_label_map.get(pt, pt.title()) for pt in distinct_types
        )
    else:
        primary_processes = "Not set"
    # Global requirements = applies to entire standard (no process scope)
    global_inspections = (
        InspectionRequirement.objects
        .filter(standard=standard, standard_process__isnull=True)
        .order_by('name')
    )

    global_classifications = (
        Classification.objects
        .filter(standard=standard, standard_process__isnull=True)
        .order_by('class_name', 'type')
    )

    periodic_tests = (
        PeriodicTest.objects
        .filter(standard=standard)
        .order_by('name')
    )

    notifications = (
        StandardRevisionNotification.objects
        .filter(standard=standard)
        .order_by('-notified_at')
    )

    context = {
        "standard": standard,
        "process_data": process_data,
        "global_inspections": global_inspections,
        "global_classifications": global_classifications,
        "periodic_tests": periodic_tests,
        "notifications": notifications,
        "primary_processes": primary_processes,
    }

    return render(request, "standard/standard_detail.html", context)


# 📌 Internal review/acknowledge page
def process_review_view(request):
    """
    Internal review/acknowledge page.
    This clears the requires_process_review flag on a Standard.
    """

    standards_to_review = Standard.objects.filter(requires_process_review=True)

    if request.method == "POST":
        standard_id = request.POST.get("standard_id")
        standard = get_object_or_404(Standard, id=standard_id)

        standard.requires_process_review = False
        standard.save()

        messages.success(
            request,
            f"Process review for {standard.name} (Rev {standard.revision}) has been acknowledged."
        )
        return redirect("process_review")

    return render(
        request,
        "standard/process_review.html",
        {
            "standards_to_review": standards_to_review,
        },
    )
