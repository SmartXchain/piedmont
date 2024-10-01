from django.db import models

class Specification(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField()

    def __str__(self):
        return self.name

class Step(models.Model):
    specification = models.ForeignKey(Specification, related_name='steps', on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    description = models.TextField()
    is_optional = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name} (Optional: {self.is_optional})"
