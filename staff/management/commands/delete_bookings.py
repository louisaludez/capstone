from django.core.management.base import BaseCommand
from staff.models import Booking, Payment, Guest


class Command(BaseCommand):
    help = 'Delete all bookings, payments, and optionally guests'

    def add_arguments(self, parser):
        parser.add_argument(
            '--delete-guests',
            action='store_true',
            help='Also delete guests (default: False, keeps guests)',
        )

    def handle(self, *args, **options):
        delete_guests = options['delete_guests']
        
        # Count before deletion
        booking_count = Booking.objects.count()
        payment_count = Payment.objects.count()
        guest_count = Guest.objects.count()
        
        self.stdout.write(f'Found {booking_count} bookings, {payment_count} payments, {guest_count} guests')
        
        # Delete payments first (they reference bookings)
        deleted_payments = Payment.objects.all().delete()[0]
        self.stdout.write(f'Deleted {deleted_payments} payments')
        
        # Delete bookings
        deleted_bookings = Booking.objects.all().delete()[0]
        self.stdout.write(f'Deleted {deleted_bookings} bookings')
        
        # Optionally delete guests
        if delete_guests:
            deleted_guests = Guest.objects.all().delete()[0]
            self.stdout.write(f'Deleted {deleted_guests} guests')
        else:
            self.stdout.write('Guests kept (use --delete-guests to delete them)')
        
        self.stdout.write(
            self.style.SUCCESS('Successfully deleted all bookings and payments')
        )

