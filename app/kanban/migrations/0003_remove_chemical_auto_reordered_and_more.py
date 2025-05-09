# Generated by Django 5.1.3 on 2025-03-05 20:59

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kanban', '0002_chemical_auto_reordered_chemical_coc_scan_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='chemical',
            name='auto_reordered',
        ),
        migrations.RemoveField(
            model_name='chemical',
            name='max_stock',
        ),
        migrations.RemoveField(
            model_name='chemical',
            name='min_stock',
        ),
        migrations.RemoveField(
            model_name='chemical',
            name='reorder_quantity',
        ),
        migrations.AddField(
            model_name='chemical',
            name='created_at',
            field=models.DateTimeField(auto_now_add=True, default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='chemical',
            name='reorder_level',
            field=models.PositiveIntegerField(default=10, help_text='Threshold for reordering'),
        ),
        migrations.AddField(
            model_name='chemical',
            name='updated_at',
            field=models.DateTimeField(auto_now=True),
        ),
        migrations.AlterField(
            model_name='chemical',
            name='coc_scan',
            field=models.FileField(blank=True, help_text='Upload Certificate of Conformance', null=True, upload_to='coc_scans/'),
        ),
        migrations.AlterField(
            model_name='chemical',
            name='expiry_date',
            field=models.DateField(help_text='Date when the chemical expires'),
        ),
        migrations.AlterField(
            model_name='chemical',
            name='lot_number',
            field=models.CharField(blank=True, help_text='Lot tracking number', max_length=100, null=True),
        ),
        migrations.AlterField(
            model_name='chemical',
            name='name',
            field=models.CharField(help_text='Enter the chemical name', max_length=255, unique=True),
        ),
        migrations.AlterField(
            model_name='chemical',
            name='quantity',
            field=models.PositiveIntegerField(default=0, help_text='Current stock quantity'),
        ),
    ]
