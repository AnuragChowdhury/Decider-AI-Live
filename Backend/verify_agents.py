import os
import json
from dotenv import load_dotenv
from agents.analytics_agent import analytics_agent
from agents.ui_agent import ui_agent
from core.schemas import AnalyticsInput, UIControllerInput

# Load env vars (ensure OPENAI_API_KEY is set)
load_dotenv()

def verify_workflows():
    print("--- Verifying Analytics Agent ---")
    
    # 1. Mock Input for Analytics Agent (using actual file now)
    analytics_input = AnalyticsInput(
        dataset_id="ds_001",
        column_profiles={}, # Empty profiles, letting the agent read the file
        file_path="data/sales_data.csv",
        business_context="retail_sales"
    )
    
    try:
        analytics_output = analytics_agent.run(analytics_input)
        print("✅ Analytics Agent Output:")
        print(analytics_output.model_dump_json(indent=2))
    except Exception as e:
        print(f"❌ Analytics Agent Failed: {e}")
        return

    print("\n--- Verifying UI Controller Agent ---")
    
    # 2. Use Analytics Output as Input for UI Agent
    ui_input = UIControllerInput(
        dataset_id=analytics_output.dataset_id,
        kpis=analytics_output.kpis,
        aggregates=analytics_output.aggregates,
        forecasts=analytics_output.forecasts,
        anomalies=analytics_output.anomalies,
        risk_analysis=analytics_output.risk_analysis,
        available_components=["kpi", "bar_chart", "line_chart", "table"],
        screen_space="dashboard_wide"
    )
    
    try:
        ui_output = ui_agent.run(ui_input)
        print("✅ UI Controller Agent Output:")
        print(ui_output.model_dump_json(indent=2))
        print("✅ Strategic Recommendations:")
        print(ui_output.recommendations)
    except Exception as e:
        print(f"❌ UI Controller Agent Failed: {e}")

if __name__ == "__main__":
    # Ensure you have GROQ_API_KEY set in your environment or .env file
    if not os.getenv("GROQ_API_KEY"):
        print("⚠️ Warning: GROQ_API_KEY not found in environment. Simulation might fail.")
    
    verify_workflows()
