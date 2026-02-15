# # # # import logging
# # # # from fastapi import FastAPI, Header, HTTPException, BackgroundTasks, Depends, Security 
# # # # from typing import Optional

# # # # from app.core.security import verify_api_key

# # # # from agno.agent import Agent
# # # # from agno.models.groq import Groq

# # # # # Import internals
# # # # from app.core.config import settings
# # # # from app.models.api_schemas import (
# # # #     IncomingMessage, AgentResponse, MessageItem, EngagementMetrics
# # # # )
# # # # from app.services.state import StateService
# # # # from app.services.callback import callback_service
# # # # # from app.agents.detector import get_detector_agent, ScamDetectionResult
# # # # from app.agents.detector import get_detector_agent
# # # # from app.agents.persona import get_persona_agent
# # # # from app.agents.extractor import get_extractor_agent

# # # # import json
# # # # import re


# # # # # Logging Setup
# # # # logging.basicConfig(level=logging.INFO)
# # # # logger = logging.getLogger("guvi-honeypot")

# # # # app = FastAPI(title="Guvi Honeypot Agent")
# # # # state_service = StateService()

# # # # # --- Helpers ---

# # # # # def verify_api_key(x_api_key: str = Header(...)):
# # # # #     if x_api_key != settings.API_KEY:
# # # # #         raise HTTPException(status_code=401, detail="Invalid API Key")

# # # # def format_history_for_agno(history: list[MessageItem]) -> list[dict]:
# # # #     """Convert GUVI history to Agno message format."""
# # # #     formatted = []
# # # #     for msg in history:
# # # #         role = "user" if msg.sender == "scammer" else "assistant"
# # # #         formatted.append({"role": role, "content": msg.text})
# # # #     return formatted

# # # # # Helper to clean LLM JSON output (handles markdown blocks if they slip through)
# # # # def clean_json_str(raw_str: str) -> str:
# # # #     # Remove json and  if present
# # # #     cleaned = re.sub(r"json\s*", "", raw_str)
# # # #     cleaned = re.sub(r"\s*$", "", cleaned)
# # # #     return cleaned.strip()

# # # # # --- Core Endpoint ---
# # # # # @app.post("/api/chat", response_model=AgentResponse)
# # # # # async def chat_endpoint(
# # # # #     payload: IncomingMessage,
# # # # #     background_tasks: BackgroundTasks,
# # # # #     # x_api_key: str = Depends(verify_api_key)
# # # # #     x_api_key: str = Security(verify_api_key)

# # # # # ):
# # # # #     session_id = payload.sessionId
# # # # #     user_text = payload.message.text
    
# # # # #     # 1. Load State
# # # # #     is_scam_confirmed = state_service.get_scam_status(session_id)
# # # # #     current_intel = state_service.get_extracted_intelligence(session_id)
    
# # # # #     # 2. Scam Detection (If not yet confirmed)
# # # # #     if not is_scam_confirmed:
# # # # #         # Fast Detector
# # # # #         detector = get_detector_agent()
# # # # #         # We only feed the LATEST message to the detector for speed
# # # # #         detection: ScamDetectionResult = detector.run(user_text).content
        
# # # # #         if detection.is_scam:
# # # # #             is_scam_confirmed = True
# # # # #             state_service.set_scam_status(session_id, True)
# # # # #             logger.info(f"Session {session_id}: SCAM DETECTED. Reason: {detection.reasoning}")
# # # # #         else:
# # # # #             # If safe, return a generic "Wrong number" response immediately
# # # # #             # We don't engage the persona yet to save costs/latency
# # # # #             return AgentResponse(
# # # # #                 status="success",
# # # # #                 scamDetected=False,
# # # # #                 response_text="Sorry, I think you have the wrong number.",
# # # # #                 extractedIntelligence=current_intel
# # # # #             )

# # # # #     # 3. Intelligence Extraction (Async - Fire & Forget style logic, but awaited for data integrity)
# # # # #     # We extract from the CURRENT message
# # # # #     extractor = get_extractor_agent()
# # # # #     # Run extractor
# # # # #     new_intel_resp = extractor.run(user_text)
# # # # #     # Merge & Save
# # # # #     if new_intel_resp.content:
# # # # #         current_intel = state_service.update_intelligence(session_id, new_intel_resp.content)

# # # # #     # 4. Generate Persona Response
# # # # #     # Convert history + current message
# # # # #     agno_history = format_history_for_agno(payload.conversationHistory)
# # # # #     # Add the current message explicitly if it's not in history yet (GUVI usually sends history excluding current)
# # # # #     # Safety check: if history is empty, it's the first message.
    
# # # # #     persona = get_persona_agent()
# # # # #     # We inject the full history + current user message into the run
# # # # #     # Note: Agno's .run() handles the current message. We prepended history.
# # # # #     response_obj = persona.run(
# # # # #         user_text,
# # # # #         messages=agno_history 
# # # # #     )
# # # # #     agent_reply_text = response_obj.content

# # # # #     # 5. Metrics & Termination Logic
# # # # #     # Calculate simple metrics
# # # # #     total_messages = len(payload.conversationHistory) + 2 # History + User + Agent
# # # # #     engagement_metrics = EngagementMetrics(
# # # # #         totalMessagesExchanged=total_messages,
# # # # #         engagementDurationSeconds=total_messages * 30 # Rough estimate
# # # # #     )
    
# # # # #     # Check Termination Heuristics
# # # # #     has_critical_intel = (
# # # # #         len(current_intel.bankAccounts) > 0 or 
# # # # #         len(current_intel.upiIds) > 0 or
# # # # #         len(current_intel.phoneNumbers) > 0
# # # # #     )
# # # # #     is_long_convo = total_messages > 15
    
# # # # #     # If we have enough intel OR it's getting too long, report it.
# # # # #     # Also ensure we haven't reported it already.
# # # # #     if is_scam_confirmed and (has_critical_intel or is_long_convo):
# # # # #         if not state_service.is_conversation_complete(session_id):
# # # # #             state_service.mark_conversation_complete(session_id)
            
# # # # #             # Prepare Final Callback Payload
# # # # #             final_payload = {
# # # # #                 "sessionId": session_id,
# # # # #                 "scamDetected": True,
# # # # #                 "totalMessagesExchanged": total_messages,
# # # # #                 "extractedIntelligence": current_intel.model_dump(),
# # # # #                 "agentNotes": "Autonomous engagement completed. Intelligence extracted."
# # # # #             }
# # # # #             # Schedule Background Task
# # # # #             background_tasks.add_task(callback_service.send_final_report, final_payload)
# # # # #             logger.info(f"Session {session_id}: Scheduled final callback.")

# # # # #     # 6. Return Response to GUVI
# # # # #     return AgentResponse(
# # # # #         status="success",
# # # # #         scamDetected=is_scam_confirmed,
# # # # #         extractedIntelligence=current_intel,
# # # # #         engagementMetrics=engagement_metrics,
# # # # #         agentNotes="Engaging...",
# # # # #         response_text=agent_reply_text
# # # # #     )

# # # # @app.post("/api/chat", response_model=AgentResponse)
# # # # async def chat_endpoint(
# # # #     payload: IncomingMessage,
# # # #     background_tasks: BackgroundTasks,
# # # #     x_api_key: str = Security(verify_api_key)
# # # # ):
# # # #     session_id = payload.sessionId
# # # #     user_text = payload.message.text
    
# # # #     # 1. Load State
# # # #     is_scam_confirmed = state_service.get_scam_status(session_id)
# # # #     current_intel = state_service.get_extracted_intelligence(session_id)
    
# # # #     # 2. Scam Detection (If not yet confirmed)
# # # #     if not is_scam_confirmed:
# # # #         detector = get_detector_agent()
# # # #         # Run detector (returns string now)
# # # #         raw_response = detector.run(user_text).content
        
# # # #         try:
# # # #             detection_data = json.loads(clean_json_str(raw_response))
# # # #             # Safe access with defaults
# # # #             is_scam = detection_data.get("is_scam", False)
# # # #             reasoning = detection_data.get("reasoning", "Unknown")
            
# # # #             if is_scam:
# # # #                 is_scam_confirmed = True
# # # #                 state_service.set_scam_status(session_id, True)
# # # #                 logger.info(f"Session {session_id}: SCAM DETECTED. Reason: {reasoning}")
# # # #             else:
# # # #                 return AgentResponse(
# # # #                     status="success",
# # # #                     scamDetected=False,
# # # #                     responseText="Sorry, I think you have the wrong number.",
# # # #                     extractedIntelligence=current_intel
# # # #                 )
# # # #         except json.JSONDecodeError:
# # # #             # Fallback if JSON fails (Assume safe to be cautious, or scam if paranoid)
# # # #             logger.error(f"Detector JSON failed: {raw_response}")
# # # #             # For hackathon: Assume safe to avoid breaking flow, or retry.
# # # #             # Let's return generic safe response.
# # # #             return AgentResponse(
# # # #                 status="success",
# # # #                 scamDetected=False,
# # # #                 responseText="Hello? Who is this?",
# # # #                 extractedIntelligence=current_intel
# # # #             )

# # # #     # 3. Intelligence Extraction
# # # #     extractor = get_extractor_agent()
# # # #     raw_intel = extractor.run(user_text).content
# # # #     try:
# # # #         new_intel_dict = json.loads(clean_json_str(raw_intel))
# # # #         # Convert dict to Pydantic model for merging
# # # #         from app.models.api_schemas import ExtractedIntelligence
# # # #         new_intel_model = ExtractedIntelligence(**new_intel_dict)
# # # #         current_intel = state_service.update_intelligence(session_id, new_intel_model)
# # # #     except Exception as e:
# # # #         logger.error(f"Extraction failed: {e}. Raw: {raw_intel}")
# # # #         # Continue without updating intel

# # # #     # 4. Generate Persona Response
# # # #     agno_history = format_history_for_agno(payload.conversationHistory)
# # # #     persona = get_persona_agent()
# # # #     response_obj = persona.run(user_text, messages=agno_history)
# # # #     agent_reply_text = response_obj.content

# # # #     # 5. Metrics & Termination (Keep logic same as before)
# # # #     total_messages = len(payload.conversationHistory) + 2
# # # #     engagement_metrics = EngagementMetrics(
# # # #         totalMessagesExchanged=total_messages,
# # # #         engagementDurationSeconds=total_messages * 30
# # # #     )
    
# # # #     has_critical_intel = (
# # # #         len(current_intel.bankAccounts) > 0 or 
# # # #         len(current_intel.upiIds) > 0 or
# # # #         len(current_intel.phoneNumbers) > 0
# # # #     )
# # # #     is_long_convo = total_messages > 15
    
# # # #     if is_scam_confirmed and (has_critical_intel or is_long_convo):
# # # #         if not state_service.is_conversation_complete(session_id):
# # # #             state_service.mark_conversation_complete(session_id)
# # # #             final_payload = {
# # # #                 "sessionId": session_id,
# # # #                 "scamDetected": True,
# # # #                 "totalMessagesExchanged": total_messages,
# # # #                 "extractedIntelligence": current_intel.model_dump(),
# # # #                 "agentNotes": "Autonomous engagement completed."
# # # #             }
# # # #             background_tasks.add_task(callback_service.send_final_report, final_payload)
# # # #             logger.info(f"Session {session_id}: Scheduled final callback.")

# # # #     # 6. Return Response
# # # #     return AgentResponse(
# # # #         status="success",
# # # #         scamDetected=is_scam_confirmed,
# # # #         extractedIntelligence=current_intel,
# # # #         engagementMetrics=engagement_metrics,
# # # #         agentNotes="Engaging...",
# # # #         response_text=agent_reply_text
# # # #     )

# # # import logging
# # # import json
# # # import re
# # # import os
# # # from dotenv import load_dotenv

# # # # #---------------------------------------------------------------------------------------------------------------
# # # # from fastapi.middleware.cors import CORSMiddleware # <--- 1. Add Import
# # # # #---------------------------------------------------------------------------------------------------------------

# # # # 1. FORCE LOAD .ENV for Windows/Agno compatibility
# # # load_dotenv()

# # # from fastapi import FastAPI, Header, HTTPException, BackgroundTasks, Depends, Security
# # # from typing import Optional

# # # from agno.agent import Agent
# # # from agno.models.groq import Groq

# # # # Import internals
# # # from app.core.config import settings
# # # from app.core.security import verify_api_key
# # # from app.models.api_schemas import (
# # #     IncomingMessage, AgentResponse, MessageItem, EngagementMetrics, ExtractedIntelligence
# # # )
# # # from app.services.state import StateService
# # # from app.services.callback import callback_service
# # # from app.agents.detector import get_detector_agent
# # # from app.agents.persona import get_persona_agent
# # # from app.agents.extractor import get_extractor_agent

# # # #------------------------------------------------------------------------------------------------------------
# # # from fastapi.exceptions import RequestValidationError
# # # from fastapi import Request
# # # from fastapi.responses import JSONResponse
# # # #------------------------------------------------------------------------------------------------------------


# # # # Logging Setup
# # # logging.basicConfig(level=logging.INFO)
# # # logger = logging.getLogger("guvi-honeypot")

