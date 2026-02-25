from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.concurrency import run_in_threadpool
from typing import List, Optional
from sqlalchemy.orm import Session
import uuid
import os
import shutil
import json
from datetime import datetime

from core import database, models, auth, schemas
# We'll need schemas for request bodies. Let's define transient ones here or in core/schemas.py
from pydantic import BaseModel
from langchain_core.messages import HumanMessage, AIMessage
import sys

router = APIRouter(prefix="/api", tags=["Session & Chat"])

# --- Schemas ---
class ChatRequest(BaseModel):
    session_id: int
    query: str

class SessionResponse(BaseModel):
    session_id: int
    dataset_id: str
    title: str
    created_at: datetime

class MessageResponse(BaseModel):
    role: str
    content: str
    timestamp: datetime

# --- Background Task ---

async def run_async_analysis(session_id: int, filename: str):
    """
    Background worker: reads file bytes from DB, runs Validation + Analytics, updates result.
    """
    db_gen = database.get_db()
    db: Session = next(db_gen)

    try:
        print(f"DEBUG: [Async] Starting Pipeline for session {session_id}")

        # ----- Read file bytes from DB (no disk access) -----
        session_row = db.query(models.Session).filter(models.Session.id == session_id).first()
        if not session_row or not session_row.file_content:
            raise RuntimeError(f"No file_content found in DB for session {session_id}")
        file_bytes = session_row.file_content

        # Import orchestrator nodes
        from agents.orchestrator import validation_node, analytics_node

        # Create minimal state for validation + analytics
        state = {
            "file_bytes": file_bytes,
            "filename": filename,
            "user_query": "",
            "validation_mode": "lenient",
            "persist": True,
            "validation_report": {},
            "analytics_output": {},
            "context": {},
            "question": "",
            "response": ""
        }

        # 1. Run Validation (Async)
        print(f"DEBUG: [Async] Running Validation Node for {session_id}")
        val_result = await validation_node(state)
        state.update(val_result)

        # 2. Run Analytics (Sync, wrapped to avoid blocking event loop)
        print(f"DEBUG: [Async] Running Analytics Node for {session_id}")
        anal_result = await run_in_threadpool(analytics_node, state)
        state.update(anal_result)

        print(f"DEBUG: [Async] Dumping results for {session_id}")
        validation_json = json.dumps(state.get("validation_report", {}))

        analytics_output = state.get("analytics_output")
        if analytics_output is None:
            print(f"DEBUG: [Async] analytics_output is None for session {session_id} — storing error.")
            analytics_json = json.dumps({"status": "ERROR", "error": "Analytics produced no output. Validation may have failed or returned no clean_data_ref."})
        else:
            analytics_json = json.dumps(analytics_output)

        # 3. Update Session
        session_row = db.query(models.Session).filter(models.Session.id == session_id).first()
        if session_row:
            session_row.validation_report = validation_json
            session_row.analytics_result  = analytics_json
            db.commit()
            print(f"DEBUG: [Async] Session {session_id} analysis COMPLETE.")

    except Exception as e:
        import traceback
        print(f"DEBUG: [Async] Exception in pipeline for {session_id}:")
        traceback.print_exc()

        session_row = db.query(models.Session).filter(models.Session.id == session_id).first()
        if session_row:
            session_row.validation_report = json.dumps({"status": "ERROR", "error": str(e)})
            session_row.analytics_result  = json.dumps({"status": "ERROR", "error": str(e)})
            db.commit()
    finally:
        db.close()

# --- Endpoints ---

