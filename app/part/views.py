from django.shortcuts import render, get_object_or_404, redirect
from .models import Part, PartDetails, JobDetails
from .forms import PartForm, PartDetailsForm, JobDetailsForm

def part_list_view(request):
    parts = Part.objects.all()
    return render(request, 'part/part_list.html', {'parts': parts})


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
    return render(request, 'part/part_form.html', {'form': form, 'part': None})  # Pass 'part': None for creation


def part_edit_view(request, part_id):
    part = get_object_or_404(Part, id=part_id)  # Get the selected Part
    if request.method == "POST":
        form = PartForm(request.POST, instance=part)  # Bind form to existing Part
        if form.is_valid():
            form.save()
            return redirect('part_list')  # Redirect back to part list after saving
    else:
        form = PartForm(instance=part)  # Prepopulate form with Part data
    return render(request, 'part/part_form.html', {'form': form, 'part': part})


def partdetails_add_view(request, part_id):
    part = get_object_or_404(Part, id=part_id)
    if request.method == "POST":
        form = PartDetailsForm(request.POST)
        if form.is_valid():
            detail = form.save(commit=False)
            detail.part = part
            detail.save()
            return redirect('part_detail', part_id=part.id)
    else:
        form = PartDetailsForm()
    return render(request, 'part/partdetails_form.html', {'form': form, 'part': part})

def partdetails_view_view(request, detail_id):
    detail = get_object_or_404(PartDetails, id=detail_id)
    return render(request, 'part/partdetails_view.html', {'detail': detail})

def partdetails_edit_view(request, detail_id):
    detail = get_object_or_404(PartDetails, id=detail_id)
    part = detail.part  # Retrieve the associated part
    if request.method == "POST":
        form = PartDetailsForm(request.POST, instance=detail)
        if form.is_valid():
            form.save()
            return redirect('part_detail', part_id=part.id)  # Redirect to part detail
    else:
        form = PartDetailsForm(instance=detail)
    return render(request, 'part/partdetails_form.html', {'form': form, 'part': part, 'detail': detail})

def jobdetails_list_view(request, part_id):
    part = get_object_or_404(Part, id=part_id)
    jobs = JobDetails.objects.filter(part_detail__part=part)
    return render(request, 'part/jobdetails_list.html', {'part': part, 'jobs': jobs})

def jobdetails_view(request, job_id):
    job = get_object_or_404(JobDetails, id=job_id)
    part = job.part_detail.part  # Get the associated Part
    return render(request, 'part/jobdetails_view.html', {'job': job, 'part': part})

def jobdetails_edit_view(request, job_id):
    job = get_object_or_404(JobDetails, id=job_id)
    part = job.part_detail.part  # Get the associated Part
    if request.method == "POST":
        form = JobDetailsForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            return redirect('part_detail', part_id=part.id)
    else:
        form = JobDetailsForm(instance=job)
    return render(request, 'part/jobdetails_form.html', {'form': form, 'part': part, 'job': job})

def jobdetails_add_view(request, part_id):
    # Get the selected part
    part_detail = get_object_or_404(PartDetails, id=part_id)

    if request.method == "POST":
        form = JobDetailsForm(request.POST)
        if form.is_valid():
            job = form.save(commit=False)
            job.part_detail = part_detail
            job.save()
            return redirect('jobdetails_list', part_id=part_id)
    else:
        form = JobDetailsForm()
    return render(request, 'part/jobdetails_form.html', {'form': form, 'part_detail': part_detail})

def job_list_view(request):
    jobs = JobDetails.objects.select_related('part').all()  # Prefetch part details
    return render(request, 'part/job_list.html', {'jobs': jobs})

def part_process_steps_view(request, detail_id):
    part_detail = get_object_or_404(PartDetails, id=detail_id)
    process_steps = part_detail.get_process_steps()  # Retrieve process steps for the part detail
    
    if process_steps is None:
        message = "No process for the current standard and/or classification. Contact Special Processing."
        return render(request, 'part/no_process_steps.html', {'part_detail': part_detail, 'message': message})

    
    return render(request, 'part/part_process_steps.html', {
        'part_detail': part_detail,
        'process_steps': process_steps,
    })

def job_process_steps_view(request, job_id):
    job = get_object_or_404(JobDetails, id=job_id)
    process_steps = job.get_process_steps()

    if not process_steps:
        message = "No process for the selected standard and classification. Contact Special Processing."
        return render(request, 'part/no_process_steps.html', {'job': job, 'message': message})

    return render(request, 'part/job_process_steps.html', {'job': job, 'process_steps': process_steps})