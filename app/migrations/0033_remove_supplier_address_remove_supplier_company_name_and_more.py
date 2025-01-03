# Generated by Django 4.1.3 on 2024-11-11 12:46

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app', '0032_purchase_supplier_purchaseitem_purchase_supplier_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='supplier',
            name='address',
        ),
        migrations.RemoveField(
            model_name='supplier',
            name='company_name',
        ),
        migrations.RemoveField(
            model_name='supplier',
            name='contact',
        ),
        migrations.RemoveField(
            model_name='supplier',
            name='email',
        ),
        migrations.RemoveField(
            model_name='supplier',
            name='gstin',
        ),
        migrations.RemoveField(
            model_name='supplier',
            name='name',
        ),
        migrations.RemoveField(
            model_name='supplier',
            name='pan_no',
        ),
        migrations.AddField(
            model_name='supplier',
            name='cash_amount',
            field=models.DecimalField(blank=True, decimal_places=2, default=1, max_digits=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='supplier',
            name='companyname',
            field=models.CharField(blank=True, max_length=50),
        ),
        migrations.AddField(
            model_name='supplier',
            name='customeraddress',
            field=models.CharField(default=1, max_length=300),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='supplier',
            name='customercontact',
            field=models.BigIntegerField(default=1, validators=[django.core.validators.MaxValueValidator(9999999999)]),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='supplier',
            name='customeremail',
            field=models.EmailField(blank=True, max_length=100),
        ),
        migrations.AddField(
            model_name='supplier',
            name='customergst',
            field=models.CharField(blank=True, max_length=15),
        ),
        migrations.AddField(
            model_name='supplier',
            name='customername',
            field=models.CharField(default=1, max_length=50),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='supplier',
            name='discount_amount',
            field=models.DecimalField(blank=True, decimal_places=2, default=1, max_digits=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='supplier',
            name='grand_total_amount',
            field=models.DecimalField(blank=True, decimal_places=2, default=1, max_digits=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='supplier',
            name='gst_amount',
            field=models.DecimalField(blank=True, decimal_places=2, default=1, max_digits=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='supplier',
            name='invoicedate',
            field=models.DateField(null=True),
        ),
        migrations.AddField(
            model_name='supplier',
            name='invoicenumber',
            field=models.CharField(default=1, max_length=12),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='supplier',
            name='modeofpayment',
            field=models.CharField(blank=True, max_length=20),
        ),
        migrations.AddField(
            model_name='supplier',
            name='online_amount',
            field=models.DecimalField(blank=True, decimal_places=2, default=1, max_digits=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='supplier',
            name='sattle',
            field=models.BooleanField(default=False),
        ),
        migrations.AddField(
            model_name='supplier',
            name='sgst_amount',
            field=models.DecimalField(blank=True, decimal_places=2, default=1, max_digits=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='supplier',
            name='subtotal_amount',
            field=models.DecimalField(blank=True, decimal_places=2, default=1, max_digits=10),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='supplier',
            name='taxtype',
            field=models.CharField(choices=[('GST', 'GST'), ('IGST', 'IGST')], default=1, max_length=5),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='supplier',
            name='total_item_amount',
            field=models.DecimalField(blank=True, decimal_places=2, default=1, max_digits=10),
            preserve_default=False,
        ),
    ]