# # # app = FastAPI(title="Guvi Honeypot Agent")
# # # # # --- 2. Add this block IMMEDIATELY after app = FastAPI(...) ---
# # # # app.add_middleware(
# # # #     CORSMiddleware,
# # # #     allow_origins=["*"],  # Allows ALL domains (Critical for Hackathon Testers)
# # # #     allow_credentials=True,
# # # #     allow_methods=["*"],
# # # #     allow_headers=["*"],
# # # # )
# # # # # -----------------------------------------------------------
# # # state_service = StateService()

# # # # --- Helpers ---
# # # def format_history_for_agno(history: list[MessageItem]) -> list[dict]:
# # #     """Convert GUVI history to Agno message format."""
# # #     formatted = []
# # #     for msg in history:
# # #         role = "user" if msg.sender == "scammer" else "assistant"
# # #         formatted.append({"role": role, "content": msg.text})
# # #     return formatted

# # # def clean_json_str(raw_str: str) -> str:
# # #     # Remove ```json and ``` if present
# # #     cleaned = re.sub(r"```json\s*", "", raw_str)
# # #     cleaned = re.sub(r"```\s*$", "", cleaned)
# # #     return cleaned.strip()

# # # #-------------------------------------------------------------------------------------------------

# # # @app.get("/health")
# # # async def health_check():
# # #     return {"status": "active", "service": "guvi-honeypot"}

# # # #-------------------------------------------------------------------------------------------------

# # # # --- Core Endpoint ---
# # # @app.post("/api/chat", response_model=AgentResponse)
# # # async def chat_endpoint(
# # #     payload: IncomingMessage,
# # #     background_tasks: BackgroundTasks,
# # #     x_api_key: str = Security(verify_api_key)
# # # ):
# # #     session_id = payload.sessionId
# # #     user_text = payload.message.text
    
# # #     # 1. Load State
# # #     is_scam_confirmed = state_service.get_scam_status(session_id)
# # #     current_intel = state_service.get_extracted_intelligence(session_id)
    
# # #     # # 2. Scam Detection (If not yet confirmed)
# # #     # if not is_scam_confirmed:
# # #     #     detector = get_detector_agent()
# # #     #     # Run detector
# # #     #     try:
# # #     #         raw_response = detector.run(user_text).content
# # #     #         detection_data = json.loads(clean_json_str(raw_response))
            
# # #     #         # Safe access
# # #     #         is_scam = detection_data.get("is_scam", False)
# # #     #         reasoning = detection_data.get("reasoning", "Unknown")
            
# # #     #         if is_scam:
# # #     #             is_scam_confirmed = True
# # #     #             state_service.set_scam_status(session_id, True)
# # #     #             logger.info(f"Session {session_id}: SCAM DETECTED. Reason: {reasoning}")
# # #     #         else:
# # #     #             return AgentResponse(
# # #     #                 status="success",
# # #     #                 scamDetected=False,
# # #     #                 response_text="Sorry, I think you have the wrong number.", # Fixed field name
# # #     #                 extractedIntelligence=current_intel
# # #     #             )
# # #     #     except Exception as e:
# # #     #         # Fallback if JSON fails or LLM errors
# # #     #         logger.error(f"Detector Failed: {e}")
# # #     #         # Safe fallback
# # #     #         return AgentResponse(
# # #     #             status="success",
# # #     #             scamDetected=False,
# # #     #             response_text="Hello? Who is this?", # Fixed field name
# # #     #             extractedIntelligence=current_intel
# # #     #         )
    

# # #     # 2. Scam Detection (If not yet confirmed)
# # #     # We initialize agent_notes with a default, but try to overwrite it from detector
# # #     current_agent_notes = "Monitoring conversation..." 

# # # #-----------------------------------------------------------------------------------------------------------   
# # #     # if not is_scam_confirmed:
# # #     #     detector = get_detector_agent()
# # #     #     try:
# # #     #         raw_response = detector.run(user_text).content
# # #     #         detection_data = json.loads(clean_json_str(raw_response))
            
# # #     #         is_scam = detection_data.get("is_scam", False)
# # #     #         reasoning = detection_data.get("reasoning", "Unknown")
# # #     #         # NEW: Capture dynamic notes
# # #     #         behavior_summary = detection_data.get("behavior_summary", "Scam intent detected.")
            
# # #     #         if is_scam:
# # #     #             is_scam_confirmed = True
# # #     #             state_service.set_scam_status(session_id, True)
# # #     #             current_agent_notes = behavior_summary # Update notes
# # #     #             logger.info(f"Session {session_id}: SCAM DETECTED. Notes: {behavior_summary}")
# # #     #         else:
# # #     #             return AgentResponse(
# # #     #                 status="success",
# # #     #                 scamDetected=False,
# # #     #                 response_text="Sorry, I think you have the wrong number.",
# # #     #                 extractedIntelligence=current_intel
# # #     #             )
# # #     #     except Exception as e:
# # #     #         logger.error(f"Detector Failed: {e}")
# # #     #         return AgentResponse(
# # #     #             status="success",
# # #     #             scamDetected=False,
# # #     #             response_text="Hello? Who is this?",
# # #     #             extractedIntelligence=current_intel
# # #     #         )

# # #     if not is_scam_confirmed:
# # #         detector = get_detector_agent()
# # #         detection_data = {}
        
# # #         # RETRY LOGIC: Try twice to get valid JSON
# # #         for attempt in range(2):
# # #             try:
# # #                 raw_response = detector.run(user_text).content
# # #                 detection_data = json.loads(clean_json_str(raw_response))
# # #                 break # Success! Exit loop
# # #             except json.JSONDecodeError:
# # #                 logger.warning(f"Detector JSON failed (Attempt {attempt+1}). Retrying...")
# # #                 if attempt == 1: # If last attempt failed
# # #                     logger.error(f"Detector Failed completely.")
        
# # #         # Proceed only if we got data
# # #         if detection_data:
# # #             # Safe access
# # #             is_scam = detection_data.get("is_scam", False)
# # #             reasoning = detection_data.get("reasoning", "Unknown")
# # #             behavior_summary = detection_data.get("behavior_summary", "Scam intent detected.")
            
# # #             if is_scam:
# # #                 is_scam_confirmed = True
# # #                 state_service.set_scam_status(session_id, True)
# # #                 current_agent_notes = behavior_summary 
# # #                 logger.info(f"Session {session_id}: SCAM DETECTED. Notes: {behavior_summary}")
# # #             else:
# # #                 return AgentResponse(
# # #                     status="success",
# # #                     # scamDetected=False,
# # #                     # response_text="Sorry, I think you have the wrong number.",
# # #                     reply="Sorry, I think you have the wrong number."
# # #                     # extractedIntelligence=current_intel
# # #                 )
# # #         else:
# # #              # Fallback if 2 retries failed
# # #              return AgentResponse(
# # #                 status="success",
# # #                 # scamDetected=False,
# # #                 # response_text="Hello? Who is this?",
# # #                 reply="Hello? Who is this?"
# # #                 # extractedIntelligence=current_intel
# # #             )
# # # #-----------------------------------------------------------------------------------------------------------
# # #     else:
# # #         # If scam was ALREADY confirmed in previous turns, we keep the previous status
# # #         # Ideally, we should persist the 'behavior_summary' in Redis too, 
# # #         # but for now, let's set a generic active note or retrieve from Redis if we added that field.
# # #         # For this Hackathon step, let's keep it simple:
# # #         current_agent_notes = "Scam previously detected. Engaging agent."

# # #     # 3. Intelligence Extraction

# # # #---------------------------------------------------------------------------------------------------------------
# # #     # try:
# # #     #     extractor = get_extractor_agent()
# # #     #     raw_intel = extractor.run(user_text).content
# # #     #     new_intel_dict = json.loads(clean_json_str(raw_intel))
        
# # #     #     # Merge
# # #     #     new_intel_model = ExtractedIntelligence(**new_intel_dict)
# # #     #     current_intel = state_service.update_intelligence(session_id, new_intel_model)
# # #     # except Exception as e:
# # #     #     logger.error(f"Extraction failed: {e}")
# # #     #     # Continue without updating intel - do not crash

# # #     try:
# # #         extractor = get_extractor_agent()
# # #         new_intel_dict = {}
        
# # #         # RETRY LOGIC
# # #         for attempt in range(2):
# # #             try:
# # #                 raw_intel = extractor.run(user_text).content
# # #                 new_intel_dict = json.loads(clean_json_str(raw_intel))
# # #                 break
# # #             except json.JSONDecodeError:
# # #                  logger.warning(f"Extractor JSON failed (Attempt {attempt+1}). Retrying...")
        
# # #         if new_intel_dict:
# # #             # Merge
# # #             new_intel_model = ExtractedIntelligence(**new_intel_dict)
# # #             current_intel = state_service.update_intelligence(session_id, new_intel_model)
            
# # #     except Exception as e:
# # #         logger.error(f"Extraction logic error: {e}")
# # #         # Continue without updating intel - do not crash

# # # #-------------------------------------------------------------------------------------------------------------------

# # #     # 4. Generate Persona Response
# # #     try:
# # #         agno_history = format_history_for_agno(payload.conversationHistory)
# # #         persona = get_persona_agent()
# # #         response_obj = persona.run(user_text, messages=agno_history)
# # #         agent_reply_text = response_obj.content
# # #     except Exception as e:
# # #         logger.error(f"Persona Generation Failed: {e}")
# # #         agent_reply_text = "I am having trouble hearing you. Can you say that again?"

# # #     # 5. Metrics & Termination Logic
# # #     total_messages = len(payload.conversationHistory) + 2
# # #     engagement_metrics = EngagementMetrics(
# # #         totalMessagesExchanged=total_messages,
# # #         engagementDurationSeconds=total_messages * 30
# # #     )
    
# # #     # has_critical_intel = (
# # #     #     len(current_intel.bankAccounts) > 0 or 
# # #     #     len(current_intel.upiIds) > 0 or
# # #     #     len(current_intel.phoneNumbers) > 0
# # #     # )

# # #     # # STRICTER TERMINATION LOGIC
# # #     # # 1. Filter bank accounts: We only want accounts with digits (e.g., "50100..."), not just "SBI".
# # #     # valid_bank_accounts = [acc for acc in current_intel.bankAccounts if any(char.isdigit() for char in acc)]
    
# # #     # has_critical_intel = (
# # #     #     len(valid_bank_accounts) > 0 or 
# # #     #     len(current_intel.upiIds) > 0 or
# # #     #     len(current_intel.phoneNumbers) > 0 or
# # #     #     len(current_intel.phishingLinks) > 0 # Added Phishing Links check
# # #     # )

# # #     # STRICTER TERMINATION LOGIC
# # #     # 1. Filter bank accounts: Must be at least 9 digits to be a real account number.
# # #     valid_bank_accounts = [
# # #         acc for acc in current_intel.bankAccounts 
# # #         if len(re.sub(r"\D", "", acc)) >= 9 # Count only digits, must be >= 9
# # #     ]
    
# # #     # 2. Filter Phone Numbers: Must be at least 10 digits
# # #     valid_phone_numbers = [
# # #         phone for phone in current_intel.phoneNumbers
# # #         if len(re.sub(r"\D", "", phone)) >= 10
# # #     ]

# # #     has_critical_intel = (
# # #         len(valid_bank_accounts) > 0 or 
# # #         len(current_intel.upiIds) > 0 or
# # #         len(valid_phone_numbers) > 0 or
# # #         len(current_intel.phishingLinks) > 0
# # #     )

# # #     is_long_convo = total_messages > 15
    
# # #     if is_scam_confirmed and (has_critical_intel or is_long_convo):
# # #         if not state_service.is_conversation_complete(session_id):
# # #             state_service.mark_conversation_complete(session_id)
            
# # #             final_payload = {
# # #                 "sessionId": session_id,
# # #                 "scamDetected": True,
# # #                 "totalMessagesExchanged": total_messages,
# # #                 "extractedIntelligence": current_intel.model_dump(),
# # #                 "agentNotes": "Autonomous engagement completed."
# # #             }
# # #             background_tasks.add_task(callback_service.send_final_report, final_payload)
# # #             logger.info(f"Session {session_id}: Scheduled final callback.")

# # #     # 6. Return Response
# # #     return AgentResponse(
# # #         status="success",
# # #         # scamDetected=is_scam_confirmed,
# # #         # extractedIntelligence=current_intel,
# # #         # engagementMetrics=engagement_metrics,
# # #         # agentNotes="Engaging...",
# # #         # agentNotes=current_agent_notes,
# # #         # response_text=agent_reply_text # Fixed field name
# # #         reply=agent_reply_text 
# # #     )


# # # # --- DEBUG HANDLER (ADD THIS) ---
# # # @app.exception_handler(RequestValidationError)
# # # async def validation_exception_handler(request: Request, exc: RequestValidationError):
# # #     """
# # #     If GUVI sends invalid JSON, this logs exactly what they sent 
# # #     so we can fix our schema.
# # #     """
# # #     body = await request.body()
# # #     error_msg = f"VALIDATION ERROR: {exc}"
# # #     body_content = body.decode()
# # #     logger.error("--- 422 ERROR DEBUG ---")
# # #     logger.error(error_msg)
# # #     logger.error(f"INCOMING BODY: {body_content}")
# # #     logger.error("-----------------------")
# # #     return JSONResponse(
# # #         status_code=422,
# # #         content={"detail": str(exc), "body_received": body_content},
# # #     )

