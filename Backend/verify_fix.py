import pandas as pd
import os
import sys

# Ensure Backend is in path
sys.path.append(os.getcwd())

from core.persistence import persist_to_sql, get_dataset_from_sql

def verify():
    print("--- Verifying Persistence Fix ---")
    
    # Create test data
    df = pd.DataFrame([
        {"id": 1, "name": "Apple", "price": 1.20},
        {"id": 2, "name": "Banana", "price": 0.50},
        {"id": 3, "name": "Cherry", "price": 2.50}
    ])
    
    dataset_id = "test_fix_ds"
    
    try:
        # Test Persist
        ref = persist_to_sql(df, dataset_id)
        print(f"Persist Result: {ref}")
        
        # Test Retrieve
        df_retrieved = get_dataset_from_sql(dataset_id)
        print(f"Retrieved {len(df_retrieved)} rows.")
        print("Data:\n", df_retrieved)
        
        if len(df_retrieved) == 3:
            print("\n✅ VERIFICATION SUCCESSFUL!")
        else:
            print("\n❌ VERIFICATION FAILED: Row count mismatch.")
            
    except Exception as e:
        print(f"\n❌ VERIFICATION FAILED with error: {e}")

if __name__ == "__main__":
    verify()
