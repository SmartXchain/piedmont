from django.db import models

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
    # NOTE:
    # Your original had "FOD Inpsection".
    # I'm using "FOD Inspection" here for clarity.
    # If you ALREADY have production data that uses the misspelled string,
    # keep the old spelling to avoid mapping/migration.
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
    Examples:
    - "Alkaline Clean – Tank 3"
    - "Masking for Cad Plate"
    - "Hydrogen Embrittlement Relief Bake"
    This model defines how to run the step, not the measured results.
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


class ParameterToBeRecorded(models.Model):
    """
    A required blank/checkpoint the operator must record by hand for this Method step.
    These are driven by Nadcap / customer requirements. We are NOT storing
    the actual measured values in the system — we're defining what must
    appear on the printed instruction/traveler so the operator can fill it in.

    Example rows for a plating step:
    - "Plating current (amps)"
    - "Surface area (in^2)"
    - "Time in bath (minutes)"
    - "Start bake time / End bake time"
    - "Oven temperature"
    """

    # Which general operation category this parameter is associated with.
    # This helps you reuse patterns (e.g. 'Anodize', 'Electroplating', 'Hydrogen Embrittlement Relief').
    title = models.CharField(
        max_length=255,
        choices=TITLE_CHOICES,
        help_text="Which type of operation this recordable applies to."
    )

    # What does the operator actually have to write down?
    description = models.TextField(
        blank=True,
        help_text="Instruction for the blank line, e.g. 'Record plating current (amps)'."
    )

    # Unit label to show next to the blank on the traveler (amps, °F, minutes, etc.).
    unit = models.CharField(
        max_length=50,
        blank=True,
        null=True,
        help_text="Optional unit text to print next to the blank (°F, amps, min, etc.)."
    )

    # Mark if this is explicitly a Nadcap-mandatory recorded parameter.
    is_nadcap_required = models.BooleanField(
        default=False,
        help_text="Required by Nadcap / customer audit? If yes, traveler can highlight it."
    )

    # Link this parameter requirement to the specific Method step.
    method = models.ForeignKey(
        Method,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="recorded_parameters",
        help_text="Which Method step this applies to."
    )

    class Meta:
        verbose_name = "Recorded Parameter"
        verbose_name_plural = "Recorded Parameters"

    def __str__(self):
        return f"{self.title} ({self.method})"