# # # state_service = StateService()


# # #---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# # #---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# # # import logging
# # # from fastapi import FastAPI, Header, HTTPException, BackgroundTasks, Depends, Security 
# # # from typing import Optional

# # # from app.core.security import verify_api_key

# # # from agno.agent import Agent
# # # from agno.models.groq import Groq

# # # # Import internals
# # # from app.core.config import settings
# # # from app.models.api_schemas import (
# # #     IncomingMessage, AgentResponse, MessageItem, EngagementMetrics
# # # )
# # # from app.services.state import StateService
# # # from app.services.callback import callback_service
# # # # from app.agents.detector import get_detector_agent, ScamDetectionResult
# # # from app.agents.detector import get_detector_agent
# # # from app.agents.persona import get_persona_agent
# # # from app.agents.extractor import get_extractor_agent

# # # import json
# # # import re


# # # # Logging Setup
# # # logging.basicConfig(level=logging.INFO)
# # # logger = logging.getLogger("guvi-honeypot")

# # # app = FastAPI(title="Guvi Honeypot Agent")
# # # state_service = StateService()

# # # # --- Helpers ---

# # # # def verify_api_key(x_api_key: str = Header(...)):
# # # #     if x_api_key != settings.API_KEY:
# # # #         raise HTTPException(status_code=401, detail="Invalid API Key")

# # # def format_history_for_agno(history: list[MessageItem]) -> list[dict]:
# # #     """Convert GUVI history to Agno message format."""
# # #     formatted = []
# # #     for msg in history:
# # #         role = "user" if msg.sender == "scammer" else "assistant"
# # #         formatted.append({"role": role, "content": msg.text})
# # #     return formatted

# # # # Helper to clean LLM JSON output (handles markdown blocks if they slip through)
# # # def clean_json_str(raw_str: str) -> str:
# # #     # Remove json and  if present
# # #     cleaned = re.sub(r"json\s*", "", raw_str)
# # #     cleaned = re.sub(r"\s*$", "", cleaned)
# # #     return cleaned.strip()

# # # # --- Core Endpoint ---
# # # # @app.post("/api/chat", response_model=AgentResponse)
# # # # async def chat_endpoint(
# # # #     payload: IncomingMessage,
# # # #     background_tasks: BackgroundTasks,
# # # #     # x_api_key: str = Depends(verify_api_key)
# # # #     x_api_key: str = Security(verify_api_key)

# # # # ):
# # # #     session_id = payload.sessionId
# # # #     user_text = payload.message.text
    
# # # #     # 1. Load State
# # # #     is_scam_confirmed = state_service.get_scam_status(session_id)
# # # #     current_intel = state_service.get_extracted_intelligence(session_id)
    
# # # #     # 2. Scam Detection (If not yet confirmed)
# # # #     if not is_scam_confirmed:
# # # #         # Fast Detector
# # # #         detector = get_detector_agent()
# # # #         # We only feed the LATEST message to the detector for speed
# # # #         detection: ScamDetectionResult = detector.run(user_text).content
        
# # # #         if detection.is_scam:
# # # #             is_scam_confirmed = True
# # # #             state_service.set_scam_status(session_id, True)
# # # #             logger.info(f"Session {session_id}: SCAM DETECTED. Reason: {detection.reasoning}")
# # # #         else:
# # # #             # If safe, return a generic "Wrong number" response immediately
# # # #             # We don't engage the persona yet to save costs/latency
# # # #             return AgentResponse(
# # # #                 status="success",
# # # #                 scamDetected=False,
# # # #                 response_text="Sorry, I think you have the wrong number.",
# # # #                 extractedIntelligence=current_intel
# # # #             )

# # # #     # 3. Intelligence Extraction (Async - Fire & Forget style logic, but awaited for data integrity)
# # # #     # We extract from the CURRENT message
# # # #     extractor = get_extractor_agent()
# # # #     # Run extractor
# # # #     new_intel_resp = extractor.run(user_text)
# # # #     # Merge & Save
# # # #     if new_intel_resp.content:
# # # #         current_intel = state_service.update_intelligence(session_id, new_intel_resp.content)

# # # #     # 4. Generate Persona Response
# # # #     # Convert history + current message
# # # #     agno_history = format_history_for_agno(payload.conversationHistory)
# # # #     # Add the current message explicitly if it's not in history yet (GUVI usually sends history excluding current)
# # # #     # Safety check: if history is empty, it's the first message.
    
# # # #     persona = get_persona_agent()
# # # #     # We inject the full history + current user message into the run
# # # #     # Note: Agno's .run() handles the current message. We prepended history.
# # # #     response_obj = persona.run(
# # # #         user_text,
# # # #         messages=agno_history 
# # # #     )
# # # #     agent_reply_text = response_obj.content

# # # #     # 5. Metrics & Termination Logic
# # # #     # Calculate simple metrics
# # # #     total_messages = len(payload.conversationHistory) + 2 # History + User + Agent
# # # #     engagement_metrics = EngagementMetrics(
# # # #         totalMessagesExchanged=total_messages,
# # # #         engagementDurationSeconds=total_messages * 30 # Rough estimate
# # # #     )
    
# # # #     # Check Termination Heuristics
# # # #     has_critical_intel = (
# # # #         len(current_intel.bankAccounts) > 0 or 
# # # #         len(current_intel.upiIds) > 0 or
# # # #         len(current_intel.phoneNumbers) > 0
# # # #     )
# # # #     is_long_convo = total_messages > 15
    
# # # #     # If we have enough intel OR it's getting too long, report it.
# # # #     # Also ensure we haven't reported it already.
# # # #     if is_scam_confirmed and (has_critical_intel or is_long_convo):
# # # #         if not state_service.is_conversation_complete(session_id):
# # # #             state_service.mark_conversation_complete(session_id)
            
# # # #             # Prepare Final Callback Payload
# # # #             final_payload = {
# # # #                 "sessionId": session_id,
# # # #                 "scamDetected": True,
# # # #                 "totalMessagesExchanged": total_messages,
# # # #                 "extractedIntelligence": current_intel.model_dump(),
# # # #                 "agentNotes": "Autonomous engagement completed. Intelligence extracted."
# # # #             }
# # # #             # Schedule Background Task
# # # #             background_tasks.add_task(callback_service.send_final_report, final_payload)
# # # #             logger.info(f"Session {session_id}: Scheduled final callback.")

# # # #     # 6. Return Response to GUVI
# # # #     return AgentResponse(
# # # #         status="success",
# # # #         scamDetected=is_scam_confirmed,
# # # #         extractedIntelligence=current_intel,
# # # #         engagementMetrics=engagement_metrics,
# # # #         agentNotes="Engaging...",
# # # #         response_text=agent_reply_text
# # # #     )

# # # @app.post("/api/chat", response_model=AgentResponse)
# # # async def chat_endpoint(
# # #     payload: IncomingMessage,
# # #     background_tasks: BackgroundTasks,
# # #     x_api_key: str = Security(verify_api_key)
# # # ):
# # #     session_id = payload.sessionId
# # #     user_text = payload.message.text
    
# # #     # 1. Load State
# # #     is_scam_confirmed = state_service.get_scam_status(session_id)
# # #     current_intel = state_service.get_extracted_intelligence(session_id)
    
# # #     # 2. Scam Detection (If not yet confirmed)
# # #     if not is_scam_confirmed:
# # #         detector = get_detector_agent()
# # #         # Run detector (returns string now)
# # #         raw_response = detector.run(user_text).content
        
# # #         try:
# # #             detection_data = json.loads(clean_json_str(raw_response))
# # #             # Safe access with defaults
# # #             is_scam = detection_data.get("is_scam", False)
# # #             reasoning = detection_data.get("reasoning", "Unknown")
            
# # #             if is_scam:
# # #                 is_scam_confirmed = True
# # #                 state_service.set_scam_status(session_id, True)
# # #                 logger.info(f"Session {session_id}: SCAM DETECTED. Reason: {reasoning}")
# # #             else:
# # #                 return AgentResponse(
# # #                     status="success",
# # #                     scamDetected=False,
# # #                     responseText="Sorry, I think you have the wrong number.",
# # #                     extractedIntelligence=current_intel
# # #                 )
# # #         except json.JSONDecodeError:
# # #             # Fallback if JSON fails (Assume safe to be cautious, or scam if paranoid)
# # #             logger.error(f"Detector JSON failed: {raw_response}")
# # #             # For hackathon: Assume safe to avoid breaking flow, or retry.
# # #             # Let's return generic safe response.
# # #             return AgentResponse(
# # #                 status="success",
# # #                 scamDetected=False,
# # #                 responseText="Hello? Who is this?",
# # #                 extractedIntelligence=current_intel
# # #             )

# # #     # 3. Intelligence Extraction
# # #     extractor = get_extractor_agent()
# # #     raw_intel = extractor.run(user_text).content
# # #     try:
# # #         new_intel_dict = json.loads(clean_json_str(raw_intel))
# # #         # Convert dict to Pydantic model for merging
# # #         from app.models.api_schemas import ExtractedIntelligence
# # #         new_intel_model = ExtractedIntelligence(**new_intel_dict)
# # #         current_intel = state_service.update_intelligence(session_id, new_intel_model)
# # #     except Exception as e:
# # #         logger.error(f"Extraction failed: {e}. Raw: {raw_intel}")
# # #         # Continue without updating intel

# # #     # 4. Generate Persona Response
# # #     agno_history = format_history_for_agno(payload.conversationHistory)
# # #     persona = get_persona_agent()
# # #     response_obj = persona.run(user_text, messages=agno_history)
# # #     agent_reply_text = response_obj.content

# # #     # 5. Metrics & Termination (Keep logic same as before)
# # #     total_messages = len(payload.conversationHistory) + 2
# # #     engagement_metrics = EngagementMetrics(
# # #         totalMessagesExchanged=total_messages,
# # #         engagementDurationSeconds=total_messages * 30
# # #     )
    
# # #     has_critical_intel = (
# # #         len(current_intel.bankAccounts) > 0 or 
# # #         len(current_intel.upiIds) > 0 or
# # #         len(current_intel.phoneNumbers) > 0
# # #     )
# # #     is_long_convo = total_messages > 15
    
# # #     if is_scam_confirmed and (has_critical_intel or is_long_convo):
# # #         if not state_service.is_conversation_complete(session_id):
# # #             state_service.mark_conversation_complete(session_id)
# # #             final_payload = {
# # #                 "sessionId": session_id,
# # #                 "scamDetected": True,
# # #                 "totalMessagesExchanged": total_messages,
# # #                 "extractedIntelligence": current_intel.model_dump(),
# # #                 "agentNotes": "Autonomous engagement completed."
# # #             }
# # #             background_tasks.add_task(callback_service.send_final_report, final_payload)
# # #             logger.info(f"Session {session_id}: Scheduled final callback.")

# # #     # 6. Return Response
# # #     return AgentResponse(
# # #         status="success",
# # #         scamDetected=is_scam_confirmed,
# # #         extractedIntelligence=current_intel,
# # #         engagementMetrics=engagement_metrics,
# # #         agentNotes="Engaging...",
# # #         response_text=agent_reply_text
# # #     )

# # import logging
# # import json
# # import re
# # import os
# # from dotenv import load_dotenv

# # #---------------------------------------------------------------------------------------------------------------
# # from fastapi.middleware.cors import CORSMiddleware # <--- 1. Add Import
# # #---------------------------------------------------------------------------------------------------------------

# # # 1. FORCE LOAD .ENV for Windows/Agno compatibility
# # load_dotenv()

# # from fastapi import FastAPI, Header, HTTPException, BackgroundTasks, Depends, Security
# # from typing import Optional

# # from agno.agent import Agent
# # from agno.models.groq import Groq

# # # Import internals
# # from app.core.config import settings
# # from app.core.security import verify_api_key
# # from app.models.api_schemas import (
# #     IncomingMessage, AgentResponse, MessageItem, EngagementMetrics, ExtractedIntelligence
# # )
# # from app.services.state import StateService
# # from app.services.callback import callback_service
# # from app.agents.detector import get_detector_agent
# # from app.agents.persona import get_persona_agent
# # from app.agents.extractor import get_extractor_agent

# # #------------------------------------------------------------------------------------------------------------
# # from fastapi.exceptions import RequestValidationError
# # from fastapi import Request
# # from fastapi.responses import JSONResponse
# # #------------------------------------------------------------------------------------------------------------


# # # Logging Setup
# # logging.basicConfig(level=logging.INFO)
# # logger = logging.getLogger("guvi-honeypot")

# # app = FastAPI(title="Guvi Honeypot Agent")
# # # --- 2. Add this block IMMEDIATELY after app = FastAPI(...) ---
# # app.add_middleware(
# #     CORSMiddleware,
# #     allow_origins=["*"],  # Allows ALL domains (Critical for Hackathon Testers)
# #     allow_credentials=True,
# #     allow_methods=["*"],
# #     allow_headers=["*"],
# # )
# # # -----------------------------------------------------------
# # state_service = StateService()

