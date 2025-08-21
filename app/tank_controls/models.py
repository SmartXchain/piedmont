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
    name = models.CharField(max_length=120, unique=True)
    process = models.CharField(max_length=120, blank=True, null=True)  # e.g., Cadmium, Chrome, Anodize
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class ControlSet(models.Model):
    """Logical bundle of controls/tests for a tank/line (e.g., 'Cad Line Controls')."""
    name = models.CharField(max_length=140, unique=True)
    tank = models.ForeignKey(Tank, on_delete=models.CASCADE, related_name="control_sets")
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.tank.name})"


class TemperatureSpec(models.Model):
    control_set = models.ForeignKey(ControlSet, on_delete=models.CASCADE, related_name="temperature_specs")
    min_c = models.DecimalField(max_digits=6, decimal_places=2)
    max_c = models.DecimalField(max_digits=6, decimal_places=2)
    frequency = models.CharField(max_length=20, choices=FREQ_CHOICES, default="daily")

    def __str__(self):
        return f"T°C {self.min_c}–{self.max_c} ({self.control_set})"


class ChemicalSpec(models.Model):
    control_set = models.ForeignKey(ControlSet, on_delete=models.CASCADE, related_name="chemical_specs")
    chemical_name = models.CharField(max_length=120)
    units = models.CharField(max_length=40, default="g/L")
    target = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True)
    min_val = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True)
    max_val = models.DecimalField(max_digits=10, decimal_places=3, blank=True, null=True)
    frequency = models.CharField(max_length=20, choices=FREQ_CHOICES, default="daily")
    method = models.CharField(max_length=240, blank=True, null=True)  # how to test/titrate, etc.

    def __str__(self):
        return f"{self.chemical_name} ({self.control_set})"


class CheckSpec(models.Model):
    """General checks/tests that aren’t a chemical or temp (e.g., pH meter cal, agitation check)."""
    TYPE_CHOICES = [
        ("visual", "Visual"),
        ("instrument", "Instrument"),
        ("documentation", "Documentation"),
        ("other", "Other"),
    ]
    control_set = models.ForeignKey(ControlSet, on_delete=models.CASCADE, related_name="check_specs")
    name = models.CharField(max_length=140)
    check_type = models.CharField(max_length=20, choices=TYPE_CHOICES, default="other")
    method = models.TextField(blank=True, null=True)
    frequency = models.CharField(max_length=20, choices=FREQ_CHOICES, default="daily")

    def __str__(self):
        return f"{self.name} ({self.control_set})"


class PeriodicTestSpec(models.Model):
    """
    The “test specimens / periodic tests” definition (e.g., salt spray panels monthly, bend tests quarterly).
    A single spec can satisfy multiple Standards via a mapping table in the Standards app.
    """
    control_set = models.ForeignKey(ControlSet, on_delete=models.CASCADE, related_name="periodic_tests")
    name = models.CharField(max_length=200)
    frequency = models.CharField(max_length=20, choices=FREQ_CHOICES, default="monthly")
    specification = models.TextField()  # method/spec paragraph
    number_of_specimens = models.PositiveIntegerField()
    material = models.CharField(max_length=255)
    dimensions = models.CharField(max_length=255)

    class Meta:
        ordering = ["control_set__name", "name"]

    def __str__(self):
        return f"{self.name} ({self.get_frequency_display()})"

