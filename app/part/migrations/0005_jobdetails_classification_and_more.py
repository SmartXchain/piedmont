# Generated by Django 5.1.3 on 2024-12-02 22:27

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('part', '0004_jobdetails_job_identity'),
        ('standard', '0008_classification'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobdetails',
            name='classification',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='standard.classification'),
        ),
        migrations.AddField(
            model_name='jobdetails',
            name='processing_standard',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='standard.standard'),
        ),
    ]
