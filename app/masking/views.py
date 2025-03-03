from django.shortcuts import render, get_object_or_404, redirect
from django.urls import reverse_lazy
from django.db.models import Q
from .models import MaskingProcess, MaskingStep
from .forms import MaskingProcessForm, MaskingStepForm


def masking_list(request):
    """Displays a list of masking processes with search functionality."""
    search_query = request.GET.get("search", "").strip()
    masking_processes = MaskingProcess.objects.all()

    if search_query:
        masking_processes = masking_processes.filter(
            Q(part_number__icontains=search_query) | Q(part_number_masking_description__icontains=search_query)
        )

    return render(request, "masking/masking_list.html", {"masking_processes": masking_processes})


def masking_process_detail(request, process_id):
    """Displays the details of a MaskingProcess, including its steps."""
    process = get_object_or_404(MaskingProcess, id=process_id)
    steps = process.masking_steps.all()
    return render(request, "masking_process_detail.html", {"process": process, "steps": steps})


def masking_process_form(request, process_id=None):
    """Handles both creation and editing of a MaskingProcess."""
    process = get_object_or_404(MaskingProcess, id=process_id) if process_id else None

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
    steps = process.masking_steps.select_related("masking_process").all()
    return render(request, "masking_step_list.html", {"process": process, "steps": steps})


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

    return render(request, "masking_step_form.html", {"form": form, "process": process})


def masking_step_delete(request, step_id):
    """Handles deletion of a masking step."""
    step = get_object_or_404(MaskingStep, id=step_id)
    process_id = step.masking_process.id

    if request.method == "POST":
        step.delete()
        return redirect("masking_step_list", process_id=process_id)

    return render(request, "masking_step_confirm_delete.html", {"step": step})