@router.post("/upload", response_model=SessionResponse)
async def upload_file(
    background_tasks: BackgroundTasks,
    file: UploadFile = File(...),
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """
    Reads file bytes into memory, stores them directly in the DB,
    then schedules analysis in the background.  No files are written to disk.
    """
    print("!!! REACHED UPLOAD ENDPOINT !!!", flush=True)
    print(f">>> [API] UPLOAD START: {file.filename}", flush=True)

    # 1. Read file bytes entirely into memory
    file_bytes = await file.read()
    file_id    = str(uuid.uuid4())
    print(f">>> [API] Read {len(file_bytes):,} bytes for {file.filename} — storing in DB.", flush=True)

    # 2. Create Session with file bytes stored in DB (no disk write)
    print(">>> [API] Creating DB Session...", flush=True)
    new_session = models.Session(
        user_id      = current_user.id,
        dataset_id   = file_id,
        filename     = file.filename,
        file_path    = f"db:{file_id}",   # marker — actual bytes are in file_content
        file_content = file_bytes,         # LONGBLOB / BLOB
        title        = f"Chat about {file.filename}",
        validation_report = json.dumps({"status": "PROCESSING", "message": "Validation is in progress..."}),
        analytics_result  = json.dumps({"status": "PROCESSING", "message": "Analytics is in progress..."}),
    )
    db.add(new_session)
    db.commit()
    db.refresh(new_session)
    print(f">>> [API] DB Session {new_session.id} created.", flush=True)

    # 3. Schedule background analysis (reads bytes from DB)
    print(">>> [API] Scheduling Background Task...", flush=True)
    background_tasks.add_task(run_async_analysis, new_session.id, file.filename)

    print(f">>> [API] UPLOAD DONE. Session: {new_session.id}.", flush=True)
    return SessionResponse(
        session_id = new_session.id,
        dataset_id = new_session.dataset_id,
        title      = new_session.title,
        created_at = new_session.created_at,
    )

@router.post("/chat")
async def chat(
    request: ChatRequest,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """
    Chat with an existing session using stored validation/analytics results.
    """
    # 1. Fetch Session
    session = db.query(models.Session).filter(
        models.Session.id == request.session_id,
        models.Session.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found or access denied")
    
    # 2. Save User Message
    user_msg = models.ChatMessage(
        session_id=session.id,
        role="user",
        content=request.query
    )
    db.add(user_msg)
    db.commit()
    
    # 3. Retrieve stored analytics/validation
    import json
    validation_report = json.loads(session.validation_report) if session.validation_report else {}
    analytics_output = json.loads(session.analytics_result) if session.analytics_result else {}
    
    # 4. Build context for chat (similar to context_builder_node)
    context = {
        "dataset_id": validation_report.get("dataset_id", session.dataset_id),  # Use validation's dataset_id
        "filename": session.filename,
        "validation_summary": validation_report.get("summary", ""),
        # Add schema and column profiles so chat knows what data exists
        "schema": validation_report.get("schema", []),
        "column_profile": validation_report.get("column_profile", []),
        "issues": validation_report.get("issues", []),
        # Analytics data
        "kpis": analytics_output.get("kpis", []),
        "aggregates": analytics_output.get("aggregates", {}),
        "forecasts": analytics_output.get("forecasts", []),
        "anomalies": analytics_output.get("anomalies", []),
        "risk_analysis": analytics_output.get("risk_analysis"),
        "rfm_analysis": analytics_output.get("rfm_analysis"),
        "basket_analysis": analytics_output.get("basket_analysis"),
    }
    
    # 5. Retrieve conversation history (last 5 messages for context)
    history_records = db.query(models.ChatMessage).filter(
        models.ChatMessage.session_id == session.id
    ).order_by(models.ChatMessage.timestamp.desc()).limit(5).all()
    
    # Convert to LangChain Messages
    history = []
    for msg in reversed(history_records):
        if msg.role == "user":
            history.append(HumanMessage(content=msg.content))
        elif msg.role == "assistant":
            history.append(AIMessage(content=msg.content))
    
    # 6. Invoke Chat Agent
    try:
        from agents.chat_agent import chat_node
        
        chat_state = {
            "context": context,
            "question": request.query,
            "response": "",
            "history": history  # Pass list of message objects
        }
        
        # DEBUG: Log what context we're passing
        import sys
        print("=" * 80, file=sys.stderr)
        print("DEBUG: Context being passed to chat_node:", file=sys.stderr)
        print(f"  - Dataset ID: {context.get('dataset_id')}", file=sys.stderr)
        print(f"  - Filename: {context.get('filename')}", file=sys.stderr)
        print(f"  - KPIs count: {len(context.get('kpis', []))}", file=sys.stderr)
        print(f"  - Aggregates keys: {list(context.get('aggregates', {}).keys())}", file=sys.stderr)
        print(f"  - Has column_profile: {'column_profile' in context}", file=sys.stderr)
        print(f"  - Has schema: {'schema' in context}", file=sys.stderr)
        print(f"  - Question: {request.query}", file=sys.stderr)
        print("=" * 80, file=sys.stderr)
        
        result = chat_node(chat_state)
        ai_response_content = result.get("response", "I couldn't process that request.")
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        ai_response_content = f"Error: {str(e)}"
    
    # 7. Save Assistant Message
    ai_msg = models.ChatMessage(
        session_id=session.id,
        role="assistant",
        content=ai_response_content
    )
    db.add(ai_msg)
    db.commit()
    
    return {
        "response": ai_response_content, 
        "session_id": session.id,
        "dataset_id": session.dataset_id
    }

@router.get("/history", response_model=List[SessionResponse])
def get_history(
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """
    List all sessions for the current user.
    """
    sessions = db.query(models.Session).filter(
        models.Session.user_id == current_user.id
    ).order_by(models.Session.created_at.desc()).all()
    
    return [
        SessionResponse(
            session_id=s.id,
            dataset_id=s.dataset_id,
            title=s.title,
            created_at=s.created_at
        ) for s in sessions
    ]

@router.get("/session/{session_id}/messages", response_model=List[MessageResponse])
def get_session_messages(
    session_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """
    Get full message history for a session.
    """
    session = db.query(models.Session).filter(
        models.Session.id == session_id,
        models.Session.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    messages = db.query(models.ChatMessage).filter(
        models.ChatMessage.session_id == session.id
    ).order_by(models.ChatMessage.timestamp).all()
    
    return [
        MessageResponse(
            role=m.role,
            content=m.content,
            timestamp=m.timestamp
        ) for m in messages
    ]

@router.delete("/session/{session_id}")
def delete_session(
    session_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """
    Delete a specific session and its associated data.
    """
    session = db.query(models.Session).filter(
        models.Session.id == session_id,
        models.Session.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")
        
    db.delete(session)
    db.commit()
    
    return {"message": "Session deleted successfully"}

@router.get("/session/{session_id}/dashboard")
async def get_session_dashboard(
    session_id: int,
    current_user: models.User = Depends(auth.get_current_user),
    db: Session = Depends(database.get_db)
):
    """
    Generates the UI Dashboard configuration for a specific session using the UI Agent.
    """
    # 1. Fetch Session
    session = db.query(models.Session).filter(
        models.Session.id == session_id,
        models.Session.user_id == current_user.id
    ).first()
    
    if not session:
        raise HTTPException(status_code=404, detail="Session not found")

    # 2. Check if we have analytics results — auto-trigger if missing
    print(f"DEBUG: Session {session_id} Analytics Result: {session.analytics_result[:100] if session.analytics_result else 'None'}")
    
    needs_analysis = False
    if not session.analytics_result:
        needs_analysis = True
    else:
        try:
            _tmp = json.loads(session.analytics_result)
            if _tmp is None or (not _tmp.get("aggregates") and not _tmp.get("kpis")):
                needs_analysis = True  # Empty analytics result — re-run
        except Exception:
            needs_analysis = True

    if needs_analysis:
        print(f"DEBUG: Session {session_id} has no/empty analytics. Auto-triggering pipeline...")
        try:
            from agents.orchestrator import validation_node, analytics_node

            # Read file bytes from DB — new sessions use file_content BLOB,
            # old sessions that still have a real file_path fall back to disk.
            file_bytes = None
            if session.file_content:
                file_bytes = session.file_content
                print(f"DEBUG: Read {len(file_bytes):,} bytes from DB file_content for auto-trigger.")
            elif session.file_path and not session.file_path.startswith("db:"):
                # Legacy session: try disk path
                file_full_path = session.file_path
                if not os.path.isabs(file_full_path):
                    candidates = [
                        file_full_path,
                        os.path.join("Backend", file_full_path),
                        os.path.join("Backend/data/uploads", f"{session.dataset_id}.csv"),
                    ]
                    file_full_path = next((p for p in candidates if os.path.exists(p)), None)

                if file_full_path and os.path.exists(file_full_path):
                    with open(file_full_path, "rb") as f:
                        file_bytes = f.read()
                    print(f"DEBUG: Read {len(file_bytes):,} bytes from disk for auto-trigger.")

            if not file_bytes:
                raise HTTPException(
                    status_code=400,
                    detail="File content missing — session cannot be re-analysed. Please upload again."
                )

            state = {
                "file_bytes": file_bytes,
                "filename": session.filename,
                "user_query": "",
                "validation_mode": "lenient",
                "persist": True,
                "validation_report": {},
                "analytics_output": {},
                "context": {},
                "question": "",
                "response": ""
            }
            val_result = await validation_node(state)
            state.update(val_result)
            anal_result = await run_in_threadpool(analytics_node, state)
            state.update(anal_result)

            analytics_output = state.get("analytics_output")
            if analytics_output is None:
                # Validation succeeded but analytics returned nothing — store a meaningful error
                analytics_json = json.dumps({"status": "ERROR", "error": "Analytics produced no output."})
            else:
                analytics_json = json.dumps(analytics_output)

            session.analytics_result = analytics_json
            db.add(session)
            db.commit()
            db.refresh(session)
            print(f"DEBUG: Auto-analysis complete for session {session_id}")
        except HTTPException:
            raise
        except Exception as e:
            import traceback
            traceback.print_exc()
            raise HTTPException(status_code=500, detail=f"Auto-analysis failed: {str(e)}")


    # 3. Parse Analytics Data
    try:
        analytics_data = json.loads(session.analytics_result)
        # Handle case where JSON is "null" -> None
        if analytics_data is None:
             raise HTTPException(status_code=400, detail="No analytics data available (Analysis likely failed)")

        # Handle processing status
        if analytics_data.get("status") == "PROCESSING":
             print(f"DEBUG: Session {session_id} is still PROCESSING.")
             # Return a temporary indicator that the frontend can recognize
             from core.schemas import UIControllerOutput, UIComponent, SessionContext
             return UIControllerOutput(
                 dashboard_id="pending",
                 components=[
                     UIComponent(
                         id="processing",
                         type="kpi",
                         title="Analysis in Progress",
                         description="The AI agents are still crunching your data. Hang tight!",
                         width="full"
                     )
                 ],
                 session_context=SessionContext(kpi_list=[], filters={})
             )

        # Handle potential error status in stored JSON
        if analytics_data.get("status") == "ERROR":
             raise HTTPException(status_code=400, detail=f"Analytics failed: {analytics_data.get('error')}")
    except json.JSONDecodeError:
        raise HTTPException(status_code=500, detail="Invalid analytics data stored")

    # 4. Prepare Input for UI Agent
    from agents.ui_agent import ui_agent
    from core.schemas import UIControllerInput
    
    # Map dictionary to schema fields
    try:
        print(f"DEBUG: Constructing UIControllerInput for session {session_id}")
        ui_input = UIControllerInput(
            dataset_id=session.dataset_id,
            kpis=analytics_data.get("kpis", []),
            aggregates=analytics_data.get("aggregates", {}),
            forecasts=analytics_data.get("forecasts"),
            anomalies=analytics_data.get("anomalies"),
            risk_analysis=analytics_data.get("risk_analysis"),
            rfm_analysis=analytics_data.get("rfm_analysis"),
            basket_analysis=analytics_data.get("basket_analysis"),
            available_components=[
                "kpi",
                "bar_chart", "horizontal_bar", "radar_chart", "pie_chart", "radial_bar",
                "line_chart", "area_chart", "scatter_plot", "slope_chart",
                "table", "anomaly_list", "recommendation_card"
            ],
            screen_space="dashboard"
        )
        
        # 5. Run UI Agent (Using ThreadPool to avoid blocking event loop)
        print(f"DEBUG: Invoking UI Agent for session {session_id}", flush=True)
        result = await run_in_threadpool(ui_agent.run, ui_input)
        print("DEBUG: UI Agent finished execution.", flush=True)
        
        # 6. Hydrate Components with Data (ROBUST VERSION)
        all_kpis = analytics_data.get("kpis", [])
        all_aggregates = analytics_data.get("aggregates", {})
        kpi_cursor = 0
        aggregate_keys = list(all_aggregates.keys())
        agg_cursor = 0

        # Helper to extract actual data rows from an aggregate value
        def extract_agg_data(val):
            """Handle both list format (from _compute_aggregates) and dict format (from LLM)."""
            if isinstance(val, list) and len(val) > 0:
                return val  # Raw list of rows - direct from _compute_aggregates
            elif isinstance(val, dict):
                # LLM-generated format: {"table_ref": ..., "data": [...]}
                inner = val.get("data")
                if inner and isinstance(inner, list) and len(inner) > 0:
                    return inner
            return None

        for comp in result.components:
            if comp.type == 'kpi':
                # Strategy 1: Exact match by ID or label
                kpi_data = next((k for k in all_kpis if k.get('id') == comp.id or k.get('label') == comp.title), None)
                
                # Strategy 2: Positional fallback - assign next available KPI
                if not kpi_data and kpi_cursor < len(all_kpis):
                    kpi_data = all_kpis[kpi_cursor]
                    kpi_cursor += 1
                
                if kpi_data:
                    comp.data = kpi_data
                    if not comp.title or comp.title.lower().startswith("kpi"):
                        comp.title = kpi_data.get("label", comp.title)
                
            elif comp.type in ('bar_chart', 'horizontal_bar', 'radar_chart', 'pie_chart', 'funnel_chart',
                               'line_chart', 'area_chart', 'scatter_plot', 'table'):
                data_attached = False
                
                # Strategy 1: Exact data_ref match in aggregates
                if comp.data_ref and comp.data_ref in all_aggregates:
                    agg_data = extract_agg_data(all_aggregates[comp.data_ref])
                    if agg_data is not None:
                        comp.data = agg_data
                        data_attached = True
                        # Override chart type from aggregate's recommended_chart
                        agg_meta = all_aggregates[comp.data_ref]
                        if isinstance(agg_meta, dict) and agg_meta.get("recommended_chart"):
                            comp.type = agg_meta["recommended_chart"]
                
                # Strategy 2: Partial key match (e.g. comp title contains aggregate key words)
                if not data_attached and comp.title:
                    title_lower = comp.title.lower()
                    for agg_key, agg_val in all_aggregates.items():
                        key_words = agg_key.lower().replace("_", " ").split()
                        if any(word in title_lower for word in key_words if len(word) > 3):
                            agg_data = extract_agg_data(agg_val)
                            if agg_data is not None:
                                comp.data = agg_data
                                data_attached = True
                                break
                
                # Strategy 3: Title keyword matching for special types
                if not data_attached and comp.title:
                    title_lc = comp.title.lower()
                    if "forecast" in title_lc or "trend" in title_lc:
                        forecasts = analytics_data.get("forecasts", [])
                        if forecasts:
                            comp.data = forecasts
                            data_attached = True
                    elif "anomal" in title_lc or "outlier" in title_lc:
                        anomalies = analytics_data.get("anomalies", [])
                        if anomalies:
                            comp.data = anomalies
                            data_attached = True
                    elif "rfm" in title_lc or "segment" in title_lc:
                        rfm = analytics_data.get("rfm_analysis", [])
                        if rfm:
                            comp.data = rfm
                            data_attached = True
                    elif "basket" in title_lc or "association" in title_lc:
                        basket = analytics_data.get("basket_analysis", [])
                        if basket:
                            comp.data = basket
                            data_attached = True
                    elif "risk" in title_lc:
                        risk = analytics_data.get("risk_analysis")
                        if risk:
                            comp.data = [{"id": risk.get("risk_level", "Low"), "value": risk.get("risk_score", 0)}]
                            data_attached = True
                
                # Strategy 4: Positional fallback - scan ALL aggregates for one with non-null data
                if not data_attached:
                    for agg_key in aggregate_keys[agg_cursor:]:
                        agg_data = extract_agg_data(all_aggregates[agg_key])
                        agg_meta = all_aggregates[agg_key]
                        agg_cursor += 1
                        if agg_data is not None:
                            comp.data = agg_data
                            data_attached = True
                            # Override type from recommended_chart if present
                            if isinstance(agg_meta, dict) and agg_meta.get("recommended_chart"):
                                comp.type = agg_meta["recommended_chart"]
                            break

            # Special top-level fields
            elif comp.data_ref == 'risk_analysis' or (comp.title and 'risk' in comp.title.lower()):
                risk = analytics_data.get("risk_analysis")
                if risk:
                    comp.data = risk
            elif comp.data_ref and comp.data_ref in analytics_data:
                comp.data = analytics_data[comp.data_ref]

        # 7. GUARANTEED CHART INJECTION + DETERMINISTIC CHART ROTATION
        # After the UI Agent runs, check if any chart components were generated.
        # If not (e.g., the LLM fallback only produced KPIs), inject chart components
        # directly from the aggregates. This is deterministic and always works.
        from core.schemas import UIComponent

        # ── Deterministic post-processor: semantic chart deduplication ────────
        # The analytics agent already assigns semantically correct chart types.
        # This function RESPECTS those choices and only swaps when the same type
        # would appear twice on the same dashboard.
        #
        # Swap logic is semantic, not positional:
        #   - Temporal types (line/area/scatter) are NEVER reassigned
        #   - pie_chart duplicates → radar_chart (if multi-dim) else horizontal_bar
        #   - bar_chart duplicates → use a semantically-appropriate alternative
        #     based on aggregate key:
        #       *_region / *_country / *_geo  → horizontal_bar (long labels)
        #       *_status / *_state / *_phase  → funnel_chart   (stage data)
        #       *_deal / *_tier / *_size      → pie_chart      (few categories)
        #       *_qty / *_quantity / *_units  → radar_chart    (multi-metric)
        #       fallback                      → horizontal_bar
        # Slope chart is TEMPORAL: it shows a start→end change view of a time series
        TEMPORAL_TYPES = {"line_chart", "area_chart", "scatter_plot", "slope_chart"}
        ALL_CHART_TYPES = TEMPORAL_TYPES | {
            "bar_chart", "horizontal_bar", "radar_chart", "pie_chart", "radial_bar"
        }

        # Swap logic comment update
        #   - Temporal: line/area/scatter/slope — NEVER reassigned
        #   - bar_chart duplicates → semantic swap based on agg key:
        #       *_region / *_country / *_geo  → horizontal_bar
        #       *_status / *_state / *_phase  → radial_bar  (circular bars, visually striking)
        #       *_deal / *_tier / *_size      → pie_chart
        #       *_qty / *_quantity / *_units  → radar_chart
        #       fallback                      → horizontal_bar
        def _semantic_swap(suggested: str, agg_key: str, data_rows: list) -> str:
            """Return the best semantically-appropriate swap for a duplicate chart type."""
            key = agg_key.lower()

            if suggested == "bar_chart":
                # Region / geography → horizontal bar (long country/city names)
                if any(w in key for w in ["region", "country", "city", "geo", "territory", "location"]):
                    return "horizontal_bar"
                # Status / stage / phase → radial bar (circular, ordered categorical)
                if any(w in key for w in ["status", "state", "stage", "phase", "step", "pipeline"]):
                    return "radial_bar"
                # Deal size / tier / size → pie (few proportion categories)
                if any(w in key for w in ["deal", "tier", "size", "segment", "class"]):
                    return "pie_chart"
                # Quantity / units by category → radar (comparison of magnitudes)
                if any(w in key for w in ["qty", "quantity", "units", "count_by"]):
                    return "radar_chart"
                # Default bar_chart swap
                return "horizontal_bar"

            elif suggested == "pie_chart":
                # If data has 3+ numeric dims → radar is appropriate
                first = data_rows[0] if data_rows and isinstance(data_rows[0], dict) else {}
                num_cols = sum(1 for v in first.values() if isinstance(v, (int, float)))
                if num_cols >= 3:
                    return "radar_chart"
                return "horizontal_bar"

            # For any other chart type, fall back to horizontal_bar
            return "horizontal_bar"

        # Temporal swap pools (preferred alternatives when a temporal type is a duplicate)
        TEMPORAL_SWAP = {
            "line_chart":   ["slope_chart", "area_chart",  "scatter_plot"],
            "slope_chart":  ["line_chart",  "area_chart",  "scatter_plot"],
            "area_chart":   ["slope_chart", "line_chart",  "scatter_plot"],
            "scatter_plot": ["slope_chart", "line_chart",  "area_chart"],
        }

        def _deduplicate_chart_type(suggested: str, agg_key: str, data_rows: list, used: set) -> str:
            """
            Accept the suggested chart type if it hasn't been used yet.
            If it's a duplicate, pick a semantically appropriate alternative.
            Temporal types deduplicate within their own pool (slope preferred as swap for line).
            """
            # If type not yet used, accept it as-is
            if suggested not in used:
                return suggested

            # Temporal duplicate → try preferred temporal alternatives
            if suggested in TEMPORAL_TYPES:
                for alt in TEMPORAL_SWAP.get(suggested, []):
                    if alt not in used:
                        return alt
                # All temporal types used — return original (edge case)
                return suggested

            # Categorical duplicate → pick a semantic alternative

            primary_swap = _semantic_swap(suggested, agg_key, data_rows)
            if primary_swap not in used:
                return primary_swap

            # Last resort: pick first unused from pool
            pool = ["bar_chart", "horizontal_bar", "pie_chart", "radar_chart", "radial_bar"]
            for t in pool:
                if t not in used:
                    return t

            # All used — just return the original suggestion (better than forcing wrong type)
            return suggested

        # ── Step 7a: Hydrate and Deduplicate types on existing components ─────
        used_chart_types: set = set()
        existing_kpi_ids = {c.id for c in result.components if c.type == 'kpi'}
        referenced_data_refs = {c.data_ref for c in result.components if c.data_ref}

        for comp in result.components:
            if comp.type == 'kpi':
                # Strategy 1: Exact match by ID or label
                kpi_data = next((k for k in all_kpis if k.get('id') == comp.id or k.get('label') == comp.title), None)
                
                # Strategy 2: Positional fallback
                if not kpi_data and kpi_cursor < len(all_kpis):
                    kpi_data = all_kpis[kpi_cursor]
                    kpi_cursor += 1
                
                if kpi_data:
                    comp.data = kpi_data
                    if not comp.title or comp.title.lower().startswith("kpi"):
                        comp.title = kpi_data.get("label", comp.title)
            
            elif comp.type in ALL_CHART_TYPES or comp.type == 'table':
                # ... (rest of hydration logic) ...
                data_attached = False
                if comp.data_ref and comp.data_ref in all_aggregates:
                    agg_data = extract_agg_data(all_aggregates[comp.data_ref])
                    if agg_data is not None:
                        comp.data = agg_data
                        data_attached = True
                        agg_meta = all_aggregates[comp.data_ref]
                        if isinstance(agg_meta, dict) and agg_meta.get("recommended_chart"):
                            comp.type = agg_meta["recommended_chart"]
                
                # ... (rest of hydration) ...
                if not data_attached and comp.title:
                    title_lower = comp.title.lower()
                    for agg_key, agg_val in all_aggregates.items():
                        key_words = agg_key.lower().replace("_", " ").split()
                        if any(word in title_lower for word in key_words if len(word) > 3):
                            agg_data = extract_agg_data(agg_val)
                            if agg_data is not None:
                                comp.data = agg_data
                                data_attached = True
                                break
                
                new_type = _deduplicate_chart_type(
                    suggested=comp.type,
                    agg_key=comp.data_ref or comp.title or "",
                    data_rows=comp.data if isinstance(comp.data, list) else [],
                    used=used_chart_types,
                )
                used_chart_types.add(new_type)
                comp.type = new_type
                if comp.type in TEMPORAL_TYPES and (comp.col_span or 2) < 4:
                    comp.col_span = 4

        # ── Step 7b: Inject missing KPIs ──────────────────────────────────────
        # Ensure that ALL discovered KPIs are on the dashboard
        for kpi in all_kpis:
            if kpi.get('id') not in existing_kpi_ids and kpi.get('label') not in {c.title for c in result.components}:
                if kpi.get('id') == 'error': continue
                
                result.components.insert(0, UIComponent(
                    id=f"auto_kpi_{kpi.get('id')}",
                    type="kpi",
                    title=kpi.get("label", "Metric"),
                    col_span=1,
                    data=kpi
                ))
                existing_kpi_ids.add(kpi.get('id'))
                print(f"DEBUG: Auto-injected missing KPI: {kpi.get('label')}")

        # ── Step 7c: Inject missing aggregate charts ──────────────────────────

        chart_types = ALL_CHART_TYPES | {'table'}
        existing_chart_types = {c.type for c in result.components}
        has_charts = bool(existing_chart_types & chart_types)

        # Track which aggregates are already referenced by existing components
        referenced_data_refs = {c.data_ref for c in result.components if c.data_ref}

        if not has_charts or len(result.components) < 4:
            # Generate chart components for every aggregate that isn't already shown
            for agg_key, agg_val in all_aggregates.items():
                if agg_key in referenced_data_refs:
                    continue  # Skip already-referenced aggregates

                agg_data = extract_agg_data(agg_val)
                if not agg_data:
                    continue

                # Get suggested chart type from the aggregate metadata
                if isinstance(agg_val, dict):
                    suggested_type = agg_val.get("recommended_chart", "bar_chart")
                    description = agg_val.get("description", "")
                else:
                    suggested_type = "bar_chart"
                    description = ""

                # Apply semantic deduplication (same logic as Step 7a)
                chart_type = _deduplicate_chart_type(
                    suggested=suggested_type,
                    agg_key=agg_key,
                    data_rows=agg_data,
                    used=used_chart_types,
                )
                used_chart_types.add(chart_type)


                # Convert underscore key to a human-readable title
                human_title = agg_key.replace("_", " ").title()

                # Set col_span: temporal charts are wide, others are half-width
                col_span = 4 if chart_type in ("line_chart", "area_chart", "scatter_plot") else 2

                chart_comp = UIComponent(
                    id=f"auto_chart_{agg_key}",
                    type=chart_type,
                    title=human_title,
                    subtitle=description,
                    col_span=col_span,
                    data_ref=agg_key,
                    data=agg_data
                )
                result.components.append(chart_comp)
                referenced_data_refs.add(agg_key)
                print(f"DEBUG: Auto-injected {chart_type} for aggregate '{agg_key}' with {len(agg_data)} rows")


        # 8. Inject Anomaly component if anomalies exist
        anomalies = analytics_data.get("anomalies", [])
        if anomalies and len(anomalies) > 0:
            from core.schemas import UIComponent
            anomaly_comp = UIComponent(
                id="anomaly_list",
                type="anomaly_list",
                title="Data Anomalies Detected",
                col_span=4,
                description=f"{len(anomalies)} statistical outliers found in your dataset.",
                data=anomalies
            )
            result.components.append(anomaly_comp)

        # 8b. Inject Market Basket Analysis card (only when rules exist)
        basket_rules = analytics_data.get("basket_analysis", [])
        if basket_rules and len(basket_rules) > 0:
            basket_comp = UIComponent(
                id="basket_analysis_card",
                type="basket_analysis_card",
                title="Market Basket Analysis",
                subtitle=f"{len(basket_rules)} product association rules discovered",
                col_span=4,
                data=basket_rules
            )
            result.components.append(basket_comp)
            print(f"DEBUG: Injected basket_analysis_card with {len(basket_rules)} rules")

        # 9. Inject Recommendations / Decision card if recommendations exist
        recommendations = analytics_data.get("recommendations", [])
        if recommendations and len(recommendations) > 0:
            # Enrich raw string recommendations with priority hints
            enriched = []
            for i, rec in enumerate(recommendations):
                if isinstance(rec, str):
                    # Assign priority based on keywords
                    text_lower = rec.lower()
                    if any(w in text_lower for w in ['critical','urgent','risk','alert','immediately','reduce','loss']):
                        priority = "high"
                    elif any(w in text_lower for w in ['improve','increase','focus','optimize','review','monitor']):
                        priority = "medium"
                    else:
                        priority = "low"
                    enriched.append({"text": rec, "priority": priority})
                elif isinstance(rec, dict):
                    enriched.append(rec)

            rec_comp = UIComponent(
                id="recommendation_card",
                type="recommendation_card",
                title="Strategic Recommendations",
                subtitle="AI-generated actions based on your data",
                col_span=4,
                data=enriched
            )
            result.components.append(rec_comp)
            print(f"DEBUG: Injected recommendation_card with {len(enriched)} items")

        # 9. Final Sanity Check: If no components, provide a fallback message
        if not result.components:
             print(f"DEBUG: UI Agent returned zero components for session {session_id}. Injecting fallback.")
             from core.schemas import UIComponent
             
             # Check if there was an error in analytics
             is_error = any(k.get("id") == "error" for k in analytics_data.get("kpis", []))
             
             result.components = [
                 UIComponent(
                     id="fallback_info",
                     type="kpi",
                     title="Limited Insights Found" if not is_error else "Analysis Warning",
                     description="The AI analyzed your data but didn't find specific trends to chart. You can still chat with the AI Analyst about the raw data." if not is_error else "There was a problem during the deep analysis phase. Try asking the AI Analyst for a summary.",
                     col_span=4,
                     data={"value": "N/A", "label": "Status"}
                 )
             ]

        print(f"DEBUG: Final Hydrated Result: {result.model_dump_json(indent=2)}")
        return result
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        raise HTTPException(status_code=500, detail=str(e))

