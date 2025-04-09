# process/forms.py
from django import forms
from .models import Process, ProcessStep
from standard.models import Classification
from methods.models import Method


class ProcessForm(forms.ModelForm):
    class Meta:
        model = Process
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Avoid trying to access standard on an unsaved instance
        standard = self.initial.get('standard') or getattr(self.instance, 'standard', None)

        if standard:
            self.fields['classification'].queryset = Classification.objects.filter(standard=standard)
        else:
            self.fields['classification'].queryset = Classification.objects.none()

    class Media:
        js = ('admin/js/jquery.init.js', 'process/js/filter_classifications.js',)


class MethodModelChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.title} — {obj.description[:60]}{'...' if len(obj.description) > 60 else ''}"


class ProcessStepInlineForm(forms.ModelForm):
    method = MethodModelChoiceField(queryset=Method.objects.all(), required=True)

    class Meta:
        model = ProcessStep
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['method'].help_text = 'Select a method below. Overview will appear underneath.'
