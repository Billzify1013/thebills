# Generated by Django 4.1.3 on 2024-12-05 08:32

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0051_becallemail'),
    ]

    operations = [
        migrations.AddField(
            model_name='beaminities',
            name='cancellention_policy',
            field=models.CharField(default=1, max_length=50),
            preserve_default=False,
        ),
    ]
