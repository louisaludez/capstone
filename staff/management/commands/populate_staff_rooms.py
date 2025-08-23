from django.core.management.base import BaseCommand
from staff.models import Room

class Command(BaseCommand):
    help = 'Populate the database with sample rooms'

    def handle(self, *args, **options):
        # Room data based on the Front Office template (12 rooms total)
        rooms_data = [
            {'room_number': '1', 'room_type': 'standard', 'capacity': 2, 'price_per_night': 100.00},
            {'room_number': '2', 'room_type': 'family', 'capacity': 4, 'price_per_night': 150.00},
            {'room_number': '3', 'room_type': 'deluxe', 'capacity': 2, 'price_per_night': 200.00},
            {'room_number': '4', 'room_type': 'standard', 'capacity': 2, 'price_per_night': 100.00},
            {'room_number': '5', 'room_type': 'family', 'capacity': 4, 'price_per_night': 150.00},
            {'room_number': '6', 'room_type': 'deluxe', 'capacity': 2, 'price_per_night': 200.00},
            {'room_number': '7', 'room_type': 'standard', 'capacity': 2, 'price_per_night': 100.00},
            {'room_number': '8', 'room_type': 'family', 'capacity': 4, 'price_per_night': 150.00},
            {'room_number': '9', 'room_type': 'deluxe', 'capacity': 2, 'price_per_night': 200.00},
            {'room_number': '10', 'room_type': 'standard', 'capacity': 2, 'price_per_night': 100.00},
            {'room_number': '11', 'room_type': 'family', 'capacity': 4, 'price_per_night': 150.00},
            {'room_number': '12', 'room_type': 'deluxe', 'capacity': 2, 'price_per_night': 200.00},
        ]
        
        created_count = 0
        for room_data in rooms_data:
            room, created = Room.objects.get_or_create(
                room_number=room_data['room_number'],
                defaults=room_data
            )
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created room {room.room_number} - {room.get_room_type_display()}')
                )
            else:
                self.stdout.write(
                    self.style.WARNING(f'Room {room.room_number} already exists')
                )
        
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} new rooms')
        ) 