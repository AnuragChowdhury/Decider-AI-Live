import pandas as pd
import numpy as np
from tools.sql_query import query_data
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
import json

class PredictionAgent:
    """
    Agent responsible for generating forecasts and predictive analytics.
    """
    
    def _detect_columns(self, dataset_id: str) -> tuple[Optional[str], Optional[str]]:
        """
        Attempts to detect date and value columns from the dataset.
        """
        # Fetch columns using a limit 1 query
        res = query_data("SELECT * FROM data LIMIT 1", dataset_id)
        
        if not res['success'] or not res['columns']:
            print(f"DEBUG: Failed to detect columns: {res.get('error')}")
            return None, None
        
        columns = res['columns']
        
        # Heuristic detection
        date_col = next((c for c in columns if 'date' in c.lower() or 'time' in c.lower()), None)
        # Look for sales, amount, revenue, or just the first numeric column that isn't ID/Date?
        # Let's stick to specific keywords for safety first
        val_col = next((c for c in columns if 'sales' in c.lower() or 'amount' in c.lower() or 'revenue' in c.lower() or 'total' in c.lower() or 'price' in c.lower()), None)
        
        return date_col, val_col

    def forecast(self, dataset_id: str, horizon_months: int = 12) -> str:
        """
        Generates a sales forecast.
        """
        date_col, val_col = self._detect_columns(dataset_id)
        
        if not date_col or not val_col:
            # Try to give a helpful error
            res = query_data("SELECT * FROM data LIMIT 1", dataset_id)
            cols = res.get('columns', [])
            return json.dumps({
                "error": f"Could not automatically detect 'date' and 'sales' columns for forecasting. Available columns: {cols}. Please retry by specifying columns if possible (not yet implemented in tool args)."
            })

        # Fetch data
        # fetching all data might be heavy, but for forecasting we need granularity.
        # Let's assume we can fetch it. If it fails, we catch it.
        # Use 'FROM data' and let query_data replace it with the table name
        query = f"SELECT {date_col}, {val_col} FROM data"
        res = query_data(query, dataset_id, bypass_validation=True)
        
        if not res['success']:
             return json.dumps({"error": f"Failed to fetch data for forecasting: {res['error']}"})
             
        df = pd.DataFrame(res['data'])
        if df.empty:
             return json.dumps({"error": "No data found in the dataset."})
             
        # Process and Forecast
        try:
            # formatting
            df[date_col] = pd.to_datetime(df[date_col], errors='coerce')
            df[val_col] = pd.to_numeric(df[val_col], errors='coerce').fillna(0)
            df = df.dropna(subset=[date_col])
            
            # Group by month
            monthly_sales = df.groupby(df[date_col].dt.to_period("M"))[val_col].sum().reset_index()
            monthly_sales['month_num'] = np.arange(len(monthly_sales))
            
            if len(monthly_sales) < 3:
                return json.dumps({"error": f"Not enough monthly data points for forecasting. Found {len(monthly_sales)} months. Need at least 3."})
            
            # Simple Polynomial Regression (Degree 2)
            z = np.polyfit(monthly_sales['month_num'], monthly_sales[val_col], 2)
            p = np.poly1d(z)
            
            last_month_num = monthly_sales['month_num'].max()
            next_months = np.arange(last_month_num + 1, last_month_num + 1 + horizon_months)
            forecast_values = p(next_months)
            
            # Format results
            forecast_data = []
            # We need to construct the future date strings
            last_period = monthly_sales[date_col].max()
            
            # Iterate and create future dates
            # last_period is a Period object
            
            for i, val in enumerate(forecast_values):
                # period logic
                future_period = last_period + (i + 1)
                forecast_data.append({
                    "month": str(future_period),
                    "forecast_value": round(float(val), 2)
                })
            
            # Calculate total predicted sales
            total_predicted = sum(x['forecast_value'] for x in forecast_data)
            
            result = {
                "forecast_summary": f"Forecast for next {horizon_months} months generated using {date_col} and {val_col}.",
                "total_predicted_sales": round(total_predicted, 2),
                "monthly_breakdown": forecast_data,
                "model": "Polynomial Regression (Degree 2)"
            }
            
            return json.dumps(result, indent=2)
            
        except Exception as e:
            return json.dumps({"error": f"Forecasting calculation failed: {str(e)}"})

# Singleton
prediction_agent = PredictionAgent()

@tool
def generate_forecast(dataset_id: str = "", horizon_months: int = 12) -> str:
    """
    Generates a sales forecast for the specified horizon (default 12 months).
    Use this tool when the user asks for future predictions, sales forecast, or trends for the next year.
    Returns monthly breakdown and total predicted sales.
    
    Args:
        dataset_id: The ID of the dataset (usually found in context).
        horizon_months: Number of months to forecast (default 12).
    """
    # If dataset_id is empty, try to get it? The LLM should extract it from context.
    if not dataset_id:
        return json.dumps({"error": "dataset_id is required."})
        
    return prediction_agent.forecast(dataset_id, horizon_months)
