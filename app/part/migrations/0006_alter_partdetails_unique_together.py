# Generated by Django 5.1.3 on 2024-12-03 00:41

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('part', '0005_jobdetails_classification_and_more'),
        ('standard', '0008_classification'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='partdetails',
            unique_together={('part', 'job_identity', 'processing_standard', 'classification')},
        ),
    ]