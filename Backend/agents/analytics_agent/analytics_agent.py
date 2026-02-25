from core.schemas import AnalyticsInput, AnalyticsOutput, KPI, AggregateItem, ForecastItem, AnomalyItem, RiskAnalysis
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from typing import Dict, Any, List
import pandas as pd
import numpy as np
import json
import os
import io

# Initialize LLM
llm = ChatGroq(model="llama-3.3-70b-versatile", temperature=0)

# Parser
parser = PydanticOutputParser(pydantic_object=AnalyticsOutput)

# Prompt
system_template = """You are an expert Data Analytics Agent.
Your goal is to analyze the provided dataset profile, business context, and AUTOMATED INSIGHTS (Forecasts, Anomalies, Risks) to decide relevancy.

Input Context:
- Dataset ID: {dataset_id}
- Business Context: {business_context}
- Column Profiles: {column_profiles}
- Automated Insights: {insights}

Instructions:
1. Identify 2-4 critical KPIs based on the business context.
2. For each KPI, provide a valid SQL-like query (conceptual) and a calculated value.
3. Identify 2-3 relevant Aggregates (grouped data) that should be visualized.
4. For each Aggregate, RECOMMEND a suitable Nivo chart type. BE CREATIVE and FLEXIBLE.
   - Do not limit yourself to Bar/Line charts.
   - Consider: 'Pie', 'Donut', 'Radar', 'ScatterPlot', 'HeatMap', 'TreeMap', 'Sunburst', 'Funnel', 'Stream', 'Choropleth' (if geo data), 'Calendar' (time density).
   - Choose the one that best tells the story of the data.
5. Review the provided 'Automated Insights' (forecasts, anomalies, risks). If they are relevant/significant, include them in the final output schema 'forecasts', 'anomalies', and 'risk_analysis' sections DO NOT MODIFY the values, just pass them through if relevant.
6. Return the response STRICTLY in the specified JSON format.

Format Instructions:
{format_instructions}
"""

prompt = ChatPromptTemplate.from_template(system_template)

