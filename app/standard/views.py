from django.shortcuts import render, redirect, get_object_or_404
from .models import list_standards, get_standard_by_id, PeriodicTest, Standard, InspectionRequirement
from .forms import get_standard_form, PeriodicTestForm, InspectionRequirementFormSet, InspectionRequirementForm
from .forms import ClassificationForm
from .models import Classification

def standard_list_view(request):
    standards = list_standards()
    return render(request, 'standard/standard_list.html', {'standards': standards})

def standard_detail_view(request, standard_id):
    standard = get_standard_by_id(standard_id)
    inspections = standard.inspections.all()
    classifications = standard.classifications.all() 
    return render(request, 'standard/standard_detail.html', {
        'standard': standard,
        'inspections': inspections,
        'classifications': classifications,
        })

def standard_create_view(request):
    form = get_standard_form(data=request.POST or None, files=request.FILES or None)
    if request.method == "POST" and form.is_valid():
        data = form.cleaned_data
        Standard.objects.create(
            name=data['name'],
            description=data['description'],
            revision=data['revision'],
            author=data['author'],
            upload_file=data['upload_file'],
        )
        return redirect('standard_list')
    return render(request, 'standard/standard_form.html', {'form': form, 'edit': False})

def standard_edit_view(request, standard_id):
    standard = get_object_or_404(Standard, id=standard_id)
    form = get_standard_form(data=request.POST or None, files=request.FILES or None, instance=standard)
    formset = InspectionRequirementFormSet(instance=standard)

    if request.method == "POST" and form.is_valid() and formset.is_valid():
        form.save()
        formset.save()
        return redirect('standard_detail', standard_id=standard.id)

    return render(request, 'standard/standard_form.html', {'form': form, 'formset': formset, 'edit': True})

def inspection_list_view(request, standard_id):
    standard = get_object_or_404(Standard, id=standard_id)
    inspections = standard.inspections.all()
    return render(request, 'standard/inspection_list.html', {'standard': standard, 'inspections': inspections})

def inspection_create_view(request, standard_id):
    standard = get_object_or_404(Standard, id=standard_id)
    if request.method == "POST":
        form = InspectionRequirementForm(request.POST)
        if form.is_valid():
            inspection = form.save(commit=False)
            inspection.standard = standard
            inspection.save()
            return redirect('inspection_list', standard_id=standard.id)
    else:
        form = InspectionRequirementForm()
    return render(request, 'standard/inspection_form.html', {'form': form, 'standard': standard})

def inspection_edit_view(request, inspection_id):
    inspection = get_object_or_404(InspectionRequirement, id=inspection_id)
    if request.method == "POST":
        form = InspectionRequirementForm(request.POST, instance=inspection)
        if form.is_valid():
            form.save()
            return redirect('inspection_list', standard_id=inspection.standard.id)
    else:
        form = InspectionRequirementForm(instance=inspection)
    return render(request, 'standard/inspection_form.html', {'form': form, 'standard': inspection.standard})

def periodic_test_list_view(request, standard_id):
    standard = get_object_or_404(Standard, id=standard_id)
    periodic_tests = standard.periodic_tests.all()
    return render(request, 'standard/periodic_test_list.html', {'standard': standard, 'periodic_tests': periodic_tests})

def periodic_test_create_view(request, standard_id):
    standard = get_object_or_404(Standard, id=standard_id)
    if request.method == "POST":
        form = PeriodicTestForm(request.POST)
        if form.is_valid():
            periodic_test = form.save(commit=False)
            periodic_test.standard = standard
            periodic_test.save()
            return redirect('periodic_test_list', standard_id=standard.id)
    else:
        form = PeriodicTestForm()
    return render(request, 'standard/periodic_test_form.html', {'form': form, 'standard': standard})

def periodic_test_edit_view(request, periodic_test_id):
    periodic_test = get_object_or_404(PeriodicTest, id=periodic_test_id)
    if request.method == "POST":
        form = PeriodicTestForm(request.POST, instance=periodic_test)
        if form.is_valid():
            form.save()
            return redirect('periodic_test_list', standard_id=periodic_test.standard.id)
    else:
        form = PeriodicTestForm(instance=periodic_test)
    return render(request, 'standard/periodic_test_form.html', {'form': form, 'standard': periodic_test.standard})

def classification_list_view(request, standard_id):
    standard = get_object_or_404(Standard, id=standard_id)
    classifications = standard.classifications.all()
    return render(request, 'standard/classification_list.html', {'standard': standard, 'classifications': classifications})

def classification_create_view(request, standard_id):
    standard = get_object_or_404(Standard, id=standard_id)
    if request.method == "POST":
        form = ClassificationForm(request.POST)
        if form.is_valid():
            classification = form.save(commit=False)
            classification.standard = standard
            classification.save()
            return redirect('classification_list', standard_id=standard.id)
    else:
        form = ClassificationForm()
    return render(request, 'standard/classification_form.html', {'form': form, 'standard': standard})

def classification_edit_view(request, classification_id):
    classification = get_object_or_404(Classification, id=classification_id)
    if request.method == "POST":
        form = ClassificationForm(request.POST, instance=classification)
        if form.is_valid():
            form.save()
            return redirect('classification_list', standard_id=classification.standard.id)
    else:
        form = ClassificationForm(instance=classification)
    return render(request, 'standard/classification_form.html', {'form': form, 'standard': classification.standard})