# Generated by Django 5.1.3 on 2024-12-18 17:50

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('part', '0011_alter_jobdetails_unique_together'),
        ('standard', '0008_classification'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='jobdetails',
            unique_together={('part_detail', 'job_identity', 'surface_repaired', 'processing_standard', 'classification')},
        ),
    ]