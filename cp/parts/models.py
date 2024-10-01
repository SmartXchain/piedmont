from django.db import models

class Part(models.Model):
    name = models.CharField(max_length=100)
    part_number = models.CharField(max_length=50)
    description = models.TextField()

    def __str__(self):
        return self.name
