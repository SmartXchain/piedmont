# Generated by Django 5.1.3 on 2024-12-18 20:32

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('part', '0015_alter_jobdetails_unique_together_and_more'),
        ('standard', '0008_classification'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='jobdetails',
            unique_together={('part_detail', 'job_number', 'job_identity', 'surface_repaired', 'processing_standard', 'classification')},
        ),
        migrations.RemoveField(
            model_name='jobdetails',
            name='current_density',
        ),
    ]