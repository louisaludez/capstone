import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.stattools import adfuller
from sklearn.metrics import mean_absolute_error, mean_squared_error
import warnings
warnings.filterwarnings('ignore')

class ReservationForecaster:
    def __init__(self):
        self.model = None
        self.fitted_model = None
        self.forecast_data = None
        
    def prepare_data(self, bookings):
        """
        Prepare time series data from booking records - monthly aggregation
        """
        # Convert to DataFrame
        data = []
        for booking in bookings:
            data.append({
                'date': booking.booking_date.date(),
                'check_in_date': booking.check_in_date,
                'check_out_date': booking.check_out_date,
                'status': booking.status,
                'num_adults': booking.num_of_adults,
                'num_children': booking.num_of_children,
                'total_guests': booking.total_of_guests
            })
        
        df = pd.DataFrame(data)
        
        if df.empty:
            # Return empty series if no data
            return pd.Series(dtype=float)
        
        # Create monthly reservation counts
        df['year_month'] = pd.to_datetime(df['date']).dt.to_period('M')
        monthly_counts = df.groupby('year_month').size()
        
        # Convert period index to datetime for easier handling
        monthly_counts.index = monthly_counts.index.to_timestamp()
        
        # Create a complete monthly date range
        start_date = monthly_counts.index.min()
        end_date = monthly_counts.index.max()
        date_range = pd.date_range(start=start_date, end=end_date, freq='MS')  # Month start
        
        # Reindex to include all months (fill missing with 0)
        monthly_counts = monthly_counts.reindex(date_range, fill_value=0)
        
        return monthly_counts
    
    def check_stationarity(self, series):
        """
        Check if the time series is stationary using Augmented Dickey-Fuller test
        """
        result = adfuller(series.dropna())
        return result[1] < 0.05  # p-value < 0.05 means stationary
    
    def make_stationary(self, series):
        """
        Make the series stationary by differencing
        """
        # First difference
        diff1 = series.diff().dropna()
        
        if self.check_stationarity(diff1):
            return diff1, 1
        
        # Second difference
        diff2 = diff1.diff().dropna()
        
        if self.check_stationarity(diff2):
            return diff2, 2
        
        return series, 0
    
    def find_optimal_params(self, series, max_p=1, max_d=1, max_q=1, max_P=1, max_D=1, max_Q=1, s=12):
        """
        Find optimal SARIMA parameters using grid search
        """
        best_aic = float('inf')
        best_params = None
        
        # If we have less than 24 data points (2 years), keep parameters minimal
        if len(series) < 24:
            max_p = min(max_p, 1)
            max_q = min(max_q, 1)
            max_P = min(max_P, 1)
            max_Q = min(max_Q, 1)
        
        for p in range(max_p + 1):
            for d in range(max_d + 1):
                for q in range(max_q + 1):
                    for P in range(max_P + 1):
                        for D in range(max_D + 1):
                            for Q in range(max_Q + 1):
                                try:
                                    model = SARIMAX(
                                        series,
                                        order=(p, d, q),
                                        seasonal_order=(P, D, Q, s),
                                        enforce_stationarity=False,
                                        enforce_invertibility=False
                                    )
                                    fitted_model = model.fit(disp=False)
                                    
                                    if fitted_model.aic < best_aic:
                                        best_aic = fitted_model.aic
                                        best_params = (p, d, q, P, D, Q, s)
                                        
                                except:
                                    continue
        
        return best_params if best_params else (1, 1, 1, 1, 1, 1, 12)
    
    def train_model(self, series):
        """
        Train SARIMA model on the time series data
        """
        if len(series) < 12:
            # Not enough data for SARIMA, return simple moving average
            return self._simple_forecast(series)
        
        # With limited data, skip expensive grid search and use a common seasonal spec
        if len(series) < 24:
            order, seasonal_order = (1, 1, 1), (0, 1, 1, 12)
        else:
            # Find optimal parameters
            params = self.find_optimal_params(series)
            order, seasonal_order = params[:3], params[3:]
        
        try:
            # Fit the model
            model = SARIMAX(
                series,
                order=order,
                seasonal_order=seasonal_order,
                enforce_stationarity=False,
                enforce_invertibility=False
            )
            
            self.fitted_model = model.fit(disp=False)
            self.model = model
            
            return True
            
        except Exception as e:
            print(f"Error fitting SARIMA model: {e}")
            return self._simple_forecast(series)
    
    def _simple_forecast(self, series):
        """
        Simple forecasting method when SARIMA fails
        """
        if len(series) == 0:
            return False
        
        # Use simple moving average
        window = min(6, len(series))  # 6 months for monthly data
        self.forecast_data = {
            'method': 'moving_average',
            'window': window,
            'last_values': series.tail(window).tolist()
        }
        return True
    
    def forecast(self, steps=6):
        """
        Generate forecast for the next 'steps' days
        """
        if self.fitted_model is not None:
            # SARIMA forecast
            forecast = self.fitted_model.forecast(steps=steps)
            confidence_intervals = self.fitted_model.get_forecast(steps=steps).conf_int()
            
            return {
                'forecast': forecast.tolist(),
                'lower_bound': confidence_intervals.iloc[:, 0].tolist(),
                'upper_bound': confidence_intervals.iloc[:, 1].tolist(),
                'method': 'sarima'
            }
        
        elif self.forecast_data and self.forecast_data['method'] == 'moving_average':
            # Simple moving average forecast
            last_values = self.forecast_data['last_values']
            avg_value = np.mean(last_values)
            
            forecast = [avg_value] * steps
            return {
                'forecast': forecast,
                'lower_bound': [max(0, avg_value - 1)] * steps,
                'upper_bound': [avg_value + 1] * steps,
                'method': 'moving_average'
            }
        
        else:
            # Fallback: constant forecast
            return {
                'forecast': [1] * steps,
                'lower_bound': [0] * steps,
                'upper_bound': [2] * steps,
                'method': 'constant'
            }
    
    def get_historical_data(self, series, months=12):
        """
        Get historical data for the last 'days' days
        """
        if len(series) == 0:
            return []
        
        # Get last 'months' months of data
        recent_data = series.tail(months)
        return recent_data.tolist()
    
    def get_forecast_chart_data(self, series, forecast_months=6, historical_months=12):
        """
        Get complete chart data including historical and forecast
        """
        # Get historical data
        historical = self.get_historical_data(series, historical_months)
        
        # Train model and get forecast
        if self.train_model(series):
            forecast_result = self.forecast(forecast_months)
            
            # Generate dates
            if len(series) > 0:
                last_date = series.index[-1]
                # Generate monthly dates
                historical_dates = []
                for i in range(len(historical)):
                    month_date = last_date - pd.DateOffset(months=len(historical)-1-i)
                    historical_dates.append(month_date)
                
                forecast_dates = []
                for i in range(forecast_months):
                    month_date = last_date + pd.DateOffset(months=i+1)
                    forecast_dates.append(month_date)
            else:
                # Fallback dates
                today = datetime.now().date()
                historical_dates = []
                for i in range(len(historical)):
                    month_date = today - pd.DateOffset(months=len(historical)-1-i)
                    historical_dates.append(month_date)
                
                forecast_dates = []
                for i in range(forecast_months):
                    month_date = today + pd.DateOffset(months=i+1)
                    forecast_dates.append(month_date)
            
            return {
                'historical': {
                    'dates': [d.strftime('%B %d, %Y') for d in historical_dates],
                    'values': historical
                },
                'forecast': {
                    'dates': [d.strftime('%B %d, %Y') for d in forecast_dates],
                    'values': forecast_result['forecast'],
                    'lower_bound': forecast_result['lower_bound'],
                    'upper_bound': forecast_result['upper_bound']
                },
                'method': forecast_result['method']
            }
        
        return None

def get_reservation_forecast():
    """
    Main function to get reservation forecast data
    """
    from staff.models import Booking
    from django.core.cache import cache
    
    # Get all bookings
    bookings = Booking.objects.all().only('booking_date', 'check_in_date', 'check_out_date', 'status', 'num_of_adults', 'num_of_children', 'total_of_guests').order_by('booking_date')

    # Build a cache key based on booking count and latest booking timestamp
    bookings_count = bookings.count()
    latest_booking_dt = Booking.objects.order_by('-booking_date').values_list('booking_date', flat=True).first()
    latest_marker = latest_booking_dt.isoformat() if latest_booking_dt else 'none'
    cache_key = f"reservation_forecast:monthly:v1:{bookings_count}:{latest_marker}"

    cached = cache.get(cache_key)
    if cached:
        return cached
    
    # Create forecaster
    forecaster = ReservationForecaster()
    
    # Prepare data
    series = forecaster.prepare_data(bookings)
    
    # Get forecast data
    result = forecaster.get_forecast_chart_data(series)
    # Cache for 30 minutes
    cache.set(cache_key, result, 60 * 30)
    return result
