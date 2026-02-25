from typing import Dict, Any, List
from langchain_groq import ChatGroq
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import PydanticOutputParser
from core.schemas import UIControllerInput, UIControllerOutput, UIComponent
import json
import os

# Initialize LLM with timeout
llm = ChatGroq(model="llama-3.1-8b-instant", temperature=0, request_timeout=30)

# Parser
parser = PydanticOutputParser(pydantic_object=UIControllerOutput)

# Prompt
system_template = """You are an expert UI Controller Agent.
Your goal is to decide the best visualization strategy for a dashboard based on the provided Analytics Data (KPIs, Aggregates) and Advanced Insights (Forecasts, Anomalies, Risk).

Input Context:
- Dataset ID: {dataset_id}
- Available KPIs: {kpis}
- Available Aggregates: {aggregates}
- Advanced Insights: {insights}
- Available Components: {available_components}
- Screen Space: {screen_space}

=== CHART TYPE SELECTION GUIDE (CRITICAL - READ CAREFULLY) ===

CATEGORICAL DATA (data with discrete groups, labels, segments, or categories):
  You have FIVE chart types for categorical data. NEVER use the same type twice in a dashboard:
  1. bar_chart       — standard vertical bar. Use for top-N ranking, counts per category.
  2. horizontal_bar  — horizontal bar. Use when category label names are long, or for sorted rankings.
  3. radar_chart     — spider/radar. Use for multi-dimensional comparisons (e.g. segments with multiple scores), OR when you need to compare 3-8 categories holistically.
  4. pie_chart       — donut/pie. Use ONLY when showing proportional breakdown (%), e.g. market share. Best with 3-7 slices.
  5. radial_bar      — circular/polar bars. Use for status or stage distributions (e.g. order status). Visually striking alternative to bar_chart.

CONTINUOUS / TIME-SERIES DATA (data with numeric X axis, dates, sequential values):
  You have FOUR chart types. NEVER use the same type twice in a dashboard:
  1. line_chart      — classic line. Use for full trends over time, one or more series.
  2. slope_chart     — slope graph. Use to highlight the START-to-END change only (e.g. revenue first vs last period). Best for before/after comparison.
  3. area_chart      — filled area. Use for cumulative trends or volume over time.
  4. scatter_plot    — scatter. Use for correlation/distribution analysis, or when X and Y are BOTH continuous metrics (not dates).

INTELLIGENT ROTATION RULES:
  - If you have 2 or more categorical aggregates, assign DIFFERENT chart types to each.
  - If you have 2 or more time-series aggregates, assign DIFFERENT chart types to each.
  - For time-series: if one shows FULL trend → use line_chart; if another shows START vs END change → use slope_chart.
  - If aggregate data shows a breakdown by % or shares → use pie_chart.
  - If aggregate data compares multiple groups on multiple dimensions → use radar_chart.
  - If aggregate data has status/stage categories → use radial_bar.
  - If aggregate data has two numeric columns → consider scatter_plot.
  - Default only to bar_chart if NONE of the above apply.
  - NEVER use bar_chart for more than ONE aggregate when you have 3+ aggregates.

=== INSTRUCTIONS ===
1. Select appropriate components to visualize the provided data. AIM FOR A DENSE AND HIGH-IMPACT DASHBOARD (at least 6-10 components if data allows).
2. **KPIs (CRITICAL)**: Always include every unique KPI provided in the input. Use the 'kpi' component type for each. Aim for exactly 4-5 KPI cards in the top row if that many are available.
3. For Aggregates, follow the CHART TYPE SELECTION GUIDE above. Use 'data_ref' to point to the keys in Aggregates.
4. **FORECASTS**: Always visualize forecasts using a 'line_chart' with 'col_span' set to 4. Highlight the predicted trend.
5. **ANOMALIES**: Use a 'table' or 'scatter_plot' to highlight outliers. Explain why they are outliers in the description.
6. **SPECIAL ANALYSES (CRITICAL)**:
   - RFM Analysis -> Use 'radar_chart' (multi-segment comparison). Set 'data_ref' to 'rfm_analysis'.
   - Basket Analysis -> Use 'table'. Set 'data_ref' to 'basket_analysis'.
   - Risk Analysis -> Use 'pie_chart'. Set 'data_ref' to 'risk_analysis'.
   - Forecasts -> Use 'line_chart'. Set 'data_ref' to 'forecasts'.
   - Anomalies -> Use 'table'. Set 'data_ref' to 'anomalies'.
7. **LAYOUT DENSITY**:
   - Use 'col_span=1' for standard KPIs.
   - Use 'col_span=2' for standard charts.
   - Use 'col_span=4' for complex time-series, anomaly tables, or wide maps.
8. **DESCRIPTIONS**: Every chart MUST have a 'subtitle' and 'description' that provides business context (e.g., "This trend indicates...").
9. Return the response STRICTLY in the specified JSON format.

{format_instructions}

STRICT RULE: Every component MUST have a valid type, title, and data_ref (unless it's a KPI).
If you have multiple Aggregates or insights, show them all! A blank dashboard is a failure.
CRITICAL: Use a VARIETY of chart types across the dashboard. A dashboard with 4 bar_charts is a FAILURE.
"""

