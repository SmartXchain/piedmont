# customer_links/models.py
from django.db import models


class CustomerLink(models.Model):
    LINK_TYPE_CHOICES = [
        ('spec', 'Specification Lookup'),
        ('change', 'Engineering Change Request'),
    ]

    name = models.CharField(max_length=100)
    url = models.URLField()
    link_type = models.CharField(max_length=10, choices=LINK_TYPE_CHOICES)
    description = models.TextField(blank=True)

    def __str__(self):
        return f"{self.name} ({self.get_link_type_display()})"
