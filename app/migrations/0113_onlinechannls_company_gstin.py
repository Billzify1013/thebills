# Generated by Django 5.1.4 on 2025-02-02 19:07

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0112_invoice_customer_company'),
    ]

    operations = [
        migrations.AddField(
            model_name='onlinechannls',
            name='company_gstin',
            field=models.CharField(blank=True, max_length=15, null=True),
        ),
    ]
