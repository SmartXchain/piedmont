# logbook/models.py
from django.db import models
from django.contrib.auth.models import User 


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


class DailyInspectionLogEntry(models.Model):
    log_date = models.DateTimeField(
        help_text="Enter the exact date and time of inspection",
        verbose_name="Log Date and Time",
    )
    
    # Inspection Checks
    containment_is_clean = models.BooleanField(
        default=True,
        help_text="Is secondary containment free of waste and liquid?",
    )
    system_undamaged = models.BooleanField(
        default=True,
        help_text="Is the system free of corrosion and evident damage?",
    )
    # The default=False logic is correct: False = No leaks found.
    leaks_present = models.BooleanField(
        default=False, 
        verbose_name="Leaks Present", # Added verbose_name for clarity
        help_text="Are there any leaks?",
    )
    pipes_are_secure = models.BooleanField(
        default=True,
        help_text="Are pipes, valves, and pumps free of leaks and in good condition?",
    )
    tank_lid_closed = models.BooleanField(
        default=True,
        help_text="Is the tank lid closed?",
    )

    # Other Data
    notes = models.TextField(
        blank=True,
        help_text="Add any notes/comments",
    )
    operator = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="recorded by"
    )
    created_at = models.DateTimeField(
        auto_now_add=True)

    class Meta:
        ordering = ['-log_date']
        verbose_name_plural = "Daily Inspection Log Entries"

    def __str__(self):
        return f"Inspection Log {self.pk} - {self.log_date.strftime('%Y-%m-%d')}"


class ScrubberLog(models.Model): # Corrected name (RECOMMENDATION 1)
    
    log_date = models.DateTimeField(
        help_text="Enter the date and time the reading was taken.",
        verbose_name="Log Date and Time",
    )
    
    # Readings - Removed null=True, blank=True assuming these are mandatory (RECOMMENDATION 2)
    stage_one_reading = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Stage 1 Reading (in)",
        help_text="Stage 1: Min 0.7 inches, Max 2.7 inches",
    )
    
    stage_two_reading = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Stage 2 Reading (in)",
        help_text="Stage 2: Min 0.7 inches, Max 4.7 inches",
    )
    
    stage_three_reading = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name="Stage 3 Reading (in)",
        help_text="Stage 3: Min 0.8 inches, Max 2.8 inches",
    )
    
    # Boolean Field Renamed for clarity (RECOMMENDATION 1)
    limits_exceeded = models.BooleanField(
        default=False,
        verbose_name="Limits Exceeded",
        help_text="Do values exceed limits?",
    )
    notes = models.TextField(
        blank=True,
        help_text="Add any notes/comments",
    )
    
    operator = models.CharField(
        max_length=100,
        blank=True,
        verbose_name="Recorded By" # Verbose name for consistency
    )

    class Meta:
        ordering = ['-log_date'] # Sort by newest first
        verbose_name_plural = "Scrubber Logs"
        
    def __str__(self):
        # Human-readable string representation
        status = "FAIL" if self.limits_exceeded else "PASS"
        return f"Scrubber Log {self.pk} ({status}) on {self.log_date.strftime('%Y-%m-%d %H:%M')}"
