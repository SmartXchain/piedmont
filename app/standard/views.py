from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import Standard, StandardRevisionNotification, PeriodicTest, InspectionRequirement, Classification
from .forms import StandardForm, PeriodicTestForm, InspectionRequirementForm, ClassificationForm
from django.db import IntegrityError
from django.utils.timezone import now
from django.db.models import Max, OuterRef, Subquery


def standard_list_view(request):
    """Fetches only the latest revision of each standard and flags those requiring review."""

    # Get the latest revision for each standard name
    latest_standards = Standard.objects.filter(
        revision=Subquery(
            Standard.objects.filter(name=OuterRef('name'))
            .order_by('-updated_at')
            .values('revision')[:1]  # Get the latest revision
        )
    ).exclude(requires_process_review=True).order_by('name')

    # Check if any standards require review
    pending_reviews = Standard.objects.filter(requires_process_review=True)
    requires_review = pending_reviews.exists()

    # Group standards by author
    authors = latest_standards.values('author').distinct()

    standards_by_author = {
        author['author']: latest_standards.filter(author=author['author'])
        for author in authors
    }

    return render(request, 'standard/standard_list.html', {
        'standards_by_author': standards_by_author,
        'pending_reviews': pending_reviews,
        'requires_review': requires_review
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


def standard_create_view(request):
    """Creates a new standard and requires process review before use."""
    if request.method == "POST":
        form = StandardForm(request.POST, request.FILES)
        if form.is_valid():
            standard = form.save(commit=False)  # Create but don’t save yet
            standard.requires_process_review = True  # Force review before approval
            standard.save()  # Save the new standard
            
            messages.success(request, "Standard created successfully. Requires process review before use.")
            return redirect("process_review")  # Redirect to the review page

    else:
        form = StandardForm()

    return render(request, "standard/standard_form.html", {"form": form})


from django.contrib import messages
from django.db import IntegrityError

def standard_edit_view(request, standard_id):
    """Handles revision updates while preserving previous versions and notifying process review."""
    standard = get_object_or_404(Standard, id=standard_id)

    if request.method == "POST":
        form = StandardForm(request.POST, request.FILES)
        
        if form.is_valid():
            try:
                # Check if revision has changed
                if form.cleaned_data["revision"] != standard.revision:
                    # Create a new standard instead of updating
                    new_standard = Standard.objects.create(
                        name=standard.name,
                        description=form.cleaned_data["description"],
                        revision=form.cleaned_data["revision"],
                        author=form.cleaned_data["author"],
                        upload_file=form.cleaned_data.get("upload_file"),
                        previous_version=standard,  # Link to old standard
                        requires_process_review=True,  # Notify process review
                    )

                    # Notify the Process App
                    StandardRevisionNotification.objects.create(
                        standard=new_standard,
                        message=f"Standard {new_standard.name} has been revised from {standard.revision} to {new_standard.revision}."
                    )

                    messages.success(request, "New revision created successfully.")
                    return redirect("standard_detail", standard_id=new_standard.id)
                
                else:
                    # If only other fields changed, update the existing standard
                    standard.description = form.cleaned_data["description"]
                    standard.author = form.cleaned_data["author"]
                    standard.upload_file = form.cleaned_data.get("upload_file")
                    standard.save()
                    
                    messages.success(request, "Standard updated successfully.")
                    return redirect("standard_detail", standard_id=standard.id)

            except IntegrityError:
                messages.error(request, "A standard with this name and revision already exists. Please choose a different revision.")

        else:
            messages.error(request, "There was an issue updating the standard. Please check the form.")

    else:
        form = StandardForm(instance=standard)

    return render(request, "standard/standard_form.html", {"form": form, "standard": standard})


def standard_review_view(request, standard_id):
    """Allows users to mark a process review as complete."""
    standard = get_object_or_404(Standard, id=standard_id)

    if request.method == "POST":
        standard.requires_process_review = False
        standard.save()
        messages.success(request, "Process review marked as complete.")
        return redirect("standard_detail", standard_id=standard.id)

    return render(request, "standard/standard_review.html", {"standard": standard})


def standard_notification_view(request, notification_id):
    """Allows users to acknowledge a standard revision notification."""
    notification = get_object_or_404(StandardRevisionNotification, id=notification_id)

    if request.method == "POST":
        notification.is_acknowledged = True
        notification.save()
        messages.success(request, "Notification acknowledged.")
        return redirect("standard_detail", standard_id=notification.standard.id)

    form = StandardRevisionNotificationForm(instance=notification)
    return render(request, "standard/standard_notification.html", {"form": form, "notification": notification})


def inspection_list_view(request, standard_id):
    """Displays all inspections for a standard."""
    standard = get_object_or_404(Standard, id=standard_id)
    inspections = standard.inspections.all()
    return render(request, "standard/inspection_list.html", {"standard": standard, "inspections": inspections})


def inspection_create_view(request, standard_id):
    """Handles creating an inspection requirement."""
    standard = get_object_or_404(Standard, id=standard_id)
    form = InspectionRequirementForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        inspection = form.save(commit=False)
        inspection.standard = standard
        inspection.save()
        messages.success(request, "Inspection requirement added.")
        return redirect("inspection_list", standard_id=standard.id)

    return render(request, "standard/inspection_form.html", {"form": form, "standard": standard})


def inspection_edit_view(request, inspection_id):
    """Handles editing an inspection requirement."""
    inspection = get_object_or_404(InspectionRequirement, id=inspection_id)
    form = InspectionRequirementForm(request.POST or None, instance=inspection)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Inspection requirement updated.")
        return redirect("inspection_list", standard_id=inspection.standard.id)

    return render(request, "standard/inspection_form.html", {"form": form, "standard": inspection.standard})


def periodic_test_list_view(request, standard_id):
    """Displays all periodic tests for a standard."""
    standard = get_object_or_404(Standard, id=standard_id)
    periodic_tests = standard.periodic_tests.all()
    return render(request, "standard/periodic_test_list.html", {"standard": standard, "periodic_tests": periodic_tests})


def periodic_test_create_view(request, standard_id):
    """Handles creating a periodic test requirement."""
    standard = get_object_or_404(Standard, id=standard_id)
    form = PeriodicTestForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        periodic_test = form.save(commit=False)
        periodic_test.standard = standard
        periodic_test.save()
        messages.success(request, "Periodic test added.")
        return redirect("periodic_test_list", standard_id=standard.id)

    return render(request, "standard/periodic_test_form.html", {"form": form, "standard": standard})


def periodic_test_edit_view(request, periodic_test_id):
    """Handles editing a periodic test requirement."""
    periodic_test = get_object_or_404(PeriodicTest, id=periodic_test_id)
    form = PeriodicTestForm(request.POST or None, instance=periodic_test)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Periodic test updated.")
        return redirect("periodic_test_list", standard_id=periodic_test.standard.id)

    return render(request, "standard/periodic_test_form.html", {"form": form, "standard": periodic_test.standard})


def classification_list_view(request, standard_id):
    """Displays all classifications for a standard."""
    standard = get_object_or_404(Standard, id=standard_id)
    classifications = standard.classifications.all()
    return render(request, "standard/classification_list.html", {"standard": standard, "classifications": classifications})


def classification_create_view(request, standard_id):
    """Handles creating a classification requirement."""
    standard = get_object_or_404(Standard, id=standard_id)
    form = ClassificationForm(request.POST or None)

    if request.method == "POST" and form.is_valid():
        classification = form.save(commit=False)
        classification.standard = standard
        classification.save()
        messages.success(request, "Classification added.")
        return redirect("classification_list", standard_id=standard.id)

    return render(request, "standard/classification_form.html", {"form": form, "standard": standard})


def classification_edit_view(request, classification_id):
    """Handles editing a classification requirement."""
    classification = get_object_or_404(Classification, id=classification_id)
    form = ClassificationForm(request.POST or None, instance=classification)

    if request.method == "POST" and form.is_valid():
        form.save()
        messages.success(request, "Classification updated.")
        return redirect("classification_list", standard_id=classification.standard.id)

    return render(request, "standard/classification_form.html", {"form": form, "standard": classification.standard})


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
