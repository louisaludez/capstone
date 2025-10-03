# SARIMA Forecasting Implementation

This implementation adds advanced time series forecasting capabilities to the Hotel Management System using SARIMA (Seasonal AutoRegressive Integrated Moving Average) models.

## Features

- **Automatic Model Selection**: Automatically finds optimal SARIMA parameters using grid search
- **Seasonal Pattern Detection**: Handles weekly seasonal patterns in reservation data
- **Confidence Intervals**: Provides upper and lower bounds for forecast uncertainty
- **Fallback Methods**: Uses moving average or constant forecasting when insufficient data
- **Real-time Dashboard**: Displays historical data and 7-day forecasts on admin dashboard

## Installation

### 1. Install Required Packages

Run the installation script:
```bash
python install_sarima.py
```

Or install manually:
```bash
pip install pandas==2.0.3 numpy==1.24.3 statsmodels==0.14.0 scikit-learn==1.3.0
```

### 2. Test the Implementation

Test the SARIMA forecasting with your current data:
```bash
python manage.py test_sarima
```

## How It Works

### Data Preparation
- Aggregates daily reservation counts from the `Booking` model
- Creates a complete time series with missing dates filled as 0
- Handles different booking statuses and guest counts

### Model Training
- **Stationarity Check**: Uses Augmented Dickey-Fuller test
- **Parameter Optimization**: Grid search for optimal (p,d,q)(P,D,Q,s) parameters
- **Seasonal Component**: 12-month seasonal pattern (yearly cycles)
- **Automatic Differencing**: Makes series stationary if needed

### Forecasting
- **12-month Forecast**: Predicts next 12 months' reservation patterns
- **Confidence Intervals**: 95% confidence bounds for uncertainty
- **Multiple Methods**: SARIMA, moving average, or constant fallback

## Dashboard Integration

The admin dashboard now displays:
- **Historical Data**: Last 14 days of actual reservations
- **Forecast Data**: Next 12 months of predicted reservations
- **Confidence Bands**: Visual uncertainty representation
- **Method Indicator**: Shows which forecasting method is being used

## Chart Features

- **Interactive Tooltips**: Hover for detailed information
- **Date Formatting**: User-friendly date display
- **Multiple Datasets**: Historical vs forecast visualization
- **Responsive Design**: Adapts to different screen sizes

## Model Parameters

The SARIMA model automatically selects optimal parameters:
- **ARIMA Order (p,d,q)**: AutoRegressive, Differencing, Moving Average
- **Seasonal Order (P,D,Q,s)**: Seasonal components with 7-day period
- **Maximum Values**: p,q ≤ 3, P,Q ≤ 2, d,D ≤ 2

## Fallback Methods

When insufficient data is available:
1. **Moving Average**: Uses recent average for forecasting
2. **Constant**: Predicts constant value when no data exists

## Performance Considerations

- **Minimum Data**: Requires at least 7 data points for SARIMA
- **Grid Search**: Limited parameter space for small datasets
- **Caching**: Model training happens on each page load (consider caching for production)

## Usage in Views

```python
from adminNew.sarima_forecast import get_reservation_forecast

# Get forecast data
forecast_data = get_reservation_forecast()

# Access components
historical = forecast_data['historical']
forecast = forecast_data['forecast']
method = forecast_data['method']
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all packages are installed correctly
2. **No Data**: Create some reservations first to test forecasting
3. **Memory Issues**: Large datasets may require parameter tuning
4. **Convergence Errors**: Model may fall back to simpler methods

### Debug Mode

Enable detailed logging by modifying the SARIMA class:
```python
# In sarima_forecast.py, add:
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

- **Model Caching**: Cache trained models to improve performance
- **Multiple Forecasts**: Support different time horizons (30-day, 90-day)
- **External Factors**: Include weather, events, or seasonality
- **Model Evaluation**: Add accuracy metrics and backtesting
- **Real-time Updates**: Refresh forecasts automatically

## Technical Details

### Dependencies
- **pandas**: Data manipulation and time series handling
- **numpy**: Numerical computations
- **statsmodels**: SARIMA model implementation
- **scikit-learn**: Additional metrics and utilities

### File Structure
```
capstone/
├── adminNew/
│   ├── sarima_forecast.py          # Main forecasting logic
│   ├── management/commands/
│   │   └── test_sarima.py          # Testing command
│   └── templates/adminNew/
│       └── home.html               # Updated dashboard
├── install_sarima.py               # Installation script
└── requirements.txt                # Updated dependencies
```

This implementation provides a robust foundation for time series forecasting in your hotel management system, with automatic model selection and graceful fallbacks for various data scenarios.
