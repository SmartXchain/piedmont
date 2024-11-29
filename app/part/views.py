from django.shortcuts import render, get_object_or_404, redirect
from .models import Part, PartDetails, JobDetails
from .forms import PartForm, PartDetailsForm, JobDetailsForm

def part_list_view(request):
    parts = Part.objects.all()
    return render(request, 'part/part_list.html', {'parts': parts})

def part_detail_view(request, part_id):
    part = get_object_or_404(Part, id=part_id)
    part_details = PartDetails.objects.filter(part=part)
    job_details = part.job_details.all() 
    return render(request, 'part/part_detail.html', {
        'part': part,
        'part_details': part_details,
        'job_details': job_details,
    })

def part_create_view(request):
    if request.method == "POST":
        part_form = PartForm(request.POST)
        details_form = PartDetailsForm(request.POST)
        if part_form.is_valid() and details_form.is_valid():
            part = part_form.save()
            details = details_form.save(commit=False)
            details.part = part
            details.save()
            return redirect('part_list')
    else:
        part_form = PartForm()
        details_form = PartDetailsForm()
    return render(request, 'part/part_form.html', {'part_form': part_form, 'details_form': details_form})

def part_edit_view(request, part_id):
    part = get_object_or_404(Part, id=part_id)
    details, created = PartDetails.objects.get_or_create(part=part)
    if request.method == "POST":
        part_form = PartForm(request.POST, instance=part)
        details_form = PartDetailsForm(request.POST, instance=details)
        if part_form.is_valid() and details_form.is_valid():
            part_form.save()
            details_form.save()
            return redirect('part_detail', part_id=part.id)
    else:
        part_form = PartForm(instance=part)
        details_form = PartDetailsForm(instance=details)
    return render(request, 'part/part_form.html', {'part_form': part_form, 'details_form': details_form, 'edit': True})

def job_details_create_view(request, part_id):
    part = get_object_or_404(Part, id=part_id)
    if request.method == "POST":
        form = JobDetailsForm(request.POST)
        if form.is_valid():
            job_details = form.save(commit=False)
            job_details.part = part
            job_details.save()
            return redirect('part_detail', part_id=part.id)
    else:
        form = JobDetailsForm()
    return render(request, 'part/job_details_form.html', {'form': form, 'part': part})

def job_list_view(request):
    jobs = JobDetails.objects.select_related('part').all()  # Prefetch part details
    return render(request, 'part/job_list.html', {'jobs': jobs})


def job_detail_view(request, job_id):
    job = get_object_or_404(JobDetails, id=job_id)
    return render(request, 'part/job_detail.html', {'job': job})


def job_create_view(request):
    part_id = request.GET.get('part_id')  # Fetch part_id from query parameters
    part = None
    if part_id:
        part = get_object_or_404(Part, id=part_id)

    if request.method == "POST":
        form = JobDetailsForm(request.POST)
        if form.is_valid():
            job_details = form.save(commit=False)
            if part:  # Ensure the part is set if provided
                job_details.part = part
            job_details.save()
            return redirect('part_detail', part_id=job_details.part.id)
    else:
        form = JobDetailsForm()
    
    return render(request, 'part/job_form.html', {'form': form, 'part': part})


def job_edit_view(request, job_id):
    job = get_object_or_404(JobDetails, id=job_id)
    if request.method == "POST":
        form = JobDetailsForm(request.POST, instance=job)
        if form.is_valid():
            form.save()
            return redirect('job_detail', job_id=job.id)
    else:
        form = JobDetailsForm(instance=job)
    return render(request, 'part/job_form.html', {'form': form, 'job': job})

def partdetails_add_view(request, part_id):
    part = get_object_or_404(Part, id=part_id)
    if request.method == "POST":
        form = PartDetailsForm(request.POST)
        if form.is_valid():
            details = form.save(commit=False)
            details.part = part
            details.save()
            return redirect('part_detail', part_id=part.id)  # Redirect to part detail
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