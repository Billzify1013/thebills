# Generated by Django 5.1.4 on 2025-02-20 21:24

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0131_booking_fnbinvoice'),
    ]

    operations = [
        migrations.AddField(
            model_name='customguestlog',
            name='advancebook',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='app.saveadvancebookguestdata'),
        ),
    ]
