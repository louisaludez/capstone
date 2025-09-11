from django.core.management.base import BaseCommand
from adminNew.sarima_forecast import get_reservation_forecast
from staff.models import Booking
import json

class Command(BaseCommand):
    help = 'Test SARIMA forecasting with current reservation data'

    def handle(self, *args, **options):
        self.stdout.write('Testing SARIMA forecasting...')
        
        # Get current booking count
        booking_count = Booking.objects.count()
        self.stdout.write(f'Total bookings in database: {booking_count}')
        
        if booking_count == 0:
            self.stdout.write(
                self.style.WARNING('No booking data found. Please create some reservations first.')
            )
            return
        
        try:
            # Get forecast data
            forecast_data = get_reservation_forecast()
            
            if forecast_data:
                self.stdout.write(
                    self.style.SUCCESS('SARIMA forecast generated successfully!')
                )
                
                # Display forecast summary
                historical_count = len(forecast_data['historical']['values'])
                forecast_count = len(forecast_data['forecast']['values'])
                method = forecast_data['method']
                
                self.stdout.write(f'Method: {method.upper()}')
                self.stdout.write(f'Historical data points: {historical_count} months')
                self.stdout.write(f'Forecast months: {forecast_count}')
                
                # Show sample forecast values
                if forecast_data['forecast']['values']:
                    avg_forecast = sum(forecast_data['forecast']['values']) / len(forecast_data['forecast']['values'])
                    self.stdout.write(f'Average forecast: {avg_forecast:.2f} reservations/month')
                
                # Show recent historical data
                recent_values = forecast_data['historical']['values'][-6:]
                recent_dates = forecast_data['historical']['dates'][-6:]
                
                self.stdout.write('\nRecent historical data:')
                for date, value in zip(recent_dates, recent_values):
                    self.stdout.write(f'  {date}: {value} reservations')
                
                # Show forecast
                forecast_values = forecast_data['forecast']['values']
                forecast_dates = forecast_data['forecast']['dates']
                
                self.stdout.write('\n6-month forecast:')
                for date, value in zip(forecast_dates, forecast_values):
                    self.stdout.write(f'  {date}: {value:.1f} reservations')
                
            else:
                self.stdout.write(
                    self.style.ERROR('Failed to generate forecast data')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error during SARIMA testing: {str(e)}')
            )
            import traceback
            traceback.print_exc()
