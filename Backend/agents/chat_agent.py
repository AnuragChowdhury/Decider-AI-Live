from langgraph.graph import START, END, StateGraph
from typing import TypedDict, Dict, Any, Optional, List
from langchain_groq import ChatGroq
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.runnables import RunnableConfig
import dotenv
import json
import re
import os
from decimal import Decimal

from agents.prompts.chat_prompt import SYSTEM_PROMPT, HUMAN_PROMPT_TEMPLATE

dotenv.load_dotenv()

# Import tools
from tools.sql_query import query_data, execute_sql_query # Check if execute_sql_query exists as a tool function or if we need to wrap it
from tools.web_search import search_web, search_internet # Same here
from tools.scenario_simulator import simulate_scenario
from agents.prediction_agent import generate_forecast, prediction_agent
from agents.diagnostic_agent import diagnose_change, diagnostic_agent

# -------------------------
# LLM
# -------------------------

llm = ChatGroq(
    model="openai/gpt-oss-120b",
    temperature=0.1
)

# -------------------------
# STATE DEFINITION
# -------------------------

class ChatState(TypedDict):
    context: Dict[str, Any]
    question: str
    decision: Optional[Dict[str, Any]] # "type": "answer" or "tool", "action": ..., "input": ...
    tool_result: Optional[str]
    response: str
    history: Optional[List[Any]] # List of messages

# -------------------------
# PROMPTS
# -------------------------

DECISION_SYSTEM_PROMPT = """You are a business data analyst. Decide whether you need tools to answer the user's question, or if the provided context is sufficient.

CONTEXT is provided in JSON format containing:
- Schema, KPI, Aggregates (pre-computed data)
- Validation summary
- **RFM Analysis** (Customer segments)
- **Basket Analysis** (Product associations)

AVAILABLE TOOLS:
1. execute_sql_query(query: str) - Execute SQL query against the dataset.
   - Use ONLY if the answer is NOT in the pre-computed aggregates/KPIs.
   - Query must SELECT from 'data' table with LIMIT clause.
   - Example: execute_sql_query("SELECT customername, SUM(sales) FROM data GROUP BY customername LIMIT 5")

2. search_internet(query: str) - Search the web for external info (trends, news).
   - Use ONLY for questions about market trends, news, or external comparisons.
   - Example: search_internet("classic cars market turnover 2024")

3. generate_forecast(dataset_id: str, horizon_months: int) - Generate sales forecasts.
   - Use when user asks for "sales forecast", "future predictions", "trends for next year/months".
   - Default horizon_months is 12.
   - Example: generate_forecast(dataset_id="ds_123", horizon_months=12)

4. diagnose_change(metric: str, start_date: str, end_date: str, compare_start: str, compare_end: str, dataset_id: str)
   - Use when user asks "WHY did [metric] drop/increase?" or "Explain the change in [metric]".
   - You MUST infer the start/end dates from the user's question (e.g., "sales dropped in May" -> May 1 to May 31 vs April 1 to April 30).

RESPONSE FORMAT (Strict Text):

Option 1: Direct Answer (No tool needed)
Answer: [Your direct answer based on context]
Additional context: [If any]
Disclaimer: [Standard disclaimer]

Option 2: Tool Call (Tool needed)
Action: [execute_sql_query OR search_internet OR generate_forecast OR diagnose_change]
Action Input: [The tool arguments]

CRITICAL RULES:
- First, check if the "context" JSON answers the question. If yes, use Option 1.
- If query regarding "future" or "forecast" isn't in context, use 'generate_forecast'.
- If internal data is missing, suggest 'search_internet'.
- One tool call MAX.
- Do NOT output "Thought:". Just output the Action or the Answer.
- Do NOT output JSON. Use the text format above.
"""

