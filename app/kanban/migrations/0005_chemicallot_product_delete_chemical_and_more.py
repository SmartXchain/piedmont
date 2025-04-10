# Generated by Django 5.1.3 on 2025-03-10 19:28

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('kanban', '0004_alter_chemical_expiry_date'),
    ]

    operations = [
        migrations.CreateModel(
            name='ChemicalLot',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('purchase_order', models.CharField(blank=True, help_text='Purchase Order Number', max_length=100, null=True)),
                ('lot_number', models.CharField(blank=True, help_text='Lot tracking number', max_length=100, null=True)),
                ('expiry_date', models.DateField(blank=True, help_text='Expiry date (leave blank if not applicable)', null=True)),
                ('quantity', models.PositiveIntegerField(default=0, help_text='Quantity in this lot')),
                ('coc_scan', models.FileField(blank=True, help_text='Upload Certificate of Conformance', null=True, upload_to='coc_scans/')),
                ('used_up', models.BooleanField(default=False, help_text='Mark if this lot has been completely used up')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.CreateModel(
            name='Product',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(help_text='Product name', max_length=255, unique=True)),
                ('supplier_name', models.CharField(blank=True, help_text='Supplier Name', max_length=255, null=True)),
                ('supplier_part_number', models.CharField(blank=True, help_text='Supplier Part Number', max_length=100, null=True)),
                ('min_quantity', models.PositiveIntegerField(default=5, help_text='Minimum stock level before reordering')),
                ('max_quantity', models.PositiveIntegerField(default=50, help_text='Maximum stock level allowed')),
                ('trigger_level', models.PositiveIntegerField(default=10, help_text='Trigger level for automatic reordering')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
        migrations.DeleteModel(
            name='Chemical',
        ),
        migrations.AddField(
            model_name='chemicallot',
            name='product',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='chemical_lots', to='kanban.product'),
        ),
    ]
