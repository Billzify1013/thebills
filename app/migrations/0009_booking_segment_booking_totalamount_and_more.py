# Generated by Django 4.1.3 on 2024-10-27 19:35

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0008_alter_booking_check_in_time_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='booking',
            name='segment',
            field=models.CharField(blank=True, max_length=40, null=True),
        ),
        migrations.AddField(
            model_name='booking',
            name='totalamount',
            field=models.CharField(blank=True, max_length=40, null=True),
        ),
        migrations.AddField(
            model_name='booking',
            name='totalroom',
            field=models.CharField(blank=True, max_length=10, null=True),
        ),
    ]
