from django.db import models
from django.core.exceptions import ValidationError


class Method(models.Model):
    METHOD_TYPE_CHOICES = [
        ('processing_tank', 'Processing Tank'),
        ('manual_method', 'Manual Method'),
    ]

    method_type = models.CharField(max_length=50, choices=METHOD_TYPE_CHOICES)
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    # Processing Tank Specific Fields
    tank_name = models.CharField(max_length=255, blank=True, null=True)
    temp_min = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    temp_max = models.DecimalField(max_digits=5, decimal_places=2, blank=True, null=True)
    immersion_time_min = models.PositiveIntegerField(blank=True, null=True)
    immersion_time_max = models.PositiveIntegerField(blank=True, null=True)
    chemical = models.CharField(max_length=255, blank=True, null=True)
    is_rectified = models.BooleanField(default=False)

    def clean(self):
        # Enforce validation for Processing Tank fields
        if self.method_type == 'processing_tank':
            required_fields = ['tank_name', 'temp_min', 'temp_max', 'immersion_time_min', 'immersion_time_max', 'chemical']
            for field in required_fields:
                if not getattr(self, field):
                    raise ValidationError({field: f"{field.replace('_', ' ').capitalize()} is required for Processing Tank."})

    def __str__(self):
        return self.title
