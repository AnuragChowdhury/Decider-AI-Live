import pandas as pd
import numpy as np
from tools.sql_query import query_data
from typing import List, Dict, Any, Optional
from langchain_core.tools import tool
import json
import re
from tools.web_search import search_web

class DiagnosticAgent:
    """
    Agent responsible for diagnosing 'Why' a metric changed.
    """
    
    def _detect_columns(self, dataset_id: str) -> tuple[Optional[str], List[str]]:
        """
        Detects date column and potential dimensions (categorical columns).
        """
        res = query_data("SELECT * FROM data LIMIT 1", dataset_id)
        
        if not res['success'] or not res['columns']:
            return None, []
        
        columns = res['columns']
        
        # Date detection
        date_col = next((c for c in columns if 'date' in c.lower() or 'time' in c.lower()), None)
        
        # Dimension detection (exclude numerics, dates, ids)
        # Since we don't have types in 'columns' list from query_data (it's just names), 
        # we'll use a heuristic or try to fetch types? 
        # Heuristic based on common names is safer for now without extra queries.
        
        excluded_keywords = ['date', 'time', 'id', 'amount', 'sales', 'revenue', 'price', 'quantity', 'cost', 'total', 'profit']
        
        dimensions = []
        for col in columns:
            col_lower = col.lower()
            if not any(k in col_lower for k in excluded_keywords):
                # Also check if it looks like a dimension?
                dimensions.append(col)
                
        # If list is too long, limit to most likely ones
        priority_keywords = ['region', 'country', 'city', 'state', 'category', 'segment', 'gender', 'source', 'channel', 'status']
        priority_dims = [d for d in dimensions if any(k in d.lower() for k in priority_keywords)]
        
        return date_col, (priority_dims if priority_dims else dimensions[:5])

    def _infer_industry_context(self, dataset_id: str) -> str:
        """
        Infers the industry/context from the most popular products/categories.
        """
        # Try to find a product or category column
        res = query_data("SELECT * FROM data LIMIT 1", dataset_id, bypass_validation=True)
        if not res['success']: return ""
        cols = [c.lower() for c in res['columns']]
        
        target_col = next((c for c in res['columns'] if 'product' in c.lower() or 'category' in c.lower()), None)
        
        if target_col:
            q = f"SELECT {target_col}, COUNT(*) as cnt FROM data GROUP BY {target_col} ORDER BY cnt DESC LIMIT 3"
            r = query_data(q, dataset_id, bypass_validation=True)
            if r['success'] and r['data']:
                top_items = [row[target_col] for row in r['data']]
                return f", specifically regarding '{', '.join(str(x) for x in top_items)}'"
        return ""

    def diagnose(self, dataset_id: str, metric: str, start_date: str, end_date: str, compare_start: str, compare_end: str) -> str:
        """
        Diagnoses changes in a metric between two periods.
        """
        date_col, dimensions = self._detect_columns(dataset_id)
        
        if not date_col:
            return json.dumps({"error": "Could not detect Date column for analysis."})
        
        if not dimensions:
            return json.dumps({"error": "Could not detect any Dimensions (categorical columns) to drill down into."})

        # 1. Global Change
        # Use simple aggregation
        def get_total(s, e):
            q = f"SELECT SUM({metric}) as val FROM data WHERE {date_col} >= '{s}' AND {date_col} <= '{e}'"
            r = query_data(q, dataset_id, bypass_validation=True)
            if r['success'] and r['data'] and r['data'][0]['val'] is not None:
                return float(r['data'][0]['val'])
            return 0.0

        current_val = get_total(start_date, end_date)
        prev_val = get_total(compare_start, compare_end)
        
        if prev_val == 0:
             return json.dumps({
                 "analysis": f"Previous period ({compare_start} to {compare_end}) has 0 value. Cannot calculate change.",
                 "current_value": current_val
             })

        delta = current_val - prev_val
        pct_change = (delta / prev_val) * 100
        
        direction = "dropped" if delta < 0 else "increased"
        
        # 2. Drill Down
        drivers = []
        
        for dim in dimensions:
            # Group by dim for both periods
            # We can do this in one query efficiently? 
            # SELECT dim, 
            #   SUM(CASE WHEN date BETWEEN s1 AND e1 THEN metric ELSE 0 END) as curr,
            #   SUM(CASE WHEN date BETWEEN s2 AND e2 THEN metric ELSE 0 END) as prev
            # FROM data GROUP BY dim
            
            query = f"""
            SELECT {dim},
                SUM(CASE WHEN {date_col} >= '{start_date}' AND {date_col} <= '{end_date}' THEN {metric} ELSE 0 END) as curr_val,
                SUM(CASE WHEN {date_col} >= '{compare_start}' AND {date_col} <= '{compare_end}' THEN {metric} ELSE 0 END) as prev_val
            FROM data
            GROUP BY {dim}
            HAVING prev_val > 0 OR curr_val > 0
            ORDER BY ABS(curr_val - prev_val) DESC
            LIMIT 3
            """
            
            res = query_data(query, dataset_id, bypass_validation=True)
            if res['success'] and res['data']:
                top_driver = res['data'][0]
                d_curr = float(top_driver['curr_val'] or 0)
                d_prev = float(top_driver['prev_val'] or 0)
                d_delta = d_curr - d_prev
                d_name = top_driver[dim]
                
                # Contribution to total delta
                # If total delta is -100, and this dim delta is -50, it explains 50%
                if abs(delta) > 0:
                    contribution = abs(d_delta / delta) * 100
                else:
                    contribution = 0
                
                # Insight logic
                # Only report if this dimension's top mover explains a significant part (>20%) of the move
                # AND moves in the same direction usually (or opposes strongly)
                
                drivers.append({
                    "dimension": dim,
                    "segment": d_name,
                    "delta": d_delta,
                    "contribution_pct": contribution,
                    "current": d_curr,
                    "previous": d_prev
                })

        # Sort drivers by contribution
        drivers.sort(key=lambda x: x['contribution_pct'], reverse=True)
        
        top_drivers = drivers[:3]
        
        # Formulate HTML/Markdown response
        summary = f"**Global Change**: {metric} {direction} by {abs(pct_change):.1f}% ({prev_val:,.0f} -> {current_val:,.0f}).\n\n"
        summary += "**Key Drivers:**\n"
        
        if not top_drivers:
            summary += "No specific single segment dominated the change. It appears to be a broad trend."
        else:
            for d in top_drivers:
                impact_dir = "dropped" if d['delta'] < 0 else "grew"
                summary += f"- **{d['dimension']}**: '{d['segment']}' {impact_dir} by {abs(d['delta']):,.0f} (from {d['previous']:,.0f} to {d['current']:,.0f}), explaining {d['contribution_pct']:.0f}% of the total change.\n"
        
        # 3. External Market Context (New)
        # Trigger if significant drop (> 10%)
        if pct_change < -10:
            industry_context = self._infer_industry_context(dataset_id)
            year_match = re.search(r'\d{4}', start_date)
            year = year_match.group(0) if year_match else ""
            
            search_query = f"market trends sales decline {year} {industry_context}"
            search_res = search_web(search_query, max_results=3)
            
            if search_res['success'] and search_res['summary']:
                summary += "\n**External Market Context:**\n"
                summary += f"Searching for trends in {year}{industry_context}...\n"
                summary += f"Found: {search_res['summary']}\n"
                summary += "*(These external factors might correlate with your internal data drop.)*"
                
        return json.dumps({
            "analysis": summary,
            "details": top_drivers
        })

# Singleton
diagnostic_agent = DiagnosticAgent()

@tool
def diagnose_change(metric: str, start_date: str, end_date: str, compare_start: str, compare_end: str, dataset_id: str = "") -> str:
    """
    Diagnoses WHY a metric changed between two periods by drilling down into data dimensions.
    Use this when user asks "Why did [metric] drop/increase...?"
    
    Args:
        metric: The column name of the metric (e.g., 'sales', 'profit').
        start_date: Start date of the main period (YYYY-MM-DD).
        end_date: End date of the main period (YYYY-MM-DD).
        compare_start: Start date of the comparison period (YYYY-MM-DD).
        compare_end: End date of the comparison period (YYYY-MM-DD).
        dataset_id: Dataset ID context.
    """
    if not dataset_id:
        return json.dumps({"error": "dataset_id is required."})
        
    return diagnostic_agent.diagnose(dataset_id, metric, start_date, end_date, compare_start, compare_end)