# # # --- Helpers ---
# # def format_history_for_agno(history: list[MessageItem]) -> list[dict]:
# #     """Convert GUVI history to Agno message format."""
# #     formatted = []
# #     for msg in history:
# #         role = "user" if msg.sender == "scammer" else "assistant"
# #         formatted.append({"role": role, "content": msg.text})
# #     return formatted

# # def clean_json_str(raw_str: str) -> str:
# #     # Remove ```json and ``` if present
# #     cleaned = re.sub(r"```json\s*", "", raw_str)
# #     cleaned = re.sub(r"```\s*$", "", cleaned)
# #     return cleaned.strip()

# # #-------------------------------------------------------------------------------------------------

# # @app.get("/health")
# # async def health_check():
# #     return {"status": "active", "service": "guvi-honeypot"}

# # #-------------------------------------------------------------------------------------------------

# # # --- Core Endpoint ---
# # @app.post("/api/chat", response_model=AgentResponse)
# # async def chat_endpoint(
# #     payload: IncomingMessage,
# #     background_tasks: BackgroundTasks,
# #     x_api_key: str = Security(verify_api_key)
# # ):
# #     session_id = payload.sessionId
# #     user_text = payload.message.text
    
# #     # 1. Load State
# #     is_scam_confirmed = state_service.get_scam_status(session_id)
# #     current_intel = state_service.get_extracted_intelligence(session_id)
    
# #     # # 2. Scam Detection (If not yet confirmed)
# #     # if not is_scam_confirmed:
# #     #     detector = get_detector_agent()
# #     #     # Run detector
# #     #     try:
# #     #         raw_response = detector.run(user_text).content
# #     #         detection_data = json.loads(clean_json_str(raw_response))
            
# #     #         # Safe access
# #     #         is_scam = detection_data.get("is_scam", False)
# #     #         reasoning = detection_data.get("reasoning", "Unknown")
            
# #     #         if is_scam:
# #     #             is_scam_confirmed = True
# #     #             state_service.set_scam_status(session_id, True)
# #     #             logger.info(f"Session {session_id}: SCAM DETECTED. Reason: {reasoning}")
# #     #         else:
# #     #             return AgentResponse(
# #     #                 status="success",
# #     #                 scamDetected=False,
# #     #                 response_text="Sorry, I think you have the wrong number.", # Fixed field name
# #     #                 extractedIntelligence=current_intel
# #     #             )
# #     #     except Exception as e:
# #     #         # Fallback if JSON fails or LLM errors
# #     #         logger.error(f"Detector Failed: {e}")
# #     #         # Safe fallback
# #     #         return AgentResponse(
# #     #             status="success",
# #     #             scamDetected=False,
# #     #             response_text="Hello? Who is this?", # Fixed field name
# #     #             extractedIntelligence=current_intel
# #     #         )
    

# #     # 2. Scam Detection (If not yet confirmed)
# #     # We initialize agent_notes with a default, but try to overwrite it from detector
# #     current_agent_notes = "Monitoring conversation..." 

# # #-----------------------------------------------------------------------------------------------------------   
# #     # if not is_scam_confirmed:
# #     #     detector = get_detector_agent()
# #     #     try:
# #     #         raw_response = detector.run(user_text).content
# #     #         detection_data = json.loads(clean_json_str(raw_response))
            
# #     #         is_scam = detection_data.get("is_scam", False)
# #     #         reasoning = detection_data.get("reasoning", "Unknown")
# #     #         # NEW: Capture dynamic notes
# #     #         behavior_summary = detection_data.get("behavior_summary", "Scam intent detected.")
            
# #     #         if is_scam:
# #     #             is_scam_confirmed = True
# #     #             state_service.set_scam_status(session_id, True)
# #     #             current_agent_notes = behavior_summary # Update notes
# #     #             logger.info(f"Session {session_id}: SCAM DETECTED. Notes: {behavior_summary}")
# #     #         else:
# #     #             return AgentResponse(
# #     #                 status="success",
# #     #                 scamDetected=False,
# #     #                 response_text="Sorry, I think you have the wrong number.",
# #     #                 extractedIntelligence=current_intel
# #     #             )
# #     #     except Exception as e:
# #     #         logger.error(f"Detector Failed: {e}")
# #     #         return AgentResponse(
# #     #             status="success",
# #     #             scamDetected=False,
# #     #             response_text="Hello? Who is this?",
# #     #             extractedIntelligence=current_intel
# #     #         )

# #     if not is_scam_confirmed:
# #         detector = get_detector_agent()
# #         detection_data = {}
        
# #         # RETRY LOGIC: Try twice to get valid JSON
# #         for attempt in range(2):
# #             try:
# #                 raw_response = detector.run(user_text).content
# #                 detection_data = json.loads(clean_json_str(raw_response))
# #                 break # Success! Exit loop
# #             except json.JSONDecodeError:
# #                 logger.warning(f"Detector JSON failed (Attempt {attempt+1}). Retrying...")
# #                 if attempt == 1: # If last attempt failed
# #                     logger.error(f"Detector Failed completely.")
        
# #         # Proceed only if we got data
# #         if detection_data:
# #             # Safe access
# #             is_scam = detection_data.get("is_scam", False)
# #             reasoning = detection_data.get("reasoning", "Unknown")
# #             behavior_summary = detection_data.get("behavior_summary", "Scam intent detected.")
            
# #             if is_scam:
# #                 is_scam_confirmed = True
# #                 state_service.set_scam_status(session_id, True)
# #                 current_agent_notes = behavior_summary 
# #                 logger.info(f"Session {session_id}: SCAM DETECTED. Notes: {behavior_summary}")
# #             else:
# #                 return AgentResponse(
# #                     status="success",
# #                     # scamDetected=False,
# #                     # response_text="Sorry, I think you have the wrong number.",
# #                     reply="Sorry, I think you have the wrong number."
# #                     # extractedIntelligence=current_intel
# #                 )
# #         else:
# #              # Fallback if 2 retries failed
# #              return AgentResponse(
# #                 status="success",
# #                 # scamDetected=False,
# #                 # response_text="Hello? Who is this?",
# #                 reply="Hello? Who is this?"
# #                 # extractedIntelligence=current_intel
# #             )
# # #-----------------------------------------------------------------------------------------------------------
# #     else:
# #         # If scam was ALREADY confirmed in previous turns, we keep the previous status
# #         # Ideally, we should persist the 'behavior_summary' in Redis too, 
# #         # but for now, let's set a generic active note or retrieve from Redis if we added that field.
# #         # For this Hackathon step, let's keep it simple:
# #         current_agent_notes = "Scam previously detected. Engaging agent."

# #     # 3. Intelligence Extraction

# # #---------------------------------------------------------------------------------------------------------------
# #     # try:
# #     #     extractor = get_extractor_agent()
# #     #     raw_intel = extractor.run(user_text).content
# #     #     new_intel_dict = json.loads(clean_json_str(raw_intel))
        
# #     #     # Merge
# #     #     new_intel_model = ExtractedIntelligence(**new_intel_dict)
# #     #     current_intel = state_service.update_intelligence(session_id, new_intel_model)
# #     # except Exception as e:
# #     #     logger.error(f"Extraction failed: {e}")
# #     #     # Continue without updating intel - do not crash

# #     try:
# #         extractor = get_extractor_agent()
# #         new_intel_dict = {}
        
# #         # RETRY LOGIC
# #         for attempt in range(2):
# #             try:
# #                 raw_intel = extractor.run(user_text).content
# #                 new_intel_dict = json.loads(clean_json_str(raw_intel))
# #                 break
# #             except json.JSONDecodeError:
# #                  logger.warning(f"Extractor JSON failed (Attempt {attempt+1}). Retrying...")
        
# #         if new_intel_dict:
# #             # Merge
# #             new_intel_model = ExtractedIntelligence(**new_intel_dict)
# #             current_intel = state_service.update_intelligence(session_id, new_intel_model)
            
# #     except Exception as e:
# #         logger.error(f"Extraction logic error: {e}")
# #         # Continue without updating intel - do not crash

# # #-------------------------------------------------------------------------------------------------------------------

# #     # 4. Generate Persona Response
# #     try:
# #         agno_history = format_history_for_agno(payload.conversationHistory)
# #         persona = get_persona_agent()
# #         response_obj = persona.run(user_text, messages=agno_history)
# #         agent_reply_text = response_obj.content
# #     except Exception as e:
# #         logger.error(f"Persona Generation Failed: {e}")
# #         agent_reply_text = "I am having trouble hearing you. Can you say that again?"

# # #-------------------------------------------------------------------------------------------------------------------
# #     # # 5. Metrics & Termination Logic
# #     # total_messages = len(payload.conversationHistory) + 2
# #     # engagement_metrics = EngagementMetrics(
# #     #     totalMessagesExchanged=total_messages,
# #     #     engagementDurationSeconds=total_messages * 30
# #     # )
    
# #     # # has_critical_intel = (
# #     # #     len(current_intel.bankAccounts) > 0 or 
# #     # #     len(current_intel.upiIds) > 0 or
# #     # #     len(current_intel.phoneNumbers) > 0
# #     # # )

# #     # # # STRICTER TERMINATION LOGIC
# #     # # # 1. Filter bank accounts: We only want accounts with digits (e.g., "50100..."), not just "SBI".
# #     # # valid_bank_accounts = [acc for acc in current_intel.bankAccounts if any(char.isdigit() for char in acc)]
    
# #     # # has_critical_intel = (
# #     # #     len(valid_bank_accounts) > 0 or 
# #     # #     len(current_intel.upiIds) > 0 or
# #     # #     len(current_intel.phoneNumbers) > 0 or
# #     # #     len(current_intel.phishingLinks) > 0 # Added Phishing Links check
# #     # # )

# #     # # STRICTER TERMINATION LOGIC
# #     # # 1. Filter bank accounts: Must be at least 9 digits to be a real account number.
# #     # valid_bank_accounts = [
# #     #     acc for acc in current_intel.bankAccounts 
# #     #     if len(re.sub(r"\D", "", acc)) >= 9 # Count only digits, must be >= 9
# #     # ]
    
# #     # # 2. Filter Phone Numbers: Must be at least 10 digits
# #     # valid_phone_numbers = [
# #     #     phone for phone in current_intel.phoneNumbers
# #     #     if len(re.sub(r"\D", "", phone)) >= 10
# #     # ]

# #     # has_critical_intel = (
# #     #     len(valid_bank_accounts) > 0 or 
# #     #     len(current_intel.upiIds) > 0 or
# #     #     len(valid_phone_numbers) > 0 or
# #     #     len(current_intel.phishingLinks) > 0
# #     # )

# #     # is_long_convo = total_messages > 15
    
# #     # if is_scam_confirmed and (has_critical_intel or is_long_convo):
# #     #     if not state_service.is_conversation_complete(session_id):
# #     #         state_service.mark_conversation_complete(session_id)
            
# #     #         final_payload = {
# #     #             "sessionId": session_id,
# #     #             "scamDetected": True,
# #     #             "totalMessagesExchanged": total_messages,
# #     #             "extractedIntelligence": current_intel.model_dump(),
# #     #             "agentNotes": "Autonomous engagement completed."
# #     #         }
# #     #         background_tasks.add_task(callback_service.send_final_report, final_payload)
# #     #         logger.info(f"Session {session_id}: Scheduled final callback.")



# # # ... inside chat_endpoint function ...

# #     # 5. Metrics & Termination Logic
# #     total_messages = len(payload.conversationHistory) + 2
# #     engagement_metrics = EngagementMetrics(
# #         totalMessagesExchanged=total_messages,
# #         engagementDurationSeconds=total_messages * 30
# #     )
    
# #     # --- PHASE 2: SINGLE REPORTING LOGIC ---
# #     # Constraint Checklist:
# #     # 1. No hardcoded turn thresholds.
# #     # 2. No intelligence-count thresholds.
# #     # 3. Must NOT miss callback if conversation ends early.
# #     # 4. Must ensure EXACTLY ONE callback.
    
# #     # We report the MOMENT scam is confirmed, if we haven't reported yet.
# #     # This guarantees we capture the session even if the evaluator stops immediately.
    
# #     if is_scam_confirmed:
# #         if not state_service.is_conversation_complete(session_id):
# #             # LOCK: Mark as reported to ensure exactly one callback
# #             state_service.mark_conversation_complete(session_id)
            
# #             final_payload = {
# #                 "sessionId": session_id,
# #                 "scamDetected": True,
# #                 "totalMessagesExchanged": total_messages,
# #                 "extractedIntelligence": current_intel.model_dump(),
# #                 "agentNotes": "Scam detected. Intelligence reported. Engagement continuing."
# #             }
# #             background_tasks.add_task(callback_service.send_final_report, final_payload)
# #             logger.info(f"Session {session_id}: First detection - Callback Triggered.")
# #         else:
# #             logger.info(f"Session {session_id}: Scam already reported. Continuing accumulation.")

# # #---------------------------------------------------------------------------------------------------------------------------------------

