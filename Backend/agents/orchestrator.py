"""
orchestrator.py
---------------
Main entry point for the Multi-Agent System.
Orchestrates Data Validation -> Analytics -> Chat using LangGraph.
"""

from typing import TypedDict, Optional, Dict, Any, List, Union
from langgraph.graph import StateGraph, START, END

# Import Agents & Tools
from agents.data_validation_agent.validate_agent import run_validation_pipeline
from agents.analytics_agent import analytics_agent
from agents.chat_agent import chat_node
from core.schemas import AnalyticsInput

# Define State
class OrchestratorState(TypedDict):
    # --- Inputs ---
    file_bytes: bytes
    filename: str
    user_query: str
    validation_mode: str
    persist: bool
    
    # --- Intermediate Outputs ---
    validation_report: Dict[str, Any]
    analytics_output: Dict[str, Any] # Dictionary representation of AnalyticsOutput
    
    # --- Chat State (Matches ChatState) ---
    context: Dict[str, Any]
    question: str
    response: str


# --- Nodes ---

async def validation_node(state: OrchestratorState):
    """
    Runs the Data Validation Agent pipeline.
    """
    print("--- [Orchestrator] Running Validation Node ---")
    report = await run_validation_pipeline(
        file_bytes=state['file_bytes'],
        filename=state['filename'],
        persist=state.get('persist', True),
        validation_mode=state.get('validation_mode', 'lenient')
    )
    return {"validation_report": report}


def analytics_node(state: OrchestratorState):
    """
    Runs the Analytics Agent using validated data.
    """
    print("--- [Orchestrator] Running Analytics Node ---")
    report = state['validation_report']
    
    if report.get('status') == 'ERROR':
        print(f"--- [Orchestrator] Validation Failed: {report.get('summary')} ---")
        return {"analytics_output": None}
    
    # Validation saves data to DuckDB and returns a reference "duckdb:ds_id.cleaned"
    clean_ref = report.get('clean_data_ref')
    
    if not clean_ref:
        print("--- [Orchestrator] No clean data ref found. ---")
        return {"analytics_output": None}
    
    input_data = AnalyticsInput(
        dataset_id=report.get('dataset_id', 'unknown'),
        column_profiles=report.get('column_profile', {}),
        file_path=clean_ref, # AnalyticsAgent now supports "duckdb:..." via shared persistence
        business_context=state.get('user_query', '')
    )
    
    # Run Analytics Agent
    # Run Analytics Agent
    try:
        output = analytics_agent.run(input_data)
        # Convert Pydantic model to dict for state
        return {"analytics_output": output.model_dump()}
    except Exception as e:
        print(f"❌ ANALYTICS NODE CRASHED: {e}")
        import traceback
        traceback.print_exc()
        raise e


def context_builder_node(state: OrchestratorState):
    """
    Assembles the context for the Chat Agent.
    Combines Validation Report + Analytics Insights.
    """
    print("--- [Orchestrator] Building Chat Context ---")
    val = state['validation_report']
    anal = state.get('analytics_output')
    
    if not anal:
        # Fallback if analytics failed or was skipped
        context = {
             "dataset_id": val.get('dataset_id'),
             "limitations": "Analytics could not be performed.",
             "validation_summary": val.get('summary')
        }
    else:
        context = {
            "dataset_id": val.get('dataset_id'),
            "summary": val.get('summary'),
            "issues": val.get('issues'),
            "schema": val.get('schema'),
            "column_profile": val.get('column_profile'),
            # Analytics data
            "kpis": anal.get('kpis', []),
            "aggregates": anal.get('aggregates', {}),
            "forecasts": anal.get('forecasts', []),
            "anomalies": anal.get('anomalies', []),
            "risk_analysis": anal.get('risk_analysis'),
            "recommendations": anal.get('recommendations', []),
        }
    
    # Ensure question is in state for chat_node
    return {"context": context, "question": state['user_query']}


# --- Workflow ---

workflow = StateGraph(OrchestratorState)

workflow.add_node("validation", validation_node)
workflow.add_node("analytics", analytics_node)
workflow.add_node("context_builder", context_builder_node)
workflow.add_node("chat", chat_node) # Using chat_node from agents.chat_agent

# Define Edges
workflow.add_edge(START, "validation")
workflow.add_edge("validation", "analytics")
workflow.add_edge("analytics", "context_builder")
workflow.add_edge("context_builder", "chat")
workflow.add_edge("chat", END)

# Compile
orchestrator_graph = workflow.compile()
