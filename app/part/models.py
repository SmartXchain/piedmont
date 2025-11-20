from django.db import models
from django.core.exceptions import ValidationError
from django.db.models import UniqueConstraint, Q
from standard.models import Standard, Classification
from process.models import Process, ProcessStep
from django.utils import timezone


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
        if self.part_revision:
            return f"{self.part_number} Rev {self.part_revision}"
        return f"{self.part_number}"


class PartStandard(models.Model):
    """
    This model keeps track of which standards/classifications are assigned to a part.
    """
    part = models.ForeignKey(
        Part,
        on_delete=models.CASCADE,
        related_name='standards'
    )
    standard = models.ForeignKey(
        Standard,
        on_delete=models.CASCADE,
        related_name='part_standards'
    )
    classification = models.ForeignKey(
        Classification,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='part_standards'
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['part', 'standard', 'classification'],
                condition=Q(classification__isnull=True),
                name='unique_part_standard_with_classification'
            ),
            models.UniqueConstraint(
                fields=['part', 'standard'],
                condition=Q(classification__isnull=True),
                name='unique_part_standard_unclassified'
            )
        ]
        verbose_name = "Part Standard"
        verbose_name_plural = "Part Standards"
        ordering = ['part']

    def __str__(self):
        if self.classification:
            classification_info = f"{self.classification.class_name} - {self.classification.type}"
        else:
            classification_info = 'No Classification'
        return f"{self.part.part_number} - {self.standard.name} - {classification_info}"


class WorkOrder(models.Model):
    """
    Represents a work order for a part, tied to a standard + classification.
    Operators fill this out for each job.
    """
    part = models.ForeignKey(
        Part,
        on_delete=models.CASCADE,
        related_name='work_orders'
    )
    rework = models.BooleanField(default=False)

    job_identity = models.CharField(
        max_length=50,
        choices=[
            ('alkaline_clean', 'Alkaline Clean'),
            ('anodize', 'Anodize'),
            ('cadmium_plate', 'Cadmium Plate'),
            ('chemical_conversion', 'Chemical Conversion'),
            ('chrome_plate', 'Chrome Plate'),
            ('cleaning', 'Cleaning'),
            ('etch', 'Etch'),
            ('ni_plate', 'Nickel Plate'),
            ('paint', 'Paint'),
            ('passivation', 'Passivation'),
            ('solvent_clean', 'Solvent Clean'),
            ('strip', 'Strip')
        ]
    )

    # NOTE: same WO number can appear multiple times for different surface areas,
    # repairs, standards, etc.
    work_order_number = models.CharField(max_length=255)

    standard = models.ForeignKey(
        Standard,
        on_delete=models.PROTECT,
        related_name='work_orders'
    )
    classification = models.ForeignKey(
        Classification,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name='work_orders'
    )

    surface_repaired = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    customer = models.CharField(
        max_length=50,
        blank=True,
        null=True
    )

    purchase_order_with_revision = models.CharField(
        max_length=255,
        blank=True,
        null=True
    )

    part_quantity = models.PositiveIntegerField(
        blank=True,
        null=True
    )

    serial_or_lot_numbers = models.TextField(
        blank=True,
        null=True
    )

    # Operator-entered data for this WO run
    surface_area = models.FloatField(
        blank=True,
        null=True,
        verbose_name="Surface Area (sq in)"
    )

    date = models.DateField(blank=True, null=True)

    requires_masking = models.BooleanField(
        default=True,
        verbose_name="Masking Required"
    )

    requires_stress_relief = models.BooleanField(
        default=True,
        verbose_name="Stress Relief Required"
    )

    requires_hydrogen_relief = models.BooleanField(
        default=True,
        verbose_name="Hydrogen Embrittlement Relief Required"
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=[
                    'part',
                    'work_order_number',
                    'standard',
                    'classification',
                    'surface_repaired',
                ],
                name='unique_work_order_details'
            )
        ]
        ordering = ['work_order_number', 'part']
        verbose_name = "Work Order"
        verbose_name_plural = "Work Orders"

    # Business logic / helpers

    def get_process_steps(self):
        """
        Retrieve process steps for the work order based on standard and classification.
        Returns a QuerySet of ProcessStep objects with related Method prefetched.
        """
        # 1. Find the Process ID efficiently
        process_id_qs = Process.objects.filter(
            standard=self.standard,
            classification=self.classification
        ).values_list('id', flat=True).first()

        if not process_id_qs:
            return []

        # 2. Fetch the steps for that Process ID, prefetching the Method to avoid N+1 queries.
        return ProcessStep.objects.filter(
            process_id=process_id_qs
        ).select_related('method').all()

    def _has_rectified_step(self):
        """
        Return True if any step in this WO's process is a processing-tank
        method that is marked rectified.
        """
        steps = self.get_process_steps()
        for step in steps:
            m = step.method
            if m and m.method_type == "processing_tank" and m.is_rectified:
                return True
        return False

    def _get_current_density_for_job(self):
        """
        Pull the correct current density / ASF from the classifcation,
        depending on the job_identity.
        Returns (strike_asf, plate_asf)
        """
        if not self.classification:
            return (None, None)

        strike_asf = self.classification.strike_asf
        plate_asf = self.classification.plate_asf

        return (strike_asf, plate_asf)

    def _calc_amps(self):
        """
        Calculate strike and plate amps required based on Classification ASF and
        surface area. Results are stashed on the instance (_plate_amps, _strike amps).
        """
        if self.surface_area is None or not self.classification:
            self._plate_amps = None
            self._strike_amps = None
            return None

        plate_amps = None
        strike_amps = None

        # 1) use classification ASF if available

        # convert in2 to ft2
        surface_area_ft2 = float(self.surface_area) / 144.0

        if self.classification.plate_asf:
            plate_amps = surface_area_ft2 * float(self.classification.plate_asf)

        if self.classification.strike_asf:
            strike_amps = surface_area_ft2 * float(self.classification.strike_asf)

        # stash on the instance so the view can read it later
        self._plate_amps = plate_amps
        self._strike_amps = strike_amps

        return plate_amps

    def clean(self):
        """
        Ensure required fields are present for rectified processing tanks,
        and calculate amps only when it's actually needed.
        """
        # if WO isn't tied to a part/standard yet, skip checks
        if not self.part_id or not self.standard_id:
            return

        needs_rectified = self._has_rectified_step()

        # rectified steps require surface area
        if needs_rectified and self.surface_area is None:
            raise ValidationError("Surface Area is required for rectified processing tanks.")

        # if rectified, try to calculate amps (won't error if data is missing)
        if needs_rectified:
            self._calc_amps()

    def save(self, *args, **kwargs):
        # run our validation / amps logic before save
        self.clean()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Work Order {self.work_order_number} for {self.part.part_number} - {self.standard.name}"


class PDFSettings(models.Model):
    """Model to store dynamic footer content for PDF generation."""
    doc_id = models.CharField(max_length=255, default="CPTS")
    revision = models.CharField(max_length=50, default="0")
    date = models.DateField(default=timezone.now)
    repair_station = models.CharField(max_length=255, default="QKPR504X")
    footer_text = models.TextField(blank=True, help_text="Additional footer content")

    class Meta:
        verbose_name_plural = "PDF Settings"

    def __str__(self):
        return f"PDF Settings (Rev {self.revision})"