# #     # 6. Return Response
# #     return AgentResponse(
# #         status="success",
# #         # scamDetected=is_scam_confirmed,
# #         # extractedIntelligence=current_intel,
# #         # engagementMetrics=engagement_metrics,
# #         # agentNotes="Engaging...",
# #         # agentNotes=current_agent_notes,
# #         # response_text=agent_reply_text # Fixed field name
# #         reply=agent_reply_text 
# #     )


# # # --- DEBUG HANDLER (ADD THIS) ---
# # @app.exception_handler(RequestValidationError)
# # async def validation_exception_handler(request: Request, exc: RequestValidationError):
# #     """
# #     If GUVI sends invalid JSON, this logs exactly what they sent 
# #     so we can fix our schema.
# #     """
# #     body = await request.body()
# #     error_msg = f"VALIDATION ERROR: {exc}"
# #     body_content = body.decode()
# #     logger.error("--- 422 ERROR DEBUG ---")
# #     logger.error(error_msg)
# #     logger.error(f"INCOMING BODY: {body_content}")
# #     logger.error("-----------------------")
# #     return JSONResponse(
# #         status_code=422,
# #         content={"detail": str(exc), "body_received": body_content},
# #     )

# # state_service = StateService()

# #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# # import logging
# # from fastapi import FastAPI, Header, HTTPException, BackgroundTasks, Depends, Security 
# # from typing import Optional

# # from app.core.security import verify_api_key

# # from agno.agent import Agent
# # from agno.models.groq import Groq

# # # Import internals
# # from app.core.config import settings
# # from app.models.api_schemas import (
# #     IncomingMessage, AgentResponse, MessageItem, EngagementMetrics
# # )
# # from app.services.state import StateService
# # from app.services.callback import callback_service
# # # from app.agents.detector import get_detector_agent, ScamDetectionResult
# # from app.agents.detector import get_detector_agent
# # from app.agents.persona import get_persona_agent
# # from app.agents.extractor import get_extractor_agent

# # import json
# # import re


# # # Logging Setup
# # logging.basicConfig(level=logging.INFO)
# # logger = logging.getLogger("guvi-honeypot")

# # app = FastAPI(title="Guvi Honeypot Agent")
# # state_service = StateService()

# # # --- Helpers ---

# # # def verify_api_key(x_api_key: str = Header(...)):
# # #     if x_api_key != settings.API_KEY:
# # #         raise HTTPException(status_code=401, detail="Invalid API Key")

# # def format_history_for_agno(history: list[MessageItem]) -> list[dict]:
# #     """Convert GUVI history to Agno message format."""
# #     formatted = []
# #     for msg in history:
# #         role = "user" if msg.sender == "scammer" else "assistant"
# #         formatted.append({"role": role, "content": msg.text})
# #     return formatted

# # # Helper to clean LLM JSON output (handles markdown blocks if they slip through)
# # def clean_json_str(raw_str: str) -> str:
# #     # Remove json and  if present
# #     cleaned = re.sub(r"json\s*", "", raw_str)
# #     cleaned = re.sub(r"\s*$", "", cleaned)
# #     return cleaned.strip()

# # # --- Core Endpoint ---
# # # @app.post("/api/chat", response_model=AgentResponse)
# # # async def chat_endpoint(
# # #     payload: IncomingMessage,
# # #     background_tasks: BackgroundTasks,
# # #     # x_api_key: str = Depends(verify_api_key)
# # #     x_api_key: str = Security(verify_api_key)

# # # ):
# # #     session_id = payload.sessionId
# # #     user_text = payload.message.text
    
# # #     # 1. Load State
# # #     is_scam_confirmed = state_service.get_scam_status(session_id)
# # #     current_intel = state_service.get_extracted_intelligence(session_id)
    
# # #     # 2. Scam Detection (If not yet confirmed)
# # #     if not is_scam_confirmed:
# # #         # Fast Detector
# # #         detector = get_detector_agent()
# # #         # We only feed the LATEST message to the detector for speed
# # #         detection: ScamDetectionResult = detector.run(user_text).content
        
# # #         if detection.is_scam:
# # #             is_scam_confirmed = True
# # #             state_service.set_scam_status(session_id, True)
# # #             logger.info(f"Session {session_id}: SCAM DETECTED. Reason: {detection.reasoning}")
# # #         else:
# # #             # If safe, return a generic "Wrong number" response immediately
# # #             # We don't engage the persona yet to save costs/latency
# # #             return AgentResponse(
# # #                 status="success",
# # #                 scamDetected=False,
# # #                 response_text="Sorry, I think you have the wrong number.",
# # #                 extractedIntelligence=current_intel
# # #             )

# # #     # 3. Intelligence Extraction (Async - Fire & Forget style logic, but awaited for data integrity)
# # #     # We extract from the CURRENT message
# # #     extractor = get_extractor_agent()
# # #     # Run extractor
# # #     new_intel_resp = extractor.run(user_text)
# # #     # Merge & Save
# # #     if new_intel_resp.content:
# # #         current_intel = state_service.update_intelligence(session_id, new_intel_resp.content)

# # #     # 4. Generate Persona Response
# # #     # Convert history + current message
# # #     agno_history = format_history_for_agno(payload.conversationHistory)
# # #     # Add the current message explicitly if it's not in history yet (GUVI usually sends history excluding current)
# # #     # Safety check: if history is empty, it's the first message.
    
# # #     persona = get_persona_agent()
# # #     # We inject the full history + current user message into the run
# # #     # Note: Agno's .run() handles the current message. We prepended history.
# # #     response_obj = persona.run(
# # #         user_text,
# # #         messages=agno_history 
# # #     )
# # #     agent_reply_text = response_obj.content

# # #     # 5. Metrics & Termination Logic
# # #     # Calculate simple metrics
# # #     total_messages = len(payload.conversationHistory) + 2 # History + User + Agent
# # #     engagement_metrics = EngagementMetrics(
# # #         totalMessagesExchanged=total_messages,
# # #         engagementDurationSeconds=total_messages * 30 # Rough estimate
# # #     )
    
# # #     # Check Termination Heuristics
# # #     has_critical_intel = (
# # #         len(current_intel.bankAccounts) > 0 or 
# # #         len(current_intel.upiIds) > 0 or
# # #         len(current_intel.phoneNumbers) > 0
# # #     )
# # #     is_long_convo = total_messages > 15
    
# # #     # If we have enough intel OR it's getting too long, report it.
# # #     # Also ensure we haven't reported it already.
# # #     if is_scam_confirmed and (has_critical_intel or is_long_convo):
# # #         if not state_service.is_conversation_complete(session_id):
# # #             state_service.mark_conversation_complete(session_id)
            
# # #             # Prepare Final Callback Payload
# # #             final_payload = {
# # #                 "sessionId": session_id,
# # #                 "scamDetected": True,
# # #                 "totalMessagesExchanged": total_messages,
# # #                 "extractedIntelligence": current_intel.model_dump(),
# # #                 "agentNotes": "Autonomous engagement completed. Intelligence extracted."
# # #             }
# # #             # Schedule Background Task
# # #             background_tasks.add_task(callback_service.send_final_report, final_payload)
# # #             logger.info(f"Session {session_id}: Scheduled final callback.")

# # #     # 6. Return Response to GUVI
# # #     return AgentResponse(
# # #         status="success",
# # #         scamDetected=is_scam_confirmed,
# # #         extractedIntelligence=current_intel,
# # #         engagementMetrics=engagement_metrics,
# # #         agentNotes="Engaging...",
# # #         response_text=agent_reply_text
# # #     )

# # @app.post("/api/chat", response_model=AgentResponse)
# # async def chat_endpoint(
# #     payload: IncomingMessage,
# #     background_tasks: BackgroundTasks,
# #     x_api_key: str = Security(verify_api_key)
# # ):
# #     session_id = payload.sessionId
# #     user_text = payload.message.text
    
# #     # 1. Load State
# #     is_scam_confirmed = state_service.get_scam_status(session_id)
# #     current_intel = state_service.get_extracted_intelligence(session_id)
    
# #     # 2. Scam Detection (If not yet confirmed)
# #     if not is_scam_confirmed:
# #         detector = get_detector_agent()
# #         # Run detector (returns string now)
# #         raw_response = detector.run(user_text).content
        
# #         try:
# #             detection_data = json.loads(clean_json_str(raw_response))
# #             # Safe access with defaults
# #             is_scam = detection_data.get("is_scam", False)
# #             reasoning = detection_data.get("reasoning", "Unknown")
            
# #             if is_scam:
# #                 is_scam_confirmed = True
# #                 state_service.set_scam_status(session_id, True)
# #                 logger.info(f"Session {session_id}: SCAM DETECTED. Reason: {reasoning}")
# #             else:
# #                 return AgentResponse(
# #                     status="success",
# #                     scamDetected=False,
# #                     responseText="Sorry, I think you have the wrong number.",
# #                     extractedIntelligence=current_intel
# #                 )
# #         except json.JSONDecodeError:
# #             # Fallback if JSON fails (Assume safe to be cautious, or scam if paranoid)
# #             logger.error(f"Detector JSON failed: {raw_response}")
# #             # For hackathon: Assume safe to avoid breaking flow, or retry.
# #             # Let's return generic safe response.
# #             return AgentResponse(
# #                 status="success",
# #                 scamDetected=False,
# #                 responseText="Hello? Who is this?",
# #                 extractedIntelligence=current_intel
# #             )

# #     # 3. Intelligence Extraction
# #     extractor = get_extractor_agent()
# #     raw_intel = extractor.run(user_text).content
# #     try:
# #         new_intel_dict = json.loads(clean_json_str(raw_intel))
# #         # Convert dict to Pydantic model for merging
# #         from app.models.api_schemas import ExtractedIntelligence
# #         new_intel_model = ExtractedIntelligence(**new_intel_dict)
# #         current_intel = state_service.update_intelligence(session_id, new_intel_model)
# #     except Exception as e:
# #         logger.error(f"Extraction failed: {e}. Raw: {raw_intel}")
# #         # Continue without updating intel

# #     # 4. Generate Persona Response
# #     agno_history = format_history_for_agno(payload.conversationHistory)
# #     persona = get_persona_agent()
# #     response_obj = persona.run(user_text, messages=agno_history)
# #     agent_reply_text = response_obj.content

# #     # 5. Metrics & Termination (Keep logic same as before)
# #     total_messages = len(payload.conversationHistory) + 2
# #     engagement_metrics = EngagementMetrics(
# #         totalMessagesExchanged=total_messages,
# #         engagementDurationSeconds=total_messages * 30
# #     )
    
# #     has_critical_intel = (
# #         len(current_intel.bankAccounts) > 0 or 
# #         len(current_intel.upiIds) > 0 or
# #         len(current_intel.phoneNumbers) > 0
# #     )
# #     is_long_convo = total_messages > 15
    
# #     if is_scam_confirmed and (has_critical_intel or is_long_convo):
# #         if not state_service.is_conversation_complete(session_id):
# #             state_service.mark_conversation_complete(session_id)
# #             final_payload = {
# #                 "sessionId": session_id,
# #                 "scamDetected": True,
# #                 "totalMessagesExchanged": total_messages,
# #                 "extractedIntelligence": current_intel.model_dump(),
# #                 "agentNotes": "Autonomous engagement completed."
# #             }
# #             background_tasks.add_task(callback_service.send_final_report, final_payload)
# #             logger.info(f"Session {session_id}: Scheduled final callback.")

# #     # 6. Return Response
# #     return AgentResponse(
# #         status="success",
# #         scamDetected=is_scam_confirmed,
# #         extractedIntelligence=current_intel,
# #         engagementMetrics=engagement_metrics,
# #         agentNotes="Engaging...",
# #         response_text=agent_reply_text
# #     )

# import logging
# import json
# import re
# import os
# from dotenv import load_dotenv

# #---------------------------------------------------------------------------------------------------------------
# from fastapi.middleware.cors import CORSMiddleware # <--- 1. Add Import
# #---------------------------------------------------------------------------------------------------------------

# # 1. FORCE LOAD .ENV for Windows/Agno compatibility
# load_dotenv()

# from fastapi import FastAPI, Header, HTTPException, BackgroundTasks, Depends, Security
# from typing import Optional

# from agno.agent import Agent
# from agno.models.groq import Groq

# # Import internals
# from app.core.config import settings
# from app.core.security import verify_api_key
# from app.models.api_schemas import (
#     IncomingMessage, AgentResponse, MessageItem, EngagementMetrics, ExtractedIntelligence
# )
# from app.services.state import StateService
# from app.services.callback import callback_service
# from app.agents.detector import get_detector_agent
# from app.agents.persona import get_persona_agent
# from app.agents.extractor import get_extractor_agent

# #------------------------------------------------------------------------------------------------------------
# from fastapi.exceptions import RequestValidationError
# from fastapi import Request
# from fastapi.responses import JSONResponse
# #------------------------------------------------------------------------------------------------------------


# # Logging Setup
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger("guvi-honeypot")

# app = FastAPI(title="Guvi Honeypot Agent")
# # --- 2. Add this block IMMEDIATELY after app = FastAPI(...) ---
# app.add_middleware(
#     CORSMiddleware,
#     allow_origins=["*"],  # Allows ALL domains (Critical for Hackathon Testers)
#     allow_credentials=True,
#     allow_methods=["*"],
#     allow_headers=["*"],
# )
# # -----------------------------------------------------------
# state_service = StateService()

