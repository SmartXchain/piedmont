from django.shortcuts import render, get_object_or_404, redirect
from .models import Process
from .forms import ProcessForm
from standard.models import Standard

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
