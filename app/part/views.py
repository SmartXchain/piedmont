from django.shortcuts import render, get_object_or_404, redirect
from .models import Part, PartDetails, JobDetails
from .forms import PartForm, PartDetailsForm, JobDetailsForm
from django.core.exceptions import ValidationError
from django.template.loader import render_to_string
from django.http import HttpResponse
from weasyprint import HTML
from django.utils import timezone
import tempfile
from process.models import Process
from methods.models import ParameterToBeRecorded


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
    part = part_detail.part

    if request.method == "POST":
        form = JobDetailsForm(request.POST, instance=job)
        if form.is_valid():
            try:
                job = form.save()
                job.clean()
                job.save()
                return redirect('part_detail', part_id=part.id)
            except ValidationError as e:
                form.add_error(None, str(e))
    else:
        form = JobDetailsForm(instance=job)

    return render(request, 'part/jobdetails_form.html', {'form': form, 'part_id': part.id if part else None, 'job': job})


def jobdetails_add_view(request, part_id):
    part = get_object_or_404(PartDetails, id=part_id)

    if request.method == "POST":
        form = JobDetailsForm(request.POST)
        form.fields['part_detail'].queryset = PartDetails.objects.filter(part_id=part_id)
        if form.is_valid():
            try:
                job = form.save()
                job.clean()
                job.save()
                return redirect('part_detail', part_id=part.part.id)
            except ValidationError as e:
                form.add_error(None, str(e))
    else:
        form = JobDetailsForm()
        form.fields['part_detail'].queryset = PartDetails.objects.filter(part_id=part_id)

    return render(request, 'part/jobdetails_form.html', {'form': form, 'part_id': part_id})


def part_process_steps_view(request, detail_id):

    detail = get_object_or_404(PartDetails, id=detail_id)
    part = detail.part
    process = Process.objects.filter(
        standard=detail.processing_standard,
        classification=detail.classification
    ).first()

    # Debug: Check if process is found
    if process:
        print(f"Process Found: {process}")
        process_steps = process.steps.all()
        print(f"Number of Steps Found: {process_steps.count()}")
    else:
        print("No Process Found")
        process_steps = None

    # Handle case where no steps are found
    if not process_steps or process_steps.count() == 0:
        return render(request, 'part/no_process_steps.html', {
            'part': part,
            'message': "No steps have been added for this part based on the current standard and classification. Please contact Special Processing."
        })

    return render(request, 'part/process_steps.html', {
        'part': part,
        'process_steps': process_steps,
        'detail': detail,
    })


def job_process_steps_view(request, job_id):
    # Fetch the job
    job = get_object_or_404(JobDetails, id=job_id)

    # Fetch the process linked to the job's processing standard and classification
    process = Process.objects.filter(
        standard=job.processing_standard,
        classification=job.classification
    ).first()

    # Debugging information
    if process:
        print(f"Process Found: {process}")
        process_steps = process.steps.all()
        print(f"Number of Steps Found: {process_steps.count()}")
    else:
        print("No Process Found")
        process_steps = None

    # If no steps are found, render the no_process_steps.html template
    if not process_steps or process_steps.count() == 0:
        return render(request, 'part/no_process_steps.html', {
            'job': job,
            'message': "No process steps found for this job's standard and classification. Contact Special Processing."
        })

    # Render process steps template if steps are found
    return render(request, 'part/job_process_steps.html', {
        'job': job,
        'process_steps': process_steps,
    })


def job_print_steps_view(request, job_id):
    job = get_object_or_404(JobDetails, id=job_id)
    process_steps = job.get_process_steps()
    inspections = job.processing_standard.inspections.all() if job.processing_standard else None
    current_date = timezone.now().strftime("%m-%d-%Y")
    # Fetch parameters for each method in process steps
    for step in process_steps:
        step.parameters = ParameterToBeRecorded.objects.filter(method=step.method)

    # Pre-compute amps and instructions based on job identity
    job_data = {
        "surface_area": job.surface_area,
        "amps": job.amps,
        "current_density": job.current_density,
        "instructions": [],
        "is_chrome_or_cadmium": job.part_detail.job_identity in ['chrome_plate', 'cadmium_plate']
    }

    if job.part_detail.job_identity == 'chrome_plate':
        if job.surface_area:
            amps = job.surface_area * job.current_density
            job_data["amps"] = amps
            job_data["instructions"] = [
                f"Reverse Etch at {amps:.2f} amps for 60 - 90 seconds.",
                f"Strike Plate at {amps * 2:.2f} amps for the 60 - 90 seconds.",
                f"Plate at {amps:.2f} amps for the required mils, using a plating rate of 1 mil per hour.",
                "_",
                "_",
                "Date and time of start of the plating: _____________________________________________",
                "",
                "Date and time of completion of the plating: ________________________________________"
            ]
    elif job.part_detail.job_identity == 'cadmium_plate':
        if job.surface_area:
            amps = job.surface_area / 144 * job.current_density
            job_data["amps"] = amps
            job_data["instructions"] = [
                f"Strike at {amps:.2f} amps for 60 to 90 seconds.",
                f"Plate at {amps:.2f} amps for 10 minutes.",
                f"Re-rack the part and continue plating at {amps:.2f} amps for an additional 10 minutes."
            ]
    else:
        job_data["instructions"] = ["See Process Engineer for further processing."]

    # Ensure there are process steps available
    if not process_steps:
        return HttpResponse("No process steps found for this job.", content_type="text/plain")

    # Render the template with precomputed context
    html_content = render_to_string('part/job_steps_pdf.html', {
        'job': job,
        'process_steps': process_steps,
        'inspections': inspections,
        'current_date': current_date,
        'footer_text': f"Printed on: {current_date}",
        'job_data': job_data
    })

    # Generate PDF and create HTTP response
    with tempfile.NamedTemporaryFile(delete=True) as temp_file:
        HTML(string=html_content).write_pdf(temp_file.name)
        temp_file.seek(0)
        pdf_file = temp_file.read()

    response = HttpResponse(pdf_file, content_type='application/pdf')
    response['Content-Disposition'] = f'inline; filename="Job_{job.job_number}_Steps.pdf"'
    return response
