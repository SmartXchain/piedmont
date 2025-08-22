from django.conf import settings
from django.db import models


FREQ_CHOICES = [
    ("daily", "Daily"),
    ("weekly", "Weekly"),
    ("monthly", "Monthly"),
    ("quarterly", "Quarterly"),
    ("semi-annual", "Semi-Annually"),
    ("annual", "Annually"),
    ("35d", "Every 35 Days"),
]


class Tank(models.Model):
    """A processing tank or line."""
    name = models.CharField(max_length=120, unique=True)
    process = models.CharField(
        max_length=120,
        blank=True,
        null=True,
        help_text="e.g., Cadmium, Chrome, Anodize",
    )
    description = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["name"]

    def __str__(self) -> str:
        return self.name


class ControlSet(models.Model):
    """
    Logical bundle of controls/tests for a tank or line
    (e.g., 'Cad Line Controls').
    """
    name = models.CharField(max_length=140, unique=True)
    tank = models.ForeignKey(
        Tank,
        on_delete=models.CASCADE,
        related_name="control_sets",
    )
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["tank__name", "name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.tank.name})"


class TemperatureSpec(models.Model):
    """Temperature control requirement."""
    control_set = models.ForeignKey(
        ControlSet,
        on_delete=models.CASCADE,
        related_name="temperature_specs",
    )
    min_c = models.DecimalField(max_digits=6, decimal_places=2)
    max_c = models.DecimalField(max_digits=6, decimal_places=2)
    frequency = models.CharField(
        max_length=20,
        choices=FREQ_CHOICES,
        default="daily",
    )

    class Meta:
        ordering = ["control_set__name", "min_c", "max_c"]

    def __str__(self) -> str:
        return f"T°C {self.min_c}–{self.max_c} ({self.control_set})"


class ChemicalSpec(models.Model):
    """Chemical concentration requirement."""
    control_set = models.ForeignKey(
        ControlSet,
        on_delete=models.CASCADE,
        related_name="chemical_specs",
    )
    chemical_name = models.CharField(max_length=120)
    units = models.CharField(max_length=40, default="g/L")
    target = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True,
    )
    min_val = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True,
    )
    max_val = models.DecimalField(
        max_digits=10,
        decimal_places=3,
        blank=True,
        null=True,
    )
    frequency = models.CharField(
        max_length=20,
        choices=FREQ_CHOICES,
        default="daily",
    )
    method = models.CharField(
        max_length=240,
        blank=True,
        null=True,
        help_text="How to test/titrate, notes, etc.",
    )

    class Meta:
        ordering = ["control_set__name", "chemical_name"]

    def __str__(self) -> str:
        return f"{self.chemical_name} ({self.control_set})"


class CheckSpec(models.Model):
    """
    General checks/tests that aren’t a chemical or temperature
    (e.g., pH meter calibration, agitation check).
    """
    TYPE_CHOICES = [
        ("visual", "Visual"),
        ("instrument", "Instrument"),
        ("documentation", "Documentation"),
        ("other", "Other"),
    ]

    control_set = models.ForeignKey(
        ControlSet,
        on_delete=models.CASCADE,
        related_name="check_specs",
    )
    name = models.CharField(max_length=140)
    check_type = models.CharField(
        max_length=20,
        choices=TYPE_CHOICES,
        default="other",
    )
    method = models.TextField(blank=True, null=True)
    frequency = models.CharField(
        max_length=20,
        choices=FREQ_CHOICES,
        default="daily",
    )

    class Meta:
        ordering = ["control_set__name", "name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.control_set})"


class PeriodicTestSpec(models.Model):
    """
    Test specimens / periodic tests (e.g., salt spray monthly, bend tests quarterly).
    A single spec can satisfy multiple Standards (via mapping in the 'standard' app).
    """
    control_set = models.ForeignKey(
        ControlSet,
        on_delete=models.CASCADE,
        related_name="periodic_tests",
    )
    name = models.CharField(max_length=200)
    frequency = models.CharField(
        max_length=20,
        choices=FREQ_CHOICES,
        default="monthly",
    )
    specification = models.TextField()
    number_of_specimens = models.PositiveIntegerField()
    material = models.CharField(max_length=255)
    dimensions = models.CharField(max_length=255)

    class Meta:
        ordering = ["control_set__name", "name"]

    def __str__(self) -> str:
        return f"{self.name} ({self.get_frequency_display()})"


class PeriodicTestExecution(models.Model):
    """
    Log of an actual execution/run of a PeriodicTestSpec
    (pass/fail, notes, who performed, when).
    """
    test_spec = models.ForeignKey(
        PeriodicTestSpec,
        on_delete=models.CASCADE,
        related_name="executions",
    )
    performed_on = models.DateField(auto_now_add=True)
    performed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="periodic_test_executions",
    )
    passed = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-performed_on"]

    def __str__(self) -> str:
        status = "Pass" if self.passed else "Fail"
        return f"{self.test_spec.name} on {self.performed_on} — {status}"
