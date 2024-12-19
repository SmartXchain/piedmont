from django.db import models
from standard.models import Standard, Classification
from process.models import Process
from django.core.exceptions import ValidationError


class Part(models.Model):
    part_number = models.CharField(max_length=255)
    part_description = models.CharField(max_length=255)
    part_revision = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=['part_number', 'part_revision'], name='unique_part_revision')
        ]

    def get_process_steps(self, processing_standard, classification):
        from process.models import Process, ProcessStep

        # Fetch the process matching the standard and classification
        process = Process.objects.filter(
            standard=processing_standard,
            classification=classification
        ).first()

        # Return the process steps if a process exists
        if process:
            return ProcessStep.objects.filter(process=process).order_by('step_number')
        return []

    def __str__(self):
        return f"{self.part_number}"


class PartDetails(models.Model):
    part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name='details')
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

        return process.steps.all() if process else None

    class Meta:
        unique_together = ('part', 'job_identity', 'processing_standard', 'classification')  # Ensure uniqueness per part and job identity
        ordering = ['job_identity']

    def clean(self):
        # Ensure `part` is assigned before validation
        if not self.part_id:
            return  # Skip validation if `part` is not yet set

        # Validate uniqueness for the combination of fields
        if PartDetails.objects.filter(
            part=self.part,
            job_identity=self.job_identity,
            processing_standard=self.processing_standard,
            classification=self.classification
        ).exclude(id=self.id).exists():
            raise ValidationError("A part detail with the same job identity, processing standard, and classification already exists.")

    def save(self, *args, **kwargs):
        self.clean()  # Call the clean method for validation
        super().save(*args, **kwargs)

    def __str__(self):
        classification_display = str(self.classification) if self.classification else "No Classification"
        return f"{self.part.part_number} - {self.job_identity} - {self.processing_standard.name if self.processing_standard else 'No Standard'} - {classification_display}"


class JobDetails(models.Model):
    part_detail = models.ForeignKey(PartDetails, on_delete=models.CASCADE, related_name='jobs')
    job_number = models.CharField(max_length=255, unique=True)
    customer = models.CharField(max_length=50, blank=True, null=True)
    purchase_order_with_revision = models.CharField(max_length=255, blank=True, null=True)
    part_quantity = models.PositiveIntegerField(blank=True, null=True)
    serial_or_lot_numbers = models.TextField(blank=True, null=True)
    surface_repaired = models.CharField(max_length=255, blank=True, null=True)
    surface_area = models.FloatField(blank=True, null=True, verbose_name="Surface Area (sq in)")
    date = models.DateField(blank=True, null=True)
    current_density = models.FloatField(blank=True, null=True, verbose_name="Current density (amps/sq in)")
    amps = models.FloatField(blank=True, null=True, verbose_name="Amps Required")

    # Relationships to standards, classifications, and job identity
    processing_standard = models.ForeignKey(Standard, on_delete=models.SET_NULL, blank=True, null=True)
    classification = models.ForeignKey(Classification, on_delete=models.SET_NULL, blank=True, null=True)
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

    def clean(self):
        if self.part_detail:
            process_steps = self.part_detail.get_process_steps()
            for step in process_steps:
                if step.method.method_type == 'processing_tank' and step.method.is_rectified:
                    if self.surface_area is None:
                        raise ValidationError("Surface Area is required for rectified processing tanks.")
                    if self.job_identity == 'cad_plate':
                        self.amps = self.surface_area / 144 * self.current_density
                    if self.job_identity == 'chrome_plate':
                        self.amps = self.surface_area * self.current_density

    def get_process_steps(self):
        process = Process.objects.filter(
            standard=self.processing_standard,
            classification=self.classification
        ).first()
        return process.steps.all() if process else []

    def save(self, *args, **kwargs):
        self.clean()  # Validate before saving
        super().save(*args, **kwargs)

    class Meta:
        ordering = ['job_number']
        unique_together = ('part_detail', 'job_number', 'job_identity', 'surface_repaired', 'processing_standard', 'classification')  # Enforce uniqueness

    def __str__(self):
        return f"Job {self.job_number} for {self.part_detail.part.part_number}"
