# Generated by Django 5.1.3 on 2024-12-17 19:14

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('part', '0009_alter_part_part_number'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobdetails',
            name='surface_area',
            field=models.FloatField(blank=True, null=True, verbose_name='Surface Area (sq inches)'),
        ),
    ]