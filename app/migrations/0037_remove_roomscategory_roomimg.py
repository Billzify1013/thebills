# Generated by Django 4.1.3 on 2024-11-15 13:11

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0036_remove_amainities_vendor_delete_marketiteams_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='roomscategory',
            name='roomimg',
        ),
    ]
