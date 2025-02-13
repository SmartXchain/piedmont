# models.py
from django.db import models
import datetime
import timedelta


class Chemical(models.Model):
    name = models.CharField(max_length=100)
    quantity = models.PositiveIntegerField()
    lot_number = models.CharField(max_length=50)
    expiry_date = models.DateField()

    @property
    def status(self):
        now = datetime.now().date()
        expiring_soon_threshold = now + timedelta(days=7)

        if self.expiry_date < now:
            return 'Expired'
        elif now <= self.expiry_date <= expiring_soon_threshold:
            return 'Expiring Soon'
        else:
            return 'Available'

    def __str__(self):
        return self.name
