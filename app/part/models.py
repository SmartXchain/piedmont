from django.db import models
from django.core.exceptions import ValidationError

from standard.models import Standard, Classification
from process.models import Process


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

    # NOTE: same WO number can appear multiple times for different surface areas,
    # repairs, standards, etc.
    work_order_number = models.CharField(max_length=255)

    standard = models.ForeignKey(
        Standard,
        on_delete=models.CASCADE,
        related_name='work_orders'
    )
    classification = models.ForeignKey(
        Classification,
        on_delete=models.CASCADE,
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

    #----------------------------------------------
    # Business logic / helpers
    #----------------------------------------------

    def get_process_steps(self):
        """
        Retrieve process steps for the work order 
        based on standard and classification.
        """
        process = Process.objects.select_related(
            'standard', 'classification'
        ).filter(
            standard=self.standard,
            classification=self.classification
        ).first()

        return process.steps.all() if process else []

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

    def _calc_amps_required(self):
        """
        Calculate amps based on:
            - surface_area (in2) from this work order
            - plate_asf (amp/ft2) from the classification
        This handles cad, ni, chrome, etc. because db is standardizing
        on ASF. Returns a float or None.
        """
        if self.surface_area is None:
            return None

        strike_asf, plate_asf = self._get_current_density_for_job()

        if self.job_identity in ["cadmium_plate", "ni_plate", "chrome_plate"]:
            if plate_asf:
                # Convert in2 to ft2
                surface_area_ft2 = float(self.surface_area) / 144.0
                self.amps = surface_area_ft2 * float(plate_asf)
            return
        return

    def _calc_amps(self):
        """
        Try to calculate amps when needed.

        Priority:
        1. If we have a classification with plate_asf / strike_asf, use that.
        2. Otherwise, if the model ends up having a 'current_density' field later, use SA * CD.
        3. Otherwise, just return None.

        We don't persist this to the DB here — we just make it available
        on the instance so views/templates can read it if they want.
        """
        if not self.surface_area:
            return None

        plate_amps = None
        strike_amps = None

        # 1) use classification ASF if available
        if self.classification and (
            self.classification.plate_asf or self.classification.strike_asf
        ):
            surface_area_ft2 = float(self.surface_area) / 144.0  # in² -> ft²
            if self.classification.plate_asf:
                plate_amps = surface_area_ft2 * float(self.classification.plate_asf)
            if self.classification.strike_asf:
                strike_amps = surface_area_ft2 * float(self.classification.strike_asf)

        # 2) fallback: if you later add current_density to the model
        elif hasattr(self, "current_density") and self.current_density:
            # this assumes current_density is already "amps per in²"
            plate_amps = float(self.surface_area) * float(self.current_density)

        # stash on the instance so the view can read it later if it wants
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
    date = models.DateField()
    repair_station = models.CharField(max_length=255, default="QKPR504X")
    footer_text = models.TextField(blank=True, help_text="Additional footer content")

    def __str__(self):
        return f"PDF Settings (Rev {self.revision})"
