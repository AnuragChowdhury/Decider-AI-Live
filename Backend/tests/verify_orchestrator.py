import sys
import os
import asyncio
from pathlib import Path
import json

# Add Backend to sys.path
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from agents.orchestrator import orchestrator_graph
except ImportError as e:
    print(f"Error importing orchestrator: {e}")
    sys.exit(1)

async def main():
    # Read from local actual file
    file_path = Path("data/sales_data_sample.csv")
    if not file_path.exists():
        print(f"File not found: {file_path}")
        return

    with open(file_path, "rb") as f:
        csv_content = f.read()
    
    inputs = {
        "file_bytes": csv_content,
        "filename": file_path.name,
        "user_query": "What is the total sales and what are the top 3 countries by sales?",
        "validation_mode": "lenient",
        "persist": True,
        # Initialize others with empty defaults
        "validation_report": {},
        "analytics_output": {},
        "context": {},
        "question": "",
        "response": ""
    }
    
    print("\n--- Invoking Orchestrator ---")
    
    try:
        result = await orchestrator_graph.ainvoke(inputs)
        
        print("\n--- Orchestration Complete ---")
        
        # Validation Check
        val_report = result.get("validation_report", {})
        print(f"Validation Status: {val_report.get('status')}")
        print(f"Dataset ID: {val_report.get('dataset_id')}")
        
        # Analytics Check
        anal_output = result.get("analytics_output")
        if anal_output:
            print("\n[Analytics Output]")
            print(f"KPIs: {len(anal_output.get('kpis', []))}")
            # print(json.dumps(anal_output, indent=2, default=str))
        else:
            print("\n[Analytics Output] None")
            
        # Chat Check
        chat_response = result.get("response")
        print("\n[Chat Response]")
        print(chat_response)
        
    except Exception as e:
        print(f"Execution failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    if sys.platform.startswith("win"):
        asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    asyncio.run(main())
