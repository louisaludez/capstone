# Generated by Django 5.2 on 2025-07-18 01:33

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('staff', '0014_alter_guest_billing_alter_guest_room_service_billing'),
    ]

    operations = [
        migrations.AlterField(
            model_name='payment',
            name='total_balance',
            field=models.DecimalField(decimal_places=2, default=0.0, max_digits=10),
        ),
    ]
