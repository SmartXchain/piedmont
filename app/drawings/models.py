# drawings/models.py
from __future__ import annotations

from decimal import Decimal

from django.conf import settings
from django.core.exceptions import ValidationError
from django.core.validators import MinValueValidator
from django.db import models
from django.db.models import UniqueConstraint


class Drawing(models.Model):
    """
    A controlled technical drawing PDF with revision tracking.
    """
    drawing_number = models.CharField(max_length=100, db_index=True)
    title = models.CharField(max_length=255, blank=True)
    revision = models.CharField(max_length=50, db_index=True)
    pdf_file = models.FileField(upload_to="drawings/")
    is_active = models.BooleanField(default=True)

    uploaded_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="uploaded_drawings",
    )
    uploaded_at = models.DateTimeField(auto_now_add=True)

    effective_date = models.DateField(blank=True, null=True)
    superseded_date = models.DateField(blank=True, null=True)

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["drawing_number", "-uploaded_at"]
        constraints = [
            UniqueConstraint(
                fields=["drawing_number", "revision"],
                name="uniq_drawing_number_revision",
            )
        ]

    def __str__(self) -> str:
        return f"{self.drawing_number} Rev {self.revision}"


class DrawingZone(models.Model):
    """
    Engineer-defined selectable zone.

    Geometry is stored in normalized coordinate space (0..1) so it is
    resolution-independent.
    """
    UNIT_CHOICES = [
        ("in2", "in²"),
        ("ft2", "ft²"),
    ]

    GEOM_TYPE_CHOICES = [
        ("polygon", "Polygon"),
        ("rect", "Rectangle"),
    ]

    PLATING_TYPE_CHOICES = [
        ("chrome", "Chrome Plate"),
        ("nickel", "Nickel Plate"),
        ("cadmium", "Cadmium Plate"),
    ]

    drawing = models.ForeignKey(
        Drawing,
        on_delete=models.CASCADE,
        related_name="zones",
        db_index=True,
    )

    plating_type = models.CharField(
        max_length=20,
        choices=PLATING_TYPE_CHOICES,
        db_index=True,
        help_text="Plating type for this zone (set by annotation session).",
    )

    # Single-page PDFs now, but leaving page_number keeps your code stable.
    page_number = models.PositiveIntegerField(
        validators=[MinValueValidator(1)],
        default=1,
        help_text="1-based page number in the PDF (defaults to 1).",
        db_index=True,
    )

    label = models.CharField(max_length=120)
    geom_type = models.CharField(
        max_length=20,
        choices=GEOM_TYPE_CHOICES,
        default="polygon",
    )

    geometry = models.JSONField(
        help_text="Normalized SVG geometry in 0..1 coordinates."
    )

    area_value = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        validators=[MinValueValidator(0)],
    )
    area_unit = models.CharField(
        max_length=10,
        choices=UNIT_CHOICES,
        default="in2",
    )

    is_exclusion_zone = models.BooleanField(
        default=False,
        help_text="If true, subtracts from plating area when selected.",
    )
    default_selected = models.BooleanField(
        default=True,
        help_text="Default selection state for operators.",
    )

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_drawing_zones",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    notes = models.TextField(blank=True)

    class Meta:
        ordering = ["drawing", "plating_type", "page_number", "id"]
        indexes = [
            models.Index(fields=["drawing", "plating_type"]),
            models.Index(fields=["drawing", "plating_type", "page_number"]),
        ]

    def __str__(self) -> str:
        return f"{self.drawing} [{self.plating_type}] p{self.page_number}: {self.label}"


class PlatingAreaCard(models.Model):
    """
    One-and-only-one card per (drawing, plating_type).
    Stores totals for audit/revision control.
    """
    PLATING_TYPE_CHOICES = DrawingZone.PLATING_TYPE_CHOICES
    UNIT_CHOICES = DrawingZone.UNIT_CHOICES

    drawing = models.ForeignKey(
        Drawing,
        on_delete=models.PROTECT,
        related_name="plating_cards",
        db_index=True,
    )

    plating_type = models.CharField(
        max_length=20,
        choices=PLATING_TYPE_CHOICES,
        db_index=True,
    )

    # Optional linkage points
    part_number = models.CharField(max_length=100, blank=True, db_index=True)

    gross_area_value = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        validators=[MinValueValidator(0)],
        default=Decimal("0.0000"),
    )
    excluded_area_value = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        validators=[MinValueValidator(0)],
        default=Decimal("0.0000"),
    )
    net_area_value = models.DecimalField(
        max_digits=12,
        decimal_places=4,
        validators=[MinValueValidator(0)],
        default=Decimal("0.0000"),
    )
    area_unit = models.CharField(
        max_length=10,
        choices=UNIT_CHOICES,
        default="in2",
    )

    basis = models.CharField(max_length=50, blank=True)
    assumptions = models.TextField(blank=True)
    drawing_reference = models.CharField(max_length=100, blank=True)

    approved_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="approved_plating_cards",
    )
    approved_at = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="created_plating_cards",
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["drawing", "plating_type"]
        constraints = [
            UniqueConstraint(
                fields=["drawing", "plating_type"],
                name="uniq_card_drawing_platingtype",
            )
        ]
        indexes = [
            models.Index(fields=["drawing", "plating_type"]),
        ]

    def __str__(self) -> str:
        return f"Plating Area Card: {self.drawing} [{self.plating_type}]"


class PlatingCardZoneSelection(models.Model):
    """
    Links the single card for a (drawing, plating_type) to its zones.
    """
    plating_card = models.ForeignKey(
        PlatingAreaCard,
        on_delete=models.CASCADE,
        related_name="zone_selections",
    )
    zone = models.ForeignKey(
        DrawingZone,
        on_delete=models.CASCADE,
        related_name="plating_card_links",
    )
    selected = models.BooleanField(default=True)

    class Meta:
        constraints = [
            UniqueConstraint(
                fields=["plating_card", "zone"],
                name="uniq_platingcard_zone",
            )
        ]

    def clean(self) -> None:
        if not self.zone_id or not self.plating_card_id:
            return

        if self.zone.drawing_id != self.plating_card.drawing_id:
            raise ValidationError("Zone drawing must match card drawing.")
        if self.zone.plating_type != self.plating_card.plating_type:
            raise ValidationError("Zone plating_type must match card plating_type.")

    def __str__(self) -> str:
        state = "on" if self.selected else "off"
        return f"{self.plating_card_id} -> {self.zone_id} ({state})"

