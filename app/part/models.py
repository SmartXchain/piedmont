from django.db import models
from standard.models import Standard

class Part(models.Model):
    part_number = models.CharField(max_length=255, unique=True)
    part_description = models.CharField(max_length=255)
    part_revision = models.CharField(max_length=50, blank=True, null=True)

    def __str__(self):
        return f"{self.part_number}"


class PartDetails(models.Model):
    part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name='details')  # Allow multiple details per Part
    job_identity = models.CharField(
        max_length=50,
        choices=[
            ('chrome_plate', 'Chrome Plate'),
            ('cadmium_plate', 'Cadmium Plate'),
            ('etch', 'Etch'),
            ('anodize', 'Anodize'),
            ('paint', 'Paint'),
            ('passivation', 'Passivation'),
        ]
    )
    processing_standard = models.ForeignKey(
        'standard.Standard', on_delete=models.SET_NULL, blank=True, null=True, related_name='part_details'
    )
    alloy_with_heat_treat_condition = models.CharField(max_length=255, blank=True, null=True)
    rework = models.BooleanField(default=False)
   
    class Meta:
        unique_together = ('part', 'job_identity', 'processing_standard')  # Ensure uniqueness per part and job identity
        ordering = ['job_identity']

    def __str__(self):
        return f"{self.part.part_number} - {self.get_job_identity_display()} - {self.processing_standard.name if self.processing_standard else 'No Standard'}"



class JobDetails(models.Model):
    part_detail = models.ForeignKey(PartDetails, on_delete=models.CASCADE, related_name='jobs')
    purchase_order_with_revision = models.CharField(max_length=255, blank=True, null=True)
    part_quantity = models.PositiveIntegerField(blank=True, null=True)
    serial_or_lot_numbers = models.TextField(blank=True, null=True)
    job_number = models.CharField(max_length=255, unique=True)
    surface_repaired = models.CharField(max_length=255, blank=True, null=True)
    date = models.DateField(blank=True, null=True)

    class Meta:
        ordering = ['job_number']

    def __str__(self):
        return f"Job {self.job_number} for {self.part_detail.part.part_number}"
