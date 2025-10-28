from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.db.models import Max, OuterRef, Subquery, F
from collections import OrderedDict

from .models import (
    Standard,
    StandardRevisionNotification,
    PeriodicTest,
    InspectionRequirement,
    Classification,
    StandardProcess,
)


def standard_list_view(request):
    """
    Show only the most recent revision of each standard.name (by updated_at),
    and group for display. Optionally filter by the high-level process tag.
    Operators should not see specs still marked as requires_process_review.
    """

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
    )

    if selected_process:
        latest_standards = latest_standards.filter(process=selected_process)

    # Check if any standards still need review
    pending_reviews = Standard.objects.filter(requires_process_review=True)
    requires_review = pending_reviews.exists()

    # Group by author (stable order, deterministic)
    standards_by_author = OrderedDict()
    for std in latest_standards:
        standards_by_author.setdefault(std.author, [])
        standards_by_author[std.author].append(std)

    context = {
        'standards_by_author': standards_by_author,
        'pending_reviews': pending_reviews,
        'requires_review': requires_review,
        'selected_process': selected_process,
        'process_choices': Standard.PROCESS_CHOICES,
    }

    return render(request, 'standard/standard_list.html', context)


def standard_detail_view(request, standard_id):
    """
    Read-only operator view for one Standard.
    We present:
    - each StandardProcess block (clean / plate / strip / etc.) with its related
      inspections and classifications
    - any global inspections/classifications (no specific block)
    - periodic test requirements
    - internal notifications / notes
    """

    standard = get_object_or_404(Standard, id=standard_id)

    # Fetch all process blocks for this standard, and prefetch related data
    process_blocks = (
        StandardProcess.objects
        .filter(standard=standard)
        .order_by('title')
        .prefetch_related(
            'inspections',        # InspectionRequirement.standard_process -> related_name='inspections'
            'classifications',    # Classification.standard_process -> related_name='classifications'
        )
    )

    process_data = []
    for block in process_blocks:
        # Because we filtered the queryset to this standard, we can safely use the prefetched related sets
        block_inspections = (
            block.inspections
            .filter(standard=standard)
            .order_by('name')
        )
        block_classifications = (
            block.classifications
            .filter(standard=standard)
            .order_by('class_name', 'type')
        )

        process_data.append({
            "process": block,
            "inspections": block_inspections,
            "classifications": block_classifications,
        })

    # Global inspections = applies to entire standard (no process scope)
    global_inspections = (
        InspectionRequirement.objects
        .filter(standard=standard, standard_process__isnull=True)
        .order_by('name')
    )

    # Global classifications = applies to entire standard (no process scope)
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
    }

    return render(request, "standard/standard_detail.html", context)


def process_review_view(request):
    """
    Internal review/acknowledge page.
    This clears the requires_process_review flag on a Standard.
    You should protect this view with auth in urls.py or a decorator.
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

