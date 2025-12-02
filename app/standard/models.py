from django.db import models
from django.db.models import UniqueConstraint, Q

"""
1. CORE STANDARD MODEL
"""


class Standard(models.Model):
    """
    Tracks standards with versioning and notifications when revised.
    """

    name = models.CharField(max_length=255)
    description = models.TextField()
    revision = models.CharField(max_length=50)
    author = models.CharField(max_length=255)
    nadcap = models.BooleanField(default=False)
    upload_file = models.FileField(
        upload_to='standard/',
        blank=True,
        null=True
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    previous_version = models.ForeignKey(
        'self',
        null=True,
        blank=True,
        on_delete=models.SET_NULL,
        related_name='next_versions'
    )

    requires_process_review = models.BooleanField(
        default=False,
        help_text="Flagged when a new revision is issued."
    )

    class Meta:
        constraints = [
            UniqueConstraint(fields=['name', 'revision'], name='unique_standard_name_revision')
        ]
        ordering = ['name']

    def save(self, *args, **kwargs):
        if self.pk:
            previous = Standard.objects.get(pk=self.pk)
            if previous.revision != self.revision:
                # mark new version as requiring downstream review
                self.requires_process_review = True

        super().save(*args, **kwargs)

    def __str__(self):
        review_flag = "🔴 Requires Process Review" if self.requires_process_review else ""
        return f"{self.name} (Rev {self.revision}) {review_flag}"


"""
2. STANDARD PROCESS (One-to-Many Link)
"""


class StandardProcess(models.Model):
    """
    A specific process block inside a standard.
    Example: 'Alkaline Clean', 'Cadmium Plate', 'Strip Nickel'.

    This solves the case where one spec includes cleaning + plating + stripping
    all in the same document.
    """

    PROCESS_CHOICES = [
        ('anodize', 'Anodizing'),
        ('brush plate', 'Brush Plating'),
        ('clean', 'Cleaning'),
        ('conversion coating', 'Conversion Coating'),
        ('electroplate', 'Electroplating'),
        ('nital etch', 'Nital Etch'),
        ('paint', 'Paint'),
        ('passivation', 'Passivation'),
        ('pre-pen etch', 'Pre-Pen Etch'),
        ('strip', 'Stripping of Coating'),
        ('thermal', 'Thermal Treatment'),
    ]

    standard = models.ForeignKey(
        Standard,
        on_delete=models.CASCADE,
        related_name='standard_processes'
    )

    process_type = models.CharField(
        max_length=50,
        choices=PROCESS_CHOICES,
        help_text="Which kind of process this represents (clean, plate, strip, etc.)."
    )

    title = models.CharField(
        max_length=255,
        help_text="Friendly label for operators, e.g. 'Alkaline Clean', 'Cadmium Plate', 'Nickel Strip'."
    )

    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Local instructions / limits that apply to this block of the spec only."
    )

    class Meta:
        unique_together = ('standard', 'title')
        ordering = ['standard__name', 'title']

    def __str__(self):
        return f"{self.standard.name} — {self.title} ({self.process_type})"


class StandardRevisionNotification(models.Model):
    """
    Tracks and alerts when a standard is updated.
    """
    standard = models.ForeignKey(
        Standard,
        on_delete=models.CASCADE,
        related_name='notifications'
    )
    message = models.TextField(
        help_text="Details of the standard update."
    )
    notified_at = models.DateTimeField(auto_now_add=True)
    is_acknowledged = models.BooleanField(default=False)

    def __str__(self):
        return f"Notification for {self.standard.name} (Rev {self.standard.revision})"


class InspectionRequirement(models.Model):
    """
    Inspection / acceptance requirement tied to a specific standard.
    Can optionally be tied to a specific process block within that standard.

    Example:
    - 'Thickness 0.0005-0.0008'  → applies to Cadmium Plate
    - 'Post-strip visual no base metal attack' → applies to Strip Nickel
    - 'Final paperwork stamp' → applies to whole spec (no process selected)
    """

    standard = models.ForeignKey(
        Standard,
        on_delete=models.CASCADE,
        related_name='inspections'
    )

    standard_process = models.ForeignKey(
        StandardProcess,
        on_delete=models.CASCADE,
        related_name='inspections',
        blank=True,
        null=True,
        help_text="If set: only applies to this sub-process. If blank: applies to the whole standard."
    )

    name = models.CharField(max_length=255)
    description = models.TextField()
    paragraph_section = models.CharField(max_length=255, blank=True, null=True)
    sampling_plan = models.CharField(max_length=255, blank=True, null=True)

    operator = models.CharField(max_length=255, blank=True, null=True)
    date = models.DateField(blank=True, null=True)

    class Meta:
        ordering = ['standard__name', 'name']

    def __str__(self):
        scope = f" [{self.standard_process.title}]" if self.standard_process else ""
        return f"{self.name}{scope}"


