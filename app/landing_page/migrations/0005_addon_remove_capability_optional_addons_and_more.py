# Generated by Django 5.1.3 on 2025-04-17 20:42

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('landing_page', '0004_capability_base_job_setup_fee_and_more'),
    ]

    operations = [
        migrations.CreateModel(
            name='AddOn',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255)),
                ('price', models.DecimalField(decimal_places=2, max_digits=10)),
            ],
        ),
        migrations.RemoveField(
            model_name='capability',
            name='optional_addons',
        ),
        migrations.AlterField(
            model_name='capability',
            name='cost_usd',
            field=models.DecimalField(decimal_places=2, max_digits=10),
        ),
        migrations.AddField(
            model_name='capability',
            name='addons',
            field=models.ManyToManyField(blank=True, to='landing_page.addon'),
        ),
    ]
