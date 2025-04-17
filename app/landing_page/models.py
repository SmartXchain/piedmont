# models.py
from django.db import models

class CapabilityCategory(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class Capability(models.Model):
    name = models.CharField(max_length=255)
    standard = models.CharField(max_length=255)
    category = models.ForeignKey(CapabilityCategory, on_delete=models.CASCADE)

    # Base pricing
    cost_usd = models.DecimalField(max_digits=10, decimal_places=2, help_text="Base process rate")

    # Breakdown fields
    setup_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    size_adjustment = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    material_surcharge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    testing_cert_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    post_process_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    env_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    # Expanded pricing fields
    base_job_setup_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    min_per_part_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    simple_part_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    complex_part_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    optional_addons = models.TextField(blank=True, help_text="Optional services or notes (e.g. expedited service, part marking)")

    def total_cost(self):
        return round(
            self.cost_usd +
            self.setup_cost +
            self.size_adjustment +
            self.material_surcharge +
            self.testing_cert_cost +
            self.post_process_cost +
            self.env_fee,
            2
        )

    def __str__(self):
        return self.standard
