# Generated by Django 5.1.4 on 2025-02-04 21:28

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0116_alter_taxslabpurchase_invoice'),
    ]

    operations = [
        migrations.AddField(
            model_name='supplierinvoiceitem',
            name='sellinghsn',
            field=models.CharField(blank=True, max_length=8),
        ),
    ]
