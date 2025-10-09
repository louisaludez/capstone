from django.db import migrations


def update_room_prices(apps, schema_editor):
    Room = apps.get_model('staff', 'Room')
    price_map = {
        'standard': 3500,
        'family': 4700,
        'deluxe': 8900,
    }
    for code, price in price_map.items():
        Room.objects.filter(room_type=code).update(price_per_night=price)


class Migration(migrations.Migration):

    dependencies = [
        ('staff', '0021_guest_mobile'),
    ]

    operations = [
        migrations.RunPython(update_room_prices, migrations.RunPython.noop),
    ]


