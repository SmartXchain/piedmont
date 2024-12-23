from django import forms
from django.forms import inlineformset_factory
from .models import Standard, InspectionRequirement, PeriodicTest, Classification


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
        if instance.upload_file:
            initial['upload_file'] = instance.upload_file

    return StandardForm(data=data, files=files, initial=initial)


InspectionRequirementFormSet = inlineformset_factory(
    Standard,
    InspectionRequirement,
    fields=['name', 'description'],
    extra=1,
    widgets={
        'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter inspection name'}),
        'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter description'}),
    }
)


class InspectionRequirementForm(forms.ModelForm):
    class Meta:
        model = InspectionRequirement
        fields = ['name', 'description']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter inspection name'}),
            'description': forms.Textarea(attrs={'class': 'form-control', 'rows': 4, 'placeholder': 'Enter description'}),
        }


class PeriodicTestForm(forms.ModelForm):
    class Meta:
        model = PeriodicTest
        fields = [
            'name',
            'time_period',
            'specification',
            'number_of_specimens',
            'material',
            'dimensions',
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter test name'}),
            'time_period': forms.Select(attrs={'class': 'form-control'}),
            'specification': forms.Textarea(attrs={'class': 'form-control', 'rows': 3, 'placeholder': 'Enter specification'}),
            'number_of_specimens': forms.NumberInput(attrs={'class': 'form-control', 'placeholder': 'Enter number of specimens'}),
            'material': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter material'}),
            'dimensions': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter dimensions'}),
        }


class ClassificationForm(forms.ModelForm):
    class Meta:
        model = Classification
        fields = [
            'method',
            'method_description',
            'class_name',
            'class_description',
            'type',
            'type_description',
        ]
        widgets = {
            'method': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter method'}),
            'method_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Enter method description'}),
            'class_name': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter class'}),
            'class_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Enter class description'}),
            'type': forms.TextInput(attrs={'class': 'form-control', 'placeholder': 'Enter type'}),
            'type_description': forms.Textarea(attrs={'class': 'form-control', 'rows': 2, 'placeholder': 'Enter type description'}),
        }