FINAL_ANSWER_SYSTEM_PROMPT = """You are a business data analyst.
Answer the user's question based on the Tool Result provided.
Format:
- ALWAYS use Markdown.
- **BE CONCISE**: Provide short, direct answers. Do NOT include fluff or long introductions.
- Use Bullet points for lists.
- Use Markdown Tables for structured data.
- **IMPORTANT**: Do NOT output any tool calls. Provide the final textual answer only.
- If the user explicitly asks for "detailed" explanation, then you may elaborate. Otherwise, keep it brief.
Answer: [Direct Answer]
Additional context: [Optional, brief]
"""

# -------------------------
# HELPER FUNCTIONS
# -------------------------

def parse_decision(text: str) -> Dict[str, Any]:
    """Parses whether the LLM wants to perform an action or give an answer."""
    # Look for Action: ...
    action_match = re.search(r'^Action:\s*(.+?)$', text, re.MULTILINE | re.IGNORECASE)
    if action_match:
        action = action_match.group(1).strip()
        
        # Look for Action Input: ...
        input_match = re.search(r'^Action Input:\s*(.+?)$', text, re.MULTILINE | re.IGNORECASE | re.DOTALL)
        action_input = input_match.group(1).strip() if input_match else ""
        
        return {
            "type": "tool",
            "action": action,
            "input": action_input
        }
    
    # Otherwise, treat as final answer
    return {
        "type": "answer",
        "content": text
    }

class DecimalEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, Decimal):
            return float(obj)
        return super(DecimalEncoder, self).default(obj)

def execute_tool_logic(action: str, action_input: str, dataset_id: str) -> str:
    """Executes the mapped tool and returns string result."""
    try:
        if action == "execute_sql_query":
            # Clean input
            query = action_input.strip().strip('"').strip("'")
            # Execute
            result = query_data(query, dataset_id)
            return json.dumps(result, indent=2, cls=DecimalEncoder)
            
        elif action == "search_internet":
            query = action_input.strip().strip('"').strip("'")
            result = search_web(query, max_results=5)
            return json.dumps(result, indent=2, cls=DecimalEncoder)
            
        elif action == "simulate_scenario":
            # Extract args
            target_column = action_input_dict.get("target_column")
            operation = action_input_dict.get("operation")
            value = action_input_dict.get("value")
            filter_condition = action_input_dict.get("filter_condition")
            # dataset_id from context
            result = simulate_scenario(target_column, operation, value, dataset_id, filter_condition)
            return json.dumps(result, indent=2, cls=DecimalEncoder)
            
        else:
            return f"Error: Unknown tool '{action}'"
            
    except Exception as e:
        return f"Error executing tool: {str(e)}"

def _format_context(context: Dict[str, Any]) -> str:
    """
    Formats the context dictionary into a token-efficient string.
    - Removes empty/null fields.
    - Formats 'column_profile' as a table instead of raw JSON.
    - Uses YAML-like format for other fields for density.
    """
    formatted = []
    
    # Prune empty keys
    param_contex = {k: v for k, v in context.items() if v}
    
    # Special handling for column_profile to save tokens
    if "column_profile" in param_contex and isinstance(param_contex["column_profile"], (list, dict)):
        profiles = param_contex.pop("column_profile")
        if profiles:
            formatted.append("Column Profiles:")
            # If it's a list (which seems to be the case in some traces), format as table
            if isinstance(profiles, list):
                 headers = ["Column", "Type", "Stats"]
                 formatted.append(f"| {' | '.join(headers)} |")
                 formatted.append(f"| {' | '.join(['---']*len(headers))} |")
                 for col in profiles[:15]: # Limit to top 15 columns to prevent overflow
                     # Simplify stats
                     stats = ""
                     if "min" in col: stats += f"Min:{col.get('min')}, Max:{col.get('max')} "
                     if "unique_count" in col: stats += f"Unique:{col.get('unique_count')} "
                     formatted.append(f"| {col.get('name', '')} | {col.get('type', '')} | {stats.strip()} |")
                 if len(profiles) > 15:
                     formatted.append(f"... and {len(profiles)-15} more columns")
            elif isinstance(profiles, dict):
                 # Handle dict format if backend sends that
                 for col_name, col_data in list(profiles.items())[:15]:
                     formatted.append(f"- {col_name}: {col_data.get('type')} {str(col_data.get('stats', ''))}")
            formatted.append("")
    
    # Rename 'schema' to 'schema_info' to avoid confusion if needed, or just dump rest
    formatted.append(json.dumps(param_contex, indent=1)) # Use indent=1 for some readability but less space
    
    return "\n".join(formatted)

