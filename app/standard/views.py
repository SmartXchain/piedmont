from django.shortcuts import render, redirect, get_object_or_404
from .models import create_standard, list_standards, get_standard_by_id, Standard
from django.http import HttpResponse
from .forms import get_standard_form, InspectionRequirementFormSet

def standard_list_view(request):
    standards = list_standards()
    return render(request, 'standard/standard_list.html', {'standards': standards})

def standard_detail_view(request, standard_id):
    standard = get_standard_by_id(standard_id)
    inspections = standard.inspections.all()
    return render(request, 'standard/standard_detail.html', {'standard': standard, 'inspections': inspections})

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

