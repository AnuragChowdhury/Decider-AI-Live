from typing import Dict, Any, Optional
import pandas as pd
import numpy as np
from scipy.stats import linregress
import json
from agents.data_validation_agent.core.persistence import get_dataset_from_sql

def calculate_elasticity(df: pd.DataFrame, price_col: str, qty_col: str) -> tuple[float, str]:
    """
    Calculates Price Elasticity of Demand using Log-Log Regression.
    Returns (elasticity, description).
    """
    try:
        # Filter for valid positive data (log requires > 0)
        valid_data = df[(df[price_col] > 0) & (df[qty_col] > 0)].copy()
        
        # 1. Insufficient Data Check
        if len(valid_data) < 5:
            return -0.5, "Default (-0.5) - Insufficient data points for regression"
            
        # 2. Variance Check
        if valid_data[price_col].nunique() < 2:
            return -0.5, "Default (-0.5) - No price variance in historical data"
            
        # 3. Log-Log Transformation
        x = np.log(valid_data[price_col])
        y = np.log(valid_data[qty_col])
        
        # 4. Regression
        slope, intercept, r_value, p_value, std_err = linregress(x, y)
        
        # 5. Safety Bounds (Clamping)
        # Elasticity > 0 implies Giffen good (rare). Clamp to 0.
        # Elasticity < -5 is extreme. Clamp to -5.
        elasticity = max(min(slope, 0.0), -5.0)
        
        r_squared = r_value ** 2
        confidence = "High" if r_squared > 0.5 else "Low"
        
        return elasticity, f"Calculated {elasticity:.2f} ({confidence} Confidence, R2={r_squared:.2f})"
        
    except Exception as e:
        return -0.5, f"Default (-0.5) - Calculation failed: {str(e)}"

def simulate_scenario(
    target_column: str,
    operation: str,
    value: float,
    dataset_id: str,
    filter_condition: Optional[str] = None,
    price_col: Optional[str] = None,
    quantity_col: Optional[str] = None,
    sales_col: Optional[str] = None
) -> Dict[str, Any]:
    """
    Simulates a "What If" scenario on the dataset.
    INCLUDES INTELLIGENT ELASTICITY LOGIC based on Data.
    
    Args:
        target_column: Column to modify (e.g., "Price").
        operation: "increase", "decrease", "set".
        value: Magnitude of change (e.g., 5 for 5%).
        dataset_id: ID of the dataset.
        filter_condition: Optional SQL-like filter.
        price_col: Name of the column representing Unit Price (optional, auto-detected if None).
        quantity_col: Name of the column representing Quantity (optional, auto-detected if None).
        sales_col: Name of the column representing Total Sales (optional, auto-detected if None).
    """
    try:
        # 1. Load Data
        df = get_dataset_from_sql(dataset_id)
        
        if df is None or df.empty:
            return {"error": "Dataset not found or empty."}
            
        # 2. Filter Rows
        if filter_condition:
            try:
                if "==" not in filter_condition and "=" in filter_condition:
                    filter_condition = filter_condition.replace("=", "==")
                target_rows = df.query(filter_condition).index
            except Exception as e:
                return {"error": f"Invalid filter condition: {str(e)}"}
        else:
            target_rows = df.index

        if len(target_rows) == 0:
            return {"error": "No rows matched the filter condition."}

        # 3. Resolve Columns (Dynamic or Heuristic)
        # If not provided, try to find them
        if not sales_col:
            sales_col = next((c for c in df.columns if 'sales' in c.lower() or 'amount' in c.lower()), None)
        if not price_col:
             price_col = next((c for c in df.columns if any(x in c.lower() for x in ['price', 'msrp', 'unit_cost'])), None)
        if not quantity_col:
             quantity_col = next((c for c in df.columns if any(x in c.lower() for x in ['qty', 'quantity', 'units', 'count'])), None)

        # 4. Capture "Before" State
        total_sales_before = df[sales_col].sum() if sales_col else 0
        
        # 5. Apply Operation & Calculate Pct Change
        modified_df = df.copy()
        
        # Fuzzy match target column if exact match fails
        col_to_mod = next((c for c in df.columns if c.upper() == target_column.upper()), None)
        if not col_to_mod:
             # Try fuzzy contains
             col_to_mod = next((c for c in df.columns if target_column.lower() in c.lower()), None)
             
        if not col_to_mod:
            return {"error": f"Column '{target_column}' not found in dataset."}
            
        pct_change = 0.0
        
        if operation == "increase":
            pct_change = value / 100.0
            factor = 1 + pct_change
            modified_df.loc[target_rows, col_to_mod] *= factor
        elif operation == "decrease":
            pct_change = -(value / 100.0)
            factor = 1 + pct_change
            modified_df.loc[target_rows, col_to_mod] *= factor
        elif operation == "set":
            modified_df.loc[target_rows, col_to_mod] = value
        else:
            return {"error": f"Unknown operation '{operation}'"}
            
        # 6. Smart Recalculation (Data-Driven Elasticity)
        elasticity_desc = ""
        elasticity_applied = False
        
        # Check if we are modifying Price
        is_price_change = False
        if price_col and col_to_mod == price_col:
            is_price_change = True
        elif any(x in col_to_mod.lower() for x in ['price', 'msrp', 'cost']):
            is_price_change = True
        
        if is_price_change and quantity_col and pct_change != 0 and operation != "set":
            # INTELLIGENT STEP: Calculate Elasticity for this specific subset
            subset_df = df.loc[target_rows]
            elasticity, elasticity_desc = calculate_elasticity(subset_df, col_to_mod, quantity_col)
            
            # Apply Elasticity: %DeltaQty = %DeltaPrice * Elasticity
            qty_change_pct = pct_change * elasticity
            qty_factor = 1 + qty_change_pct
            
            # Update Quantity
            modified_df.loc[target_rows, quantity_col] *= qty_factor
            elasticity_applied = True
            
        # 7. Recalculate Dependent Columns (Sales)
        if sales_col and price_col and quantity_col:
             # If we modified Price or Quantity, update Sales
             # We need to know which actual columns are Price/Qty in the modified DF
             # We use the resolved names
             modified_df.loc[target_rows, sales_col] = (
                modified_df.loc[target_rows, quantity_col] * modified_df.loc[target_rows, price_col]
             )
            
        # 8. Capture "After" State
        total_sales_after = modified_df[sales_col].sum() if sales_col else 0
        
        # 9. Summary
        diff = total_sales_after - total_sales_before
        pct_change_sales = (diff / total_sales_before * 100) if total_sales_before != 0 else 0
        
        summary = {
            "scenario": f"{operation} {col_to_mod} by {value}",
            "filter": filter_condition or "All Data",
            "impact_metric": "Total Sales" if sales_col else "Unknown Metric",
            "before": total_sales_before,
            "after": total_sales_after,
            "difference": diff,
            "percent_change": pct_change_sales,
            "rows_affected": len(target_rows),
            "assumptions": []
        }
        
        if elasticity_applied:
            summary["assumptions"].append(f"Price Elasticity Model: {elasticity_desc}")
            summary["assumptions"].append(f"Quantity Adjustment: {qty_change_pct*100:.1f}%")
        elif not quantity_col:
             summary["assumptions"].append("Could not calculate elasticity (Quantity column not found).")
            
        return summary

    except Exception as e:
        import traceback
        return {"error": f"Simulation failed: {str(e)}", "trace": traceback.format_exc()}
