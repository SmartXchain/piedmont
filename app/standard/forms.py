from django import forms
from .models import Standard, InspectionRequirement, PeriodicTest, Classification, StandardRevisionNotification

class StandardForm(forms.ModelForm):
    """Form to create and edit Standards with revision tracking."""

    class Meta:
        model = Standard
        fields = ["name", "description", "revision", "author", "upload_file"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3}),
            "revision": forms.TextInput(attrs={"class": "form-control"}),
            "author": forms.TextInput(attrs={"class": "form-control"}),
            "upload_file": forms.ClearableFileInput(attrs={"class": "form-control"}),
        }

    def clean(self):
        """Ensure revision updates create a new entry instead of modifying the existing one."""
        cleaned_data = super().clean()
        name = cleaned_data.get("name")
        revision = cleaned_data.get("revision")

        # Check if a standard with the same name and revision already exists
        if Standard.objects.filter(name=name, revision=revision).exists():
            raise forms.ValidationError("A standard with this name and revision already exists. Choose a new revision number.")

        return cleaned_data


class InspectionRequirementForm(forms.ModelForm):
    """Form for adding/editing Inspection Requirements."""

    class Meta:
        model = InspectionRequirement
        fields = ["name", "description"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter inspection name"}),
            "description": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Enter description"}),
        }


class PeriodicTestForm(forms.ModelForm):
    """Form for adding/editing Periodic Testing requirements."""

    class Meta:
        model = PeriodicTest
        fields = ["name", "time_period", "specification", "number_of_specimens", "material", "dimensions"]
        widgets = {
            "name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter test name"}),
            "time_period": forms.Select(attrs={"class": "form-control"}),
            "specification": forms.Textarea(attrs={"class": "form-control", "rows": 3, "placeholder": "Enter specification"}),
            "number_of_specimens": forms.NumberInput(attrs={"class": "form-control"}),
            "material": forms.TextInput(attrs={"class": "form-control"}),
            "dimensions": forms.TextInput(attrs={"class": "form-control"}),
        }


class ClassificationForm(forms.ModelForm):
    """Form for adding/editing Classifications linked to a Standard."""

    class Meta:
        model = Classification
        fields = ["method", "method_description", "class_name", "class_description", "type", "type_description"]
        widgets = {
            "method": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter method"}),
            "method_description": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Enter method description"}),
            "class_name": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter class"}),
            "class_description": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Enter class description"}),
            "type": forms.TextInput(attrs={"class": "form-control", "placeholder": "Enter type"}),
            "type_description": forms.Textarea(attrs={"class": "form-control", "rows": 2, "placeholder": "Enter type description"}),
        }


class StandardRevisionNotificationForm(forms.ModelForm):
    """Form for marking a standard revision notification as acknowledged."""

    class Meta:
        model = StandardRevisionNotification
        fields = ["is_acknowledged"]
        widgets = {
            "is_acknowledged": forms.CheckboxInput(attrs={"class": "form-check-input"}),
        }
