from django.core.management.base import BaseCommand
from adminNew.sarima_forecast import ReservationForecaster
from staff.models import Booking
import pickle
import os
from django.conf import settings


class Command(BaseCommand):
    help = 'Train SARIMA model and save forecast data to pickle file for faster loading'

    def add_arguments(self, parser):
        parser.add_argument(
            '--output',
            type=str,
            default='sarima_forecast.pkl',
            help='Output pickle file name (default: sarima_forecast.pkl)',
        )

    def handle(self, *args, **options):
        output_file = options['output']
        
        # Determine output path (save in project root or static files)
        output_path = os.path.join(settings.BASE_DIR, output_file)
        
        self.stdout.write('Fetching bookings data...')
        # Get all bookings
        bookings = Booking.objects.all().only(
            'booking_date', 'check_in_date', 'check_out_date', 
            'status', 'num_of_adults', 'num_of_children', 'total_of_guests'
        ).order_by('booking_date')
        
        booking_count = bookings.count()
        self.stdout.write(f'Found {booking_count} bookings')
        
        if booking_count == 0:
            self.stdout.write(
                self.style.WARNING('No bookings found. Cannot generate forecast.')
            )
            return
        
        self.stdout.write('Creating forecaster and preparing data...')
        # Create forecaster
        forecaster = ReservationForecaster()
        
        # Prepare data
        series = forecaster.prepare_data(bookings)
        
        if len(series) == 0:
            self.stdout.write(
                self.style.WARNING('No time series data generated. Cannot create forecast.')
            )
            return
        
        self.stdout.write(f'Time series length: {len(series)} months')
        self.stdout.write('Training SARIMA model...')
        
        # Get forecast data
        result = forecaster.get_forecast_chart_data(series)
        
        if result is None:
            self.stdout.write(
                self.style.ERROR('Failed to generate forecast data.')
            )
            return
        
        # Save the fitted model and forecast data
        save_data = {
            'forecast_data': result,
            'fitted_model': forecaster.fitted_model,
            'model_params': {
                'order': forecaster.model.order if forecaster.model else None,
                'seasonal_order': forecaster.model.seasonal_order if forecaster.model else None,
            } if forecaster.model else None,
            'series_length': len(series),
            'last_date': series.index[-1] if len(series) > 0 else None,
        }
        
        self.stdout.write(f'Saving to {output_path}...')
        try:
            with open(output_path, 'wb') as f:
                pickle.dump(save_data, f)
            
            file_size = os.path.getsize(output_path) / 1024  # Size in KB
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully saved SARIMA forecast data to {output_path}\n'
                    f'File size: {file_size:.2f} KB\n'
                    f'Forecast method: {result.get("method", "unknown")}\n'
                    f'Historical data points: {len(result.get("historical", {}).get("values", []))}\n'
                    f'Forecast data points: {len(result.get("forecast", {}).get("values", []))}'
                )
            )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error saving pickle file: {e}')
            )

