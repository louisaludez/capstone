import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from statsmodels.tsa.statespace.sarimax import SARIMAX
from statsmodels.tsa.arima.model import ARIMA
from statsmodels.tsa.holtwinters import ExponentialSmoothing
from statsmodels.tsa.seasonal import seasonal_decompose
from statsmodels.graphics.tsaplots import plot_acf, plot_pacf
from statsmodels.tsa.stattools import adfuller
from sklearn.metrics import mean_absolute_error, mean_squared_error
import math
import warnings
import pickle
import os
import time
from django.conf import settings
warnings.filterwarnings('ignore')

class ReservationForecaster:
    def __init__(self):
        self.model = None
        self.fitted_model = None
        self.forecast_data = None
        self.model_type = 'sarima'  # Default model type
        self.comparison_results = {}  # Store comparison results
        
    def prepare_data(self, bookings):
        """
        Prepare time series data from booking records - monthly aggregation
        Based on booking_date from Booking table, removes null values
        """
        # Convert to DataFrame, only include bookings with valid booking_date
        data = []
        for booking in bookings:
            # Skip bookings with null booking_date
            if booking.booking_date is None:
                continue
            
            # Only include essential fields, skip if any are null
            booking_date = booking.booking_date
            if booking_date is None:
                continue
            
            data.append({
                'date': booking_date.date() if hasattr(booking_date, 'date') else booking_date,
            })
        
        if not data:
            # Return empty series if no data
            return pd.Series(dtype=float)
        
        df = pd.DataFrame(data)
        
        # Remove any rows with null values
        df = df.dropna()
        
        if df.empty:
            # Return empty series if no data after removing nulls
            return pd.Series(dtype=float)
        
        # Ensure date column is datetime
        df['date'] = pd.to_datetime(df['date'], errors='coerce')
        
        # Remove any rows where date conversion failed (null dates)
        df = df.dropna(subset=['date'])
        
        if df.empty:
            return pd.Series(dtype=float)
        
        # Create monthly reservation counts based on booking_date
        df['year_month'] = df['date'].dt.to_period('M')
        monthly_counts = df.groupby('year_month').size()
        
        # Convert period index to datetime for easier handling
        monthly_counts.index = monthly_counts.index.to_timestamp()
        
        # Create a complete monthly date range
        start_date = monthly_counts.index.min()
        end_date = monthly_counts.index.max()
        date_range = pd.date_range(start=start_date, end=end_date, freq='MS')  # Month start
        
        # Reindex to include all months (fill missing with 0)
        monthly_counts = monthly_counts.reindex(date_range, fill_value=0)
        
        print(f"Prepared data: {len(monthly_counts)} months, {monthly_counts.sum()} total bookings")
        print(f"Date range: {start_date.strftime('%Y-%m')} to {end_date.strftime('%Y-%m')}")
        
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
    
    def find_optimal_params(self, series, max_p=2, max_d=2, max_q=2, max_P=1, max_D=1, max_Q=1, s=12):
        """
        Find optimal SARIMA parameters using grid search
        Expanded search space for better model fit
        """
        best_aic = float('inf')
        best_params = None
        best_bic = float('inf')
        
        # If we have less than 24 data points (2 years), keep parameters minimal
        if len(series) < 24:
            max_p = min(max_p, 1)
            max_d = min(max_d, 1)
            max_q = min(max_q, 1)
            max_P = min(max_P, 1)
            max_D = min(max_D, 1)
            max_Q = min(max_Q, 1)
        
        print(f"Searching for optimal SARIMA parameters (this may take a moment)...")
        models_tried = 0
        
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
                                    fitted_model = model.fit(disp=False, maxiter=100)
                                    models_tried += 1
                                    
                                    # Use both AIC and BIC for better model selection
                                    # Prefer models with lower BIC (penalizes complexity more)
                                    if fitted_model.bic < best_bic or (fitted_model.bic == best_bic and fitted_model.aic < best_aic):
                                        best_aic = fitted_model.aic
                                        best_bic = fitted_model.bic
                                        best_params = (p, d, q, P, D, Q, s)
                                        
                                except:
                                    continue
        
        if best_params:
            print(f"Tried {models_tried} models. Best parameters: SARIMA{best_params[:3]}x{best_params[3:]} (AIC: {best_aic:.2f}, BIC: {best_bic:.2f})")
        else:
            print("Could not find optimal parameters, using default")
        
        return best_params if best_params else (1, 1, 1, 0, 1, 1, 12)  # Default: (1,1,1) x (0,1,1,12)
    
    def calculate_metrics(self, y_true, y_pred, model_name=None):
        """
        Calculate evaluation metrics: MAPE, MSE, RMSE, MAE
        Improved MAPE calculation to handle edge cases and outliers
        model_name: Optional name to include in printed output
        """
        # Remove any NaN or inf values
        mask = np.isfinite(y_true) & np.isfinite(y_pred)
        y_true = np.array(y_true)[mask]
        y_pred = np.array(y_pred)[mask]
        
        # Ensure predictions are non-negative (bookings can't be negative)
        y_pred = np.maximum(y_pred, 0)
        
        if len(y_true) == 0 or len(y_pred) == 0:
            return {
                'mape': 0.0,
                'mse': 0.0,
                'rmse': 0.0,
                'mae': 0.0
            }
        
        # Calculate MAE
        mae = mean_absolute_error(y_true, y_pred)
        
        # Calculate MSE
        mse = mean_squared_error(y_true, y_pred)
        
        # Calculate RMSE
        rmse = math.sqrt(mse)
        
        # Improved MAPE calculation
        # Use symmetric MAPE (sMAPE) for better handling of small values and outliers
        # sMAPE = mean(200 * |actual - forecast| / (|actual| + |forecast|))
        # This avoids division by zero issues and handles outliers better
        
        # Calculate symmetric MAPE
        denominator = np.abs(y_true) + np.abs(y_pred)
        mask_valid = denominator > 0  # Avoid division by zero
        if np.any(mask_valid):
            symmetric_mape = np.mean(200 * np.abs(y_true[mask_valid] - y_pred[mask_valid]) / denominator[mask_valid])
        else:
            symmetric_mape = 0.0
        
        # Also calculate traditional MAPE for comparison (but cap outliers)
        mask_nonzero = y_true > 0
        if np.any(mask_nonzero):
            mape_values = np.abs((y_true[mask_nonzero] - y_pred[mask_nonzero]) / y_true[mask_nonzero]) * 100
            # Cap individual MAPE values at 200% to prevent outliers from skewing the average
            mape_values = np.minimum(mape_values, 200)
            mape = np.mean(mape_values)
        else:
            mape = symmetric_mape  # Use symmetric MAPE if no non-zero values
        
        # Use the better of the two (usually symmetric MAPE is more stable)
        final_mape = min(mape, symmetric_mape) if mape > 0 else symmetric_mape
        
        metrics = {
            'mape': round(final_mape, 2),
            'mse': round(mse, 2),
            'rmse': round(rmse, 2),
            'mae': round(mae, 2)
        }
        
        # Print metrics to console if model_name is provided
        if model_name:
            print(f"\n{model_name.upper()} Model Metrics:")
            print(f"  MAPE: {metrics['mape']:.2f}%")
            print(f"  MSE:  {metrics['mse']:.2f}")
            print(f"  RMSE: {metrics['rmse']:.2f}")
            print(f"  MAE:  {metrics['mae']:.2f}")
            
            # MAPE Interpretation
            mape_value = metrics['mape']
            if mape_value < 10:
                accuracy_level = "EXCELLENT"
            elif mape_value < 15:
                accuracy_level = "VERY GOOD"
            elif mape_value < 20:
                accuracy_level = "GOOD"
            elif mape_value < 25:
                accuracy_level = "REASONABLE"
            elif mape_value < 35:
                accuracy_level = "NEEDS IMPROVEMENT"
            else:
                accuracy_level = "INACCURATE"
            
            print(f"  Accuracy Level: {accuracy_level}")
        
        return metrics
    
    def train_arima(self, train_series, test_series):
        """Train ARIMA model and evaluate on test set"""
        try:
            print("\nTraining ARIMA model...")
            # Try common ARIMA orders
            best_aic = float('inf')
            best_order = (1, 1, 1)
            
            for p in range(0, 3):
                for d in range(0, 2):
                    for q in range(0, 3):
                        try:
                            model = ARIMA(train_series, order=(p, d, q))
                            fitted = model.fit()
                            if fitted.aic < best_aic:
                                best_aic = fitted.aic
                                best_order = (p, d, q)
                        except:
                            continue
            
            model = ARIMA(train_series, order=best_order)
            fitted_model = model.fit()
            print(f"ARIMA{best_order} fitted (AIC: {best_aic:.2f})")
            
            # Forecast on test set
            test_forecast = fitted_model.forecast(steps=len(test_series))
            metrics = self.calculate_metrics(test_series.values, test_forecast.values, model_name='ARIMA')
            
            return {
                'model': fitted_model,
                'order': best_order,
                'metrics': metrics,
                'method': 'arima'
            }
        except Exception as e:
            print(f"ARIMA training failed: {e}")
            return None
    
    def train_holtwinters(self, train_series, test_series):
        """Train Holt-Winters (Exponential Smoothing) model and evaluate on test set"""
        try:
            print("\nTraining Holt-Winters (Exponential Smoothing) model...")
            # Holt-Winters with seasonal component (monthly data, seasonality=12)
            if len(train_series) >= 24:  # Need at least 2 years for seasonal
                model = ExponentialSmoothing(
                    train_series,
                    seasonal_periods=12,
                    trend='add',
                    seasonal='add'
                )
            else:
                # Simple exponential smoothing if not enough data
                model = ExponentialSmoothing(
                    train_series,
                    trend='add',
                    seasonal=None
                )
            
            fitted_model = model.fit(optimized=True)
            print("Holt-Winters model fitted")
            
            # Forecast on test set
            test_forecast = fitted_model.forecast(steps=len(test_series))
            metrics = self.calculate_metrics(test_series.values, test_forecast.values, model_name='Holt-Winters')
            
            return {
                'model': fitted_model,
                'metrics': metrics,
                'method': 'holtwinters'
            }
        except Exception as e:
            print(f"Holt-Winters training failed: {e}")
            return None
    
    def train_model(self, series, test_size=0.2):
        """
        Train and compare ARIMA, SARIMA, and Holt-Winters models
        Uses 80/20 split: 80% training, 20% testing
        Based on booking_date from Booking table only (room_id not included)
        Selects the best model based on lowest MAPE
        """
        if len(series) < 12:
            # Not enough data for SARIMA, return simple moving average
            return self._simple_forecast(series)
        
        # Split data into 80% training, 20% testing
        total_months = len(series)
        test_months = int(total_months * 0.2)  # Exactly 20% for test
        
        # Ensure minimum sizes: at least 12 months for training, at least 6 months for testing
        if test_months < 6:
            test_months = 6
        if total_months - test_months < 12:
            test_months = max(6, total_months - 12)
        
        split_idx = total_months - test_months
        train_series = series[:split_idx]
        test_series = series[split_idx:]
        
        train_percentage = (len(train_series) / total_months) * 100
        test_percentage = (len(test_series) / total_months) * 100
        
        print(f"Data split (80/20 basis):")
        print(f"  Training: {len(train_series)} months ({train_percentage:.1f}%)")
        print(f"  Testing:  {len(test_series)} months ({test_percentage:.1f}%)")
        
        # Train and compare all three models
        results = {}
        
        # 1. Train ARIMA
        arima_result = self.train_arima(train_series, test_series)
        if arima_result:
            results['arima'] = arima_result
        
        # 2. Train SARIMA
        print("\nTraining SARIMA model...")
        try:
            if len(train_series) < 24:
                order, seasonal_order = (1, 1, 1), (0, 1, 1, 12)
                print("Using simple SARIMA(1,1,1)x(0,1,1,12) for small dataset")
            elif len(train_series) < 36:
                print("Trying common SARIMA configurations...")
                best_aic = float('inf')
                best_order = (1, 1, 1)
                best_seasonal = (0, 1, 1, 12)
                
                configs = [
                    ((1, 1, 1), (0, 1, 1, 12)),
                    ((1, 1, 0), (0, 1, 1, 12)),
                    ((0, 1, 1), (0, 1, 1, 12)),
                    ((2, 1, 0), (0, 1, 1, 12)),
                ]
                
                for ord, seas in configs:
                    try:
                        model = SARIMAX(train_series, order=ord, seasonal_order=seas, 
                                       enforce_stationarity=False, enforce_invertibility=False)
                        fitted = model.fit(disp=False, maxiter=100)
                        if fitted.aic < best_aic:
                            best_aic = fitted.aic
                            best_order = ord
                            best_seasonal = seas
                    except:
                        continue
                
                order, seasonal_order = best_order, best_seasonal
                print(f"Selected SARIMA{order}x{best_seasonal} (AIC: {best_aic:.2f})")
            else:
                params = self.find_optimal_params(train_series)
                order, seasonal_order = params[:3], params[3:]
            
            model = SARIMAX(train_series, order=order, seasonal_order=seasonal_order,
                          enforce_stationarity=False, enforce_invertibility=False)
            fitted_model = model.fit(disp=False, maxiter=200)
            
            test_forecast = fitted_model.forecast(steps=len(test_series))
            print(f"SARIMA{order}x{seasonal_order} fitted")
            metrics = self.calculate_metrics(test_series.values, test_forecast.values, model_name='SARIMA')
            
            results['sarima'] = {
                'model': fitted_model,
                'order': order,
                'seasonal_order': seasonal_order,
                'metrics': metrics,
                'method': 'sarima'
            }
        except Exception as e:
            print(f"SARIMA training failed: {e}")
        
        # 3. Train Holt-Winters
        holtwinters_result = self.train_holtwinters(train_series, test_series)
        if holtwinters_result:
            results['holtwinters'] = holtwinters_result
        
        # Compare models and select best
        if not results:
            print("\nAll models failed, using simple forecast")
            return self._simple_forecast(series)
        
        # Find best model based on MAPE
        best_model_name = None
        best_mape = float('inf')
        
        print(f"\n{'='*70}")
        print("MODEL COMPARISON RESULTS")
        print(f"{'='*70}")
        print(f"{'Model':<15} {'MAPE':<10} {'MSE':<12} {'RMSE':<10} {'MAE':<10}")
        print("-" * 70)
        
        for model_name, result in results.items():
            m = result['metrics']
            print(f"{model_name.upper():<15} {m['mape']:<10.2f} {m['mse']:<12.2f} {m['rmse']:<10.2f} {m['mae']:<10.2f}")
            if m['mape'] < best_mape:
                best_mape = m['mape']
                best_model_name = model_name
        
        print("-" * 70)
        print(f"BEST MODEL: {best_model_name.upper()} (Lowest MAPE: {best_mape:.2f}%)")
        print(f"{'='*70}\n")
        
        # Store best model
        best_result = results[best_model_name]
        self.fitted_model = best_result['model']
        self.model_type = best_result['method']
        self.evaluation_metrics = best_result['metrics']
        self.comparison_results = results
        
        # Save to pickle file for fast loading
        self._save_model_to_pickle(best_result, results, series)
        
        return True
    
    def _save_model_to_pickle(self, best_result, comparison_results, full_series):
        """Save the best model and results to pickle file"""
        try:
            pickle_file = os.path.join(settings.BASE_DIR, 'sarima_forecast.pkl')
            
            # Prepare data to save
            # Version number - increment this if pickle format changes
            PICKLE_VERSION = 2  # Updated to include comparison_results and all model metrics
            
            save_data = {
                'version': PICKLE_VERSION,
                'model': best_result['model'],
                'model_type': best_result['method'],
                'metrics': best_result['metrics'],
                'comparison_results': comparison_results,
                'full_series': full_series,  # Save full series for refitting if needed
                'saved_at': datetime.now(),
                'model_info': {
                    'order': best_result.get('order'),
                    'seasonal_order': best_result.get('seasonal_order'),
                }
            }
            
            with open(pickle_file, 'wb') as f:
                pickle.dump(save_data, f)
            
            print(f"\nModel saved to pickle file: {pickle_file}")
            print(f"Model will be retrained after 7 days (1 week)")
        except Exception as e:
            print(f"Warning: Could not save model to pickle file: {e}")
    
    def _load_model_from_pickle(self, force_retrain=False):
        """Load model from pickle file if it's less than 7 days old"""
        try:
            pickle_file = os.path.join(settings.BASE_DIR, 'sarima_forecast.pkl')
            
            if not os.path.exists(pickle_file):
                return None
            
            # Force retrain if requested
            if force_retrain:
                print("Force retrain requested. Deleting old pickle file...")
                try:
                    os.remove(pickle_file)
                    print("Old pickle file deleted. Will retrain model.")
                except Exception as e:
                    print(f"Warning: Could not delete pickle file: {e}")
                return None
            
            # Check file age
            file_time = os.path.getmtime(pickle_file)
            file_age_days = (time.time() - file_time) / (24 * 3600)
            
            if file_age_days > 7:
                print(f"Pickle file is {file_age_days:.1f} days old (> 7 days). Retraining model...")
                return None
            
            with open(pickle_file, 'rb') as f:
                saved_data = pickle.load(f)
            
            # Check pickle version - if version mismatch, retrain
            PICKLE_VERSION = 2  # Current version
            saved_version = saved_data.get('version', 1)  # Old pickles don't have version
            if saved_version != PICKLE_VERSION:
                print(f"Pickle file version mismatch (saved: {saved_version}, current: {PICKLE_VERSION}). Retraining model...")
                try:
                    os.remove(pickle_file)
                    print("Old pickle file deleted due to version mismatch.")
                except:
                    pass
                return None
            
            # Check if saved_at exists and is less than 7 days old
            if 'saved_at' in saved_data:
                saved_at = saved_data['saved_at']
                if isinstance(saved_at, str):
                    saved_at = datetime.fromisoformat(saved_at)
                age_days = (datetime.now() - saved_at).days
                
                if age_days > 7:
                    print(f"Saved model is {age_days} days old (> 7 days). Retraining model...")
                    return None
                
                print(f"Loading model from pickle file (saved {age_days} days ago, {7 - age_days} days until retrain)")
            else:
                print("Loading model from pickle file (age check not available)")
            
            # Restore model state
            self.fitted_model = saved_data.get('model')
            self.model_type = saved_data.get('model_type', 'sarima')
            self.evaluation_metrics = saved_data.get('metrics', {})
            self.comparison_results = saved_data.get('comparison_results', {})
            
            return saved_data
            
        except Exception as e:
            print(f"Warning: Could not load model from pickle file: {e}")
            return None
    
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
        # Calculate simple metrics for moving average
        if len(series) > window:
            test_data = series.tail(window).values
            avg_value = np.mean(series.head(-window).tail(window).values)
            predictions = [avg_value] * len(test_data)
            self.evaluation_metrics = self.calculate_metrics(test_data, predictions)
        else:
            self.evaluation_metrics = {'mape': 0.0, 'mse': 0.0, 'rmse': 0.0, 'mae': 0.0}
        return True
    
    def forecast(self, steps=12):
        """
        Generate forecast for the next 'steps' months
        Ensures forecasts are non-negative and reasonable
        """
        if self.fitted_model is not None:
            # Generate forecast based on model type
            if self.model_type == 'holtwinters':
                # Holt-Winters forecast
                forecast = self.fitted_model.forecast(steps=steps)
                # Holt-Winters doesn't provide confidence intervals easily, use simple approximation
                std = np.std(forecast) if len(forecast) > 1 else forecast[0] * 0.1
                lower_bound = np.maximum(forecast - 1.96 * std, 0)
                upper_bound = forecast + 1.96 * std
            else:
                # ARIMA or SARIMA forecast
                forecast = self.fitted_model.forecast(steps=steps)
                try:
                    confidence_intervals = self.fitted_model.get_forecast(steps=steps).conf_int()
                    lower_bound = confidence_intervals.iloc[:, 0] if hasattr(confidence_intervals, 'iloc') else forecast - forecast * 0.2
                    upper_bound = confidence_intervals.iloc[:, 1] if hasattr(confidence_intervals, 'iloc') else forecast + forecast * 0.2
                except:
                    # Fallback if confidence intervals not available
                    std = np.std(forecast) if len(forecast) > 1 else forecast[0] * 0.1
                    lower_bound = np.maximum(forecast - 1.96 * std, 0)
                    upper_bound = forecast + 1.96 * std
            
            # Ensure forecasts are non-negative (bookings can't be negative)
            forecast = np.maximum(forecast, 0)
            lower_bound = np.maximum(lower_bound, 0) if hasattr(lower_bound, '__iter__') else max(0, lower_bound)
            upper_bound = np.maximum(upper_bound, 0) if hasattr(upper_bound, '__iter__') else max(0, upper_bound)
            
            # Convert to lists
            if hasattr(forecast, 'tolist'):
                forecast = forecast.tolist()
            if hasattr(lower_bound, 'tolist'):
                lower_bound = lower_bound.tolist()
            elif hasattr(lower_bound, '__iter__') and not isinstance(lower_bound, str):
                lower_bound = list(lower_bound)
            if hasattr(upper_bound, 'tolist'):
                upper_bound = upper_bound.tolist()
            elif hasattr(upper_bound, '__iter__') and not isinstance(upper_bound, str):
                upper_bound = list(upper_bound)
            
            return {
                'forecast': forecast,
                'lower_bound': lower_bound,
                'upper_bound': upper_bound,
                'method': self.model_type
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
    
    def get_forecast_chart_data(self, series, forecast_months=12, historical_months=12, use_saved_model=False):
        """
        Get complete chart data including historical and forecast
        If use_saved_model=True, uses already loaded model without retraining
        """
        # Get historical data
        historical = self.get_historical_data(series, historical_months)
        
        # If using saved model, skip training
        if use_saved_model and self.fitted_model is not None:
            print("Using saved model for forecasting (no retraining needed)")
        elif not self.train_model(series):
            # Training failed, return None
            return None
        
        # Generate forecast
        if self.fitted_model is not None:
            # If not using saved model, refit on full dataset for better forecasting
            if not use_saved_model and len(series) >= 12:
                # Refit on full dataset for actual forecasting
                if self.model_type == 'sarima':
                    if len(series) < 24:
                        order, seasonal_order = (1, 1, 1), (0, 1, 1, 12)
                    else:
                        params = self.find_optimal_params(series)
                        order, seasonal_order = params[:3], params[3:]
                    
                    try:
                        full_model = SARIMAX(
                            series,
                            order=order,
                            seasonal_order=seasonal_order,
                            enforce_stationarity=False,
                            enforce_invertibility=False
                        )
                        self.fitted_model = full_model.fit(disp=False)
                    except:
                        pass  # Keep the previous model if refitting fails
                elif self.model_type == 'arima':
                    # Refit ARIMA on full dataset
                    try:
                        order = self.comparison_results.get('arima', {}).get('order', (1, 1, 1))
                        full_model = ARIMA(series, order=order)
                        self.fitted_model = full_model.fit()
                    except:
                        pass
                elif self.model_type == 'holtwinters':
                    # Refit Holt-Winters on full dataset
                    try:
                        if len(series) >= 24:
                            full_model = ExponentialSmoothing(
                                series,
                                seasonal_periods=12,
                                trend='add',
                                seasonal='add'
                            )
                        else:
                            full_model = ExponentialSmoothing(
                                series,
                                trend='add',
                                seasonal=None
                            )
                        self.fitted_model = full_model.fit(optimized=True)
                    except:
                        pass
            
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
            
            result = {
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
            
            # Add evaluation metrics if available
            if hasattr(self, 'evaluation_metrics') and self.evaluation_metrics:
                result['metrics'] = self.evaluation_metrics
            
            return result
        
        return None

def get_reservation_forecast(force_retrain=False):
    """
    Main function to get reservation forecast data
    Loads from pickle file if less than 7 days old, otherwise retrains
    force_retrain: If True, will delete pickle file and retrain regardless of age
    """
    from staff.models import Booking
    from django.core.cache import cache
    
    print("\n" + "="*60)
    print("LOADING FORECAST MODEL")
    print("="*60)
    
    # Create forecaster instance
    forecaster = ReservationForecaster()
    
    # Try to load from pickle file first (if less than 7 days old)
    saved_data = forecaster._load_model_from_pickle(force_retrain=force_retrain)
    
    if saved_data:
        # Model loaded from pickle, generate forecast
        print("Using saved model from pickle file")
        series = saved_data.get('full_series')
        
        # Print all model comparison results if available
        comparison_results = saved_data.get('comparison_results', {})
        if comparison_results:
            print(f"\n{'='*70}")
            print("SAVED MODEL COMPARISON RESULTS")
            print(f"{'='*70}")
            print(f"{'Model':<15} {'MAPE':<10} {'MSE':<12} {'RMSE':<10} {'MAE':<10}")
            print("-" * 70)
            
            for model_name, result in comparison_results.items():
                m = result.get('metrics', {})
                if m:
                    print(f"{model_name.upper():<15} {m.get('mape', 0):<10.2f} {m.get('mse', 0):<12.2f} {m.get('rmse', 0):<10.2f} {m.get('mae', 0):<10.2f}")
            
            best_model = saved_data.get('model_type', 'unknown')
            best_metrics = saved_data.get('metrics', {})
            print("-" * 70)
            print(f"BEST MODEL: {best_model.upper()} (Lowest MAPE: {best_metrics.get('mape', 0):.2f}%)")
            print(f"{'='*70}\n")
        
        if series is not None and len(series) > 0:
            # Generate forecast using saved model
            result = forecaster.get_forecast_chart_data(series, use_saved_model=True)
            
            if result:
                print("\n" + "="*60)
                print("FORECAST GENERATED FROM SAVED MODEL")
                print("="*60)
                if 'metrics' in result:
                    print(f"Model: {result.get('method', 'unknown').upper()}")
                    print(f"Metrics: {result['metrics']}")
                return result
    
    # Need to retrain (pickle doesn't exist or is older than 7 days)
    print("\n" + "="*60)
    print("TRAINING NEW MODEL (ARIMA vs SARIMA vs Holt-Winters)")
    print("="*60)

    # Get all bookings from Booking table, filter out null booking_date
    # Only fetch booking_date field (room_id and other fields not included)
    bookings = Booking.objects.exclude(booking_date__isnull=True).only('booking_date').order_by('booking_date')
    bookings_count = bookings.count()
    print(f"Total bookings in database (excluding null booking_date): {bookings_count}")
    print(f"Using only booking_date field from Booking table (room_id not included)")
    
    # Prepare data
    print("Preparing time series data...")
    series = forecaster.prepare_data(bookings)
    print(f"Time series length: {len(series)} months")
    if len(series) > 0:
        print(f"Date range: {series.index[0]} to {series.index[-1]}")
    
    # Train models and generate forecast (this will save to pickle automatically)
    print("Training and comparing models...")
    result = forecaster.get_forecast_chart_data(series)
    
    if result and 'metrics' in result:
        print("\n" + "="*60)
        print("FORECAST GENERATION COMPLETE")
        print("="*60)
        print(f"Best Model: {result.get('method', 'unknown').upper()}")
        print(f"Metrics: {result['metrics']}")
        print(f"Model saved to pickle file (will retrain after 7 days)")
    else:
        print("\nWarning: Forecast generated but no metrics found in result")
        if result:
            print(f"Result keys: {result.keys()}")
    
    return result
