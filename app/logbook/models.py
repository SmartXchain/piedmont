from django.conf import settings
from django.db import models
from django.core.exceptions import ValidationError


class ProcessRun(models.Model):
    """
    One logbook line = one actual processing event.
    Part is recorded as plain text (barcode/manual) to avoid FK dependency.
    """

    # Manual part / template / drawing number
    part_number_text = models.CharField(
        max_length=255,
        help_text="Part number"
    )

    # Snapshots for reporting (optional but useful)
    standard_text = models.CharField(
        max_length=255,
        blank=True,
        help_text="Standard or specification name. (e.g. AMS 2400, MIL-A-8625, etc...)"
    )
    classification_text = models.CharField(
        max_length=255,
        blank=True,
        help_text="Classification, method, or type description per standard."
    )
    spec_revision = models.CharField(
        max_length=50,
        blank=True,
        help_text="Revision of the spec used for this run."
    )

    # Work order / job identity
    work_order_number = models.CharField(
        max_length=100,
        blank=True,
        help_text="WO / traveler number as written."
    )

    # Process info
    process_name = models.CharField(
        max_length=150,
        help_text="Operation performed (e.g. Cad plate, Strip chrome, Pre-pen etch)."
    )
    repaired_surface = models.CharField(
        max_length=150,
        blank=True,
        help_text="Section/surface of the part that was processed/repaired."
    )

    # Traceability
    date_of_process = models.DateField(
        help_text="Calendar date when the processing was performed/logged.")
    plating_end_time = models.DateTimeField(
        null=True,
        blank=True,
        help_text="Actual end time / removal from bath when applicable"
    )

    quantity_processed = models.PositiveIntegerField(
        default=1
    )
    lot_number = models.CharField(
        max_length=100,
        blank=True
    )

    # Operator
    technician = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='process_runs'
    )

    # Rework
    REWORK_SOURCE_CHOICES = [
        ('TRAVELER', 'Traveler labeled rework'),
        ('OPERATOR', 'Operator identified rework'),
        ('SUPERVISOR', 'Supervisor tagged as rework'),
        ('UNKNOWN', 'Unknown source'),
    ]
    is_rework = models.BooleanField(default=False)
    rework_source = models.CharField(
        max_length=20,
        choices=REWORK_SOURCE_CHOICES,
        blank=True
    )
    rework_reason = models.CharField(
        max_length=255,
        blank=True
    )

    notes = models.TextField(blank=True)

    # Audit
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='process_runs_created'
    )
    updated_at = models.DateTimeField(auto_now=True)
    updated_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='process_runs_updated'
    )

    class Meta:
        ordering = ['-date_of_process', '-plating_end_time']
        verbose_name = "Process Run"
        verbose_name_plural = "Process Runs"

    def __str__(self):
        bits = [
            self.process_name,
            self.part_number_text,
            self.work_order_number,
            self.date_of_process.strftime("%Y-%m-%d") if self.date_of_process else "",
        ]
        return " - ".join([b for b in bits if b])

    def clean(self):
        # With FK removed, just make sure part_number_text is not empty
        if not self.part_number_text:
            raise ValidationError("Part number is required for the logbook entry.")


class EmbrittlementRelief(models.Model):
    """
    Optional 1:1 details for post-process bake / hydrogen embrittlement relief.
    Re-bake is not allowed, so we keep this simple and single.
    """
    LINKED_OP_CHOICES = [
        ('MACHINING', 'Machining operation'),
        ('PLATING', 'Plating operation'),
        ('INSPECTION', 'Inspection operation'),
    ]

    process_run = models.OneToOneField(
        ProcessRun,
        on_delete=models.CASCADE,
        related_name='embrittlement_relief'
    )
    required = models.BooleanField(default=False)
    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)
    furnace_number = models.CharField(max_length=100, blank=True)
    linked_operation = models.CharField(
        max_length=20,
        choices=LINKED_OP_CHOICES,
        blank=True
    )
    remarks = models.TextField(blank=True)

    def __str__(self):
        return f"Embrittlement relief for run {self.process_run_id}"


class ControlInspection(models.Model):
    """
    One processing run may have several inspection requirements
    coming from the specification (thickness, adhesion, visual, etc.)
    """
    RESULT_CHOICES = [
        ('OK', 'OK'),
        ('NOT_OK', 'Not OK'),
    ]

    process_run = models.ForeignKey(
        ProcessRun,
        on_delete=models.CASCADE,
        related_name='control_inspections'
    )
    inspection_name = models.CharField(
        max_length=150,
        help_text="Name of the inspection/test (e.g. 'Thickness', 'Visual', 'Adhesion')."
    )
    inspection_spec = models.CharField(
        max_length=255,
        blank=True,
        help_text="Specification + paragraph as performed (spec is revision-controlled)."
    )
    sample_size = models.PositiveIntegerField(
        default=1,
        help_text="Number of parts tested for this inspection."
    )
    inspection_result = models.CharField(
        max_length=10,
        choices=RESULT_CHOICES
    )
    inspected_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When the inspection was actually done (operator may enter later)."
    )
    inspector = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='control_inspections_performed'
    )
    comments = models.TextField(blank=True)

    class Meta:
        verbose_name = "Control Inspection"
        verbose_name_plural = "Control Inspections"

    def __str__(self):
        return f"{self.inspection_name} for run {self.process_run_id}"