# # --- Helpers ---
# def format_history_for_agno(history: list[MessageItem]) -> list[dict]:
#     """Convert GUVI history to Agno message format."""
#     formatted = []
#     for msg in history:
#         role = "user" if msg.sender == "scammer" else "assistant"
#         formatted.append({"role": role, "content": msg.text})
#     return formatted

# def clean_json_str(raw_str: str) -> str:
#     # Remove ```json and ``` if present
#     cleaned = re.sub(r"```json\s*", "", raw_str)
#     cleaned = re.sub(r"```\s*$", "", cleaned)
#     return cleaned.strip()

# #-------------------------------------------------------------------------------------------------

# @app.get("/health")
# async def health_check():
#     return {"status": "active", "service": "guvi-honeypot"}

# #-------------------------------------------------------------------------------------------------

# # --- Core Endpoint ---
# @app.post("/api/chat", response_model=AgentResponse)
# async def chat_endpoint(
#     payload: IncomingMessage,
#     background_tasks: BackgroundTasks,
#     x_api_key: str = Security(verify_api_key)
# ):
#     session_id = payload.sessionId
#     user_text = payload.message.text
    
#     # 1. Load State
#     is_scam_confirmed = state_service.get_scam_status(session_id)
#     current_intel = state_service.get_extracted_intelligence(session_id)
    
#     # # 2. Scam Detection (If not yet confirmed)
#     # if not is_scam_confirmed:
#     #     detector = get_detector_agent()
#     #     # Run detector
#     #     try:
#     #         raw_response = detector.run(user_text).content
#     #         detection_data = json.loads(clean_json_str(raw_response))
            
#     #         # Safe access
#     #         is_scam = detection_data.get("is_scam", False)
#     #         reasoning = detection_data.get("reasoning", "Unknown")
            
#     #         if is_scam:
#     #             is_scam_confirmed = True
#     #             state_service.set_scam_status(session_id, True)
#     #             logger.info(f"Session {session_id}: SCAM DETECTED. Reason: {reasoning}")
#     #         else:
#     #             return AgentResponse(
#     #                 status="success",
#     #                 scamDetected=False,
#     #                 response_text="Sorry, I think you have the wrong number.", # Fixed field name
#     #                 extractedIntelligence=current_intel
#     #             )
#     #     except Exception as e:
#     #         # Fallback if JSON fails or LLM errors
#     #         logger.error(f"Detector Failed: {e}")
#     #         # Safe fallback
#     #         return AgentResponse(
#     #             status="success",
#     #             scamDetected=False,
#     #             response_text="Hello? Who is this?", # Fixed field name
#     #             extractedIntelligence=current_intel
#     #         )
    

#     # 2. Scam Detection (If not yet confirmed)
#     # We initialize agent_notes with a default, but try to overwrite it from detector
#     current_agent_notes = "Monitoring conversation..." 

# #-----------------------------------------------------------------------------------------------------------   
#     # if not is_scam_confirmed:
#     #     detector = get_detector_agent()
#     #     try:
#     #         raw_response = detector.run(user_text).content
#     #         detection_data = json.loads(clean_json_str(raw_response))
            
#     #         is_scam = detection_data.get("is_scam", False)
#     #         reasoning = detection_data.get("reasoning", "Unknown")
#     #         # NEW: Capture dynamic notes
#     #         behavior_summary = detection_data.get("behavior_summary", "Scam intent detected.")
            
#     #         if is_scam:
#     #             is_scam_confirmed = True
#     #             state_service.set_scam_status(session_id, True)
#     #             current_agent_notes = behavior_summary # Update notes
#     #             logger.info(f"Session {session_id}: SCAM DETECTED. Notes: {behavior_summary}")
#     #         else:
#     #             return AgentResponse(
#     #                 status="success",
#     #                 scamDetected=False,
#     #                 response_text="Sorry, I think you have the wrong number.",
#     #                 extractedIntelligence=current_intel
#     #             )
#     #     except Exception as e:
#     #         logger.error(f"Detector Failed: {e}")
#     #         return AgentResponse(
#     #             status="success",
#     #             scamDetected=False,
#     #             response_text="Hello? Who is this?",
#     #             extractedIntelligence=current_intel
#     #         )

#     if not is_scam_confirmed:
#         detector = get_detector_agent()
#         detection_data = {}
        
#         # RETRY LOGIC: Try twice to get valid JSON
#         for attempt in range(2):
#             try:
#                 raw_response = detector.run(user_text).content
#                 detection_data = json.loads(clean_json_str(raw_response))
#                 break # Success! Exit loop
#             except json.JSONDecodeError:
#                 logger.warning(f"Detector JSON failed (Attempt {attempt+1}). Retrying...")
#                 if attempt == 1: # If last attempt failed
#                     logger.error(f"Detector Failed completely.")
        
#         # Proceed only if we got data
#         if detection_data:
#             # Safe access
#             is_scam = detection_data.get("is_scam", False)
#             reasoning = detection_data.get("reasoning", "Unknown")
#             behavior_summary = detection_data.get("behavior_summary", "Scam intent detected.")
            
#             if is_scam:
#                 is_scam_confirmed = True
#                 state_service.set_scam_status(session_id, True)
#                 current_agent_notes = behavior_summary 
#                 logger.info(f"Session {session_id}: SCAM DETECTED. Notes: {behavior_summary}")
#             else:
#                 return AgentResponse(
#                     status="success",
#                     # scamDetected=False,
#                     # response_text="Sorry, I think you have the wrong number.",
#                     reply="Sorry, I think you have the wrong number."
#                     # extractedIntelligence=current_intel
#                 )
#         else:
#              # Fallback if 2 retries failed
#              return AgentResponse(
#                 status="success",
#                 # scamDetected=False,
#                 # response_text="Hello? Who is this?",
#                 reply="Hello? Who is this?"
#                 # extractedIntelligence=current_intel
#             )
# #-----------------------------------------------------------------------------------------------------------
#     else:
#         # If scam was ALREADY confirmed in previous turns, we keep the previous status
#         # Ideally, we should persist the 'behavior_summary' in Redis too, 
#         # but for now, let's set a generic active note or retrieve from Redis if we added that field.
#         # For this Hackathon step, let's keep it simple:
#         current_agent_notes = "Scam previously detected. Engaging agent."

#     # 3. Intelligence Extraction

# #---------------------------------------------------------------------------------------------------------------
#     # try:
#     #     extractor = get_extractor_agent()
#     #     raw_intel = extractor.run(user_text).content
#     #     new_intel_dict = json.loads(clean_json_str(raw_intel))
        
#     #     # Merge
#     #     new_intel_model = ExtractedIntelligence(**new_intel_dict)
#     #     current_intel = state_service.update_intelligence(session_id, new_intel_model)
#     # except Exception as e:
#     #     logger.error(f"Extraction failed: {e}")
#     #     # Continue without updating intel - do not crash

#     try:
#         extractor = get_extractor_agent()
#         new_intel_dict = {}
        
#         # RETRY LOGIC
#         for attempt in range(2):
#             try:
#                 raw_intel = extractor.run(user_text).content
#                 new_intel_dict = json.loads(clean_json_str(raw_intel))
#                 break
#             except json.JSONDecodeError:
#                  logger.warning(f"Extractor JSON failed (Attempt {attempt+1}). Retrying...")
        
#         if new_intel_dict:
#             # Merge
#             new_intel_model = ExtractedIntelligence(**new_intel_dict)
#             current_intel = state_service.update_intelligence(session_id, new_intel_model)
            
#     except Exception as e:
#         logger.error(f"Extraction logic error: {e}")
#         # Continue without updating intel - do not crash

# #-------------------------------------------------------------------------------------------------------------------

#     # 4. Generate Persona Response
#     try:
#         agno_history = format_history_for_agno(payload.conversationHistory)
#         persona = get_persona_agent()
#         response_obj = persona.run(user_text, messages=agno_history)
#         agent_reply_text = response_obj.content
#     except Exception as e:
#         logger.error(f"Persona Generation Failed: {e}")
#         agent_reply_text = "I am having trouble hearing you. Can you say that again?"

# #-------------------------------------------------------------------------------------------------------------------
# #     # 5. Metrics & Termination Logic
# #     total_messages = len(payload.conversationHistory) + 2
# #     engagement_metrics = EngagementMetrics(
# #         totalMessagesExchanged=total_messages,
# #         engagementDurationSeconds=total_messages * 30
# #     )
    
# #     # has_critical_intel = (
# #     #     len(current_intel.bankAccounts) > 0 or 
# #     #     len(current_intel.upiIds) > 0 or
# #     #     len(current_intel.phoneNumbers) > 0
# #     # )

# #     # # STRICTER TERMINATION LOGIC
# #     # # 1. Filter bank accounts: We only want accounts with digits (e.g., "50100..."), not just "SBI".
# #     # valid_bank_accounts = [acc for acc in current_intel.bankAccounts if any(char.isdigit() for char in acc)]
    
# #     # has_critical_intel = (
# #     #     len(valid_bank_accounts) > 0 or 
# #     #     len(current_intel.upiIds) > 0 or
# #     #     len(current_intel.phoneNumbers) > 0 or
# #     #     len(current_intel.phishingLinks) > 0 # Added Phishing Links check
# #     # )

# #     # STRICTER TERMINATION LOGIC
# #     # 1. Filter bank accounts: Must be at least 9 digits to be a real account number.
# #     valid_bank_accounts = [
# #         acc for acc in current_intel.bankAccounts 
# #         if len(re.sub(r"\D", "", acc)) >= 9 # Count only digits, must be >= 9
# #     ]
    
# #     # 2. Filter Phone Numbers: Must be at least 10 digits
# #     valid_phone_numbers = [
# #         phone for phone in current_intel.phoneNumbers
# #         if len(re.sub(r"\D", "", phone)) >= 10
# #     ]

# #     has_critical_intel = (
# #         len(valid_bank_accounts) > 0 or 
# #         len(current_intel.upiIds) > 0 or
# #         len(valid_phone_numbers) > 0 or
# #         len(current_intel.phishingLinks) > 0
# #     )

# #     is_long_convo = total_messages > 15
    
# #     if is_scam_confirmed and (has_critical_intel or is_long_convo):
# #         if not state_service.is_conversation_complete(session_id):
# #             state_service.mark_conversation_complete(session_id)
            
# #             final_payload = {
# #                 "sessionId": session_id,
# #                 "scamDetected": True,
# #                 "totalMessagesExchanged": total_messages,
# #                 "extractedIntelligence": current_intel.model_dump(),
# #                 "agentNotes": "Autonomous engagement completed."
# #             }
# #             background_tasks.add_task(callback_service.send_final_report, final_payload)
# #             logger.info(f"Session {session_id}: Scheduled final callback.")



# # # # ... inside chat_endpoint function ...

# # #     # 5. Metrics & Termination Logic
# # #     total_messages = len(payload.conversationHistory) + 2
# # #     engagement_metrics = EngagementMetrics(
# # #         totalMessagesExchanged=total_messages,
# # #         engagementDurationSeconds=total_messages * 30
# # #     )
    
# # #     # --- PHASE 2: SINGLE REPORTING LOGIC ---
# # #     # Constraint Checklist:
# # #     # 1. No hardcoded turn thresholds.
# # #     # 2. No intelligence-count thresholds.
# # #     # 3. Must NOT miss callback if conversation ends early.
# # #     # 4. Must ensure EXACTLY ONE callback.
    
# # #     # We report the MOMENT scam is confirmed, if we haven't reported yet.
# # #     # This guarantees we capture the session even if the evaluator stops immediately.
    
# # #     if is_scam_confirmed:
# # #         if not state_service.is_conversation_complete(session_id):
# # #             # LOCK: Mark as reported to ensure exactly one callback
# # #             state_service.mark_conversation_complete(session_id)
            
# # #             final_payload = {
# # #                 "sessionId": session_id,
# # #                 "scamDetected": True,
# # #                 "totalMessagesExchanged": total_messages,
# # #                 "extractedIntelligence": current_intel.model_dump(),
# # #                 "agentNotes": "Scam detected. Intelligence reported. Engagement continuing."
# # #             }
# # #             background_tasks.add_task(callback_service.send_final_report, final_payload)
# # #             logger.info(f"Session {session_id}: First detection - Callback Triggered.")
# # #         else:
# # #             logger.info(f"Session {session_id}: Scam already reported. Continuing accumulation.")

# # ... inside chat_endpoint ...

#     # 5. Metrics & Termination Logic
#     total_messages = len(payload.conversationHistory) + 2
#     engagement_metrics = EngagementMetrics(
#         totalMessagesExchanged=total_messages,
#         engagementDurationSeconds=total_messages * 30
#     )
    
#     # STRICTER TERMINATION LOGIC
#     # 1. Filter bank accounts: Must be at least 9 digits
#     valid_bank_accounts = [
#         acc for acc in current_intel.bankAccounts 
#         if len(re.sub(r"\D", "", acc)) >= 9
#     ]
    
#     # 2. Filter Phone Numbers: Must be at least 10 digits
#     valid_phone_numbers = [
#         phone for phone in current_intel.phoneNumbers
#         if len(re.sub(r"\D", "", phone)) >= 10
#     ]

