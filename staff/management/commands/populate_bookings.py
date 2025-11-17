from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime, timedelta
import random
from decimal import Decimal

from staff.models import Guest, Booking, Room, Payment


class Command(BaseCommand):
    help = 'Populate the database with bookings from today to 5 years past, with seasonal patterns for SARIMA modeling'

    def add_arguments(self, parser):
        parser.add_argument(
            '--count',
            type=int,
            default=500,
            help='Number of bookings to create (default: 500)',
        )

    def get_seasonal_weight(self, date):
        """
        Calculate seasonal weight for a given date.
        Returns a weight factor that influences booking probability.
        Higher weight = more likely to have bookings on that date.
        """
        month = date.month
        weekday = date.weekday()  # 0=Monday, 6=Sunday
        
        # Monthly seasonal patterns
        # Summer months (June, July, August): peak season
        # Holiday months (December, January): high season
        # Spring (April, May): moderate
        # Fall (September, October): moderate
        # Winter (February, March, November): low season
        monthly_weights = {
            1: 1.5,   # January - Holiday season
            2: 0.6,   # February - Low season
            3: 0.7,   # March - Low season
            4: 1.2,   # April - Spring moderate
            5: 1.3,   # May - Spring moderate
            6: 1.8,   # June - Summer peak
            7: 2.0,   # July - Summer peak (highest)
            8: 1.8,   # August - Summer peak
            9: 1.1,   # September - Fall moderate
            10: 1.2,  # October - Fall moderate
            11: 0.8,  # November - Low season
            12: 1.6,  # December - Holiday season
        }
        
        # Weekly patterns - weekends are more popular
        # Friday (4), Saturday (5), Sunday (6) get higher weights
        if weekday in [4, 5, 6]:  # Friday, Saturday, Sunday
            weekly_weight = 1.4
        elif weekday in [0, 3]:  # Monday, Thursday
            weekly_weight = 1.1
        else:  # Tuesday, Wednesday
            weekly_weight = 0.9
        
        return monthly_weights[month] * weekly_weight

    def select_date_with_seasonal_pattern(self, start_date, end_date):
        """
        Select a date between start_date and end_date with seasonal weighting.
        Uses weighted random selection based on seasonal patterns.
        Optimized for large date ranges by sampling and weighting.
        """
        # For efficiency with large ranges, we'll use a two-step approach:
        # 1. First, randomly select a date (uniform distribution)
        # 2. Then, accept/reject based on seasonal weight (acceptance-rejection sampling)
        
        max_weight = 2.8  # Maximum possible weight (July weekend = 2.0 * 1.4)
        
        while True:
            # Random date in range
            days_diff = (end_date - start_date).days
            random_days = random.randint(0, days_diff)
            candidate_date = start_date + timedelta(days=random_days)
            
            # Get weight for this date
            weight = self.get_seasonal_weight(candidate_date)
            
            # Acceptance-rejection sampling: accept with probability weight/max_weight
            if random.random() < (weight / max_weight):
                return candidate_date

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
        
        # Calculate date range: from today to 5 years past
        today = timezone.now().date()
        start_date = today - timedelta(days=5*365)  # 5 years ago
        end_date = today  # Today
        
        self.stdout.write(f'Creating {count} bookings from {start_date} to {end_date} (5 years of data with seasonal patterns)...')
        
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
            
            # Generate check-in date with seasonal pattern weighting
            # Use seasonal weighting to create realistic booking patterns
            check_in_date = self.select_date_with_seasonal_pattern(start_date, end_date)
            
            # Generate check-out date (1-7 days after check-in, with longer stays in peak seasons)
            # Peak seasons tend to have longer stays
            month = check_in_date.month
            if month in [6, 7, 8, 12, 1]:  # Peak seasons
                stay_duration = random.choices([1, 2, 3, 4, 5, 6, 7], weights=[5, 10, 15, 20, 20, 15, 15])[0]
            else:
                stay_duration = random.choices([1, 2, 3, 4, 5, 6, 7], weights=[15, 20, 20, 15, 10, 10, 10])[0]
            
            check_out_date = check_in_date + timedelta(days=stay_duration)
            
            # Ensure check-out is not in the future
            if check_out_date > end_date:
                check_out_date = end_date
                # Adjust check-in if needed
                if check_in_date >= check_out_date:
                    check_in_date = check_out_date - timedelta(days=1)
                    stay_duration = 1
            
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
                f'Date range: {start_date} to {end_date} (5 years of historical data)\n'
                f'Seasonal patterns included: Summer peaks (Jun-Aug), Holiday peaks (Dec-Jan), Weekend preferences'
            )
        )

