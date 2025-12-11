from django.db import models
from django.utils import timezone
from django.contrib.auth import get_user_model

from process.models import Process, ProcessStep
from methods.models import Method

User = get_user_model()


class Resource(models.Model):
    RESOURCE_TYPE_CHOICES = [
        ('tank', 'Tank'),
        ('oven', 'Oven'),
        ('line', 'Line'),
        ('operator', 'Operator'),
        ('cell', 'Work Cell'),
    ]

    name = models.CharField(max_length=100)
    resource_type = models.CharField(max_length=20, choices=RESOURCE_TYPE_CHOICES)
    # Optional: capacity, department, etc.
    department = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.get_resource_type_display()})"

class ManufacturingOrder(models.Model):
    """
    Top-level manufacturing / production order.
    """

    # routing selection
    process = models.ForeignKey(
        Process,
        on_delete=models.PROTECT,
        related_name='manufacturing_orders',
        help_text="Process routing to use for this work order"
    )

    work_order = models.CharField(
        max_length=100,
        unique=True,
        help_text="Manufacturing work order number"
    )
    part_number = models.CharField(max_length=100)
    part_description = models.CharField(max_length=255, blank=True)
    quantity = models.PositiveIntegerField()

    start_date = models.DateField(null=True, blank=True)
    due_date = models.DateField(null=True, blank=True)
    estimated_finish_date = models.DateField(null=True, blank=True)

    assigned_to = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='manufacturing_orders',
        help_text="Primary operator / owner"
    )

    ORDER_STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('scheduled', 'Scheduled'),
        ('in_progress', 'In Progress'),
        ('done', 'Done'),
        ('hold', 'On Hold'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(
        max_length=20,
        choices=ORDER_STATUS_CHOICES,
        default='planned'
    )

    PART_STATUS_CHOICES = [
        ('not_received', 'Not Received'),
        ('received', 'Received'),
        ('not_booked', 'Not Booked'),
        ('booked', 'Booked'),
    ]
    part_status = models.CharField(
        max_length=20,
        choices=PART_STATUS_CHOICES,
        default='not_received'
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['due_date', 'work_order']

    def __str__(self):
        return f"WO {self.work_order} – {self.part_number} x{self.quantity}"

    @property
    def is_late(self):
        return (
            self.due_date
            and self.status not in ['done', 'cancelled']
            and timezone.localdate() > self.due_date
        )


class Operation(models.Model):
    """
    One scheduled piece of work for a job on a single resource.
    Typically corresponds 1:1 with a ProcessStep for that manufacturing order.
    """

    manufacturing_order = models.ForeignKey(
        ManufacturingOrder,
        on_delete=models.CASCADE,
        related_name='operations'
    )

    process_step = models.ForeignKey(
        ProcessStep,
        on_delete=models.PROTECT,
        related_name='operations'
    )

    method = models.ForeignKey(
        Method,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='operations'
    )

    resource = models.ForeignKey(
        Resource,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='operations'
    )

    sequence = models.PositiveIntegerField(
        help_text="Order of this operation within the routing"
    )

    planned_start = models.DateTimeField()
    planned_end = models.DateTimeField()

    STATUS_CHOICES = [
        ('planned', 'Planned'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('hold', 'On Hold'),
        ('cancelled', 'Cancelled'),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='planned'
    )

    # Optional: actual timestamps
    actual_start = models.DateTimeField(null=True, blank=True)
    actual_end = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['manufacturing_order', 'sequence']
        unique_together = [('manufacturing_order', 'sequence')]

    def __str__(self):
        return f"{self.manufacturing_order.work_order} - Op {self.sequence} ({self.process_step})"

    @property
    def duration_minutes(self):
        return (self.planned_end - self.planned_start).total_seconds() / 60.0

