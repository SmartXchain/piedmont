from django.db import models

TITLE_CHOICES = [
    ('Abrasive Blasting', 'Abrasive Blasting'),
    ('Acid Desmut', 'Acid Desmut'),
    ('Air Dry', 'Air Dry'),
    ('Alkaline Clean', 'Alkaline Clean'),
    ('Anodize', 'Anodize'),
    ('Barrel Plating', 'Barrel Plating'),
    ('Brush Plating', 'Brush Plating'),
    ('Cad Strip', 'Cad Strip'),
    ('Chemical Milling', 'Chemical Milling'),
    ('Cleaning', 'Cleaning'),
    ('Chrome Strip', 'Chrome Strip'),
    ('Conversion Coating', 'Conversion Coating'),
    ('De-Oxidize/Pickle', 'De-Oxidize/Pickle'),
    ('Demasking', 'Demasking'),
    ('Electroless Plating', 'Electroless Plating'),
    ('Electrolytic Clean', 'Electrolytic Clean'),
    ('Electroplating', 'Electroplating'),
    ('Etching', 'Etching'),
    ('FOD Inpsection', 'FOD Inspection'),
    ('Hydrogen Embrittlement Relief', 'Hydrogen Embrittlement Relief'),
    ('Masking', 'Masking'),
    ('Nickel Strip', 'Nickel Strip'),
    ('Oven Dry', 'Oven Dry'),
    ('Painting/Dry Film Coating', 'Painting/Dry Film Coating'),
    ('Pre-Cleaning', 'Pre-Cleaning'),
    ('Pre-Pen Etching', 'Pre-Pen Etching'),
    ('Racking', 'Racking'),
    ('Rinsing', 'Rinsing'),
    ('Scrub Surface', 'Scrub Surface'),
    ('Sealing', 'Sealing'),
    ('Solvent Clean', 'Solvent Clean'),
    ('Stress Relief', 'Stress Relief'),
    ('Thermal Treatment', 'Thermal Treatment'),
    ('Unracking', 'Unracking'),
    ('Vacuum Cadmium & Aluminum IVD', 'Vacuum Cadmium & Aluminum IVD'),
    ('Water-Break Test', 'Water-Break Test'),
]

METHOD_TYPE_CHOICES = [
    ('processing_tank', 'Processing Tank'),
    ('manual_method', 'Manual Method'),
]


class Method(models.Model):
    method_type = models.CharField(max_length=50, choices=METHOD_TYPE_CHOICES, blank=True)
    title = models.CharField(max_length=255, choices=TITLE_CHOICES, blank=True)
    description = models.TextField(blank=True)

    tank_name = models.CharField(max_length=255, blank=True, null=True)
    temp_min = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    temp_max = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    immersion_time_min = models.PositiveIntegerField(blank=True, null=True)
    immersion_time_max = models.PositiveIntegerField(blank=True, null=True)
    chemical = models.CharField(max_length=255, blank=True, null=True)
    is_rectified = models.BooleanField(default=False)

    class Meta:
        verbose_name = "Method"
        verbose_name_plural = "Methods"

    def __str__(self):
        return f"{self.title} ({self.method_type})"


class ParameterToBeRecorded(models.Model):
    title = models.CharField(max_length=255, choices=TITLE_CHOICES)
    description = models.TextField(blank=True)
    method = models.ForeignKey(Method, on_delete=models.SET_NULL, blank=True, null=True)

    class Meta:
        verbose_name = "Recorded Parameter"
        verbose_name_plural = "Recorded Parameters"

    def __str__(self):
        return f"{self.title} ({self.method})"
