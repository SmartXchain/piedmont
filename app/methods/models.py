from django.db import models
from django.core.exceptions import ValidationError

TITLE_CHOICES = [
    ('Pre-Cleaning', 'Pre-Cleaning'),
    ('Masking', 'Masking'),
    ('Abrasive Blasting', 'Abrasive Blasting'),
    ('Cleaning', 'Cleaning'),
    ('Rinsing', 'Rinsing'),
    ('De-Oxidize/Pickle', 'De-Oxidize/Pickle'),
    ('Electrolytic Clean', 'Electrolytic Clean'),
    ('Acid Desmut', 'Acid Desmut'),
    ('Etching', 'Etching'),
    ('Chemical Milling', 'Chemical Milling'),
    ('Conversion Coating', 'Conversion Coating'),
    ('Electroless Plating', 'Electroless Plating'),
    ('Anodize', 'Anodize'),
    ('Sealing/Dying', 'Sealing/Dying'),
    ('Barrel Plating', 'Barrel Plating'),
    ('Brush Plating', 'Brush Plating'),
    ('Electroplating', 'Electroplating'),
    ('Painting/Dry Film Coating', 'Painting/Dry Film Coating'),
    ('Thermal Treatment', 'Thermal Treatment'),
    ('Vacuum Cadmium & Aluminum IVD', 'Vacuum Cadmium & Aluminum IVD'),
    ('Stress Relief', 'Stress Relief'),
    ('Hydrogen Embrittlement Relief', 'Hydrogen Embrittlement Relief')
]


class Method(models.Model):
    METHOD_TYPE_CHOICES = [
        ('processing_tank', 'Processing Tank'),
        ('manual_method', 'Manual Method'),
    ]

    method_type = models.CharField(max_length=50, choices=METHOD_TYPE_CHOICES)
    title = models.CharField(max_length=255, choices=TITLE_CHOICES, blank=True)
    description = models.TextField(null=True, blank=True)

    # Processing Tank Specific Fields
    tank_name = models.CharField(max_length=255, blank=True, null=True)
    temp_min = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    temp_max = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    immersion_time_min = models.PositiveIntegerField(blank=True, null=True)
    immersion_time_max = models.PositiveIntegerField(blank=True, null=True)
    chemical = models.CharField(max_length=255, blank=True, null=True)
    is_rectified = models.BooleanField(default=False)

    def clean(self):
        if self.method_type == 'processing_tank':
            required_fields = ['tank_name', 'temp_min', 'temp_max', 'immersion_time_min', 'immersion_time_max', 'chemical']
            errors = {}
            for field in required_fields:
                if getattr(self, field) is None:  # Checking for None explicitly
                    errors[field] = f"{field.replace('_', ' ').capitalize()} is required for Processing Tank."
            if errors:
                raise ValidationError(errors)

    def __str__(self):
        return self.title


class ParameterToBeRecorded(models.Model):
    TITLE_CHOICES = [
        ('Pre-Cleaning', 'Pre-Cleaning'),
        ('Masking', 'Masking'),
        ('Abrasive Blasting', 'Abrasive Blasting'),
        ('Cleaning', 'Cleaning'),
        ('Rinsing', 'Rinsing'),
        ('De-Oxidize/Pickle', 'De-Oxidize/Pickle'),
        ('Electrolytic Clean', 'Electrolytic Clean'),
        ('Acid Desmut', 'Acid Desmut'),
        ('Etching', 'Etching'),
        ('Chemical Milling', 'Chemical Milling'),
        ('Conversion Coating', 'Conversion Coating'),
        ('Electroless Plating', 'Electroless Plating'),
        ('Anodize', 'Anodize'),
        ('Sealing/Dying', 'Sealing/Dying'),
        ('Barrel Plating', 'Barrel Plating'),
        ('Brush Plating', 'Brush Plating'),
        ('Electroplating', 'Electroplating'),
        ('Painting/Dry Film Coating', 'Painting/Dry Film Coating'),
        ('Thermal Treatment', 'Thermal Treatment'),
        ('Vacuum Cadmium & Aluminum IVD', 'Vacuum Cadmium & Aluminum IVD'),
    ]

    title = models.CharField(max_length=255, choices=TITLE_CHOICES)
    description = models.TextField(blank=True, null=True)
    method = models.ForeignKey('Method', on_delete=models.SET_NULL, blank=True, null=True)

    def save(self, *args, **kwargs):
        # Automatically populate the description based on the title
        descriptions = {
            'Pre-Cleaning': "None as long as method is non-etching. Process sheet must specify the maximum time. Immersion/Contact Time if etching.",
            'Masking': "It is only necessary to record the masking family, e.g. tape, lacquer, bung, etc. If the masking material is specifically defined on the shop papers then there is no need to record it.",
            'Abrasive Blasting': "Media, Pressure, Offset distance",
            'Cleaning': "None so long as method is non-etching. Process sheet must specify the maximum time. Immersion/Contact Time if etching",
            'Rinsing': "None",
            'De-Oxidize/Pickle': "Immersion Time",
            'Electrolytic Clean': "Immersion time. Voltage or Amperage - as required by specification. Surface area if current density (amperage) controlled. Anodic/Cathodic/Reversing unless it is fixed.",
            'Acid Desmut': "None for dilute acid solutions used for alkaline etch desmut or neutralizing. Process sheet specify maximum immersion time.",
            'Etching': "Immersion/Contact Time. Voltage or Amperage - as required by specification. Surface area if current density (amperage) controlled.",
            'Chemical Milling': "Immersion Time",
            'Conversion Coating': "Immersion Time",
            'Electroless Plating': "Immersion Time",
            'Anodize': "Ramp up data for each ramp and hold step (e.g. time ramp starts and time ramp finishes or duration of ramp). Voltage or Amperage - as required by specification. Surface area if current density (amperage) controlled. Anodize Time. Ramp down data (e.g. time ramp starts and time ramp finishes or duration of ramp).",
            'Sealing/Dying': "Immersion Time",
            'Barrel Plating': "Voltage or Amperage - as required by specification. Surface area if current density (amperage) controlled. Time",
            'Brush Plating': "Surface Area. Solution Type. Voltage. Ampere Hours",
            'Electroplating': "Strike voltage or amperage. Ramp up data for each ramp and hold step (e.g. time ramp starts and time ramp finishes or duration of ramp). Plating voltage or amperage as required by specification. Surface area if strike or plating are controlled by amperage. Time. NOTE: Where a cathometer is used to control the plating current density the actual current density, rather than amperage, shall be recorded.",
            'Painting/Dry Film Coating': "Batch # of each paint component. Batch # of thinners if part of a kit. Viscosity for each paint mix. Mixing start time and mixing finish time (or mixing start time and duration) for each paint mix. Application start time and finish time for each coat. Start of cure, end of cure and cure temperature for each cure cycle. If curing is performed in an oven fitted with a recording system then traceability to the oven recording would be acceptable.",
            'Thermal Treatment': "Time. Temperature",
            'Vacuum Cadmium & Aluminum IVD': "Glow Discharge. Partial Pressure. Voltage. Amperage. Time"
        }

        if self.title and not self.description:
            self.description = descriptions.get(self.title, "")
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title
