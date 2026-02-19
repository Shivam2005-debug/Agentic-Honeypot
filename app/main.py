import logging
import json
import re
import os
from datetime import datetime
from dotenv import load_dotenv

# 1. FORCE LOAD .ENV for Windows/Agno compatibility
load_dotenv()

from fastapi import FastAPI, Header, HTTPException, BackgroundTasks, Depends, Security
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi import Request
from fastapi.responses import JSONResponse

from app.core.config import settings
from app.core.security import verify_api_key
from app.models.api_schemas import (
    IncomingMessage, AgentResponse, MessageItem, EngagementMetrics, ExtractedIntelligence
)
from app.services.state import StateService
from app.services.callback import callback_service
from app.agents.detector import get_detector_agent
from app.agents.persona import get_persona_agent
from app.agents.extractor import get_extractor_agent

# Logging Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("guvi-honeypot")

app = FastAPI(title="Guvi Honeypot Agent")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

state_service = StateService()

# --- Helpers ---
def format_history_for_agno(history: list[MessageItem]) -> list[dict]:
    """Convert GUVI history to Agno message format."""
    formatted = []
    for msg in history:
        role = "user" if msg.sender == "scammer" else "assistant"
        formatted.append({"role": role, "content": msg.text})
    return formatted

def clean_json_str(raw_str: str) -> str:
    # Remove markdown code blocks
    cleaned = re.sub(r"```json\s*", "", raw_str)
    cleaned = re.sub(r"```\s*$", "", cleaned)
    # Remove any text before the first '{' and after the last '}'
    # This handles cases where Llama says "Here is the JSON: { ... }"
    start = cleaned.find('{')
    end = cleaned.rfind('}') + 1
    if start != -1 and end != -1:
        cleaned = cleaned[start:end]
    return cleaned.strip()

def parse_timestamp(ts) -> float:
    """Safely parse timestamp to unix float (milliseconds)."""
    try:
        # If it's already a number (int/float)
        if isinstance(ts, (int, float)):
            return float(ts)
        # If ISO string, convert to timestamp
        dt = datetime.fromisoformat(str(ts).replace("Z", "+00:00"))
        return dt.timestamp() * 1000 
    except:
        return 0.0

@app.get("/health")
async def health_check():
    return {"status": "active", "service": "guvi-honeypot"}

