# Generated by Django 5.1.4 on 2025-02-24 14:26

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0134_companies_is_ota'),
    ]

    operations = [
        migrations.AlterField(
            model_name='companies',
            name='address',
            field=models.CharField(blank=True, max_length=300, null=True),
        ),
        migrations.AlterField(
            model_name='companies',
            name='contact',
            field=models.BigIntegerField(blank=True, null=True, validators=[django.core.validators.MaxValueValidator(9999999999)]),
        ),
        migrations.AlterField(
            model_name='companies',
            name='contactpersonname',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
    ]
