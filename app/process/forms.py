# process/forms.py
from django import forms
from django.core.exceptions import ValidationError
from django.forms.models import BaseInlineFormSet

from .models import Process, ProcessStep
from standard.models import Classification, Standard
from methods.models import Method


class ProcessForm(forms.ModelForm):
    class Meta:
        model = Process
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        standard = None

        # POST data
        if 'standard' in self.data:
            try:
                standard_id = int(self.data.get('standard'))
                standard = Standard.objects.get(id=standard_id)
            except (ValueError, Standard.DoesNotExist):
                pass
        # Instance (edit)
        elif getattr(self.instance, 'standard_id', None):
            standard = self.instance.standard
        # Initial
        elif 'standard' in self.initial:
            init = self.initial.get('standard')
            standard = init if isinstance(init, Standard) else Standard.objects.filter(id=init).first()

        # Filter classifications to that standard
        if 'classification' in self.fields:
            self.fields['classification'].queryset = (
                Classification.objects.filter(standard=standard)
                if standard else Classification.objects.none()
            )


class MethodModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj: Method):
        desc = (obj.description or '').strip()
        short = (desc[:60] + '...') if len(desc) > 60 else desc
        return f"{obj.title} — {short}" if short else obj.title


class ProcessStepInlineForm(forms.ModelForm):
    method = MethodModelChoiceField(queryset=Method.objects.all(), required=True)

    class Meta:
        model = ProcessStep
        fields = ['step_number', 'method']
        widgets = {
            'step_number': forms.NumberInput(attrs={'style': 'width: 80px;'}),
        }


class ProcessStepInlineFormSet(BaseInlineFormSet):
    """
    Validates that step_number values are unique and (optionally) contiguous.
    """
    def clean(self):
        super().clean()
        numbers = []
        for form in self.forms:
            if self.can_delete and form.cleaned_data.get('DELETE'):
                continue
            if not form.cleaned_data or form.errors:
                continue
            n = form.cleaned_data.get('step_number')
            if n is None:
                continue
            numbers.append(n)

        # No duplicates
        if len(numbers) != len(set(numbers)):
            raise ValidationError("Duplicate step numbers detected. Each step number must be unique.")

        # Optional: enforce contiguous 1..N during admin save (nice guard)
        if numbers:
            expected = set(range(1, len(numbers) + 1))
            if set(numbers) != expected:
                raise ValidationError("Step numbers must be contiguous starting at 1 (no gaps).")