# -------------------------
# NODES
# -------------------------

def decision_node(state: ChatState):
    """Decides next step: Answer or Tool using bind_tools."""
    print("--- [ChatAgent] Decision Node ---")
    context = state["context"]
    question = state["question"]
    history = state.get("history", [])
    
    # Bind tools to the LLM just for this node
    tools = [execute_sql_query, search_internet, simulate_scenario, generate_forecast, diagnose_change]
    llm_with_tools = llm.bind_tools(tools, tool_choice="auto")
    
    system_msg = SystemMessage(content="""You are a business data analyst. Decide whether you need tools to answer the user's question, or if the provided context is sufficient.

CONTEXT is provided in JSON format containing:
- Schema, KPI, Aggregates (pre-computed data)
- Validation summary
- **RFM Analysis** (Customer segments)
- **Basket Analysis** (Product associations)

CRITICAL RULES:
- First, check if the "context" JSON answers the question. If yes, respond directly with text.
- If you need to query data NOT in context, use the 'execute_sql_query' tool.
- If you need market trends/news, use the 'search_internet' tool.
- If the user asks "What if..." or "Simulate...", use the 'simulate_scenario' tool.
- If the user asks for "Forecast", "Future Sales", or "Prediction", use the 'generate_forecast' tool.
- If the user asks "Why did X change?", use 'diagnose_change'.
- **COMPARISON RULE**: If comparing two periods/entities (e.g. "Compare 2023 vs 2024"), write a SQL query that selects both or uses UNION/CASE to get data side-by-side. Do NOT ask for two separate queries.
- Make ONE tool call maximum.
- **SQL RULE**: ALWAYS use table name 'data' in your FROM clause (e.g. FROM data). Do NOT hallucinate table names like 'orders' or 'users'.
- **FORMAT RULE**: If answering directly, ALWAYS use Markdown format (Tables, Bold, Lists).
""")
    
    formatted_context = _format_context(context)

    user_msg = HumanMessage(
        content=f"""Dataset Context:
{formatted_context}

User Question:
{question}
"""
    )
    
    messages = [system_msg]
    
    # Add history messages if they exist and are in the right format
    # Assuming history is a list of LangChain messages or dicts
    if history:
        # Simple validation/conversion if needed, but assuming compatible objects for now
        # If history is just string logs (as per user snippet), we might need to append to system msg or context
        if isinstance(history, str):
             messages.append(HumanMessage(content=f"Conversation History:\n{history}"))
        elif isinstance(history, list):
             messages.extend(history)

    messages.append(user_msg)
    
    response = llm_with_tools.invoke(messages)
    
    # Check for tool calls
    if response.tool_calls:
        # Take the first tool call
        tool_call = response.tool_calls[0]
        return {
            "decision": {
                "type": "tool",
                "action": tool_call["name"],
                "input": tool_call["args"] # dict
            }
        }
    else:
        # Direct answer
        return {
            "decision": {
                "type": "answer",
                "content": response.content
            }
        }

