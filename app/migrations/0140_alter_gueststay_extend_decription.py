# Generated by Django 5.1.4 on 2025-02-27 00:19

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0139_alter_booking_totalamount'),
    ]

    operations = [
        migrations.AlterField(
            model_name='gueststay',
            name='extend_decription',
            field=models.CharField(blank=True, default=True, max_length=500),
        ),
    ]
