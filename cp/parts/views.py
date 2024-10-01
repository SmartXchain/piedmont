from django.shortcuts import render
from .models import Part

def list_parts(request):
    parts = Part.objects.all()
    return render(request, 'parts/list_parts.html', {'parts': parts})

# View to list all parts that have instructions
def list_parts_with_instructions(request):
    parts_with_instructions = TechnicalSheet.objects.values_list('part', flat=True).distinct()
    parts = Part.objects.filter(id__in=parts_with_instructions)
    return render(request, 'list_parts.html', {'parts': parts})

from django.shortcuts import render, redirect
from .models import Part
from .forms import PartForm

def add_part(request):
    if request.method == 'POST':
        form = PartForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('list_parts')
    else:
        form = PartForm()

    return render(request, 'parts/add_part.html', {'form': form})

from django.shortcuts import render, redirect, get_object_or_404
from .models import Part
from .forms import PartForm

def edit_part(request, part_id):
    part = get_object_or_404(Part, pk=part_id)
    if request.method == 'POST':
        form = PartForm(request.POST, instance=part)
        if form.is_valid():
            form.save()
            return redirect('list_parts')
    else:
        form = PartForm(instance=part)

    return render(request, 'parts/edit_part.html', {'form': form, 'part': part})

