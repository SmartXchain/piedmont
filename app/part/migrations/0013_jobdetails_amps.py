# Generated by Django 5.1.3 on 2024-12-18 18:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('part', '0012_alter_jobdetails_unique_together'),
    ]

    operations = [
        migrations.AddField(
            model_name='jobdetails',
            name='amps',
            field=models.FloatField(blank=True, null=True, verbose_name='Amps Required'),
        ),
    ]