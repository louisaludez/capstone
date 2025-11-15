from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
import random
from decimal import Decimal

from staff.models import Guest, Booking, Room, Payment


class Command(BaseCommand):
    help = 'Populate the database with at least 500 past bookings (at least 1 year old)'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=500,
            help='Number of bookings to create (default: 500)',
        )

    def handle(self, *args, **options):
        count = options['count']
        
        # Get all rooms
        rooms = Room.objects.all()
        if not rooms.exists():
            self.stdout.write(
                self.style.ERROR('No rooms found. Please run populate_staff_rooms first.')
            )
            return
        
        room_numbers = [str(room.room_number) for room in rooms]
        room_types = ['standard', 'family', 'deluxe']
        statuses = ['Checked-out']  # All bookings should be checked out
        sources = ['walkin', 'reservation', 'checkin']
        
        # First names and last names for generating guest names
        first_names = [
            'John', 'Jane', 'Michael', 'Sarah', 'David', 'Emily', 'Robert', 'Jessica',
            'William', 'Ashley', 'James', 'Amanda', 'Christopher', 'Melissa', 'Daniel',
            'Michelle', 'Matthew', 'Kimberly', 'Anthony', 'Amy', 'Mark', 'Angela',
            'Donald', 'Brenda', 'Steven', 'Emma', 'Paul', 'Olivia', 'Andrew', 'Cynthia',
            'Joshua', 'Marie', 'Kenneth', 'Janet', 'Kevin', 'Catherine', 'Brian', 'Frances',
            'George', 'Christine', 'Timothy', 'Samantha', 'Ronald', 'Deborah', 'Jason',
            'Rachel', 'Edward', 'Carol', 'Jeffrey', 'Janet', 'Ryan', 'Maria', 'Jacob',
            'Heather', 'Gary', 'Diane', 'Nicholas', 'Julie', 'Eric', 'Joyce', 'Jonathan',
            'Victoria', 'Stephen', 'Kelly', 'Larry', 'Christina', 'Justin', 'Joan',
            'Scott', 'Evelyn', 'Brandon', 'Judith', 'Benjamin', 'Megan', 'Samuel',
            'Cheryl', 'Gregory', 'Andrea', 'Alexander', 'Hannah', 'Patrick', 'Jacqueline',
            'Frank', 'Martha', 'Raymond', 'Gloria', 'Jack', 'Teresa', 'Dennis', 'Sara',
            'Jerry', 'Janice', 'Tyler', 'Marie', 'Aaron', 'Julia', 'Jose', 'Grace',
            'Henry', 'Judy', 'Adam', 'Theresa', 'Douglas', 'Madison', 'Nathan', 'Beverly',
            'Zachary', 'Denise', 'Kyle', 'Marilyn', 'Noah', 'Amber', 'Ethan', 'Danielle',
            'Jeremy', 'Brittany', 'Christian', 'Diana', 'Sean', 'Abigail', 'Connor', 'Jane'
        ]
        
        last_names = [
            'Smith', 'Johnson', 'Williams', 'Brown', 'Jones', 'Garcia', 'Miller', 'Davis',
            'Rodriguez', 'Martinez', 'Hernandez', 'Lopez', 'Wilson', 'Anderson', 'Thomas',
            'Taylor', 'Moore', 'Jackson', 'Martin', 'Lee', 'Thompson', 'White', 'Harris',
            'Sanchez', 'Clark', 'Ramirez', 'Lewis', 'Robinson', 'Walker', 'Young', 'Allen',
            'King', 'Wright', 'Scott', 'Torres', 'Nguyen', 'Hill', 'Flores', 'Green',
            'Adams', 'Nelson', 'Baker', 'Hall', 'Rivera', 'Campbell', 'Mitchell', 'Carter',
            'Roberts', 'Gomez', 'Phillips', 'Evans', 'Turner', 'Diaz', 'Parker', 'Cruz',
            'Edwards', 'Collins', 'Reyes', 'Stewart', 'Morris', 'Morales', 'Murphy', 'Cook',
            'Rogers', 'Gutierrez', 'Ortiz', 'Morgan', 'Cooper', 'Peterson', 'Bailey', 'Reed',
            'Kelly', 'Howard', 'Ramos', 'Kim', 'Cox', 'Ward', 'Richardson', 'Watson',
            'Brooks', 'Chavez', 'Wood', 'James', 'Bennett', 'Gray', 'Mendoza', 'Ruiz',
            'Hughes', 'Price', 'Alvarez', 'Castillo', 'Sanders', 'Patel', 'Myers', 'Long',
            'Ross', 'Foster', 'Jimenez', 'Powell', 'Jenkins', 'Perry', 'Russell', 'Sullivan',
            'Bell', 'Coleman', 'Butler', 'Henderson', 'Barnes', 'Gonzales', 'Fisher', 'Vasquez',
            'Simmons', 'Romero', 'Jordan', 'Patterson', 'Alexander', 'Hamilton', 'Graham', 'Reynolds'
        ]
        
        # Calculate date range: from 2 years ago to 1 year ago (all past, at least 1 year old)
        today = timezone.now().date()
        end_date = today - timedelta(days=365)  # 1 year ago
        start_date = end_date - timedelta(days=365)  # 2 years ago
        
        self.stdout.write(f'Creating {count} bookings from {start_date} to {end_date}...')
        
        created_count = 0
        guest_count = 0
        
        for i in range(count):
            # Generate random guest data
            first_name = random.choice(first_names)
            last_name = random.choice(last_names)
            name = f"{first_name} {last_name}"
            email = f"{first_name.lower()}.{last_name.lower()}{i}@example.com"
            
            # Create or get guest
            guest, guest_created = Guest.objects.get_or_create(
                email=email,
                defaults={
                    'name': name,
                    'address': f"{random.randint(100, 9999)} {random.choice(['Main St', 'Oak Ave', 'Park Blvd', 'Elm St', 'Maple Dr'])}",
                    'zip_code': f"{random.randint(10000, 99999)}",
                    'mobile': f"{random.randint(1000000000, 9999999999)}",
                    'date_of_birth': datetime(1970, 1, 1).date() + timedelta(days=random.randint(0, 18250)),  # Random DOB between 1970 and 2020
                    'billing': str(random.randint(500, 5000)),
                    'room_service_billing': str(random.randint(0, 500)),
                    'laundry_billing': str(random.randint(0, 300)),
                    'cafe_billing': str(random.randint(0, 200)),
                    'excess_pax_billing': str(random.randint(0, 1000)),
                    'additional_charge_billing': str(random.randint(0, 500)),
                }
            )
            
            if guest_created:
                guest_count += 1
            
            # Generate random check-in date (within the past year range)
            days_offset = random.randint(0, 365)
            check_in_date = start_date + timedelta(days=days_offset)
            
            # Generate check-out date (1-7 days after check-in)
            stay_duration = random.randint(1, 7)
            check_out_date = check_in_date + timedelta(days=stay_duration)
            
            # Ensure check-out is still in the past (before end_date)
            if check_out_date > end_date:
                check_out_date = end_date
                # Adjust check-in if needed
                if check_in_date >= check_out_date:
                    check_in_date = check_out_date - timedelta(days=1)
            
            # Select random room
            room_number = random.choice(room_numbers)
            room_obj = rooms.get(room_number=room_number)
            
            # Format room string (various formats used in the system)
            room_formats = [
                room_number,
                f"R{room_number}",
                f"Room {room_number}",
                f"Room {room_number} : {room_obj.get_room_type_display()}",
            ]
            room_string = random.choice(room_formats)
            
            # Generate guest counts
            # For standard rooms: 1-2 guests, family: 2-4, deluxe: 1-2
            if room_obj.room_type == 'family':
                total_guests = random.randint(2, 4)
            else:
                total_guests = random.randint(1, 2)
            
            num_adults = random.randint(1, total_guests)
            num_children = total_guests - num_adults
            children_below_7 = random.randint(0, num_children) if num_children > 0 else 0
            
            # All bookings should be checked out
            status = 'Checked-out'
            
            # Select source
            source = random.choice(sources)
            
            # Create booking with past booking_date
            booking_date = check_in_date - timedelta(days=random.randint(0, 30))
            booking_datetime = datetime.combine(booking_date, datetime.min.time())
            booking_datetime = timezone.make_aware(booking_datetime)
            
            booking = Booking.objects.create(
                guest=guest,
                room=room_string,
                check_in_date=check_in_date,
                check_out_date=check_out_date,
                total_of_guests=total_guests,
                num_of_adults=num_adults,
                num_of_children=num_children,
                no_of_children_below_7=children_below_7,
                status=status,
                source=source,
            )
            
            # Override booking_date to be in the past
            booking.booking_date = booking_datetime
            booking.save(update_fields=['booking_date'])
            
            # Calculate total balance based on room price, stay duration, and additional charges
            nights = (check_out_date - check_in_date).days
            base_room_charge = float(room_obj.price_per_night) * nights
            additional_charges = random.randint(0, 500)
            total_balance = Decimal(str(round(base_room_charge + additional_charges, 2)))
            
            # Select payment method (70% card, 30% cash)
            payment_method = random.choices(['card', 'cash'], weights=[0.7, 0.3])[0]
            
            # Create payment record
            payment_data = {
                'booking': booking,
                'method': payment_method,
                'total_balance': total_balance,
            }
            
            # Add card details if payment method is card
            if payment_method == 'card':
                # Generate realistic card number (masked format: last 4 digits visible)
                card_last4 = random.randint(1000, 9999)
                payment_data['card_number'] = f"**** **** **** {card_last4}"
                # Generate expiration date (MM/YY format, in the past but realistic)
                exp_month = random.randint(1, 12)
                exp_year = random.randint(20, 25)  # 2020-2025
                payment_data['exp_date'] = f"{exp_month:02d}/{exp_year:02d}"
                payment_data['cvc_code'] = f"{random.randint(100, 999)}"
                payment_data['billing_address'] = guest.address
            
            # Create payment with past created_at
            payment = Payment.objects.create(**payment_data)
            payment.created_at = booking_datetime
            payment.save(update_fields=['created_at'])
            
            created_count += 1
            
            if created_count % 50 == 0:
                self.stdout.write(f'Created {created_count} bookings with payments...')
        
        self.stdout.write(
            self.style.SUCCESS(
                f'Successfully created {created_count} bookings with {guest_count} new guests and payments.\n'
                f'Date range: {start_date} to {end_date} (all at least 1 year old)'
            )
        )

