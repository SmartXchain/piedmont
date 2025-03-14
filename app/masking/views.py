from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.db.models import Q, Max
from .models import MaskingProcess, MaskingStep
from .forms import MaskingProcessForm, MaskingStepForm
from django.http import HttpResponse
from django.template.loader import render_to_string
from weasyprint import HTML
import tempfile
from django.utils import timezone
from django.conf import settings
import os


def masking_list(request):
    """Displays a list of masking processes with search functionality."""
    search_query = request.GET.get("search", "").strip()
    masking_processes = MaskingProcess.objects.filter(is_active=True)

    if search_query:
        masking_processes = masking_processes.filter(
            Q(part_number__icontains=search_query) | Q(masking_description__icontains=search_query)
        )

    return render(request, "masking/masking_list.html", {"masking_processes": masking_processes})


def masking_process_detail(request, process_id):
    """Displays the details of a MaskingProcess, including its steps."""
    process = get_object_or_404(MaskingProcess, id=process_id)
    steps = process.masking_steps.all()
    previous_versions = MaskingProcess.objects.filter(part_number=process.part_number).exclude(id=process_id).order_by("-version")

    return render(request, "masking/masking_process_detail.html", {
        "process": process,
        "steps": steps,
        "previous_versions": previous_versions,
    })


def masking_process_form(request, process_id=None):
    """Handles both creation and editing of a MaskingProcess."""
    process = get_object_or_404(MaskingProcess, id=process_id) if process_id else None

    if request.method == "POST":
        form = MaskingProcessForm(request.POST, instance=process)
        if form.is_valid():
            form.save()
            return redirect("masking_list")
    else:
        form = MaskingProcessForm(instance=process)

    return render(request, "masking/masking_process_form.html", {"form": form})


def masking_step_list(request, process_id):
    """Displays a list of masking steps for a specific masking process."""
    process = get_object_or_404(MaskingProcess, id=process_id)
    steps = process.masking_steps.select_related("masking_process").all()
    return render(request, "masking/masking_step_list.html", {"process": process, "steps": steps})


def masking_step_form(request, process_id=None, step_id=None):
    """Handles both creation and editing of a masking step."""
    process = get_object_or_404(MaskingProcess, id=process_id) if process_id else None
    step = get_object_or_404(MaskingStep, id=step_id) if step_id else None

    if request.method == "POST":
        form = MaskingStepForm(request.POST, request.FILES, instance=step)
        if form.is_valid():
            new_step = form.save(commit=False)
            if process:
                new_step.masking_process = process
            new_step.save()
            return redirect("masking_step_list", process_id=new_step.masking_process.id)
    else:
        form = MaskingStepForm(instance=step)

    return render(request, "masking/masking_step_form.html", {"form": form, "process": process})


def masking_process_pdf_view(request, process_id):
    """Generates a PDF of the Masking Process and its steps."""
    process = get_object_or_404(MaskingProcess, id=process_id)
    steps = MaskingStep.objects.filter(masking_process=process).order_by("step_number")

    # Ensure images have absolute URLs using MEDIA_URL & MEDIA_ROOT
    step_data = []
    for step in steps:
        image_url = None
        if step.image:
            # Ensure correct MEDIA_URL path for production
            image_url = os.path.join(settings.MEDIA_ROOT, step.image.name)
            if not os.path.exists(image_url):  # Debugging
                print(f"Image NOT FOUND: {image_url}")

        step_data.append({
            "step_number": step.step_number,
            "title": step.title,
            "description": step.description,
            "image_absolute_url": image_url
        })

    # Add Company Logo
    company_logo = request.build_absolute_uri('/static/images/company_logo.png')

    # Render the template
    html_content = render_to_string(
        "masking/masking_process_pdf.html",
        {
            "process": process,
            "steps": step_data,  # Pass cleaned-up step data
            "company_logo": company_logo,
            "current_date": timezone.now().strftime("%Y-%m-%d"),
        },
        request=request
    )

    # Generate PDF
    with tempfile.NamedTemporaryFile(delete=True) as temp_file:
        HTML(string=html_content, base_url=request.build_absolute_uri()).write_pdf(temp_file.name)
        temp_file.seek(0)
        pdf_file = temp_file.read()

    # Create response
    response = HttpResponse(pdf_file, content_type="application/pdf")

    # Check if user wants to download or view
    if "download" in request.GET:
        response["Content-Disposition"] = f'attachment; filename="Masking_Process_{process.part_number}.pdf"'
    else:
        response["Content-Disposition"] = f'inline; filename="Masking_Process_{process.part_number}.pdf"'

    return response
