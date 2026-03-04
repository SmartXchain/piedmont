from django.db import models
from django.conf import settings
from django.utils import timezone
from standard.models import PeriodicTest
from methods.models import Method


class FailureLog(models.Model):
    PASS_FAIL_CHOICES = [
        ('Pass', 'Pass'),
        ('Fail', 'Fail'),
    ]

    TEST_TYPE_CHOICES = [
        ('Replacement', 'Replacement'),
        ('Retest', 'Retest'),
    ]

    test_report_number = models.CharField(max_length=100)
    test_date = models.DateField()
    original_po = models.CharField(max_length=50, blank=True, null=True)
    test_result = models.CharField(max_length=4, choices=PASS_FAIL_CHOICES)
    failure_reason = models.TextField(verbose_name="Reason for Failure & Investigation")
    investigated_by = models.CharField(max_length=100)

    test_type = models.CharField(max_length=20, choices=TEST_TYPE_CHOICES)
    retest_report_number = models.CharField(max_length=100, blank=True, null=True)
    retest_date = models.DateField(blank=True, null=True)
    retest_po = models.CharField(max_length=50, blank=True, null=True)
    retest_result = models.CharField(max_length=4, choices=PASS_FAIL_CHOICES, blank=True, null=True)

    evidence_of_trend = models.TextField(blank=True, null=True)
    reviewed_by = models.CharField(max_length=100)

    class Meta:
        ordering = ['-test_date']

    def __str__(self):
        return f"Failure Log - {self.test_report_number}"


class DailyTaskTemplate(models.Model):
    """Created by Engineers/Quality once; auto-generates a task instance every day."""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    active = models.BooleanField(default=True)

    created_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name="daily_task_templates_created"
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class DailyTask(models.Model):
    """Concrete daily occurrence that operators sign off."""
    RESULT_CHOICES = [
        ("pass", "Pass"),
        ("fail", "Fail"),
    ]

    template = models.ForeignKey(DailyTaskTemplate, on_delete=models.CASCADE, related_name="instances")
    scheduled_for = models.DateField(db_index=True, default=timezone.localdate)

    # Operator sign-off
    completed = models.BooleanField(default=False)
    result = models.CharField(max_length=4, choices=RESULT_CHOICES, blank=True, null=True)
    note = models.TextField(blank=True)

    completed_at = models.DateTimeField(blank=True, null=True)
    completed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, blank=True, null=True,
        on_delete=models.SET_NULL, related_name="daily_tasks_signed"
    )

    class Meta:
        unique_together = ("template", "scheduled_for")
        ordering = ["template__name"]

    def __str__(self):
        return f"{self.template.name} — {self.scheduled_for}"


# periodic_testing/models.py
class PeriodicTestTank(models.Model):
    """
    Binds a Standard periodic test requirement (PeriodicTest) to a specific tank Method.
    This gives you: Specification (from PeriodicTest) -> Tank Name (from Method).
    """

    periodic_test = models.ForeignKey(
        PeriodicTest,
        on_delete=models.CASCADE,
        related_name="tank_links",
        db_index=True,
    )

    # Tank comes from Process -> ProcessStep -> Method; we store the Method here.
    tank_method = models.ForeignKey(
        Method,
        on_delete=models.PROTECT,
        related_name="periodic_test_links",
        db_index=True,
        help_text="Select the tank Method that this periodic test applies to.",
    )

    active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["periodic_test", "tank_method"],
                name="uniq_periodic_test_per_tank_method",
            )
        ]
        ordering = ["periodic_test__standard__name", "periodic_test__name", "tank_method__title"]

    def __str__(self) -> str:
        return f"{self.periodic_test.standard.name} — {self.periodic_test.name} — {self.tank_label}"

    @property
    def tank_label(self) -> str:
        # Prefer explicit tank_name if you use it, else fall back to method title
        return self.tank_method.tank_name or self.tank_method.title


class TankPanelSerial(models.Model):
    """
    Serial numbers (Panels' S/N) stored under each Specification->Tank link.
    So: PeriodicTest (spec) -> Tank Method -> Serial Numbers.
    """

    tank_link = models.ForeignKey(
        PeriodicTestTank,
        on_delete=models.CASCADE,
        related_name="panel_serials",
        db_index=True,
    )

    serial_number = models.CharField(
        max_length=255,
        db_index=True,
        verbose_name="Panels' S/N",
    )

    active = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["tank_link", "serial_number"],
                name="uniq_panel_serial_per_tank_link",
            )
        ]
        ordering = ["tank_link__id", "serial_number"]

    def __str__(self) -> str:
        return f"{self.tank_link.tank_label} — {self.serial_number}"


class PeriodicTestTankResult(models.Model):
    """
    Monthly (or other frequency) execution record per Specification->Tank link.
    Stores pass/fail, reviewed by, pdf.
    """

    tank_link = models.ForeignKey(
        PeriodicTestTank,
        on_delete=models.CASCADE,
        related_name="results",
        db_index=True,
    )

    performed_on = models.DateField(default=timezone.localdate, db_index=True)

    performed_by = models.CharField(max_length=255, blank=True, null=True)

    reviewed_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        blank=True,
        null=True,
        related_name="periodic_tank_results_reviewed",
    )

    passed = models.BooleanField(default=True)

    report_pdf = models.FileField(
        upload_to="periodic_tests/",
        blank=True,
        null=True,
    )

    # You can test one or many panels in a report; keep it flexible:
    panels_used = models.ManyToManyField(
        TankPanelSerial,
        blank=True,
        related_name="results_used_in",
    )

    notes = models.TextField(blank=True, null=True)

    class Meta:
        ordering = ["-performed_on", "-id"]

        # Optional but very useful: prevent duplicates for the same month.
        # If you want this, tell me and I’ll add the clean month-key constraint.
        # constraints = []

    def __str__(self) -> str:
        status = "Pass" if self.passed else "Fail"
        return f"{self.tank_link.tank_label} — {self.performed_on} — {status}"
