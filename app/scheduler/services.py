# scheduler/services.py
from datetime import timedelta

from django.utils import timezone

from process.models import ProcessStep
from .models import Operation


def build_initial_schedule_for_order(order, start_time=None, default_resource=None):
    """
    Build a continuous sequence of Operations for a ManufacturingOrder
    based on its selected Process and that process's steps/methods.

    - Uses step.method.touch_time_minutes + run_time_minutes (if present)
    - Makes each operation start exactly when the previous one ends
    """
    if start_time is None:
        # If order has a requested start_date, respect that at 08:00
        if order.start_date:
            start_dt = timezone.datetime.combine(
                order.start_date,
                timezone.datetime.min.time(),
            )
            start_time = timezone.make_aware(start_dt) + timedelta(hours=8)
        else:
            start_time = timezone.now()

    # Get steps for this process in order
    steps = (
        ProcessStep.objects
        .filter(process=order.process)
        .order_by("step_number")
    )

    current_start = start_time
    sequence = 1
    operations = []

    for step in steps:
        method = getattr(step, "method", None)

        # Pull time estimates from Method (if you have these fields)
        touch = getattr(method, "touch_time_minutes", 0) or 0
        run = getattr(method, "run_time_minutes", 0) or 0
        est_minutes = max(touch + run, 1)  # avoid zero-duration

        planned_end = current_start + timedelta(minutes=est_minutes)

        op = Operation.objects.create(
            manufacturing_order=order,
            process_step=step,
            method=method,
            resource=default_resource,  # choose based on method / tank later if needed
            sequence=sequence,
            planned_start=current_start,
            planned_end=planned_end,
        )
        operations.append(op)

        # Next operation starts exactly when this one ends → continuous
        current_start = planned_end
        sequence += 1

    # Mark order as scheduled if we created anything
    if operations:
        order.status = "scheduled"
        order.estimated_finish_date = current_start.date()
        order.save(update_fields=["status", "estimated_finish_date"])

    return operations

