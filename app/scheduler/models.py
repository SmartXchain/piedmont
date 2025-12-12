# scheduler/models.py
from __future__ import annotations

from django.db import models


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

    work_order = models.CharField(max_length=100, unique=True)
    part_number = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()

    # Link to the process template
    process = models.ForeignKey(
        "process.Process",
        on_delete=models.PROTECT,
        related_name="manufacturing_orders"
    )

    # When the work is intended to start
    planned_start_time = models.DateTimeField()

    status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS_CHOICES,
        default="planned"
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Manufacturing Order"
        verbose_name_plural = "Manufacturing Orders"
        ordering = ["planned_start_time"]

    def __str__(self) -> str:
        return f"WO {self.work_order} - {self.part_number}"


class DelayLog(models.Model):
    """Records manual time extensions and mandatory reasons."""

    order = models.ForeignKey(
        ManufacturingOrder,
        on_delete=models.CASCADE,
        related_name="delays"
    )
    # Refers to the step_number in the process
    step_number = models.PositiveIntegerField()
    added_minutes = models.PositiveIntegerField()
    reason = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.order.work_order} Step {self.step_number} Delay"
