from django.db import models


class Chemical(models.Model):
    name = models.CharField(max_length=255)
    sds_url = models.URLField(verbose_name="SDS Link")

    def __str__(self):
        return self.name


class HazComSection(models.Model):
    section_title = models.CharField(max_length=200)
    section_description = models.TextField()

    def __str__(self):
        return self.section_title
