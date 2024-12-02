from django.db import models
from standard.models import Standard, Classification
from process.models import Process



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
    classification = models.ForeignKey(
        'standard.Classification', on_delete=models.SET_NULL, blank=True, null=True
    )
    alloy_with_heat_treat_condition = models.CharField(max_length=255, blank=True, null=True)
    rework = models.BooleanField(default=False)
   
    def get_process_steps(self):
        # Fetch the process using the processing standard and classification
        process = Process.objects.filter(
            standard=self.processing_standard,
            classification=self.classification
        ).first()

        if process:
            print(f"Process Found: {process}")
        else:
            print("No matching process found.")
        # Return the steps if the process exists, otherwise return an empty queryset
        
        return process.steps.all() if process else None

    class Meta:
        unique_together = ('part', 'job_identity', 'processing_standard')  # Ensure uniqueness per part and job identity
        ordering = ['job_identity']

    def __str__(self):
        return f"{self.part.part_number} - {self.job_identity}"



class JobDetails(models.Model):
    part_detail = models.ForeignKey(PartDetails, on_delete=models.CASCADE, related_name='jobs')
    purchase_order_with_revision = models.CharField(max_length=255, blank=True, null=True)
    part_quantity = models.PositiveIntegerField(blank=True, null=True)
    serial_or_lot_numbers = models.TextField(blank=True, null=True)
    job_number = models.CharField(max_length=255, unique=True)
    surface_repaired = models.CharField(max_length=255, blank=True, null=True)
    date = models.DateField(blank=True, null=True)
    job_identity = models.CharField(
        max_length=50,
        choices=[
            ('chrome_plate', 'Chrome Plate'),
            ('cadmium_plate', 'Cadmium Plate'),
            ('etch', 'Etch'),
            ('anodize', 'Anodize'),
            ('paint', 'Paint'),
        ]
    )

    processing_standard = models.ForeignKey(Standard, on_delete=models.SET_NULL, blank=True, null=True)
    classification = models.ForeignKey(Classification, on_delete=models.SET_NULL, blank=True, null=True)


    def get_process_steps(self):
        # Retrieve the process for the selected standard and classification
        process = Process.objects.filter(
            standard=self.processing_standard,
            classification=self.classification
        ).first()
        return process.steps.all() if process else []
    
    class Meta:
        ordering = ['job_number']

    def __str__(self):
        return f"Job {self.job_number} for {self.part_detail.part.part_number}"