#     has_critical_intel = (
#         len(valid_bank_accounts) > 0 or 
#         len(current_intel.upiIds) > 0 or
#         len(valid_phone_numbers) > 0 or
#         len(current_intel.phishingLinks) > 0
#     )

#     is_long_convo = total_messages > 15
    
#     # NEW: Accumulation Threshold
#     # Turn 1 = 2 msgs. Turn 2 = 4 msgs. Turn 3 = 6 msgs.
#     # We wait until Turn 3 (6 messages) to fire the callback, allowing accumulation.
#     # OR we fire immediately if the conversation is getting very long (timeout).
#     # MIN_ACCUMULATION_DEPTH = 6 
#     MIN_ACCUMULATION_DEPTH = 10
    
#     should_report = is_scam_confirmed and has_critical_intel and (total_messages >= MIN_ACCUMULATION_DEPTH or is_long_convo)

#     if should_report:
#         if not state_service.is_conversation_complete(session_id):
#             state_service.mark_conversation_complete(session_id)
            
#             final_payload = {
#                 "sessionId": session_id,
#                 "scamDetected": True,
#                 "totalMessagesExchanged": total_messages,
#                 "extractedIntelligence": current_intel.model_dump(),
#                 "agentNotes": "Autonomous engagement completed. Intelligence extracted."
#             }
#             background_tasks.add_task(callback_service.send_final_report, final_payload)
#             logger.info(f"Session {session_id}: Scheduled final callback (Accumulated).")

#     # 6. Return Response
#     # ...

# #---------------------------------------------------------------------------------------------------------------------------------------

#     # 6. Return Response
#     return AgentResponse(
#         status="success",
#         # scamDetected=is_scam_confirmed,
#         # extractedIntelligence=current_intel,
#         # engagementMetrics=engagement_metrics,
#         # agentNotes="Engaging...",
#         # agentNotes=current_agent_notes,
#         # response_text=agent_reply_text # Fixed field name
#         reply=agent_reply_text 
#     )


# # --- DEBUG HANDLER (ADD THIS) ---
# @app.exception_handler(RequestValidationError)
# async def validation_exception_handler(request: Request, exc: RequestValidationError):
#     """
#     If GUVI sends invalid JSON, this logs exactly what they sent 
#     so we can fix our schema.
#     """
#     body = await request.body()
#     error_msg = f"VALIDATION ERROR: {exc}"
#     body_content = body.decode()
#     logger.error("--- 422 ERROR DEBUG ---")
#     logger.error(error_msg)
#     logger.error(f"INCOMING BODY: {body_content}")
#     logger.error("-----------------------")
#     return JSONResponse(
#         status_code=422,
#         content={"detail": str(exc), "body_received": body_content},
#     )

# state_service = StateService()

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# import logging
# from fastapi import FastAPI, Header, HTTPException, BackgroundTasks, Depends, Security 
# from typing import Optional

# from app.core.security import verify_api_key

# from agno.agent import Agent
# from agno.models.groq import Groq

# # Import internals
# from app.core.config import settings
# from app.models.api_schemas import (
#     IncomingMessage, AgentResponse, MessageItem, EngagementMetrics
# )
# from app.services.state import StateService
# from app.services.callback import callback_service
# # from app.agents.detector import get_detector_agent, ScamDetectionResult
# from app.agents.detector import get_detector_agent
# from app.agents.persona import get_persona_agent
# from app.agents.extractor import get_extractor_agent

# import json
# import re


# # Logging Setup
# logging.basicConfig(level=logging.INFO)
# logger = logging.getLogger("guvi-honeypot")

# app = FastAPI(title="Guvi Honeypot Agent")
# state_service = StateService()

# # --- Helpers ---

# # def verify_api_key(x_api_key: str = Header(...)):
# #     if x_api_key != settings.API_KEY:
# #         raise HTTPException(status_code=401, detail="Invalid API Key")

# def format_history_for_agno(history: list[MessageItem]) -> list[dict]:
#     """Convert GUVI history to Agno message format."""
#     formatted = []
#     for msg in history:
#         role = "user" if msg.sender == "scammer" else "assistant"
#         formatted.append({"role": role, "content": msg.text})
#     return formatted

# # Helper to clean LLM JSON output (handles markdown blocks if they slip through)
# def clean_json_str(raw_str: str) -> str:
#     # Remove json and  if present
#     cleaned = re.sub(r"json\s*", "", raw_str)
#     cleaned = re.sub(r"\s*$", "", cleaned)
#     return cleaned.strip()

# # --- Core Endpoint ---
# # @app.post("/api/chat", response_model=AgentResponse)
# # async def chat_endpoint(
# #     payload: IncomingMessage,
# #     background_tasks: BackgroundTasks,
# #     # x_api_key: str = Depends(verify_api_key)
# #     x_api_key: str = Security(verify_api_key)

# # ):
# #     session_id = payload.sessionId
# #     user_text = payload.message.text
    
# #     # 1. Load State
# #     is_scam_confirmed = state_service.get_scam_status(session_id)
# #     current_intel = state_service.get_extracted_intelligence(session_id)
    
# #     # 2. Scam Detection (If not yet confirmed)
# #     if not is_scam_confirmed:
# #         # Fast Detector
# #         detector = get_detector_agent()
# #         # We only feed the LATEST message to the detector for speed
# #         detection: ScamDetectionResult = detector.run(user_text).content
        
# #         if detection.is_scam:
# #             is_scam_confirmed = True
# #             state_service.set_scam_status(session_id, True)
# #             logger.info(f"Session {session_id}: SCAM DETECTED. Reason: {detection.reasoning}")
# #         else:
# #             # If safe, return a generic "Wrong number" response immediately
# #             # We don't engage the persona yet to save costs/latency
# #             return AgentResponse(
# #                 status="success",
# #                 scamDetected=False,
# #                 response_text="Sorry, I think you have the wrong number.",
# #                 extractedIntelligence=current_intel
# #             )

# #     # 3. Intelligence Extraction (Async - Fire & Forget style logic, but awaited for data integrity)
# #     # We extract from the CURRENT message
# #     extractor = get_extractor_agent()
# #     # Run extractor
# #     new_intel_resp = extractor.run(user_text)
# #     # Merge & Save
# #     if new_intel_resp.content:
# #         current_intel = state_service.update_intelligence(session_id, new_intel_resp.content)

# #     # 4. Generate Persona Response
# #     # Convert history + current message
# #     agno_history = format_history_for_agno(payload.conversationHistory)
# #     # Add the current message explicitly if it's not in history yet (GUVI usually sends history excluding current)
# #     # Safety check: if history is empty, it's the first message.
    
# #     persona = get_persona_agent()
# #     # We inject the full history + current user message into the run
# #     # Note: Agno's .run() handles the current message. We prepended history.
# #     response_obj = persona.run(
# #         user_text,
# #         messages=agno_history 
# #     )
# #     agent_reply_text = response_obj.content

# #     # 5. Metrics & Termination Logic
# #     # Calculate simple metrics
# #     total_messages = len(payload.conversationHistory) + 2 # History + User + Agent
# #     engagement_metrics = EngagementMetrics(
# #         totalMessagesExchanged=total_messages,
# #         engagementDurationSeconds=total_messages * 30 # Rough estimate
# #     )
    
# #     # Check Termination Heuristics
# #     has_critical_intel = (
# #         len(current_intel.bankAccounts) > 0 or 
# #         len(current_intel.upiIds) > 0 or
# #         len(current_intel.phoneNumbers) > 0
# #     )
# #     is_long_convo = total_messages > 15
    
# #     # If we have enough intel OR it's getting too long, report it.
# #     # Also ensure we haven't reported it already.
# #     if is_scam_confirmed and (has_critical_intel or is_long_convo):
# #         if not state_service.is_conversation_complete(session_id):
# #             state_service.mark_conversation_complete(session_id)
            
# #             # Prepare Final Callback Payload
# #             final_payload = {
# #                 "sessionId": session_id,
# #                 "scamDetected": True,
# #                 "totalMessagesExchanged": total_messages,
# #                 "extractedIntelligence": current_intel.model_dump(),
# #                 "agentNotes": "Autonomous engagement completed. Intelligence extracted."
# #             }
# #             # Schedule Background Task
# #             background_tasks.add_task(callback_service.send_final_report, final_payload)
# #             logger.info(f"Session {session_id}: Scheduled final callback.")

# #     # 6. Return Response to GUVI
# #     return AgentResponse(
# #         status="success",
# #         scamDetected=is_scam_confirmed,
# #         extractedIntelligence=current_intel,
# #         engagementMetrics=engagement_metrics,
# #         agentNotes="Engaging...",
# #         response_text=agent_reply_text
# #     )

# @app.post("/api/chat", response_model=AgentResponse)
# async def chat_endpoint(
#     payload: IncomingMessage,
#     background_tasks: BackgroundTasks,
#     x_api_key: str = Security(verify_api_key)
# ):
#     session_id = payload.sessionId
#     user_text = payload.message.text
    
#     # 1. Load State
#     is_scam_confirmed = state_service.get_scam_status(session_id)
#     current_intel = state_service.get_extracted_intelligence(session_id)
    
#     # 2. Scam Detection (If not yet confirmed)
#     if not is_scam_confirmed:
#         detector = get_detector_agent()
#         # Run detector (returns string now)
#         raw_response = detector.run(user_text).content
        
#         try:
#             detection_data = json.loads(clean_json_str(raw_response))
#             # Safe access with defaults
#             is_scam = detection_data.get("is_scam", False)
#             reasoning = detection_data.get("reasoning", "Unknown")
            
#             if is_scam:
#                 is_scam_confirmed = True
#                 state_service.set_scam_status(session_id, True)
#                 logger.info(f"Session {session_id}: SCAM DETECTED. Reason: {reasoning}")
#             else:
#                 return AgentResponse(
#                     status="success",
#                     scamDetected=False,
#                     responseText="Sorry, I think you have the wrong number.",
#                     extractedIntelligence=current_intel
#                 )
#         except json.JSONDecodeError:
#             # Fallback if JSON fails (Assume safe to be cautious, or scam if paranoid)
#             logger.error(f"Detector JSON failed: {raw_response}")
#             # For hackathon: Assume safe to avoid breaking flow, or retry.
#             # Let's return generic safe response.
#             return AgentResponse(
#                 status="success",
#                 scamDetected=False,
#                 responseText="Hello? Who is this?",
#                 extractedIntelligence=current_intel
#             )

#     # 3. Intelligence Extraction
#     extractor = get_extractor_agent()
#     raw_intel = extractor.run(user_text).content
#     try:
#         new_intel_dict = json.loads(clean_json_str(raw_intel))
#         # Convert dict to Pydantic model for merging
#         from app.models.api_schemas import ExtractedIntelligence
#         new_intel_model = ExtractedIntelligence(**new_intel_dict)
#         current_intel = state_service.update_intelligence(session_id, new_intel_model)
#     except Exception as e:
#         logger.error(f"Extraction failed: {e}. Raw: {raw_intel}")
#         # Continue without updating intel

#     # 4. Generate Persona Response
#     agno_history = format_history_for_agno(payload.conversationHistory)
#     persona = get_persona_agent()
#     response_obj = persona.run(user_text, messages=agno_history)
#     agent_reply_text = response_obj.content

#     # 5. Metrics & Termination (Keep logic same as before)
#     total_messages = len(payload.conversationHistory) + 2
#     engagement_metrics = EngagementMetrics(
#         totalMessagesExchanged=total_messages,
#         engagementDurationSeconds=total_messages * 30
#     )
    
#     has_critical_intel = (
#         len(current_intel.bankAccounts) > 0 or 
#         len(current_intel.upiIds) > 0 or
#         len(current_intel.phoneNumbers) > 0
#     )
#     is_long_convo = total_messages > 15
    
#     if is_scam_confirmed and (has_critical_intel or is_long_convo):
#         if not state_service.is_conversation_complete(session_id):
#             state_service.mark_conversation_complete(session_id)
#             final_payload = {
#                 "sessionId": session_id,
#                 "scamDetected": True,
#                 "totalMessagesExchanged": total_messages,
#                 "extractedIntelligence": current_intel.model_dump(),
#                 "agentNotes": "Autonomous engagement completed."
#             }
#             background_tasks.add_task(callback_service.send_final_report, final_payload)
#             logger.info(f"Session {session_id}: Scheduled final callback.")

#     # 6. Return Response
#     return AgentResponse(
#         status="success",
#         scamDetected=is_scam_confirmed,
#         extractedIntelligence=current_intel,
#         engagementMetrics=engagement_metrics,
#         agentNotes="Engaging...",
#         response_text=agent_reply_text
#     )

import logging
import json
import re
import os
from dotenv import load_dotenv

#---------------------------------------------------------------------------------------------------------------
from fastapi.middleware.cors import CORSMiddleware # <--- 1. Add Import
#---------------------------------------------------------------------------------------------------------------

# 1. FORCE LOAD .ENV for Windows/Agno compatibility
load_dotenv()

from fastapi import FastAPI, Header, HTTPException, BackgroundTasks, Depends, Security
from typing import Optional

