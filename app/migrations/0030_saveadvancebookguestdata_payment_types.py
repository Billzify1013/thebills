# Generated by Django 4.1.3 on 2024-11-10 20:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0029_travelagencyhandling'),
    ]

    operations = [
        migrations.AddField(
            model_name='saveadvancebookguestdata',
            name='Payment_types',
            field=models.CharField(blank=True, choices=[('book', 'Book'), ('cancel', 'Cancel'), ('modify', 'modify')], max_length=20, null=True),
        ),
    ]
