from pydantic import BaseModel, Field
from typing import List, Optional, Any, Union

# --- GUVI Input Format ---
class MessageItem(BaseModel):
    sender: str  # "scammer" or "user" (agent)
    text: str
    # FIX: Allow both String (ISO format) AND Integer (Unix timestamp)
    timestamp: Union[str, int, float] 

class IncomingMessage(BaseModel):
    sessionId: str
    message: MessageItem
    # Keep this optional/default empty to be safe
    conversationHistory: Optional[List[MessageItem]] = []
    metadata: Optional[dict] = {}

# --- GUVI Output Format ---
class EngagementMetrics(BaseModel):
    engagementDurationSeconds: int = 0
    totalMessagesExchanged: int = 0

class ExtractedIntelligence(BaseModel):
    bankAccounts: List[str] = []
    upiIds: List[str] = []
    phishingLinks: List[str] = []
    phoneNumbers: List[str] = []
    emailAddresses: List[str] = [] # <--- NEW FIELD
    suspiciousKeywords: List[str] = []

class AgentResponse(BaseModel):
    status: str = "success"
    reply: str = Field(..., description="The agent's reply text")
