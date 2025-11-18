from django.db import models

# This is your common process dictionary
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
    ('FOD Inspection', 'FOD Inspection'),
    ('Hydrogen Embrittlement Relief', 'Hydrogen Embrittlement Relief'),
    ('Masking', 'Masking'),
    ('Nickel Strip', 'Nickel Strip'),
    ('Oven Dry', 'Oven Dry'),
    ('Painting/Dry Film Coating', 'Painting/Dry Film Coating'),
    ('Passivation', 'Passivation'),
    ('Pre-Cleaning', 'Pre-Cleaning'),
    ('Pre-Pen Etching', 'Pre-Pen Etching'),
    ('Racking', 'Racking'),
    ('Rinsing', 'Rinsing'),
    ('Scrub Surface', 'Scrub Surface'),
    ('Sealing', 'Sealing'),
    ('Solvent Clean', 'Solvent Clean'),
    ('Spray Rinse', 'Spray Rinse'),
    ('Stress Relief', 'Stress Relief'),
    ('Strip', 'Strip'),
    ('Thermal Treatment', 'Thermal Treatment'),
    ('Unmasking', 'Unmasking'),
    ('Unracking', 'Unracking'),
    ('Vacuum Cadmium & Aluminum IVD', 'Vacuum Cadmium & Aluminum IVD'),
    ('Water-Break Test', 'Water-Break Test'),
]

METHOD_TYPE_CHOICES = [
    ('processing_tank', 'Processing Tank'),
    ('manual_method', 'Manual Method'),
]


class Method(models.Model):
    """
    A single work step an operator will perform.
    `title` stays free-form (prod-safe).
    `category` is the normalized bucket (from TITLE_CHOICES) we can use to auto-fill parameters.
    """

    method_type = models.CharField(
        max_length=50,
        choices=METHOD_TYPE_CHOICES,
        blank=True,
        help_text="How this step is executed (tank vs. manual, etc.)."
    )

    title = models.CharField(
        max_length=255,
        blank=True,
        help_text="Operation title. You can match one of the predefined titles or write your own."
    )

    category = models.CharField(
        max_length=255,
        choices=TITLE_CHOICES,
        blank=True,
        null=True,
        help_text="Select the process category to auto-attach required recorded parameters."
    )

    description = models.TextField(
        blank=True,
        help_text="Operator-facing work instruction / narrative for how to do this step."
    )

    # Helper list for UI use (not a DB field, just class-level metadata)
    PREDEFINED_TITLES = [title for title, _ in TITLE_CHOICES]

    # --- Process / bath / tank parameters ---
    tank_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Tank name / line position / station ID if applicable."
    )

    temp_min = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Minimum bath or oven temperature (°F or °C per your standard)."
    )
    temp_max = models.DecimalField(
        max_digits=5,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Maximum bath or oven temperature."
    )

    immersion_time_min = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Minimum contact/immersion time. Units defined by your SOP."
    )
    immersion_time_max = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Maximum contact/immersion time."
    )

    chemical = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Bath chemistry / product / material callout (optional)."
    )

    is_rectified = models.BooleanField(
        default=False,
        help_text="Check if this step uses a rectifier (current-controlled step like electroclean or plate)."
    )

    is_strike_etch = models.BooleanField(
        default=False,
        help_text="Check if this is a strike / activation / etch prior to plating."
    )

    rectifier_notes = models.TextField(
        blank=True,
        null=True,
        help_text="Ramp rate, ASF, volts, anode/cathode setup, polarity, etc."
    )

    # --- Flags for downstream routing / traveler formatting ---
    is_masking_operation = models.BooleanField(
        default=False,
        help_text="True if this is masking, demasking, tape, or stop-off application/removal."
    )

    is_bake_operation = models.BooleanField(
        default=False,
        help_text="True if this step is an oven/bake/stress-relief/thermal soak."
    )

    is_hydrogen_relief_operation = models.BooleanField(
        default=False,
        help_text="True if this bake is specifically Hydrogen Embrittlement Relief after plating."
    )

    class Meta:
        verbose_name = "Method"
        verbose_name_plural = "Methods"
        ordering = ['title']

    def __str__(self):
        # ex: "Anodize (processing_tank)" or "Masking (manual_method)"
        return f"{self.title} ({self.method_type})"

    def create_required_parameters_from_template(self):
        """
        Creates instances of required ParameterToBeRecored from ParameterTemplate
        based on the Method's Category.
        """
        if not self.category:
            return

        if self.recorded_parameters.exists():
            # do not duplicate if they alreay exist
            return

        templates = ParameterTemplate.objects.filter(category=self.category)
        for tpl in templates:
            ParameterToBeRecorded.objects.create(
                description=tpl.description,
                unit=tpl.unit,
                is_nadcap_required=tpl.is_nadcap_required,
                method=self,
            )

    def save(self, *args, **kwargs):
        is_new = self.pk is None
        super().save(*args, **kwargs)
        # only auto-apply on first save so we don't duplicate
        if is_new:
            self.create_required_parameters_from_template()


class ParameterTemplate(models.Model):
    """
    Master list: for a given category (Anodize, Electroplating, Passivation...),
    what should the operator be required to record?
    """
    category = models.CharField(
        max_length=255,
        choices=TITLE_CHOICES,
        help_text="Category this template applies to."
    )
    description = models.TextField(
        blank=True,
        help_text="What must be written on the traveler (e.g. 'Record immersion time (sec)')."
    )
    unit = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Unit to show next to blank (°F, amps, min, sec, etc.)."
    )
    is_nadcap_required = models.BooleanField(
        default=False,
        help_text="Check if this is Nadcap / customer required."
    )

    class Meta:
        verbose_name = "Parameter Template"
        verbose_name_plural = "Parameter Templates"
        ordering = ['category']

    def __str__(self):
        label = self.description[:40] + "..." if self.description and len(self.description) > 40 else self.description
        return f"{self.category} – {label or 'parameter'}"


class ParameterToBeRecorded(models.Model):
    """
    Actual per-method rows that the traveler will print with blank lines.
    Usually auto-created from ParameterTemplate, but can be edited per method.
    """
    description = models.TextField(
        blank=True,
        help_text="Instruction for the blank line, e.g. 'Record plating current (amps)'."
    )
    unit = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Optional unit text to print next to the blank (°F, amps, min, etc.)."
    )
    is_nadcap_required = models.BooleanField(
        default=False,
        help_text="Required by Nadcap / customer audit? If yes, traveler can highlight it."
    )
    method = models.ForeignKey(
        Method,
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name="recorded_parameters",
        help_text="Which Method step this applies to."
    )

    class Meta:
        verbose_name = "Recorded Parameter"
        verbose_name_plural = "Recorded Parameters"
        constraints = [
            models.UniqueConstraint(
                fields=['method', 'description'],
                name='unique_param_per_method'
            )
        ]

    def __str__(self):
        return f"{self.method.category} – {self.description[:20]}"


