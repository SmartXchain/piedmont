# Generated by Django 5.1.3 on 2024-11-29 02:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('standard', '0003_alter_standard_upload_file'),
    ]

    operations = [
        migrations.AlterField(
            model_name='standard',
            name='upload_file',
            field=models.FileField(upload_to='standard/'),
        ),
    ]