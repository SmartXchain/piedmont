from django.shortcuts import render, get_object_or_404, redirect
from .models import Part, PartDetails, JobDetails
from .forms import PartForm, PartDetailsForm, JobDetailsForm
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML
from django.utils import timezone
import tempfile


def part_list_view(request):
    query = request.GET.get('q', '')  # Get the search query from the URL
    if query:
        parts = Part.objects.filter(part_number__icontains=query)
    else:
        parts = Part.objects.all()
    return render(request, 'part/part_list.html', {'parts': parts, 'query': query})


def part_detail_view(request, part_id):
    part = get_object_or_404(Part, id=part_id)
    part_details = PartDetails.objects.filter(part=part).order_by('job_identity')
    job_details = JobDetails.objects.filter(part_detail__in=part_details).order_by('job_number')
    return render(request, 'part/part_detail.html', {
        'part': part,
        'part_details': part_details,
        'job_details': job_details,
    })


def part_create_view(request):
    if request.method == "POST":
        form = PartForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('part_list')
    else:
        form = PartForm()
    return render(request, 'part/part_form.html', {'form': form, 'part': None})


def part_edit_view(request, part_id):
    part = get_object_or_404(Part, id=part_id)
    if request.method == "POST":
        form = PartForm(request.POST, instance=part)
        if form.is_valid():
            form.save()
            return redirect('part_list')
    else:
        form = PartForm(instance=part)
    return render(request, 'part/part_form.html', {'form': form, 'part': part})


def partdetails_add_view(request, part_id):
    part = get_object_or_404(Part, id=part_id)
    if request.method == "POST":
        form = PartDetailsForm(request.POST)
        if form.is_valid():
            part_detail = form.save(commit=False)
            part_detail.part = part
            try:
                part_detail.save()
                return redirect('part_detail', part_id=part.id)
            except ValidationError as e:
                form.add_error(None, e.message)
    else:
        form = PartDetailsForm()
    return render(request, 'part/partdetails_form.html', {'form': form, 'part': part})


def partdetails_view_view(request, detail_id):
    detail = get_object_or_404(PartDetails, id=detail_id)
    return render(request, 'part/partdetails_view.html', {'detail': detail})


def partdetails_edit_view(request, detail_id):
    detail = get_object_or_404(PartDetails, id=detail_id)
    part = detail.part
    if request.method == "POST":
        form = PartDetailsForm(request.POST, instance=detail)
        if form.is_valid():
            form.save()
            return redirect('part_detail', part_id=part.id)
    else:
        form = PartDetailsForm(instance=detail)
    return render(request, 'part/partdetails_form.html', {'form': form, 'part': part, 'detail': detail})


def jobdetails_list_view(request, part_id):
    part = get_object_or_404(Part, id=part_id)
    jobs = JobDetails.objects.filter(part_detail__part=part)
    return render(request, 'part/jobdetails_list.html', {'part': part, 'jobs': jobs})


def jobdetails_view(request, job_id):
    job = get_object_or_404(JobDetails, id=job_id)
    part = job.part_detail.part
    return render(request, 'part/jobdetails_view.html', {'job': job, 'part': part})


def jobdetails_edit_view(request, job_id):
    job = get_object_or_404(JobDetails, id=job_id)
    part_detail = job.part_detail

    if request.method == "POST":
        form = JobDetailsForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            return redirect('part_detail', part_id=part_detail.part.id)
    else:
        form = JobDetailsForm(instance=job)

    return render(request, 'part/jobdetails_form.html', {'form': form, 'part_detail': part_detail, 'detail': job})


def jobdetails_add_view(request, part_id):
    part_detail = get_object_or_404(PartDetails, part_id=part_id)
    if request.method == "POST":
        form = JobDetailsForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.part_detail = part_detail
            job.save()
            return redirect('part_detail', part_id=part_detail.part.id)
    else:
        form = JobDetailsForm()
    return render(request, 'part/jobdetails_form.html', {'form': form, 'part_detail': part_detail})


def job_list_view(request):
    jobs = JobDetails.objects.select_related('part').all()
    return render(request, 'part/job_list.html', {'jobs': jobs})


def part_process_steps_view(request, detail_id):
    detail = get_object_or_404(PartDetails, id=detail_id)
    part = detail.part

    # Fetch process steps using the method in the Part model
    process_steps = part.get_process_steps(detail.processing_standard, detail.classification)

    if not process_steps:
        # Render no_process_steps.html with the part ID
        return render(request, 'part/no_process_steps.html', {
            'part': part,
            'message': "No steps have been added for this part based on the current standard and classification. Please contact Special Processing."
        })

    return render(request, 'part/process_steps.html', {
        'part': part,
        'process_steps': process_steps,
    })


def job_process_steps_view(request, job_id):
    job = get_object_or_404(JobDetails, id=job_id)
    process_steps = job.get_process_steps()

    if process_steps is None:
        message = "No process for the selected standard, job identity, and classification. Contact Special Processing."
        return render(request, 'part/no_process_steps.html', {'job': job, 'message': message})

    return render(request, 'part/job_process_steps.html', {'job': job, 'process_steps': process_steps})


def job_print_steps_view(request, job_id):
    job = get_object_or_404(JobDetails, id=job_id)
    process_steps = job.get_process_steps()
    inspections = job.processing_standard.inspections.all() if job.processing_standard else None
    current_date = timezone.now().strftime("%m-%d-%Y")

    # Ensure there are process steps available
    if process_steps is None:
        return HttpResponse("No process steps found for this job.", content_type="text/plain")

    # Render the template with context
    html_content = render_to_string('part/job_steps_pdf.html', {
        'job': job,
        'process_steps': process_steps,
        'inspections': inspections,
        'current_date': current_date,
        'footer_text': f"Printed on: {current_date}",
    })

    # Generate PDF and create HTTP response
    with tempfile.NamedTemporaryFile(delete=True) as temp_file:
        HTML(string=html_content).write_pdf(temp_file.name)
        temp_file.seek(0)
        pdf_file = temp_file.read()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Job_{job.job_number}_Steps.pdf"'
    return response
