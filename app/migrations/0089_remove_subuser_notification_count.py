# Generated by Django 5.1.4 on 2025-01-14 22:45

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0088_subuser_notification_count'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='subuser',
            name='notification_count',
        ),
    ]
