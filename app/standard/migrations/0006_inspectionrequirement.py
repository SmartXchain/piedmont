# Generated by Django 5.1.3 on 2024-11-29 03:44

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('standard', '0005_alter_standard_upload_file'),
    ]

    operations = [
        migrations.CreateModel(
            name='InspectionRequirement',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('description', models.TextField()),
                ('standard', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='inspections', to='standard.standard')),
            ],
        ),
    ]