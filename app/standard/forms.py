from django import forms
from django.forms import inlineformset_factory
from .models import Standard, InspectionRequirement

def get_standard_form(data=None, files=None, instance=None):
    """Creates a form for Standard, with optional instance support for editing."""

    # Define the Standard form dynamically
    class StandardForm(forms.Form):
        name = forms.CharField(
            max_length=255,
            widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter standard name'}),
        )
        description = forms.CharField(
            widget=forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter description'}),
        )
        revision = forms.CharField(
            max_length=50,
            widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter revision'}),
        )
        author = forms.CharField(
            max_length=255,
            widget=forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter author name'}),
        )
        upload_file = forms.FileField(
            required=False,
            widget=forms.ClearableFileInput(attrs={'class': 'form-control'}),
        )

    # Initialize with instance data if provided
    initial = {}
    if instance:
        initial = {
            'name': instance.name,
            'description': instance.description,
            'revision': instance.revision,
            'author': instance.author,
        }

    return StandardForm(data=data, files=files, initial=initial)

InspectionRequirementFormSet = inlineformset_factory(
    Standard,
    InspectionRequirement,
    fields=['name', 'description'],
    extra=1,
    widgets={
        'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter inspection name'}),
        'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Enter description'}),
    }
)
