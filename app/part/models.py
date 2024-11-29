from django.db import models
from standard.models import Standard

class Part(models.Model):
    part_number = models.CharField(max_length=255, unique=True)
    part_description = models.CharField(max_length=255)
    part_revision = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.part_number} - {self.part_description}"


class PartDetails(models.Model):
    JOB_IDENTITY_CHOICES = [
        ('chrome_plate', 'Chrome Plate'),
        ('cadmium_plate', 'Cadmium Plate'),
        ('etch', 'Etch'),
        ('anodize', 'Anodize'),
        ('paint', 'Paint'),
    ]

    part = models.OneToOneField(Part, on_delete=models.CASCADE, related_name='details')
    is_export_controlled = models.BooleanField(default=False, blank=True, null=True)
    job_identity = models.CharField(
        max_length=50, choices=JOB_IDENTITY_CHOICES, blank=True, null=True
    )
    customer = models.CharField(max_length=255, blank=True, null=True)
    prime_contractor = models.CharField(max_length=255, blank=True, null=True)
    alloy_with_heat_treat_condition = models.CharField(max_length=255, blank=True, null=True)
    processing_standard = models.ForeignKey(
        Standard, on_delete=models.SET_NULL, blank=True, null=True, related_name='parts')
    is_frozen_process = models.BooleanField(default=False, blank=True, null=True)

    def __str__(self):
        return f"Details for {self.part.part_number}"


class JobDetails(models.Model):
    part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name='job_details')
    purchase_order_with_revision = models.CharField(max_length=255, blank=True, null=True)
    part_quantity = models.PositiveIntegerField(blank=True, null=True)
    serial_or_lot_numbers = models.TextField(blank=True, null=True)
    job_number = models.CharField(max_length=255, unique=True)
    surface_repaired = models.CharField(max_length=255, blank=True, null=True)
    date = models.DateField(blank=True, null=True) 

    def __str__(self):
        return f"Job {self.job_number} for Part {self.part.part_number}"