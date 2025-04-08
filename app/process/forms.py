# process/forms.py

from django import forms
from .models import Process
from standard.models import Classification, Standard


class ProcessAdminForm(forms.ModelForm):
    class Meta:
        model = Process
        fields = '__all__'

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        # Only show classifications for the selected standard (if any)
        if 'standard' in self.data:
            try:
                standard_id = int(self.data.get('standard'))
                self.fields['classification'].queryset = Classification.objects.filter(standard_id=standard_id)
            except (ValueError, TypeError):
                self.fields['classification'].queryset = Classification.objects.none()
        elif self.instance.pk and self.instance.standard:
            self.fields['classification'].queryset = Classification.objects.filter(standard=self.instance.standard)
        else:
            self.fields['classification'].queryset = Classification.objects.none()
