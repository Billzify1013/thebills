# Generated by Django 5.1.4 on 2025-02-05 22:49

import datetime
import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0122_supplier_due_amount_supplier_reviced_amount'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='PurchasePayment',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('payment_amount', models.DecimalField(decimal_places=2, max_digits=10)),
                ('payment_date', models.DateTimeField(null=True)),
                ('payment_mode', models.CharField(max_length=50)),
                ('transaction_id', models.CharField(blank=True, max_length=100, null=True)),
                ('descriptions', models.CharField(blank=True, max_length=50, null=True)),
                ('maindate', models.DateField(blank=True, default=datetime.date.today, null=True)),
                ('invoice', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='app.supplier')),
                ('vendor', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
