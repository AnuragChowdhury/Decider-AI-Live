from core.schemas import AnalyticsInput, AnalyticsOutput, KPI, AggregateItem, ForecastItem, AnomalyItem, RiskAnalysis, RFMSegment, BasketRule
from itertools import combinations, chain
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from typing import Dict, Any, List
import pandas as pd
import numpy as np
import json
import os
import io

import duckdb

# Initialize LLM
llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0)

# Parser
parser = PydanticOutputParser(pydantic_object=AnalyticsOutput)

# Prompt
system_template = """You are an expert Data Analytics Agent. Your job is to analyze a dataset and return a structured JSON response.

Input Context:
- Dataset ID: {dataset_id}
- Business Context: {business_context}
- Column Summary: {column_profiles}
- Column Roles Found: {column_mapping}
- Automated Insights: {insights}

Instructions:
1. Define 3-4 significant KPIs. Each must have: "id" (snake_case string), "label" (human string), "value" (NUMBER, not string), and "sql" (a SQL query against table called 'dataset').
2. Define 3-5 visual Aggregates as a dict. Keys are snake_case names. Each must have: "table_ref" (SQL query), "description", and "recommended_chart" (one of: bar_chart, pie_chart, line_chart).
3. Include "recommendations" as a list of 2-3 actionable strings.
4. If the dataset is too small (< 5 rows), generate KPIs with value=0 and aggregates with empty data.
5. CRITICAL: Return ONLY a single valid JSON object, no markdown, no explanation, no extra text.

Output EXACTLY this JSON structure (fill in real values):
{{
  "dataset_id": "{dataset_id}",
  "kpis": [
    {{"id": "total_revenue", "label": "Total Revenue", "value": 123456.78, "sql": "SELECT SUM(amount) FROM dataset"}},
    {{"id": "total_orders", "label": "Total Orders", "value": 500, "sql": "SELECT COUNT(*) FROM dataset"}}
  ],
  "aggregates": {{
    "revenue_by_category": {{
      "table_ref": "SELECT category, SUM(amount) as total FROM dataset GROUP BY category",
      "description": "Revenue breakdown by product category",
      "recommended_chart": "bar_chart",
      "data": null
    }}
  }},
  "recommendations": ["Focus on top categories", "Investigate anomalies in Q3"]
}}
"""

prompt = ChatPromptTemplate.from_template(system_template)

