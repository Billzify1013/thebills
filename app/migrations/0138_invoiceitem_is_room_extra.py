# Generated by Django 5.1.4 on 2025-02-25 13:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0137_invoice_is_ota'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoiceitem',
            name='is_room_extra',
            field=models.BooleanField(default=False),
        ),
    ]
