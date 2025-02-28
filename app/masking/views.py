from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse
from .models import MaskingProcess, MaskingStep
from .forms import MaskingProcessForm, MaskingStepForm

def masking_list(request):
    """Displays a list of masking processes with search functionality."""
    search_query = request.GET.get("search", "").strip()
    masking_processes = MaskingProcess.objects.all()
    
    if search_query:
        masking_processes = masking_processes.filter(
            models.Q(part_number__icontains=search_query) |
            models.Q(part_number_masking_description__icontains=search_query)
        )
    return render(request, "masking/masking_list.html", {"masking_processes": masking_processes})

def masking_process_detail(request, process_id):
    """Displays the details of a MaskingProcess including its steps."""
    process = get_object_or_404(MaskingProcess, id=process_id)
    steps = process.masking_steps.all()
    return render(request, "masking_process_detail.html", {"process": process, "steps": steps})

def masking_process_create(request):
    """Handles creation of a new MaskingProcess."""
    if request.method == "POST":
        form = MaskingProcessForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("masking_process_list")
    else:
        form = MaskingProcessForm()
    return render(request, "masking_process_form.html", {"form": form})

def masking_process_edit(request, process_id):
    """Handles editing of a MaskingProcess."""
    process = get_object_or_404(MaskingProcess, id=process_id)
    if request.method == "POST":
        form = MaskingProcessForm(request.POST, instance=process)
        if form.is_valid():
            form.save()
            return redirect("masking_process_list")
    else:
        form = MaskingProcessForm(instance=process)
    return render(request, "masking_process_form.html", {"form": form})

def masking_process_delete(request, process_id):
    """Handles deletion of a MaskingProcess."""
    process = get_object_or_404(MaskingProcess, id=process_id)
    if request.method == "POST":
        process.delete()
        return redirect("masking_process_list")
    return render(request, "masking_process_confirm_delete.html", {"process": process})


def masking_step_list(request, process_id):
    """Displays a list of masking steps for a specific masking process."""
    process = get_object_or_404(MaskingProcess, id=process_id)
    steps = process.masking_steps.all()
    return render(request, "masking_step_list.html", {"process": process, "steps": steps})

def masking_step_create(request, process_id):
    """Handles creation of a new masking step."""
    process = get_object_or_404(MaskingProcess, id=process_id)
    if request.method == "POST":
        form = MaskingStepForm(request.POST, request.FILES)
        if form.is_valid():
            step = form.save(commit=False)
            step.masking_process = process
            step.save()
            return redirect("masking_step_list", process_id=process.id)
    else:
        form = MaskingStepForm()
    return render(request, "masking_step_form.html", {"form": form, "process": process})

def masking_step_edit(request, step_id):
    """Handles editing of a masking step."""
    step = get_object_or_404(MaskingStep, id=step_id)
    if request.method == "POST":
        form = MaskingStepForm(request.POST, request.FILES, instance=step)
        if form.is_valid():
            form.save()
            return redirect("masking_step_list", process_id=step.masking_process.id)
    else:
        form = MaskingStepForm(instance=step)
    return render(request, "masking_step_form.html", {"form": form, "process": step.masking_process})

def masking_step_delete(request, step_id):
    """Handles deletion of a masking step."""
    step = get_object_or_404(MaskingStep, id=step_id)
    process_id = step.masking_process.id
    if request.method == "POST":
        step.delete()
        return redirect("masking_step_list", process_id=process_id)
    return render(request, "masking_step_confirm_delete.html", {"step": step})
