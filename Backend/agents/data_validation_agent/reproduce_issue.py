
import pandas as pd
import numpy as np
from core.cleaning import clean
from core.schema_inference import infer_schema

# Create a dataframe that mimics the issue
# A column that looks numeric (mostly) but is technically object dtype
df = pd.DataFrame({
    'mixed_col': ['10', '20', '30', '40', 'should_be_nan_but_is_intact?'] 
})

# Let's say standardize failed to catch 'should_be_nan_but_is_intact?' or it was just some other string
# Or more likely, 'standardize' replaced specific placeholders, but maybe not all strings.
# But 'infer_schema' is robust.

# Let's manually create the situation where schema says 'numeric' but df is object
df['mixed_col'] = df['mixed_col'].astype(object)

# Mock schema: infer_schema would likely call this numeric if > 80% are numeric
# 4/5 = 80%. So it hits the threshold 0.8.
schema = [{'column': 'mixed_col', 'type': 'numeric'}]

# Mock issues: Missing values
# Wait, median is only calculated if we are fixing "Missing values".
# So we need missing values in the column.

df = pd.DataFrame({
    'mixed_col': ['10', '20', '30', np.nan, '50'] # If it has NaNs and is object dtype
})
df['mixed_col'] = df['mixed_col'].astype(object)

# Let's try to calculate median on this object column directly to verify the error
try:
    print("Attempting median on object column...")
    print(df['mixed_col'].median())
except Exception as e:
    print(f"Caught expected error: {e}")

# Now lets try running the clean function which contains the bug
issues = [{
    'column': 'mixed_col',
    'issue': 'Missing values',
    'rows_affected': 1,
    'fix_applied': None, 
    'why': None, 
    'impact': None
}]

config = {
    'imputation': {
        'numeric': 'median',
        'categorical': 'mode',
        'date': 'keep_nat'
    }
}

print("\nRunning clean()...")
try:
    cleaned_df, _ = clean(df, issues, schema, 'lenient', config)
    print("Clean successful!")
except Exception as e:
    print(f"Clean failed with: {e}")
