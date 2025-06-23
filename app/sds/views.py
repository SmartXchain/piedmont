from django.shortcuts import render
from .models import Chemical, HazComSection


def chemical_list(request):
    chemicals = Chemical.objects.all()
    hazcom_sections = HazComSection.objects.all()
    return render(request, 'sds/chemical_list.html', {'chemicals': chemicals, 'hazcom_sections': hazcom_sections, })
