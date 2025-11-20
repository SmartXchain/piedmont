from django.db import models

# These are NADCAP process parameters to be recorded
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
    ('Anodize', 'Anodize'),
    ('Sealing/Dying', 'Sealing/Dying'),
    ('Barrel Plating', 'Barrel Plating'),
    ('Brush Plating', 'Brush Plating'),
    ('Electroplating', 'Electroplating'),
    ('Painting/Dry Film Coating', 'Painting/Dry Film Coating'),
    ('Thermal Treatment', 'Thermal Treatment'),
    ('Vacuum Cadmium/Aluminum IVD', 'Vacuum Cadmium/Aluminum IVD'),
    ('Stress Relieve', 'Stress Relieve'),
    ('Hydrogen Embrittlement Relief', 'Hydrogen Embrittlement Relief'),
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

    # --- Process / bath / tank parameters ---
    tank_name = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Tank name / line position / station ID if applicable."
    )

    temp_min = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Minimum bath °F."
    )
    temp_max = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Maximum bath °F."
    )

    immersion_time_min = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Minimum contact/immersion time."
    )
    immersion_time_max = models.DecimalField(
        max_digits=7,
        decimal_places=2,
        blank=True,
        null=True,
        help_text="Maximum contact/immersion time."
    )

    chemical = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Bath chemistry / product / material callout."
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

    is_stress_relief_operation = models.BooleanField(
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
        # making the title field unique and prevent duplicate title definitions
        constraints = [
            models.UniqueConstraint(
                fields=['title'],
                name='unique_method_title'
            )
        ]

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
        max_length=100,
        choices=TITLE_CHOICES,
        help_text="Category this template applies to."
    )
    description = models.TextField(
        blank=True,
        help_text="What must be written on the tech sheet (e.g. 'Record immersion time (sec)')."
    )
    is_nadcap_required = models.BooleanField(
        default=False,
        help_text="Check if this is Nadcap / customer required."
    )

    class Meta:
        verbose_name = "Parameter Template"
        verbose_name_plural = "Parameter Templates"
        ordering = ['category']
        # making the category field unique and prevent duplicate template definitions
        constraints = [
            models.UniqueConstraint(
                fields=['category'],
                name='unique_parameter_template_category'
            )
        ]

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
