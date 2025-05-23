import numpy as np
import pandas as pd

# Set random seed for reproducibility
np.random.seed(42)

# Generate 1000 samples
n_samples = 1000

# Generate TV advertising (in thousands of dollars)
# Most companies spend between 0 and 300 on TV ads
tv = np.random.uniform(0, 300, n_samples)

# Generate radio advertising (in thousands of dollars)
# Most companies spend between 0 and 50 on radio ads
radio = np.random.uniform(0, 50, n_samples)

# Generate newspaper advertising (in thousands of dollars)
# Most companies spend between 0 and 100 on newspaper ads
newspaper = np.random.uniform(0, 100, n_samples)

# Generate sales (in thousands of units)
# Sales are influenced by all three advertising channels with different weights
# TV has the strongest impact, followed by radio, then newspaper
sales = (
    0.05 * tv +  # TV has the strongest impact
    0.1 * radio +  # Radio has moderate impact
    0.01 * newspaper +  # Newspaper has the weakest impact
    np.random.normal(0, 5, n_samples)  # Add some random noise
)

# Ensure sales are positive
sales = np.maximum(sales, 0)

# Create DataFrame
df = pd.DataFrame({
    'TV': tv,
    'radio': radio,
    'newspaper': newspaper,
    'sales': sales
})

# Round all values to 1 decimal place
df = df.round(1)

# Save to CSV
df.to_csv('Advertising.csv', index=False) 