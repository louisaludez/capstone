# Generated by Django 5.2 on 2025-07-05 10:31

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('concierge', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='conciergerequestspa',
            name='assigned_to',
        ),
        migrations.RemoveField(
            model_name='conciergerequestspa',
            name='customer',
        ),
        migrations.RemoveField(
            model_name='conciergerequestspa',
            name='room',
        ),
        migrations.RemoveField(
            model_name='conciergerequesttour',
            name='assigned_to',
        ),
        migrations.RemoveField(
            model_name='conciergerequesttour',
            name='customer',
        ),
        migrations.RemoveField(
            model_name='conciergerequesttour',
            name='room',
        ),
        migrations.DeleteModel(
            name='ConciergeRequestCafe',
        ),
        migrations.DeleteModel(
            name='ConciergeRequestSpa',
        ),
        migrations.DeleteModel(
            name='ConciergeRequestTour',
        ),
    ]
