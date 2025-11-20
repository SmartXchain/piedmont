# logbook/forms.py
from django import forms
from .models import LogEntry
from datetime import date


class LogEntryForm(forms.ModelForm):
    class Meta:
        model = LogEntry
        fields = [
            "date_of_process",
            "part_number",
            "process_name",
            "work_order_number",
            "repaired_surface",
            "standard_text",
            "classification_text",
            "spec_revision",
            "quantity_processed",
            "lot_number",
            "process_end_time",
            "is_rework",
            "rework_reason",
            "inspection_result",
            "failure_mode",
            "notes",
        ]
        widgets = {
            "date_of_process": forms.DateInput(attrs={"type": "date"}),
            "process_end_time": forms.DateTimeInput(attrs={"type": "datetime-local"}),
            "notes": forms.Textarea(
                attrs={
                    "class": "form-control",
                    "rows": 6,
                    "placeholder": "Enter your notes here"
                },
            ),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # default today
        if not self.initial.get("date_of_process"):
            self.initial["date_of_process"] = date.today()