class AnalyticsAgent:
    def __init__(self):
        self.chain = prompt | llm | parser

    def _analyze_csv(self, file_path: str) -> Dict[str, Any]:
        """
        Reads CSV or DuckDB dataset and generates a profile.
        """
        try:
            df = None
            
            # Helper to load data
            if file_path.startswith("duckdb:"):
                try:
                    from .data_validation_agent.core.persistence import get_dataset_from_duckdb
                    # file_path format: duckdb:ds_id.cleaned
                    dataset_id = file_path.split(":")[1].split(".")[0]
                    df = get_dataset_from_duckdb(dataset_id) 
                except ImportError:
                     return {"error": "core.persistence not found"}
                except Exception as e:
                     return {"error": f"Failed to load from DuckDB: {str(e)}"}
            elif file_path.startswith("sql:"):
                try:
                    from agents.data_validation_agent.core.persistence import get_dataset_from_sql
                    # file_path format: sql:ds_id_cleaned
                    dataset_id = file_path.split(":")[1].replace("_cleaned", "")
                    df = get_dataset_from_sql(dataset_id)
                except Exception as e:
                    return {"error": f"Failed to load from MySQL: {str(e)}"}
            else:
                if not os.path.exists(file_path):
                    if os.path.exists(os.path.join("data", os.path.basename(file_path))):
                        file_path = os.path.join("data", os.path.basename(file_path))
                    else:
                        return {"error": f"File not found: {file_path}"}
                
                # Use on_bad_lines='skip' to handle rows with extra commas
                try:
                    df = pd.read_csv(file_path, on_bad_lines='skip')
                except TypeError:
                    # Fallback for older pandas versions
                    df = pd.read_csv(file_path, error_bad_lines=False)
            
            if df is None:
                 return {"error": "Failed to load dataframe"}

            profile = {}
            for col in df.columns:
                dtype = str(df[col].dtype)
                col_profile = {"type": dtype}
                if "int" in dtype or "float" in dtype:
                    col_profile.update({
                        "min": float(df[col].min()),
                        "max": float(df[col].max()),
                        "mean": float(df[col].mean()),
                        "sum": float(df[col].sum()),
                        "std": float(df[col].std()) if pd.notna(df[col].std()) else 0.0
                    })
                elif "object" in dtype:
                    col_profile.update({
                        "unique_count": int(df[col].nunique()),
                        "top_values": df[col].value_counts().head(5).to_dict()
                    })
                profile[col] = col_profile
            
            return profile, df
        except Exception as e:
            return {"error": str(e)}, None

    def _detect_anomalies(self, df: pd.DataFrame) -> List[Dict]:
        """
        Detects anomalies using Z-score (> 3.0) for numeric columns.
        """
        anomalies = []
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols:
            mean = df[col].mean()
            std = df[col].std()
            if std == 0: continue
            
            z_scores = (df[col] - mean) / std
            outliers = df[np.abs(z_scores) > 2.0]
            
            for idx, row in outliers.iterrows():
                if len(anomalies) > 5: break # Limit number of anomalies
                anomalies.append({
                    "row_index": idx,
                    "column": col,
                    "value": float(row[col]),
                    "z_score": float(z_scores[idx])
                })
        return anomalies

    def _detect_correlations(self, df: pd.DataFrame) -> List[Dict]:
        """
        Calculates correlation matrix for numeric columns using Pearson correlation.
        Returns top 5 strong correlations (positive or negative).
        """
        correlations = []
        numeric_df = df.select_dtypes(include=[np.number])
        if numeric_df.empty or len(numeric_df.columns) < 2:
            return correlations
            
        corr_matrix = numeric_df.corr(method='pearson')
        
        # Iterate and find strong correlations (|r| > 0.7)
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                col1 = corr_matrix.columns[i]
                col2 = corr_matrix.columns[j]
                r = corr_matrix.iloc[i, j]
                
                if abs(r) > 0.7:  # Strong correlation threshold
                    correlations.append({
                        "col1": col1,
                        "col2": col2,
                        "correlation": round(r, 2),
                        "strength": "High" if abs(r) > 0.9 else "Medium"
                    })
        
        # Sort by absolute correlation strength (descending)
        correlations.sort(key=lambda x: abs(x["correlation"]), reverse=True)
        return correlations[:5]

    def _analyze_distributions(self, df: pd.DataFrame) -> List[Dict]:
        """
        Calculates simple histograms/distributions for key numeric and categorical columns.
        """
        distributions = []
        # 1. Numeric Distributions (Histograms)
        numeric_cols = df.select_dtypes(include=[np.number]).columns
        for col in numeric_cols[:3]: # Limit to top 3 numeric cols to save token/compute
            try:
                hist, bin_edges = np.histogram(df[col].dropna(), bins=10)
                distributions.append({
                    "column": col,
                    "type": "numeric",
                    "bins": [round(b, 2) for b in bin_edges.tolist()],
                    "counts": hist.tolist()
                })
            except Exception:
                continue

        # 2. Categorical Distributions (Top Values)
        cat_cols = df.select_dtypes(include=['object', 'category']).columns
        for col in cat_cols[:3]:
            try:
                counts = df[col].value_counts().head(10).to_dict()
                distributions.append({
                    "column": col,
                    "type": "categorical",
                    "counts": counts
                })
            except Exception:
                continue
                
        return distributions

    def _generate_forecast(self, df: pd.DataFrame) -> List[Dict]:
        """
        Generates a naive linear forecast for 'sales' if a date column exists.
        """
        forecasts = []
        # Try to find a date column
        date_col = None
        for col in df.columns:
            if 'date' in col.lower():
                date_col = col
                break
        
        if date_col and 'sales' in df.columns:
            try:
                df[date_col] = pd.to_datetime(df[date_col])
                monthly_sales = df.groupby(df[date_col].dt.to_period("M"))['sales'].sum().reset_index()
                monthly_sales['month_num'] = np.arange(len(monthly_sales))
                
                # Simple Linear Regression (Polyfit)
                z = np.polyfit(monthly_sales['month_num'], monthly_sales['sales'], 1)
                p = np.poly1d(z)
                
                # Forecast next 3 months
                next_months = np.arange(len(monthly_sales), len(monthly_sales) + 3)
                forecast_values = p(next_months).tolist()
                
                forecasts.append({
                    "series": "Sales Forecast",
                    "forecast_values": forecast_values,
                    "period": "Next 3 Months"
                })
            except Exception as e:
                print(f"Forecast Error: {e}")
                
        return forecasts

    def _analyze_risk(self, df: pd.DataFrame) -> Dict:
        """
        Analyzes Order Health based on 'status' column.
        """
        risk_analysis = None
        if 'status' in df.columns:
            status_counts = df['status'].value_counts(normalize=True)
            bad_statuses = ['Disputed', 'Cancelled', 'On Hold']
            risk_score = 0.0
            reasons = []
            
            for status in bad_statuses:
                if status in status_counts:
                    risk_score += status_counts[status] * 100
                    reasons.append(f"{status}: {status_counts[status]:.1%}")
            
            risk_level = "Low"
            if risk_score > 5: risk_level = "Medium"
            if risk_score > 10: risk_level = "High"
            
            if risk_score > 0:
                risk_analysis = {
                    "risk_score": risk_score,
                    "risk_level": risk_level,
                    "reason": ", ".join(reasons)
                }
                
        return risk_analysis

    def run(self, input_data: AnalyticsInput) -> AnalyticsOutput:
        """
        Runs the analytics agent logic.
        """
        generated_profile = {}
        df = None
        
        insights = {
            "anomalies": [],
            "forecasts": [],
            "risk_analysis": None,
            "correlations": [],
            "distributions": []
        }

        if input_data.file_path:
            generated_profile, df = self._analyze_csv(input_data.file_path)
            
            if df is not None:
                print(f"DEBUG: Loaded DF with shape {df.shape}")
                insights["anomalies"] = self._detect_anomalies(df)
                insights["forecasts"] = self._generate_forecast(df)
                insights["anomalies"] = self._detect_anomalies(df)
                insights["forecasts"] = self._generate_forecast(df)
                insights["risk_analysis"] = self._analyze_risk(df)
                insights["correlations"] = self._detect_correlations(df)
                insights["distributions"] = self._analyze_distributions(df)
                print(f"DEBUG: Generated Insights: {json.dumps(insights, indent=2, default=str)}")
        
        final_profiles = generated_profile if "error" not in generated_profile else input_data.column_profiles
        
        # DEBUG PRINT
        if "error" in generated_profile:
            print(f"DEBUG: Analysis Error: {generated_profile['error']}")
            
        column_profiles_str = json.dumps(final_profiles, indent=2, default=str)
        insights_str = json.dumps(insights, indent=2, default=str)
        
        response = self.chain.invoke({
            "dataset_id": input_data.dataset_id,
            "business_context": input_data.business_context or "General Analysis",
            "column_profiles": column_profiles_str,
            "insights": insights_str,
            "format_instructions": parser.get_format_instructions()
        })
        

        
        # --- POST-PROCESSING: Calculate Real Data for Aggregates ---
        if df is not None:
             for key, agg_item in response.aggregates.items():
                try:
                    # Heuristic: If recommendation is "distribution" or "histogram", use distribution data
                    if agg_item.recommended_chart in ["histogram", "bar_chart"] and agg_item.table_ref:
                         # Try to find if table_ref matches a column distribution
                         matching_dist = next((d for d in insights["distributions"] if d["column"] == agg_item.table_ref), None)
                         if matching_dist:
                             agg_item.data = [{"label": str(k), "value": v} for k, v in matching_dist["counts"].items()] if matching_dist["type"] == "categorical" else [{"bin": str(b), "count": c} for b, c in zip(matching_dist["bins"], matching_dist["counts"])]
                             
                    # Heuristic: If recommendation is "heatmap" or "scatter", use correlation data
                    elif agg_item.recommended_chart in ["heatmap", "scatter_plot"]:
                         agg_item.data = insights["correlations"]
                    
                    # Default: Basic Group By if SQL-like logic (Simplified)
                    # For now, we trust the LLM to select charts that we pre-calculated data for (Distributions/Correlations)
                    # OR we implement a simple grouper based on description if possible.
                    
                except Exception as e:
                    print(f"Error populating aggregate data for {key}: {e}")

        return response

# Singleton instance
analytics_agent = AnalyticsAgent()
