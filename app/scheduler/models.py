# scheduler/models.py
from __future__ import annotations

from django.db import models
from django.db.models import Max
from django.utils import timezone


class ManufacturingOrder(models.Model):
    """
    The core work order model.
    Links a specific process to a timeline without duplicating steps.
    """

    ORDER_STATUS_CHOICES = [
        ("planned", "Planned"),
        ("in_progress", "In Progress"),
        ("done", "Done"),
        ("hold", "On Hold"),
    ]

    work_order = models.CharField(max_length=100)
    occurrence = models.PositiveIntegerField(default=1)

    part_number = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()

    process = models.ForeignKey(
        "process.Process",
        on_delete=models.PROTECT,
        related_name="manufacturing_orders",
    )

    planned_start_time = models.DateTimeField()

    status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS_CHOICES,
        default="planned",
    )
    completed_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Manufacturing Order"
        verbose_name_plural = "Manufacturing Orders"
        ordering = ["planned_start_time"]
        indexes = [
            models.Index(fields=["work_order", "occurrence"]),
        ]
        constraints = [
            models.UniqueConstraint(
                fields=["work_order", "occurrence"],
                name="uq_work_order_occurrence",
            )
        ]

    def __str__(self) -> str:
        return f"WO {self.work_order} #{self.occurrence} - {self.part_number}"

    def mark_done(self) -> None:
        if self.status != "done":
            self.status = "done"
            self.completed_at = timezone.now()
            self.save(update_fields=["status", "completed_at", "updated_at"])

    def save(self, *args, **kwargs) -> None:
        """
        Auto-assign occurrence for the same work_order.

        - If occurrence is left as default (1) on a NEW object, we assign next available.
        - If user explicitly sets occurrence != 1, we respect it.
        """
        is_new = self.pk is None

        if is_new and self.occurrence == 1:
            last = (
                ManufacturingOrder.objects.filter(work_order=self.work_order)
                .aggregate(m=Max("occurrence"))
                .get("m")
                or 0
            )
            self.occurrence = last + 1

        super().save(*args, **kwargs)


class DelayLog(models.Model):
    """Records manual time extensions and mandatory reasons."""

    order = models.ForeignKey(
        ManufacturingOrder,
        on_delete=models.CASCADE,
        related_name="delays",
    )
    step_number = models.PositiveIntegerField()
    added_minutes = models.PositiveIntegerField(default=0)
    reason = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-timestamp"]

    def __str__(self) -> str:
        return f"{self.order.work_order} Step {self.step_number} Delay"