class AnalyticsAgent:
    def __init__(self):
        self.chain = prompt | llm  # We parse manually now

    def _extract_json(self, text: str) -> Dict[str, Any]:
        """
        Robustly extract JSON from text, handling markdown blocks and extra text.
        """
        import re
        try:
            # Try to find JSON block in ```json ... ``` or just { ... }
            json_match = re.search(r'\{.*\}', text, re.DOTALL)
            if json_match:
                clean_json = json_match.group(0)
                # Remove common LLM artifacts or half-baked comments that break json.loads
                clean_json = re.sub(r'//.*', '', clean_json) # Remove line comments
                # Handle cases where LLM might put extra commas at the end of lists
                clean_json = re.sub(r',\s*\}', '}', clean_json)
                clean_json = re.sub(r',\s*\]', ']', clean_json)
                return json.loads(clean_json)
            return {}
        except Exception as e:
            print(f"DEBUG: JSON extraction failed: {e}")
            return {}

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
                    return {"error": "core.persistence not found"}, None
                except Exception as e:
                     return {"error": f"Failed to load from DuckDB: {str(e)}"}, None
            elif file_path.startswith("sql:"):
                try:
                    from agents.data_validation_agent.core.persistence import get_dataset_from_sql
                    # file_path format: sql:ds_id_cleaned
                    dataset_id = file_path.split(":")[1].replace("_cleaned", "")
                    df = get_dataset_from_sql(dataset_id)
                except Exception as e:
                    return {"error": f"Failed to load from MySQL: {str(e)}"}, None

            else:
                if not os.path.exists(file_path):
                    if os.path.exists(os.path.join("data", os.path.basename(file_path))):
                        file_path = os.path.join("data", os.path.basename(file_path))
                    else:
                        return {"error": f"File not found: {file_path}"}, None
                
                # Use on_bad_lines='skip' to handle rows with extra commas
                try:
                    df = pd.read_csv(file_path, on_bad_lines='skip')
                except TypeError:
                    # Fallback for older pandas versions
                    df = pd.read_csv(file_path, error_bad_lines=False)
            
            if df is None:
                    return {"error": "Failed to load dataframe"}, None

            profile = {}
            for col in df.columns:
                dtype = str(df[col].dtype)
                col_profile = {"type": dtype}
                if "int" in dtype or "float" in dtype:
                    try:
                        col_profile.update({
                            "min": float(df[col].min()),
                            "max": float(df[col].max()),
                            "mean": float(df[col].mean()),
                            "sum": float(df[col].sum()),
                            "std": float(df[col].std()) if pd.notna(df[col].std()) else 0.0
                        })
                    except: pass
                elif "object" in dtype:
                    try:
                        col_profile.update({
                            "unique_count": int(df[col].nunique()),
                            "top_values": df[col].value_counts().head(5).to_dict()
                        })
                    except: pass
                profile[col] = col_profile
            
            return profile, df
        except Exception as e:
            return {"error": str(e)}, None

    def _detect_column_roles(self, df: pd.DataFrame, mapping: Dict[str, str] = None) -> Dict[str, str]:
        """
        Unified method to find key columns using keywords + optional LLM mapping.
        """
        def find_col(keywords, exclude=None):
            for kw in keywords:
                for col in df.columns:
                    if col == exclude: continue
                    if kw in col.lower():
                        return col
            return None

        m = mapping or {}
        roles = {
            "date": m.get("date") or find_col(['orderdate','date','time','created','shipped','invoice']),
            "amount": m.get("amount") or find_col(['sales','revenue','amount','total','price','value','gmv']),
            "quantity": m.get("quantity") or find_col(['qty','quantity','ordered','units']),
            "customer_id": m.get("customer_id") or find_col(['customername','customer_id','cust_id','email','client']),
            "order_id": m.get("order_id") or find_col(['ordernumber','order_id','orderid','invoice','purchase_id']),
            "product_id": m.get("product_id") or find_col(['productline','product','item','sku','article','name']),
            "category": m.get("category") or find_col(['category','segment','line','type','dept','class']),
            "country": m.get("country") or find_col(['country','region','territory','city','location']),
            "status": m.get("status") or find_col(['status','state','stage','phase'])
        }
        return {k: v for k, v in roles.items() if v}

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

    def _generate_forecast(self, df: pd.DataFrame, mapping: Dict[str, str]) -> List[Dict]:
        """
        Generates a naive linear forecast if date and amount columns are identified.
        """
        forecasts = []
        date_col = mapping.get("date")
        val_col = mapping.get("amount") # Use 'amount' or 'sales' logic
        
        # Fallback if amount not mapped but sales exists (legacy)
        if not val_col:
             val_col = next((c for c in df.columns if 'sales' in c.lower()), None)

        if date_col and val_col:
            try:
                df[date_col] = pd.to_datetime(df[date_col])
                monthly_sales = df.groupby(df[date_col].dt.to_period("M"))[val_col].sum().reset_index()
                monthly_sales['month_num'] = np.arange(len(monthly_sales))
                
                # Simple Polynomial Regression (Degree 2) to capture curves
                z = np.polyfit(monthly_sales['month_num'], monthly_sales[val_col], 2)
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

    def _analyze_risk(self, df: pd.DataFrame, mapping: Dict[str, str]) -> Dict:
        """
        Analyzes Order Health.
        """
        risk_analysis = None
        
        # Heuristic: Look for "Status" column or use mapping if we had a role for it (we don't currently map status)
        # So we'll iterate to find a likely status column
        status_col = next((c for c in df.columns if c.lower() in ['status', 'order_status', 'state']), None)
        
        if status_col:
            status_counts = df[status_col].value_counts(normalize=True)
            bad_statuses = ['Disputed', 'Cancelled', 'On Hold', 'Returned', 'Refunded']
            risk_score = 0.0
            reasons = []
            
            for status in bad_statuses:
                # Fuzzy match values
                matches = [val for val in status_counts.index if status.lower() in str(val).lower()]
                for match in matches:
                     score = status_counts[match] * 100
                     risk_score += score
                     reasons.append(f"{match}: {status_counts[match]:.1%}")
            
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

    def _infer_column_roles(self, df: pd.DataFrame, profile: Dict) -> Dict[str, str]:
        """
        Uses LLM to identify which columns correspond to business concepts.
        """
        try:
            # Sample data for better context (random sample of 10 rows)
            sample_df = df.sample(min(10, len(df))).astype(str)
            columns = list(df.columns)
            
            # Simple prompt for column mapping
            prompt = f"""
            Identify the column names in the provided dataset that match these roles:
            1. 'date': Transaction date/time.
            2. 'amount': Transaction total value/price.
            3. 'customer_id': Unique customer identifier (email, ID, phone).
            4. 'order_id': Unique order identifier.
            5. 'product_id': Product identifier or name.
            
            Columns: {columns}
            
            Sample Data:
            {sample_df.to_string(index=False)}
            
            Return PRECISELY a JSON object with keys: "date", "amount", "customer_id", "order_id", "product_id".
            If a role cannot be confidently matched, set value to null.
            """
            
            mapping_response = llm.invoke(prompt).content
            mapping = self._extract_json(mapping_response)
            if mapping:
                print(f"DEBUG: Infered Column Mapping: {mapping}")
                return mapping
            return {}
        except Exception as e:
            print(f"Column Inference Error: {e}")
            return {}

    def _perform_rfm_analysis(self, df: pd.DataFrame, mapping: Dict[str, str]) -> List[RFMSegment]:
        """
        Performs basic RFM segmentation.
        """
        date_col = mapping.get("date")
        amt_col = mapping.get("amount")
        cust_col = mapping.get("customer_id")
        
        if not (date_col and amt_col and cust_col):
            print(f"DEBUG [RFM] Skipped — missing one of: date={date_col}, amt={amt_col}, cust={cust_col}")
            return None
            
        try:
            # Prepare data
            rfm_df = df[[date_col, amt_col, cust_col]].copy()
            rfm_df[date_col] = pd.to_datetime(rfm_df[date_col], errors='coerce')
            rfm_df = rfm_df.dropna(subset=[date_col])
            rfm_df[amt_col] = pd.to_numeric(rfm_df[amt_col], errors='coerce').fillna(0)
            
            # Calculate RFM metrics
            now = rfm_df[date_col].max()
            rfm = rfm_df.groupby(cust_col).agg({
                date_col: lambda x: (now - x.max()).days, # Recency
                cust_col: 'count',                        # Frequency
                amt_col: 'sum'                            # Monetary
            }).rename(columns={
                date_col: 'recency',
                cust_col: 'frequency',
                amt_col: 'monetary'
            })
            
            # Simple Scoring (Quantiles) - Safe bounds
            # Handle edge case where all values are same
            try:
                rfm['r_score'] = pd.qcut(rfm['recency'].rank(method='first'), 4, labels=[4, 3, 2, 1])
                rfm['f_score'] = pd.qcut(rfm['frequency'].rank(method='first'), 4, labels=[1, 2, 3, 4])
                rfm['m_score'] = pd.qcut(rfm['monetary'].rank(method='first'), 4, labels=[1, 2, 3, 4])
            except Exception:
                # Fallback if too little variance
                return None

            rfm['rfm_score'] = rfm['r_score'].astype(str) + rfm['f_score'].astype(str)
            
            # Segment Logic
            def segment_customer(row):
                r = int(row['r_score'])
                f = int(row['f_score'])
                
                if r >= 4 and f >= 4: return "Champions"
                if r >= 3 and f >= 3: return "Loyal"
                if r >= 2 and f <= 2: return "At Risk"
                if r <= 1: return "Hibernating"
                return "General"

            rfm['segment'] = rfm.apply(segment_customer, axis=1)
            
            # Aggregate for output
            segments = rfm.groupby('segment').agg({
                'monetary': ['count', 'mean']
            }).reset_index()
            segments.columns = ['segment', 'count', 'avg_monetary']
            
            result = []
            descriptions = {
                "Champions": "Best customers, buy often and recently.",
                "Loyal": "Steady spenders, good retention.",
                "At Risk": "Big spenders who haven't visited lately.",
                "Hibernating": "Lost customers, low value.",
                "General": "Average customers."
            }
            
            for _, row in segments.iterrows():
                result.append(RFMSegment(
                    segment_name=row['segment'],
                    count=int(row['count']),
                    avg_monetary=float(row['avg_monetary']),
                    description=descriptions.get(row['segment'], "")
                ))
            
            return result
            
        except Exception as e:
            print(f"RFM Analysis Error: {e}")
            return None

    def _perform_basket_analysis(self, df: pd.DataFrame, mapping: Dict[str, str]) -> List[BasketRule]:
        """
        Performs Market Basket Analysis (Co-occurrence scoring).
        Uses LLM mapping first, then falls back to keyword heuristics so the
        analysis still runs even when order_id / product_id aren't explicitly mapped.
        """
        order_col = mapping.get("order_id")
        prod_col = mapping.get("product_id")

        if not (order_col and prod_col):
            print(f"DEBUG [MBA] Skipped — could not identify order/product columns.")
            return None

        print(f"DEBUG [MBA] Running on order_col='{order_col}', prod_col='{prod_col}'")

        try:
            transactions = df[[order_col, prod_col]].dropna().astype(str)

            baskets = transactions.groupby(order_col)[prod_col].apply(list).tolist()
            baskets = [b for b in baskets if len(b) >= 2]

            if len(baskets) < 10:
                print(f"DEBUG [MBA] Too few multi-item transactions ({len(baskets)}), skipping.")
                return None

            pair_counts  = {}
            item_counts  = {}

            for basket in baskets:
                unique_items = list(set(basket))
                for item in unique_items:
                    item_counts[item] = item_counts.get(item, 0) + 1
                for pair in combinations(sorted(unique_items), 2):
                    pair_counts[pair] = pair_counts.get(pair, 0) + 1

            total_baskets = len(baskets)
            rules = []
            sorted_pairs = sorted(pair_counts.items(), key=lambda x: x[1], reverse=True)[:15]

            for (item_A, item_B), support_count in sorted_pairs:
                support_A  = item_counts[item_A]
                confidence = support_count / support_A
                prob_B     = item_counts[item_B] / total_baskets
                lift       = confidence / prob_B if prob_B > 0 else 0.0

                if lift > 1.0:
                    rules.append(BasketRule(
                        antecedents=[item_A],
                        consequents=[item_B],
                        confidence=round(confidence, 2),
                        lift=round(lift, 2),
                    ))

            print(f"DEBUG [MBA] Generated {len(rules)} association rules.")
            return rules or None

        except Exception as e:
            print(f"Basket Analysis Error: {e}")
            return None

    def _compute_aggregates(self, df: pd.DataFrame, mapping: Dict[str, str]) -> Dict[str, AggregateItem]:
        """
        Computes rich, diverse aggregations for dashboard visualization.
        Produces line, area, pie, and bar charts based on data shape.
        """
        aggregates = {}

        date_col    = mapping.get("date")
        amount_col  = mapping.get("amount")
        qty_col     = mapping.get("quantity")
        cat_col     = mapping.get("category")
        country_col = mapping.get("country")
        status_col  = mapping.get("status")

        print(f"DEBUG [Aggregates] Mapping used: {mapping}")

        # 1. Orders Over Time (Monthly)  →  LINE CHART
        if date_col:
            try:
                temp = df.copy()
                temp[date_col] = pd.to_datetime(temp[date_col], errors='coerce')
                temp = temp.dropna(subset=[date_col])
                if len(temp) >= 3:
                    monthly = (temp.groupby(temp[date_col].dt.to_period("M"))
                               .size().reset_index(name='y'))
                    monthly['x'] = monthly[date_col].astype(str)
                    records = monthly[['x', 'y']].to_dict(orient='records')
                    if len(records) >= 2:
                        aggregates['orders_over_time'] = AggregateItem(
                            table_ref=f"SELECT strftime('%Y-%m', {date_col}) as x, COUNT(*) as y FROM dataset GROUP BY x ORDER BY x",
                            description="Order volume trend over time",
                            recommended_chart="line_chart",
                            data=records
                        )
            except Exception as e:
                print(f"Agg Error (Time): {e}")

        # 2. Revenue Over Time (Monthly)  →  AREA CHART
        if date_col and amount_col:
            try:
                temp = df.copy()
                temp[date_col] = pd.to_datetime(temp[date_col], errors='coerce')
                temp = temp.dropna(subset=[date_col])
                monthly = (temp.groupby(temp[date_col].dt.to_period("M"))[amount_col]
                           .sum().reset_index())
                monthly['x'] = monthly[date_col].astype(str)
                records = monthly[['x', amount_col]].rename(columns={amount_col: 'y'}).to_dict(orient='records')
                if len(records) >= 2:
                    aggregates['revenue_over_time'] = AggregateItem(
                        table_ref=f"SELECT strftime('%Y-%m', {date_col}) as x, SUM({amount_col}) as y FROM dataset GROUP BY x ORDER BY x",
                        description=f"Revenue start-to-end change (slope view)",
                        recommended_chart="slope_chart",
                        data=records
                    )
            except Exception as e:
                print(f"Agg Error (Revenue Time): {e}")

        # 3. Sales by Category  →  PIE CHART (if ≤12 categories) else BAR
        if cat_col and amount_col:
            try:
                n_unique = df[cat_col].nunique()
                cat_sales = (df.groupby(cat_col)[amount_col].sum()
                             .reset_index().sort_values(amount_col, ascending=False))
                records = [{"id": str(r[cat_col]), "value": round(float(r[amount_col]), 2)}
                           for _, r in cat_sales.head(9).iterrows()]
                if records:
                    chart = "pie_chart" if n_unique <= 12 else "bar_chart"
                    aggregates['sales_by_category'] = AggregateItem(
                        table_ref=f"SELECT {cat_col} as id, SUM({amount_col}) as value FROM dataset GROUP BY {cat_col} ORDER BY value DESC LIMIT 9",
                        description=f"Revenue breakdown by {cat_col}",
                        recommended_chart=chart,
                        data=records
                    )
            except Exception as e:
                print(f"Agg Error (Category): {e}")

        # 4. Count by Category (when no amount col)  →  PIE CHART
        if cat_col and not amount_col:
            try:
                n_unique = df[cat_col].nunique()
                if n_unique <= 12:
                    counts = (df.groupby(cat_col).size()
                              .reset_index(name='value').sort_values('value', ascending=False))
                    records = [{"id": str(r[cat_col]), "value": int(r['value'])} for _, r in counts.head(9).iterrows()]
                    if records:
                        aggregates['count_by_category'] = AggregateItem(
                            table_ref=f"SELECT {cat_col} as id, COUNT(*) as value FROM dataset GROUP BY {cat_col} ORDER BY value DESC LIMIT 9",
                            description=f"Record count by {cat_col}",
                            recommended_chart="pie_chart",
                            data=records
                        )
            except Exception as e:
                print(f"Agg Error (Category Count): {e}")

        # 5. Revenue by Region / Country  →  BAR CHART
        if country_col and amount_col:
            try:
                geo = (df.groupby(country_col)[amount_col].sum()
                       .reset_index().sort_values(amount_col, ascending=False))
                records = [{"id": str(r[country_col]), "value": round(float(r[amount_col]), 2)}
                           for _, r in geo.head(10).iterrows()]
                if records:
                    aggregates['sales_by_region'] = AggregateItem(
                        table_ref=f"SELECT {country_col} as id, SUM({amount_col}) as value FROM dataset GROUP BY {country_col} ORDER BY value DESC LIMIT 10",
                        description=f"Revenue by {country_col}",
                        recommended_chart="bar_chart",
                        data=records
                    )
            except Exception:
                pass

        # 6. Orders by Status  →  BAR CHART
        if status_col:
            try:
                counts = (df.groupby(status_col).size()
                          .reset_index(name='value').sort_values('value', ascending=False))
                records = [{"id": str(r[status_col]), "value": int(r['value'])} for _, r in counts.iterrows()]
                if records:
                    aggregates['orders_by_status'] = AggregateItem(
                        table_ref=f"SELECT {status_col} as id, COUNT(*) as value FROM dataset GROUP BY {status_col} ORDER BY value DESC",
                        description="Order distribution by status",
                        recommended_chart="bar_chart",
                        data=records
                    )
            except Exception:
                pass

        # 7. Quantity by Category  →  BAR CHART (only if we also have a pie chart for revenue)
        if cat_col and qty_col and 'sales_by_category' in aggregates:
            try:
                qty = (df.groupby(cat_col)[qty_col].sum()
                       .reset_index().sort_values(qty_col, ascending=False))
                records = [{"id": str(r[cat_col]), "value": round(float(r[qty_col]), 2)}
                           for _, r in qty.head(8).iterrows()]
                if records:
                    aggregates['qty_by_category'] = AggregateItem(
                        table_ref=f"SELECT {cat_col} as id, SUM({qty_col}) as value FROM dataset GROUP BY {cat_col} ORDER BY value DESC LIMIT 8",
                        description=f"Units sold by {cat_col}",
                        recommended_chart="bar_chart",
                        data=records
                    )
            except Exception:
                pass

        print(f"DEBUG [Aggregates] Computed {len(aggregates)} aggregates: {list(aggregates.keys())}")
        return aggregates



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
            "rfm_analysis": None,
            "basket_analysis": None,
            "aggregates": {}
        }
        
        mapping = {}

        if input_data.file_path:
            generated_profile, df = self._analyze_csv(input_data.file_path)
            
            if df is not None:
                print(f"DEBUG: Loaded DF with shape {df.shape}")
                
                # 1. Infer Columns via LLM (if possible)
                mapping = self._infer_column_roles(df, generated_profile)
                
                # 2. Refine Columns with keywords
                mapping = self._detect_column_roles(df, mapping)
                print(f"DEBUG: Final Column Mapping: {mapping}")

                # 3. Run Analyses
                insights["anomalies"] = self._detect_anomalies(df)
                insights["forecasts"] = self._generate_forecast(df, mapping)
                insights["risk_analysis"] = self._analyze_risk(df, mapping)
                
                # Automatically generate standard aggregates
                insights["aggregates"] = self._compute_aggregates(df, mapping)
                
                # 4. New E-commerce Analyses
                insights["rfm_analysis"] = self._perform_rfm_analysis(df, mapping)
                insights["basket_analysis"] = self._perform_basket_analysis(df, mapping)

                # SERIALIZATION FIX: Convert Pydantic models to dicts for JSON dump
                if insights["rfm_analysis"]:
                     insights["rfm_analysis"] = [x.model_dump() for x in insights["rfm_analysis"]]
                if insights["basket_analysis"]:
                     insights["basket_analysis"] = [x.model_dump() for x in insights["basket_analysis"]]

        final_profiles = generated_profile if "error" not in generated_profile else input_data.column_profiles
        column_profiles_str = json.dumps(final_profiles, indent=2, default=str)
        insights_str = json.dumps(insights, indent=2, default=str)
        mapping_str = json.dumps(mapping, indent=2)
        
        # Smarter Truncation
        TRUNC_LIMIT = 20000
        if len(column_profiles_str) > TRUNC_LIMIT:
            column_profiles_str = column_profiles_str[:TRUNC_LIMIT] + "... (truncated)"
        if len(insights_str) > TRUNC_LIMIT:
            insights_str = insights_str[:TRUNC_LIMIT] + "... (truncated)"
            
        try:
            # Invoke LLM and get raw text
            raw_output = (prompt | llm).invoke({
                "dataset_id": input_data.dataset_id,
                "business_context": input_data.business_context or "General Sales Analysis",
                "column_profiles": column_profiles_str,
                "column_mapping": mapping_str,
                "insights": insights_str,
            })
            raw_text = raw_output.content

            print(f"DEBUG: [Analytics Agent] RAW LLM RESPONSE:\n{raw_text[:2000]}")

            # Parse JSON from raw text
            clean_data = self._extract_json(raw_text)
            if not clean_data:
                raise ValueError("LLM returned no parseable JSON. Raw output was empty or malformed.")

            # Manually validate against AnalyticsOutput
            response = AnalyticsOutput.model_validate(clean_data)
            
            # --- KPI MERCY INJECTION ---
            # If the LLM didn't suggest enough KPIs, inject the automated ones
            existing_kpi_ids = {k.id for k in response.kpis}
            
            m = mapping or self._detect_column_roles(df)
            if amt_col := m.get("amount"):
                if "total_revenue" not in existing_kpi_ids:
                    response.kpis.append(KPI(id="total_revenue", label="Total Revenue", value=float(df[amt_col].sum()), sql=f"SELECT SUM({amt_col}) FROM dataset"))
                
                if "avg_order_value" not in existing_kpi_ids and "avg_transaction" not in existing_kpi_ids:
                    if ord_col := m.get("order_id"):
                        aov = float(df[amt_col].sum()) / df[ord_col].nunique() if df[ord_col].nunique() > 0 else 0
                        response.kpis.append(KPI(id="avg_order_value", label="Avg Order Value", value=aov, sql=f"SELECT SUM({amt_col})/COUNT(DISTINCT {ord_col}) FROM dataset"))

            if "total_orders" not in existing_kpi_ids and (ord_col := m.get("order_id")):
                response.kpis.append(KPI(id="total_orders", label="Total Orders", value=0.0, sql=f"SELECT COUNT(DISTINCT {ord_col}) FROM dataset"))
                existing_kpi_ids.add("total_orders")
            
            if "total_records" not in existing_kpi_ids and "total_rows" not in existing_kpi_ids:
                response.kpis.append(KPI(id="total_records", label="Total Records", value=float(len(df)), sql="SELECT COUNT(*) FROM dataset"))

        except Exception as e:
            print(f"❌ LLM INVOCATION/PARSING FAILED: {e}")
            auto_aggs = insights.get("aggregates", {})
            auto_kpis = []
            
            if df is not None:
                try:
                    m = mapping or self._detect_column_roles(df)
                    
                    if amt_col := m.get("amount"):
                        rev = float(df[amt_col].sum())
                        auto_kpis.append(KPI(id="total_revenue", label="Total Revenue", value=rev, sql=f"SELECT SUM({amt_col}) FROM dataset"))
                        
                        if ord_col := m.get("order_id"):
                             aov = rev / df[ord_col].nunique() if df[ord_col].nunique() > 0 else 0
                             auto_kpis.append(KPI(id="avg_order_value", label="Avg Order Value", value=float(aov), sql=f"SELECT SUM({amt_col})/COUNT(DISTINCT {ord_col}) FROM dataset"))
                        else:
                             auto_kpis.append(KPI(id="avg_transaction", label="Avg Transaction", value=float(df[amt_col].mean()), sql=f"SELECT AVG({amt_col}) FROM dataset"))

                    if qty_col := m.get("quantity"):
                        auto_kpis.append(KPI(id="total_units", label="Total Units Sold", value=float(df[qty_col].sum()), sql=f"SELECT SUM({qty_col}) FROM dataset"))

                    if ord_col := m.get("order_id"):
                        auto_kpis.append(KPI(id="total_orders", label="Total Orders", value=float(df[ord_col].nunique()), sql=f"SELECT COUNT(DISTINCT {ord_col}) FROM dataset"))
                    
                    auto_kpis.append(KPI(id="total_records", label="Total Records", value=float(len(df)), sql="SELECT COUNT(*) FROM dataset"))

                except Exception as fe:
                    print(f"DEBUG: Fallback KPI generation failed: {fe}")

            if not auto_kpis:
                auto_kpis = [KPI(id="total_records", label="Total Records", value=float(len(df)) if df is not None else 0.0, sql="SELECT COUNT(*) FROM dataset")]

            fallback = AnalyticsOutput(
                dataset_id=input_data.dataset_id,
                kpis=auto_kpis,
                aggregates=auto_aggs,  # ← Keep all computed aggregates!
                recommendations=[
                    "Review your top performing categories and double down on what's working.",
                    "Monitor revenue trends over time to identify seasonality patterns.",
                    "Investigate any orders with high quantities for bulk pricing opportunities."
                ]
            )
            # Still inject anomalies/forecasts if computed
            if insights.get("anomalies"):
                try:
                    fallback.anomalies = [AnomalyItem(**x) for x in insights["anomalies"]]
                except Exception:
                    pass
            if insights.get("rfm_analysis"):
                try:
                    fallback.rfm_analysis = [RFMSegment(**x) for x in insights["rfm_analysis"]]
                except Exception:
                    pass
            if insights.get("basket_analysis"):
                try:
                    fallback.basket_analysis = [BasketRule(**x) for x in insights["basket_analysis"]]
                    print(f"DEBUG [Fallback] Injected {len(fallback.basket_analysis)} basket rules.")
                except Exception:
                    pass
            return fallback

        
        # INJECT AUTOMATED INSIGHTS
        if insights["anomalies"]:
             response.anomalies = [AnomalyItem(**x) for x in insights["anomalies"]]
        if insights["forecasts"]:
             response.forecasts = [ForecastItem(**x) for x in insights["forecasts"]]
        if insights["risk_analysis"]:
             response.risk_analysis = RiskAnalysis(**insights["risk_analysis"])
        
        if insights["rfm_analysis"]:
             response.rfm_analysis = [RFMSegment(**x) for x in insights["rfm_analysis"]]
        
        if insights["basket_analysis"]:
             response.basket_analysis = [BasketRule(**x) for x in insights["basket_analysis"]]

        if insights["aggregates"]:
             response.aggregates.update(insights["aggregates"])

        # --- POST-PROCESSING: Fetch Actual Data using DuckDB ---
        if df is not None:
            try:
                duckdb.register('dataset', df)
                
                for kpi in response.kpis:
                    try:
                        if kpi.sql and "select" in kpi.sql.lower():
                             kpi_val = duckdb.query(kpi.sql).fetchone()[0]
                             if kpi_val is not None:
                                 kpi.value = float(kpi_val)
                    except Exception as e:
                        pass

                for key, agg in response.aggregates.items():
                    if not isinstance(agg, AggregateItem): continue
                    try:
                        df_agg = duckdb.query(agg.table_ref).to_df()
                        agg_data = df_agg.to_dict(orient='records')
                        for row in agg_data:
                           for k, v in row.items():
                               if isinstance(v, (pd.Timestamp, np.datetime64)):
                                   row[k] = str(v)
                               elif isinstance(v, (np.int64, np.int32)):
                                   row[k] = int(v)
                               elif isinstance(v, (np.float64, np.float32)):
                                   row[k] = float(v)
                        agg.data = agg_data
                    except Exception as e:
                        pass
            except Exception as e:
                print(f"DuckDB Processing Error: {e}")
        
        return response

# Singleton instance
analytics_agent = AnalyticsAgent()
