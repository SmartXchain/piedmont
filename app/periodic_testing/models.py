from django.db import models
from django.conf import settings
from django.utils import timezone


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

