from django.core.management.base import BaseCommand
from laundry.models import LaundryTransaction
from staff.models import Guest, Booking
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Create sample laundry data for testing'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=20,
            help='Number of sample orders to create'
        )

    def handle(self, *args, **options):
        count = options['count']
        
        # Get existing guests and bookings
        guests = list(Guest.objects.all())
        bookings = list(Booking.objects.all())
        
        if not guests:
            self.stdout.write(self.style.ERROR('No guests found. Please create some guests first.'))
            return
            
        if not bookings:
            self.stdout.write(self.style.ERROR('No bookings found. Please create some bookings first.'))
            return
        
        service_types = ['Wash and Fold', 'Dry Clean', 'Press Only']
        statuses = ['pending', 'in_progress', 'completed', 'cancelled']
        payment_methods = ['cash', 'room']
        
        created_count = 0
        
        for i in range(count):
            # Randomly select guest and booking
            guest = random.choice(guests)
            booking = random.choice(bookings)
            
            # Random date within last 30 days
            days_ago = random.randint(0, 30)
            order_date = datetime.now() - timedelta(days=days_ago)
            
            # Create laundry transaction
            transaction = LaundryTransaction.objects.create(
                guest=guest,
                booking=booking,
                room_number=booking.room,
                service_type=random.choice(service_types),
                no_of_bags=random.randint(1, 5),
                specifications=random.choice(['', 'Fragile items', 'Starch required', 'No bleach', 'Cold water only']),
                date_time=order_date,
                payment_method=random.choice(payment_methods),
                total_amount=75.00 * random.randint(1, 5),
                status=random.choice(statuses)
            )
            
            created_count += 1
            
        self.stdout.write(
            self.style.SUCCESS(f'Successfully created {created_count} sample laundry orders')
        ) 