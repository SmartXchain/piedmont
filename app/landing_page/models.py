from django.db import models


class CapabilityCategory(models.Model):
    name = models.CharField(max_length=100)

    def __str__(self):
        return self.name


class CapabilityTag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class AddOnTag(models.Model):
    name = models.CharField(max_length=100, unique=True)

    def __str__(self):
        return self.name


class AddOn(models.Model):
    name = models.CharField(max_length=255)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    tags = models.ManyToManyField(AddOnTag, blank=True, related_name='addons')

    def __str__(self):
        return f"{self.name} (${self.price})"


class Capability(models.Model):
    name = models.CharField(max_length=255)
    standard = models.CharField(max_length=255)
    category = models.ForeignKey(CapabilityCategory, on_delete=models.CASCADE)
    tags = models.ManyToManyField(CapabilityTag, blank=True, related_name='capabilities')
    addons = models.ManyToManyField(AddOn, blank=True)

    # Pricing fields
    cost_usd = models.DecimalField(max_digits=10, decimal_places=2)
    setup_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    size_adjustment = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    material_surcharge = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    testing_cert_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    post_process_cost = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    env_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    base_job_setup_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    min_per_part_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    simple_part_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    complex_part_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)

    def total_cost(self):
        return round(
            self.cost_usd
            + self.setup_cost
            + self.size_adjustment
            + self.material_surcharge
            + self.testing_cert_cost
            + self.post_process_cost
            + self.env_fee,
            2
        )

    def total_addon_cost(self):
        return sum(addon.price for addon in self.addons.all())

    def total_with_addons(self):
        return self.total_cost() + self.total_addon_cost()

    def __str__(self):
        return self.standard
