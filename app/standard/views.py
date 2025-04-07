from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Standard, StandardRevisionNotification, PeriodicTest, InspectionRequirement, Classification
from .forms import StandardForm, StandardRevisionNotificationForm, PeriodicTestForm, InspectionRequirementForm, ClassificationForm
from django.db import IntegrityError
from django.utils.timezone import now
from django.db.models import Max, OuterRef, Subquery
from collections import defaultdict, OrderedDict


def standard_list_view(request):
    """Fetches only the latest revision of each standard and flags those requiring review."""

    selected_process = request.GET.get('process')

    # Get the latest revision for each standard name
    latest_standards = Standard.objects.filter(
        revision=Subquery(
            Standard.objects.filter(name=OuterRef('name'))
            .order_by('-updated_at')  # Get latest revision by update date
            .values('revision')[:1]
        )
    ).exclude(requires_process_review=True).order_by('name')

    if selected_process:
        latest_standards = latest_standards.filter(process=selected_process)

    latest_standards = latest_standards.order_by('name')

    # Fetch pending review standards separately
    pending_reviews = Standard.objects.filter(requires_process_review=True)
    requires_review = pending_reviews.exists()

    # Group standards by author (ensuring alphabetical sorting)
    authors = latest_standards.values_list('author', flat=True).distinct().order_by('author')

    standards_by_author = OrderedDict()
    for author in authors:
        standards_by_author[author] = latest_standards.filter(author=author)

    return render(request, 'standard/standard_list.html', {
        'standards_by_author': standards_by_author,  # Grouped and sorted
        'pending_reviews': pending_reviews,
        'requires_review': requires_review,
        'selected_process': selected_process,
        'process_choices': Standard.PROCESS_CHOICES,
    })


def standard_detail_view(request, standard_id):
    """Displays the details of a Standard, including revisions and process review status."""
    standard = get_object_or_404(Standard, id=standard_id)
    inspections = standard.inspections.all()
    classifications = standard.classifications.all()
    periodic_tests = standard.periodic_tests.all()
    notifications = standard.notifications.all()

    return render(
        request,
        "standard/standard_detail.html",
        {
            "standard": standard,
            "inspections": inspections,
            "classifications": classifications,
            "periodic_tests": periodic_tests,
            "notifications": notifications,
        },
    )


def process_review_view(request):
    """Displays a list of standards that require process review."""
    standards_to_review = Standard.objects.filter(requires_process_review=True)

    if request.method == "POST":
        standard_id = request.POST.get("standard_id")
        standard = get_object_or_404(Standard, id=standard_id)

        # Mark as reviewed
        standard.requires_process_review = False
        standard.save()

        messages.success(request, f"Process review for {standard.name} (Rev {standard.revision}) has been acknowledged.")
        return redirect("process_review")

    return render(request, "standard/process_review.html", {"standards_to_review": standards_to_review})
