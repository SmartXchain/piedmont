from django.shortcuts import render, get_object_or_404, redirect
from .models import Process, ProcessStep
from .forms import ProcessForm, ProcessStepForm
from django.db import transaction

def process_list_view(request):
    processes = Process.objects.all()
    return render(request, 'process/process_list.html', {'processes': processes})

def process_create_view(request):
    if request.method == "POST":
        form = ProcessForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('process_list')
    else:
        form = ProcessForm()
    return render(request, 'process/process_form.html', {'form': form})

def process_edit_view(request, process_id):
    process = get_object_or_404(Process, id=process_id)
    if request.method == "POST":
        form = ProcessForm(request.POST, instance=process)
        if form.is_valid():
            form.save()
            return redirect('process_list')
    else:
        form = ProcessForm(instance=process)
    return render(request, 'process/process_form.html', {'form': form, 'process': process})

def process_step_list_view(request, process_id):
    process = get_object_or_404(Process, id=process_id)
    steps = process.steps.all()  # Fetch all steps for the process
    return render(request, 'process/process_step_list.html', {'process': process, 'steps': steps})

def process_step_add_view(request, process_id):
    process = get_object_or_404(Process, id=process_id)
    if request.method == "POST":
        form = ProcessStepForm(request.POST)
        if form.is_valid():
            step = form.save(commit=False)
            step.process = process
            # Auto-increment step number
            step.step_number = process.steps.count() + 1
            step.save()
            return redirect('process_step_list', process_id=process.id)
    else:
        form = ProcessStepForm()
    return render(request, 'process/process_step_form.html', {'form': form, 'process': process})


def process_step_edit_view(request, step_id):
    step = get_object_or_404(ProcessStep, id=step_id)
    process = step.process
    if request.method == "POST":
        form = ProcessStepForm(request.POST, instance=step)
        if form.is_valid():
            form.save()
            return redirect('process_step_list', process_id=process.id)
    else:
        form = ProcessStepForm(instance=step)
    return render(request, 'process/process_step_form.html', {'form': form, 'process': process, 'step': step})


def process_step_delete_view(request, step_id):
    step = get_object_or_404(ProcessStep, id=step_id)
    process = step.process

    # Delete the step
    step.delete()

    # Renumber remaining steps for the process
    with transaction.atomic():
        steps = process.steps.order_by('step_number')
        for i, step in enumerate(steps, start=1):
            step.step_number = i
            step.save()

    return redirect('process_step_list', process_id=process.id)

def process_steps_view(request, process_id):
    process = get_object_or_404(Process, id=process_id)
    steps = process.steps.all()  # Fetch all steps linked to this process
    return render(request, 'process/process_steps.html', {'process': process, 'steps': steps})
