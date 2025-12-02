# logbook/forms.py
from django import forms
from .models import DailyInspectionLogEntry, ScrubberLog, LogEntry
from datetime import date


# --- Base Form for Operator and Date/Time Fields ---
# This class handles the common non-logged-in requirements
class BaseEnvironmentalLogForm(forms.ModelForm):
    # 1. Manual Date/Time Entry (REQUIRED)
    # Uses a DateTimeInput widget so the operator can select the date and time.
    log_date = forms.DateTimeField(
        widget=forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        label="Date and Time of Inspection",
        help_text="Set the exact date and time the log was performed."
    )

    # 2. Operator Dropdown (REQUIRED)
    # Overrides the ForeignKey to show all active users as a simple select list.
    operator = forms.CharField(
        max_length=100,
        required=False,
        label="Operator Name",
        help_text="Enter the name of the operator who performed this log entry."
    )


# --- Daily Inspection Log Form ---
class DailyInspectionLogForm(BaseEnvironmentalLogForm):
    class Meta:
        model = DailyInspectionLogEntry
        # Exclude no fields here, as all model fields will be included.
        # We manually defined log_date and operator above, which overrides the model fields.
        fields = '__all__'


# --- Scrubber Log Form ---


class ScrubberLogForm(BaseEnvironmentalLogForm):
    # Explicitly set numerical fields as NOT REQUIRED,
    # even though they are null/blank in the model.
    stage_one_reading = forms.DecimalField(required=False)
    stage_two_reading = forms.DecimalField(required=False)
    stage_three_reading = forms.DecimalField(required=False)

    class Meta:
        model = ScrubberLog
        fields = "__all__"


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
