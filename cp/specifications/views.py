from django.shortcuts import render, redirect
from .forms import SpecificationForm, StepFormSet
from .models import Specification
from django.shortcuts import render, redirect, get_object_or_404
from .models import Specification
from .forms import SpecificationForm

def create_specification(request):
    if request.method == 'POST':
        form = SpecificationForm(request.POST)
        formset = StepFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            specification = form.save()
            steps = formset.save(commit=False)
            for step in steps:
                step.specification = specification
                step.save()
            return redirect('list_specifications')
    else:
        form = SpecificationForm()
        formset = StepFormSet()

    return render(request, 'specifications/create_specification.html', {'form': form, 'formset': formset})

# View to list all specifications
def list_specifications(request):
    specifications = Specification.objects.all()
    return render(request, 'specifications/list_specifications.html', {'specifications': specifications})

def add_specification(request):
    if request.method == 'POST':
        form = SpecificationForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('list_specifications')
    else:
        form = SpecificationForm()

    return render(request, 'specifications/add_specification.html', {'form': form})

def edit_specification(request, specification_id):
    specification = get_object_or_404(Specification, pk=specification_id)
    if request.method == 'POST':
        form = SpecificationForm(request.POST, instance=specification)
        if form.is_valid():
            form.save()
            return redirect('list_specifications')
    else:
        form = SpecificationForm(instance=specification)

    return render(request, 'specifications/edit_specification.html', {'form': form, 'specification': specification})

