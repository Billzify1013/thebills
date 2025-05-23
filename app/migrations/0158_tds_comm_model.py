# Generated by Django 5.1.4 on 2025-05-14 20:35

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0157_remove_whatsaap_link_active'),
    ]

    operations = [
        migrations.CreateModel(
            name='tds_comm_model',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('commission', models.FloatField(blank=True, default=0.0, null=True)),
                ('tds', models.FloatField(blank=True, default=0.0, null=True)),
                ('tcs', models.FloatField(blank=True, default=0.0, null=True)),
                ('roombook', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='app.saveadvancebookguestdata')),
            ],
        ),
    ]
