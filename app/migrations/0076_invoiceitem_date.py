# Generated by Django 3.2.20 on 2025-01-01 09:08

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0075_remove_invpermit_room_billing_active'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoiceitem',
            name='date',
            field=models.DateField(auto_now=True),
        ),
    ]