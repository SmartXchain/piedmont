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
            models.UniqueConstraint(
                fields=['part_number', 'part_revision'],
                name='unique_part_revision'
            )
        ]
        verbose_name = "Part"
        verbose_name_plural = "Parts"
        ordering = ['part_number']

    def __str__(self):
        return f"{self.part_number}"


class PartStandard(models.Model):
    """
    This model keeps track of which standards/classifications are assigned to a part.
    """
    part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name='standards')
    standard = models.ForeignKey(Standard, on_delete=models.CASCADE, related_name='part_standards')
    classification = models.ForeignKey(Classification, on_delete=models.CASCADE, blank=True, null=True, related_name='part_standards')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['part', 'standard', 'classification'],
                name='unique_part_standard_classification'
            )
        ]
        verbose_name = "Part Standard"
        verbose_name_plural = "Part Standards"
        ordering = ['part']

    def __str__(self):
        return f"{self.part.part_number} - {self.standard.name} - {self.classification or 'No Classification'}"


class WorkOrder(models.Model):
    """
    Represents a work order for a part, associated with a specific standard/classification.
    """
    part = models.ForeignKey(Part, on_delete=models.CASCADE, related_name='work_orders')
    rework = models.BooleanField(default=False)
    job_identity = models.CharField(
        max_length=50,
        choices=[
            ('alkaline clean', 'Alkaline Clean'),
            ('anodize', 'Anodize'),
            ('cadmium_plate', 'Cadmium Plate'),
            ('chemical conversion', 'Chemical Conversion'),
            ('chrome_plate', 'Chrome Plate'),
            ('cleaning', 'Cleaning'),
            ('etch', 'Etch'),
            ('ni_plate', 'Nickel Plate'),
            ('paint', 'Paint'),
            ('passivation', 'Passivation'),
            ('solvent_clean', 'Solvent Clean'),
            ('Strip', 'Strip')
        ]
    )
    work_order_number = models.CharField(max_length=255)  # Allow duplicates with different standards/classifications/surface_repaired
    standard = models.ForeignKey(Standard, on_delete=models.CASCADE, related_name='work_orders')
    classification = models.ForeignKey(Classification, on_delete=models.CASCADE, blank=True, null=True, related_name='work_orders')
    surface_repaired = models.CharField(max_length=255, blank=True, null=True)

    customer = models.CharField(max_length=50, blank=True, null=True)
    purchase_order_with_revision = models.CharField(max_length=255, blank=True, null=True)
    part_quantity = models.PositiveIntegerField(blank=True, null=True)
    serial_or_lot_numbers = models.TextField(blank=True, null=True)
    surface_area = models.FloatField(blank=True, null=True, verbose_name="Surface Area (sq in)")
    date = models.DateField(blank=True, null=True)
    current_density = models.FloatField(blank=True, null=True, verbose_name="Current Density (amps/sq in)")
    amps = models.FloatField(blank=True, null=True, verbose_name="Amps Required")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['part', 'work_order_number', 'standard', 'classification', 'surface_repaired'],
                name='unique_work_order_details'
            )
        ]
        ordering = ['work_order_number', 'part']
        verbose_name = "Work Order"
        verbose_name_plural = "Work Orders"

    def get_process_steps(self):
        """Retrieve process steps for the work order based on standard and classification."""
        process = Process.objects.select_related('standard', 'classification').filter(
            standard=self.standard,
            classification=self.classification
        ).first()
        return process.steps.all() if process else []

    def clean(self):
        """Ensure required fields are present for rectified processing tanks."""
        if not self.part_id:
            return

        process_steps = self.get_process_steps()
        rectified_steps = [step for step in process_steps if step.method.method_type == 'processing_tank' and step.method.is_rectified]

        if rectified_steps:
            if self.surface_area is None:
                raise ValidationError("Surface Area is required for rectified processing tanks.")
            if self.job_identity in ['cadmium_plate', 'chrome_plate']:
                self.amps = self.surface_area * self.current_density if self.job_identity == 'chrome_plate' else self.surface_area / 144 * self.current_density

    def save(self, *args, **kwargs):
        """Ensure validation is applied before saving."""
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Work Order {self.work_order_number} for {self.part.part_number} - {self.standard.name}"


class PDFSettings(models.Model):
    """Model to store dynamic footer content for PDF generation."""
    doc_id = models.CharField(max_length=255, default="CPTS")
    revision = models.CharField(max_length=50, default="0")
    date = models.DateField()
    repair_station = models.CharField(max_length=255, default="QKPR504X")
    footer_text = models.TextField(blank=True, help_text="Additional footer content")

    def __str__(self):
        return f"PDF Settings (Rev {self.revision})"