prompt = ChatPromptTemplate.from_template(system_template)

class UIControllerAgent:
    def __init__(self):
        self.chain = prompt | llm | parser

    def run(self, input_data: UIControllerInput) -> UIControllerOutput:
        """
        Runs the UI Controller agent logic.
        """
        print(f"--- [UI Agent] Starting run for dataset: {input_data.dataset_id} ---")
        # Convert Pydantic models to JSON strings for the prompt
        kpis_str = json.dumps([k.model_dump() for k in input_data.kpis], indent=2)
        # Aggregates are now raw dicts/lists, so direct dump
        aggregates_str = json.dumps(input_data.aggregates, indent=2, default=str)
        
        insights = {
            "forecasts": [f.model_dump() for f in input_data.forecasts] if input_data.forecasts else [],
            "anomalies": [a.model_dump() for a in input_data.anomalies] if input_data.anomalies else [],
            "risk_analysis": input_data.risk_analysis.model_dump() if input_data.risk_analysis else None,
            "rfm_analysis": [r.model_dump() for r in input_data.rfm_analysis] if input_data.rfm_analysis else None,
            "basket_analysis": [b.model_dump() for b in input_data.basket_analysis] if input_data.basket_analysis else None
        }

        
        try:
            # Step 1: Just invoke the prompt and LLM to see raw text
            raw_chain = prompt | llm
            raw_text = raw_chain.invoke({
                "dataset_id": input_data.dataset_id,
                "kpis": kpis_str,
                "aggregates": aggregates_str,
                "insights": json.dumps(insights, indent=2),
                "recommendations": json.dumps(input_data.recommendations) if input_data.recommendations else "[]",
                "available_components": input_data.available_components,
                "screen_space": input_data.screen_space,
                "format_instructions": parser.get_format_instructions()
            }).content
            
            print(f"DEBUG: [UI Agent] RAW LLM RESPONSE:\n{raw_text}")
            
            # Step 2: Parse manually
            response = parser.parse(raw_text)
            
        except Exception as e:
            print(f"❌ [UI Agent] INVOCATION/PARSING FAILED: {type(e).__name__}")
            if hasattr(e, 'errors'):
                 print(f"Validation Errors: {json.dumps(e.errors(), indent=2, default=str)}")
            else:
                 print(f"Error Detail: {e}")
            
            from core.schemas import SessionContext
            # Ensure the fallback is BULLETPROOF
            fallback_components = []
            safe_kpis = input_data.kpis or []
            
            # Check if there is an error KPI from analytics_agent
            anal_error = next((k for k in safe_kpis if k.id == "error"), None)
            
            if anal_error:
                fallback_components.append(UIComponent(
                    id="err_manual",
                    type="kpi",
                    title="Deep Analysis Issue",
                    col_span=4,
                    data={"value": "Limited", "label": "Analysis Status"},
                    description="The AI encountered a data structure it couldn't fully map. Basic metrics are shown below. Try asking the Assistant for a summary."
                ))

            for i, k in enumerate(safe_kpis[:4]):
                if k.id == "error": continue
                fallback_components.append(UIComponent(
                    id=f"fallback_kpi_{i}",
                    type="kpi",
                    title=getattr(k, 'label', 'Metric'),
                    col_span=1,
                    data={"value": getattr(k, 'value', 0), "label": getattr(k, 'label', 'Metric')}
                ))
            
            # If still no components, add one manual one
            if not fallback_components:
                fallback_components.append(UIComponent(
                    id="err_manual",
                    type="kpi",
                    title="System Status",
                    col_span=4,
                    data={"value": "Minimal Data", "label": "Insights"},
                    description="No significant patterns were identified automatically. Please use the AI Assistant for custom interrogation."
                ))

            fallback_output = UIControllerOutput(
                dashboard_id=f"fallback_{input_data.dataset_id}",
                components=fallback_components,
                session_context=SessionContext(kpi_list=[getattr(k, 'label', 'Error') for k in safe_kpis if k.id != "error"]),
                recommendations=["The UI Agent generated a simplified dashboard due to processing limitations."]
            )
            return fallback_output
        
        # DEBUG LOGGING (Requested by User)
        print("------------- UI AGENT OUTPUT -------------")
        print(response.model_dump_json(indent=2))
        print("-------------------------------------------")

        if not response.recommendations and input_data.recommendations:
            response.recommendations = input_data.recommendations

        return response

# Singleton instance
ui_agent = UIControllerAgent()
