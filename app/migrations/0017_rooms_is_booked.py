# Generated by Django 4.1.3 on 2024-11-01 20:12

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0016_vendorcm_dynamic_price_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='rooms',
            name='is_booked',
            field=models.BooleanField(blank=True, default=False, null=True),
        ),
    ]