from agno.agent import Agent
from agno.models.groq import Groq

# Import internals
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

#------------------------------------------------------------------------------------------------------------
from fastapi.exceptions import RequestValidationError
from fastapi import Request
from fastapi.responses import JSONResponse
#------------------------------------------------------------------------------------------------------------


# Logging Setup
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("guvi-honeypot")

app = FastAPI(title="Guvi Honeypot Agent")
# --- 2. Add this block IMMEDIATELY after app = FastAPI(...) ---
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allows ALL domains (Critical for Hackathon Testers)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)
# -----------------------------------------------------------
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
    # Remove ```json and ``` if present
    cleaned = re.sub(r"```json\s*", "", raw_str)
    cleaned = re.sub(r"```\s*$", "", cleaned)
    return cleaned.strip()

#-------------------------------------------------------------------------------------------------

@app.get("/health")
async def health_check():
    return {"status": "active", "service": "guvi-honeypot"}

#-------------------------------------------------------------------------------------------------

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
    
    # # 2. Scam Detection (If not yet confirmed)
    # if not is_scam_confirmed:
    #     detector = get_detector_agent()
    #     # Run detector
    #     try:
    #         raw_response = detector.run(user_text).content
    #         detection_data = json.loads(clean_json_str(raw_response))
            
    #         # Safe access
    #         is_scam = detection_data.get("is_scam", False)
    #         reasoning = detection_data.get("reasoning", "Unknown")
            
    #         if is_scam:
    #             is_scam_confirmed = True
    #             state_service.set_scam_status(session_id, True)
    #             logger.info(f"Session {session_id}: SCAM DETECTED. Reason: {reasoning}")
    #         else:
    #             return AgentResponse(
    #                 status="success",
    #                 scamDetected=False,
    #                 response_text="Sorry, I think you have the wrong number.", # Fixed field name
    #                 extractedIntelligence=current_intel
    #             )
    #     except Exception as e:
    #         # Fallback if JSON fails or LLM errors
    #         logger.error(f"Detector Failed: {e}")
    #         # Safe fallback
    #         return AgentResponse(
    #             status="success",
    #             scamDetected=False,
    #             response_text="Hello? Who is this?", # Fixed field name
    #             extractedIntelligence=current_intel
    #         )
    

    # 2. Scam Detection (If not yet confirmed)
    # We initialize agent_notes with a default, but try to overwrite it from detector
    current_agent_notes = "Monitoring conversation..." 

#-----------------------------------------------------------------------------------------------------------   
    # if not is_scam_confirmed:
    #     detector = get_detector_agent()
    #     try:
    #         raw_response = detector.run(user_text).content
    #         detection_data = json.loads(clean_json_str(raw_response))
            
    #         is_scam = detection_data.get("is_scam", False)
    #         reasoning = detection_data.get("reasoning", "Unknown")
    #         # NEW: Capture dynamic notes
    #         behavior_summary = detection_data.get("behavior_summary", "Scam intent detected.")
            
    #         if is_scam:
    #             is_scam_confirmed = True
    #             state_service.set_scam_status(session_id, True)
    #             current_agent_notes = behavior_summary # Update notes
    #             logger.info(f"Session {session_id}: SCAM DETECTED. Notes: {behavior_summary}")
    #         else:
    #             return AgentResponse(
    #                 status="success",
    #                 scamDetected=False,
    #                 response_text="Sorry, I think you have the wrong number.",
    #                 extractedIntelligence=current_intel
    #             )
    #     except Exception as e:
    #         logger.error(f"Detector Failed: {e}")
    #         return AgentResponse(
    #             status="success",
    #             scamDetected=False,
    #             response_text="Hello? Who is this?",
    #             extractedIntelligence=current_intel
    #         )

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
                if attempt == 1: # If last attempt failed
                    logger.error(f"Detector Failed completely.")
        
        # Proceed only if we got data
        if detection_data:
            # Safe access
            is_scam = detection_data.get("is_scam", False)
            reasoning = detection_data.get("reasoning", "Unknown")
            behavior_summary = detection_data.get("behavior_summary", "Scam intent detected.")
            
            if is_scam:
                is_scam_confirmed = True
                state_service.set_scam_status(session_id, True)
                current_agent_notes = behavior_summary 
                logger.info(f"Session {session_id}: SCAM DETECTED. Notes: {behavior_summary}")
            else:
                return AgentResponse(
                    status="success",
                    # scamDetected=False,
                    # response_text="Sorry, I think you have the wrong number.",
                    reply="Sorry, I think you have the wrong number."
                    # extractedIntelligence=current_intel
                )
        else:
             # Fallback if 2 retries failed
             return AgentResponse(
                status="success",
                # scamDetected=False,
                # response_text="Hello? Who is this?",
                reply="Hello? Who is this?"
                # extractedIntelligence=current_intel
            )
#-----------------------------------------------------------------------------------------------------------
    else:
        # If scam was ALREADY confirmed in previous turns, we keep the previous status
        # Ideally, we should persist the 'behavior_summary' in Redis too, 
        # but for now, let's set a generic active note or retrieve from Redis if we added that field.
        # For this Hackathon step, let's keep it simple:
        current_agent_notes = "Scam previously detected. Engaging agent."

    # 3. Intelligence Extraction

#---------------------------------------------------------------------------------------------------------------
    # try:
    #     extractor = get_extractor_agent()
    #     raw_intel = extractor.run(user_text).content
    #     new_intel_dict = json.loads(clean_json_str(raw_intel))
        
    #     # Merge
    #     new_intel_model = ExtractedIntelligence(**new_intel_dict)
    #     current_intel = state_service.update_intelligence(session_id, new_intel_model)
    # except Exception as e:
    #     logger.error(f"Extraction failed: {e}")
    #     # Continue without updating intel - do not crash

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

#-------------------------------------------------------------------------------------------------------------------

    # 4. Generate Persona Response
    try:
        agno_history = format_history_for_agno(payload.conversationHistory)
        persona = get_persona_agent()
        response_obj = persona.run(user_text, messages=agno_history)
        agent_reply_text = response_obj.content
    except Exception as e:
        logger.error(f"Persona Generation Failed: {e}")
        agent_reply_text = "I am having trouble hearing you. Can you say that again?"

#-------------------------------------------------------------------------------------------------------------------
#     # 5. Metrics & Termination Logic
#     total_messages = len(payload.conversationHistory) + 2
#     engagement_metrics = EngagementMetrics(
#         totalMessagesExchanged=total_messages,
#         engagementDurationSeconds=total_messages * 30
#     )
    
#     # has_critical_intel = (
#     #     len(current_intel.bankAccounts) > 0 or 
#     #     len(current_intel.upiIds) > 0 or
#     #     len(current_intel.phoneNumbers) > 0
#     # )

#     # # STRICTER TERMINATION LOGIC
#     # # 1. Filter bank accounts: We only want accounts with digits (e.g., "50100..."), not just "SBI".
#     # valid_bank_accounts = [acc for acc in current_intel.bankAccounts if any(char.isdigit() for char in acc)]
    
#     # has_critical_intel = (
#     #     len(valid_bank_accounts) > 0 or 
#     #     len(current_intel.upiIds) > 0 or
#     #     len(current_intel.phoneNumbers) > 0 or
#     #     len(current_intel.phishingLinks) > 0 # Added Phishing Links check
#     # )

#     # STRICTER TERMINATION LOGIC
#     # 1. Filter bank accounts: Must be at least 9 digits to be a real account number.
#     valid_bank_accounts = [
#         acc for acc in current_intel.bankAccounts 
#         if len(re.sub(r"\D", "", acc)) >= 9 # Count only digits, must be >= 9
#     ]
    
#     # 2. Filter Phone Numbers: Must be at least 10 digits
#     valid_phone_numbers = [
#         phone for phone in current_intel.phoneNumbers
#         if len(re.sub(r"\D", "", phone)) >= 10
#     ]

#     has_critical_intel = (
#         len(valid_bank_accounts) > 0 or 
#         len(current_intel.upiIds) > 0 or
#         len(valid_phone_numbers) > 0 or
#         len(current_intel.phishingLinks) > 0
#     )

#     is_long_convo = total_messages > 15
    
#     if is_scam_confirmed and (has_critical_intel or is_long_convo):
#         if not state_service.is_conversation_complete(session_id):
#             state_service.mark_conversation_complete(session_id)
            
#             final_payload = {
#                 "sessionId": session_id,
#                 "scamDetected": True,
#                 "totalMessagesExchanged": total_messages,
#                 "extractedIntelligence": current_intel.model_dump(),
#                 "agentNotes": "Autonomous engagement completed."
#             }
#             background_tasks.add_task(callback_service.send_final_report, final_payload)
#             logger.info(f"Session {session_id}: Scheduled final callback.")



# # # ... inside chat_endpoint function ...

# #     # 5. Metrics & Termination Logic
# #     total_messages = len(payload.conversationHistory) + 2
# #     engagement_metrics = EngagementMetrics(
# #         totalMessagesExchanged=total_messages,
# #         engagementDurationSeconds=total_messages * 30
# #     )
    
# #     # --- PHASE 2: SINGLE REPORTING LOGIC ---
# #     # Constraint Checklist:
# #     # 1. No hardcoded turn thresholds.
# #     # 2. No intelligence-count thresholds.
# #     # 3. Must NOT miss callback if conversation ends early.
# #     # 4. Must ensure EXACTLY ONE callback.
    
# #     # We report the MOMENT scam is confirmed, if we haven't reported yet.
# #     # This guarantees we capture the session even if the evaluator stops immediately.
    
# #     if is_scam_confirmed:
# #         if not state_service.is_conversation_complete(session_id):
# #             # LOCK: Mark as reported to ensure exactly one callback
# #             state_service.mark_conversation_complete(session_id)
            
# #             final_payload = {
# #                 "sessionId": session_id,
# #                 "scamDetected": True,
# #                 "totalMessagesExchanged": total_messages,
# #                 "extractedIntelligence": current_intel.model_dump(),
# #                 "agentNotes": "Scam detected. Intelligence reported. Engagement continuing."
# #             }
# #             background_tasks.add_task(callback_service.send_final_report, final_payload)
# #             logger.info(f"Session {session_id}: First detection - Callback Triggered.")
# #         else:
# #             logger.info(f"Session {session_id}: Scam already reported. Continuing accumulation.")

# ... inside chat_endpoint ...

    # 5. Metrics & Termination Logic
    total_messages = len(payload.conversationHistory) + 2
    engagement_metrics = EngagementMetrics(
        totalMessagesExchanged=total_messages,
        engagementDurationSeconds=total_messages * 30
    )
    
    # STRICTER TERMINATION LOGIC
    # 1. Filter bank accounts: Must be at least 9 digits
    valid_bank_accounts = [
        acc for acc in current_intel.bankAccounts 
        if len(re.sub(r"\D", "", acc)) >= 9
    ]
    
    # 2. Filter Phone Numbers: Must be at least 10 digits
    valid_phone_numbers = [
        phone for phone in current_intel.phoneNumbers
        if len(re.sub(r"\D", "", phone)) >= 10
    ]

    has_critical_intel = (
        len(valid_bank_accounts) > 0 or 
        len(current_intel.upiIds) > 0 or
        len(valid_phone_numbers) > 0 or
        len(current_intel.phishingLinks) > 0
    )

    # is_long_convo = total_messages > 15
    is_long_convo = total_messages > 30
    
    # NEW: Accumulation Threshold
    # Turn 1 = 2 msgs. Turn 2 = 4 msgs. Turn 3 = 6 msgs.
    # We wait until Turn 3 (6 messages) to fire the callback, allowing accumulation.
    # OR we fire immediately if the conversation is getting very long (timeout).
    # MIN_ACCUMULATION_DEPTH = 6 
    # MIN_ACCUMULATION_DEPTH = 10
    MIN_ACCUMULATION_DEPTH = 20
    
    should_report = is_scam_confirmed and has_critical_intel and (total_messages >= MIN_ACCUMULATION_DEPTH or is_long_convo)

    if should_report:
        if not state_service.is_conversation_complete(session_id):
            state_service.mark_conversation_complete(session_id)
            
            final_payload = {
                "sessionId": session_id,
                "scamDetected": True,
                "totalMessagesExchanged": total_messages,
                "extractedIntelligence": current_intel.model_dump(),
                "agentNotes": "Autonomous engagement completed. Intelligence extracted."
            }
            background_tasks.add_task(callback_service.send_final_report, final_payload)
            logger.info(f"Session {session_id}: Scheduled final callback (Accumulated).")

    # 6. Return Response
    # ...

#---------------------------------------------------------------------------------------------------------------------------------------

    # 6. Return Response
    return AgentResponse(
        status="success",
        # scamDetected=is_scam_confirmed,
        # extractedIntelligence=current_intel,
        # engagementMetrics=engagement_metrics,
        # agentNotes="Engaging...",
        # agentNotes=current_agent_notes,
        # response_text=agent_reply_text # Fixed field name
        reply=agent_reply_text 
    )


# --- DEBUG HANDLER (ADD THIS) ---
@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """
    If GUVI sends invalid JSON, this logs exactly what they sent 
    so we can fix our schema.
    """
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

state_service = StateService()
