# Generated by Django 3.2.20 on 2024-12-31 10:41

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0071_alter_supplierinvoiceitem_tax_rate'),
    ]

    operations = [
        migrations.AlterField(
            model_name='supplierinvoiceitem',
            name='tax_rate',
            field=models.PositiveIntegerField(default=0),
        ),
    ]
