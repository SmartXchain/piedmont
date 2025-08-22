from django.utils import timezone
from django.db import IntegrityError, transaction
from .models import DailyTaskTemplate, DailyTask


def ensure_daily_instances_for(date=None):
    """Create a DailyTask for every active template for the given date if missing."""
    if date is None:
        date = timezone.localdate()
    templates = DailyTaskTemplate.objects.filter(active=True).only("id")
    for tpl in templates:
        try:
            with transaction.atomic():
                DailyTask.objects.get_or_create(template=tpl, scheduled_for=date)
        except IntegrityError:
            # Another request created it concurrently; ignore
            pass
