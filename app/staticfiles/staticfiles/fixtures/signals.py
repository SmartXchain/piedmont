# signals.py

from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import Rack, PMTask, RackPMPlan

@receiver(post_save, sender=Rack)
def create_default_pm_plan(sender, instance, created, **kwargs):
    if created:
        default_tasks = PMTask.objects.all()
        for task in default_tasks:
            RackPMPlan.objects.create(
                rack=instance,
                task=task,
                due_every_days=task.frequency_days
            )