class PeriodicTest(models.Model):
    """
    Periodic test requirements for standards.
    (Salt spray, solution analysis, etc.)
    These are at the standard level, not per-process block.
    """

    TIME_PERIOD_CHOICES = [
        ('35d', 'Every 35 Days'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('yearly', 'Yearly'),
    ]

    standard = models.ForeignKey(
        Standard,
        on_delete=models.CASCADE,
        related_name='periodic_tests'
    )

    name = models.CharField(max_length=255)

    time_period = models.CharField(
        max_length=50,
        choices=TIME_PERIOD_CHOICES
    )

    specification = models.TextField(
        help_text="Spec paragraph, method, acceptance criteria, etc."
    )

    number_of_specimens = models.PositiveIntegerField()
    material = models.CharField(max_length=255)
    dimensions = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name} ({self.get_time_period_display()})"


class PeriodicTestResult(models.Model):
    """
    Actual execution / logging of a periodic test
    (monthly salt spray panel, quarterly adhesion test, etc.).
    """

    test = models.ForeignKey(
        PeriodicTest,
        on_delete=models.CASCADE,
        related_name="results"
    )

    performed_on = models.DateField(auto_now_add=True)
    performed_by = models.CharField(max_length=255, blank=True, null=True)

    passed = models.BooleanField(default=True)

    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-performed_on"]

    def __str__(self):
        status = "Pass" if self.passed else "Fail"
        return f"{self.test.name} on {self.performed_on} — {status}"


class StandardPeriodicRequirement(models.Model):
    """
    Mapping from a Standard to a PeriodicTestSpec defined elsewhere
    (for example, tank_controls.PeriodicTestSpec).
    One PeriodicTestSpec can satisfy multiple Standards.
    """

    standard = models.ForeignKey(
        Standard,
        on_delete=models.CASCADE,
        related_name="periodic_requirements",
    )

    test_spec = models.ForeignKey(
        "tank_controls.PeriodicTestSpec",
        on_delete=models.CASCADE,
        related_name="standard_links",
    )

    active = models.BooleanField(default=True)

    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Any tailoring for this standard (panel alloy, thickness, etc.)."
    )

    class Meta:
        unique_together = ("standard", "test_spec")
        ordering = ["standard__name", "test_spec__name"]

    def __str__(self) -> str:
        return f"{self.standard.name} ⇄ {self.test_spec.name}"


class Classification(models.Model):
    """
    Classifications (method/class/type).
    Can optionally be scoped to a specific process block
    (e.g. plating classes only apply to the plating block).
    """

    standard = models.ForeignKey(
        Standard,
        on_delete=models.CASCADE,
        related_name='classifications',
        null=True
    )

    standard_process = models.ForeignKey(
        StandardProcess,
        on_delete=models.SET_NULL,
        related_name='classifications',
        blank=True,
        null=True,
        help_text="If set: this classification only applies to that sub-process."
    )

    method = models.CharField(max_length=255, blank=True, null=True)
    method_description = models.TextField(blank=True, null=True)

    class_name = models.CharField(max_length=255, blank=True, null=True)
    class_description = models.TextField(blank=True, null=True)

    type = models.CharField(max_length=255, blank=True, null=True)
    type_description = models.TextField(blank=True, null=True)

    # Plating calculation inputs
    strike_asf = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Strike ASF (Amps per Square Foot)"
    )
    plate_asf = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Plating ASF (Amps per Square Foot)"
    )
    plating_time_minutes = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Plating Time in Minutes"
    )

    def __str__(self):
        base = (
            f"Method: {self.method or 'N/A'}, "
            f"Class: {self.class_name or 'N/A'}, "
            f"Type: {self.type or 'N/A'}"
        )
        if self.standard_process:
            return f"{base} [{self.standard_process.title}]"
        return f"{self.standard.name} - {base}"


# --- Utility helpers (unchanged from yours) ---

def create_standard(name, description, revision, author, upload_file=None):
    return Standard.objects.create(
        name=name,
        description=description,
        revision=revision,
        author=author,
        upload_file=upload_file
    )


def list_standards():
    return Standard.objects.all()


def get_standard_by_id(standard_id):
    return Standard.objects.get(id=standard_id)
