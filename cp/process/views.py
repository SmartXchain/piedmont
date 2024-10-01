from django.shortcuts import render, redirect
from django.urls import reverse
from .models import TechnicalSheet, Step
from .forms import TechnicalSheetForm

def create_technical_sheet(request):
    if request.method == 'POST':
        form = TechnicalSheetForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect(reverse('list_technical_sheets'))
    else:
        form = TechnicalSheetForm()

    return render(request, 'process/create_technical_sheet.html', {'form': form})

from django.shortcuts import render, redirect
from django.forms import modelformset_factory

def select_rework_steps(request, technical_sheet_id):
    technical_sheet = TechnicalSheet.objects.get(pk=technical_sheet_id)
    StepFormSet = modelformset_factory(Step, fields=('name', 'description', 'is_optional'), extra=0)
    if request.method == 'POST':
        formset = StepFormSet(request.POST, queryset=technical_sheet.specifications.all())
        if formset.is_valid():
            # Process the selected steps
            # For simplicity, just save to technical sheet
            for form in formset:
                if form.cleaned_data['is_optional']:
                    form.save()
            return redirect('list_technical_sheets')
    else:
        formset = StepFormSet(queryset=technical_sheet.specifications.all())

    return render(request, 'process/select_rework_steps.html', {'formset': formset, 'technical_sheet': technical_sheet})

def list_technical_sheets(request):
    technical_sheets = TechnicalSheet.objects.all()
    return render(request, 'process/list_technical_sheets.html', {'technical_sheets': technical_sheets})