@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Log exact payload on validation error for debugging."""
    body = await request.body()
    error_msg = f"VALIDATION ERROR: {exc}"
    body_content = body.decode()
    logger.error("--- 422 ERROR DEBUG ---")
    logger.error(error_msg)
    logger.error(f"INCOMING BODY: {body_content}")
    logger.error("-----------------------")
    return JSONResponse(
        status_code=422,
        content={"detail": str(exc), "body_received": body_content},
    )

# --- Core Endpoint ---
@app.post("/api/chat", response_model=AgentResponse)
async def chat_endpoint(
    payload: IncomingMessage,
    background_tasks: BackgroundTasks,
    x_api_key: str = Security(verify_api_key)
):
    session_id = payload.sessionId
    user_text = payload.message.text
    
    # 1. Load State
    is_scam_confirmed = state_service.get_scam_status(session_id)
    current_intel = state_service.get_extracted_intelligence(session_id)
    current_agent_notes = "Monitoring conversation..." 

    # 2. Scam Detection (If not yet confirmed)
    if not is_scam_confirmed:
        detector = get_detector_agent()
        detection_data = {}
        
        # RETRY LOGIC: Try twice to get valid JSON
        for attempt in range(2):
            try:
                raw_response = detector.run(user_text).content
                detection_data = json.loads(clean_json_str(raw_response))
                break # Success! Exit loop
            except json.JSONDecodeError:
                logger.warning(f"Detector JSON failed (Attempt {attempt+1}). Retrying...")
                if attempt == 1: 
                    logger.error(f"Detector Failed completely.")
        
        # Proceed only if we got data
        if detection_data:
            is_scam = detection_data.get("is_scam", False)
            # Capture dynamic notes
            behavior_summary = detection_data.get("behavior_summary", "Scam intent detected.")
            
            if is_scam:
                is_scam_confirmed = True
                state_service.set_scam_status(session_id, True)
                current_agent_notes = behavior_summary 
                logger.info(f"Session {session_id}: SCAM DETECTED. Notes: {behavior_summary}")
            else:
                return AgentResponse(
                    status="success",
                    reply="Sorry, I think you have the wrong number."
                )
        else:
             # Fallback if 2 retries failed
             return AgentResponse(
                status="success",
                reply="Hello? Who is this?"
            )
    else:
        current_agent_notes = "Scam previously detected. Engaging agent."

    # 3. Intelligence Extraction
    try:
        extractor = get_extractor_agent()
        new_intel_dict = {}
        
        # RETRY LOGIC
        for attempt in range(2):
            try:
                raw_intel = extractor.run(user_text).content
                new_intel_dict = json.loads(clean_json_str(raw_intel))
                break
            except json.JSONDecodeError:
                 logger.warning(f"Extractor JSON failed (Attempt {attempt+1}). Retrying...")
        
        if new_intel_dict:
            # Merge
            new_intel_model = ExtractedIntelligence(**new_intel_dict)
            current_intel = state_service.update_intelligence(session_id, new_intel_model)
            
    except Exception as e:
        logger.error(f"Extraction logic error: {e}")
        # Continue without updating intel - do not crash

    # 4. Generate Persona Response
    try:
        agno_history = format_history_for_agno(payload.conversationHistory)
        persona = get_persona_agent()
        response_obj = persona.run(user_text, messages=agno_history)
        agent_reply_text = response_obj.content
    except Exception as e:
        logger.error(f"Persona Generation Failed: {e}")
        agent_reply_text = "I am having trouble hearing you. Can you say that again?"

    # 5. Metrics & Termination Logic
    total_messages = len(payload.conversationHistory) + 2
    
    # --- DURATION CALCULATION ---
    # Strategy: Use Payload Timestamps (Best for Scoring)
    start_time = 0.0
    end_time = parse_timestamp(payload.message.timestamp)
    
    if payload.conversationHistory:
        # Get timestamp of the FIRST message in history
        first_msg = payload.conversationHistory[0]
        start_time = parse_timestamp(first_msg.timestamp)
    else:
        # This is the first message
        start_time = end_time

    # Calculate duration (Absolute diff)
    duration_ms = abs(end_time - start_time)
    duration_seconds = int(duration_ms / 1000)
    
    # Fallback: If duration is 0 but we have messages (e.g. timestamps missing/bad), use estimate
    if duration_seconds == 0 and total_messages > 1:
        duration_seconds = total_messages * 30

    engagement_metrics = EngagementMetrics(
        totalMessagesExchanged=total_messages,
        engagementDurationSeconds=duration_seconds
    )
    
    # --- CALLBACK TRIGGER ---
    # Logic: 20 Messages OR Scam Confirmed + Very Long Convo
    
    MIN_ACCUMULATION_DEPTH = 20
    
    should_report = is_scam_confirmed and (total_messages >= MIN_ACCUMULATION_DEPTH)

    if should_report:
        if not state_service.is_conversation_complete(session_id):
            state_service.mark_conversation_complete(session_id)
            
            final_payload = {
                "status": "completed",
                "sessionId": session_id,
                "scamDetected": True,
                "scamType": "financial_fraud_generic", # Default, refined by agentNotes
                "totalMessagesExchanged": total_messages,
                "extractedIntelligence": current_intel.model_dump(),
                "engagementMetrics": engagement_metrics.model_dump(),
                "agentNotes": current_agent_notes
            }
            background_tasks.add_task(callback_service.send_final_report, final_payload)
            logger.info(f"Session {session_id}: Scheduled final callback (Accumulated).")
        else:
             logger.info(f"Session {session_id}: Continuing engagement (Report already sent).")

    # 6. Return Response
    return AgentResponse(
        status="success",
        reply=agent_reply_text 
    )