def tool_execution_node(state: ChatState):
    """Executes the tool if decision was to use one."""
    print("--- [ChatAgent] Tool Execution Node ---")
    decision = state["decision"]
    dataset_id = state["context"].get("dataset_id", "")
    
    action = decision["action"]
    action_input_dict = decision["input"]
    
    try:
        if action == "execute_sql_query":
            # Extract query from args
            query = action_input_dict.get("query")
            result = query_data(query, dataset_id)
            
            # Helper logic: Check if empty
            if result.get("success") and result.get("row_count", 0) == 0:
                 # Append hint
                 result["hint"] = "Query returned 0 rows. If you are looking for external info or trends, try 'search_internet' next."
            
            tool_result = json.dumps(result, indent=2, cls=DecimalEncoder)
            
        elif action == "search_internet":
            query = action_input_dict.get("query")
            result = search_web(query, max_results=5)
            tool_result = json.dumps(result, indent=2, cls=DecimalEncoder)

        elif action == "generate_forecast":
            # Extract args
            ds_id_arg = action_input_dict.get("dataset_id")
            horizon = action_input_dict.get("horizon_months", 12)
            
            # Use context dataset_id if arg is missing
            target_ds = ds_id_arg if ds_id_arg else dataset_id
            
            result = prediction_agent.forecast(target_ds, int(horizon))
            tool_result = str(result) # Result is already JSON string

        elif action == "diagnose_change":
            result = diagnostic_agent.diagnose(
                dataset_id=dataset_id,
                metric=action_input_dict.get("metric"),
                start_date=action_input_dict.get("start_date"),
                end_date=action_input_dict.get("end_date"),
                compare_start=action_input_dict.get("compare_start"),
                compare_end=action_input_dict.get("compare_end")
            )
            tool_result = str(result)

        elif action == "simulate_scenario":
            # Extract args
            target_column = action_input_dict.get("target_column")
            operation = action_input_dict.get("operation")
            value = action_input_dict.get("value")
            filter_condition = action_input_dict.get("filter_condition")
            # dataset_id from context
            result = simulate_scenario(target_column, operation, value, dataset_id, filter_condition)
            tool_result = json.dumps(result, indent=2, cls=DecimalEncoder)
            
        else:
            tool_result = f"Error: Unknown tool '{action}'"
            
    except Exception as e:
        tool_result = f"Error executing tool: {str(e)}"
    
    return {"tool_result": tool_result}

def final_answer_node(state: ChatState):
    """Generates final answer using tool result."""
    print("--- [ChatAgent] Final Answer Node ---")
    question = state["question"]
    tool_result = state["tool_result"]
    decision = state["decision"]
    
    system_msg = SystemMessage(content=FINAL_ANSWER_SYSTEM_PROMPT)
    user_msg = HumanMessage(
        content=f"""Original Question: {question}

Tool ({decision['action']}) executed.
Result:
{tool_result}

Provide any necessary data analysis and the final answer."""
    )
    
    # No tools bound here - strictly text generation
    response = llm.invoke([system_msg, user_msg])
    
    return {"response": response.content}

def direct_answer_node(state: ChatState):
    """Passes through the direct answer from decision node."""
    print("--- [ChatAgent] Direct Answer Node ---")
    decision = state["decision"]
    return {"response": decision["content"]}

# -------------------------
# CONDITIONAL ROUTING
# -------------------------

def route_decision(state: ChatState):
    decision = state["decision"]
    if decision["type"] == "tool":
        return "tool_execution"
    else:
        return "direct_answer"

# -------------------------
# GRAPH CONSTRUCTION
# -------------------------

workflow = StateGraph(ChatState)

workflow.add_node("decision", decision_node)
workflow.add_node("tool_execution", tool_execution_node)
workflow.add_node("final_answer", final_answer_node)
workflow.add_node("direct_answer", direct_answer_node)

workflow.add_edge(START, "decision")
workflow.add_conditional_edges(
    "decision",
    route_decision,
    {
        "tool_execution": "tool_execution",
        "direct_answer": "direct_answer"
    }
)
workflow.add_edge("tool_execution", "final_answer")
workflow.add_edge("final_answer", END)
workflow.add_edge("direct_answer", END)

# Export compiled graph as callable
chat_node_graph = workflow.compile()

# Adapter to match the expected calling signature in orchestration (single func)
def chat_node(state: Dict[str, Any]):
    """
    Adapter function that invokes the compiled graph.
    The orchestrator expects a function that takes 'state' dict and returns dict updates.
    """
    # Simply invoke the graph
    result = chat_node_graph.invoke(state)
    return {"response": result["response"]}
