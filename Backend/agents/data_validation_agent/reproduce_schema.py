
import pandas as pd
import numpy as np
from core.schema_inference import infer_schema

# Mock config
config = {
    'coercion_thresholds': {
        'numeric': 0.8,
        'date': 0.7,
        'categorical_unique_ratio': 0.3
    }
}

# Create sample data similar to user report
df = pd.DataFrame({
    'orderdate': ['1/15/2024', '1/16/2024', '1/17/2024'] * 100, # Repeats, so unique ratio is low. Could be detected as categorical if date check fails or is strictly ordered after numeric?
    # Note: '1/15/2024' is parsable. But if infer_schema checks numeric -> fail. date -> pass? 
    # If date_ratio >= 0.7.
    
    'postalcode': ['94043', '10001', '90210'] * 100, # Numeric-looking strings.
    # num_ratio will be 1.0. So it detects as numeric.
    
    'sales': [100.5, 200.5, 300.0] * 100, # Should be numeric
    'status': ['Shipped', 'Pending', 'Cancelled'] * 100 # Categorical
})

print("Inferred Schema (Before Fix):")
schema = infer_schema(df, config)
for item in schema:
    print(f"{item['column']}: {item['type']}")

# Expected behavior we want:
# orderdate: date
# postalcode: categorical (or string)
# sales: numeric
# status: categorical
