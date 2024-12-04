from django import forms
from .models import Process, ProcessStep


class ProcessForm(forms.ModelForm):
    class Meta:
        model = Process
        fields = ['standard', 'classification', 'description']
        widgets = {
            'standard': forms.Select(attrs={'class': 'form-control'}),
            'classification': forms.Select(attrs={'class': 'form-control'}),
            'description': forms.Textarea(attrs={'class': 'form-control'}),
        }


class ProcessStepForm(forms.ModelForm):
    class Meta:
        model = ProcessStep
        fields = ['method']
        widgets = {
            'method': forms.Select(attrs={'class': 'form-control'}),
        }
