# logbook/models.py
from django.db import models

REWORK_SOURCE_CHOICES = [
    ('TRAVELER', 'Traveler labeled rework'),
    ('OPERATOR', 'Operator identified rework'),
    ('SUPERVISOR', 'Supervisor tagged as rework'),
    ('UNKNOWN', 'Unknown source'),
]

PROCESS_NAME_CHOICES = [
    ('alkaline_clean', 'Alkaline Clean'),
    ('anodize', 'Anodize'),
    ('cadmium_plate', 'Cadmium Plate'),
    ('chemical_conversion', 'Chemical Conversion'),
    ('chrome_plate', 'Chrome Plate'),
    ('cleaning', 'Cleaning'),
    ('etch', 'Etch'),
    ('ni_plate', 'Nickel Plate'),
    ('paint', 'Paint'),
    ('passivation', 'Passivation'),
    ('solvent_clean', 'Solvent Clean'),
    ('strip', 'Strip')
]

FAILURE_MODE_CHOICES = [
    ('NONE', 'None'),
    ('MASKING_ERROR', 'Masking error / leak'),
    ('WRONG_SECTION', 'Wrong section / wrong area processed'),
    ('LOW_THICKNESS', 'Low thickness'),
    ('HIGH_THICKNESS', 'High thickness'),
    ('NON_UNIFORM', 'Non-uniform coverage'),
    ('ADHESION_FAIL', 'Adhesion failure / peel'),
    ('CONTAMINATION', 'Contamination / roughness / pitting'),
    ('BURNED_AREA', 'Burned area / overheating'),
    ('ETCH_DAMAGE', 'Etch or strip damage'),
    ('POST_TREAT_ERROR', 'Post-treatment / bake / rinse error'),
    ('OTHER', 'Other'),
]

INSPECTION_RESULT_CHOICES = [
    ('OK', 'OK'),
    ('NOT_OK', 'Not Ok'),
]

 
class LogEntry(models.Model):
    # minimum identification
    date_of_process = models.DateField()
    part_number = models.CharField(max_length=50)
    process_name = models.CharField(max_length=50, choices=PROCESS_NAME_CHOICES, blank=True)

    # optional but common in your flow
    work_order_number = models.CharField(max_length=100, blank=True)
    repaired_surface = models.CharField(max_length=150, blank=True)

    # spec info (still text, no FK)
    standard_text = models.CharField(max_length=100, blank=True)
    classification_text = models.CharField(max_length=255, blank=True)
    spec_revision = models.CharField(max_length=50, blank=True)

    # results
    quantity_processed = models.PositiveIntegerField(default=1)
    lot_number = models.CharField(max_length=50, blank=True)

    # optional time (not always used)
    process_end_time = models.DateTimeField(null=True, blank=True)

    # rework flag
    is_rework = models.BooleanField(default=False)
    rework_reason = models.CharField(max_length=20, choices=REWORK_SOURCE_CHOICES, blank=True)

    # failure mode
    inspection_result = models.CharField(
        max_length=10,
        choices=INSPECTION_RESULT_CHOICES,
        default='OK',
        help_text="Final inspection result for this run."
    )

    failure_mode = models.CharField(
        max_length=30,
        choices=FAILURE_MODE_CHOICES,
        default='NONE',
        help_text="Observed failure mode or 'None' if acceptable."
    )

    # free text
    notes = models.TextField(blank=True)

    # auto time so supervisors can see when it was submitted
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date_of_process", "-created_at"]

    def __str__(self):
        return f"{self.date_of_process} - {self.process_name} - {self.part_number}"

