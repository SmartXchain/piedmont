# Generated by Django 5.1.3 on 2024-12-19 12:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('part', '0018_alter_jobdetails_current_density_and_more'),
    ]

    operations = [
        migrations.AlterField(
            model_name='jobdetails',
            name='current_density',
            field=models.FloatField(blank=True, null=True, verbose_name='Current density (amps/sq in)'),
        ),
        migrations.AlterField(
            model_name='jobdetails',
            name='surface_area',
            field=models.FloatField(blank=True, null=True, verbose_name='Surface Area (sq in)'),
        ),
    ]
