# # # from pydantic import BaseModel, Field
# # # from typing import List, Optional, Any

# # # # --- GUVI Input Format ---
# # # class MessageItem(BaseModel):
# # #     sender: str  # "scammer" or "user" (agent)
# # #     text: str
# # #     timestamp: str

# # # class IncomingMessage(BaseModel):
# # #     sessionId: str
# # #     message: MessageItem
# # #     conversationHistory: List[MessageItem]
# # #     metadata: Optional[dict] = {}

# # # # --- GUVI Output Format ---
# # # class EngagementMetrics(BaseModel):
# # #     engagementDurationSeconds: int = 0
# # #     totalMessagesExchanged: int = 0

# # # class ExtractedIntelligence(BaseModel):
# # #     bankAccounts: List[str] = []
# # #     upiIds: List[str] = []
# # #     phishingLinks: List[str] = []
# # #     phoneNumbers: List[str] = []
# # #     suspiciousKeywords: List[str] = []

# # # class AgentResponse(BaseModel):
# # #     status: str = "success"
# # #     scamDetected: bool
# # #     engagementMetrics: Optional[EngagementMetrics] = None
# # #     extractedIntelligence: Optional[ExtractedIntelligence] = None
# # #     agentNotes: Optional[str] = None
# # #     # Note: "message" (the actual text reply) isn't explicitly asked for 
# # #     # in the PDF's *JSON Response* section (Page 10), 
# # #     # but logically we MUST return the text reply to continue the chat.
# # #     # We will include it to be safe, or headers if the API expects it differently.
# # #     response_text: str = Field(..., description="The agent's reply text")

# # from pydantic import BaseModel, Field
# # from typing import List, Optional, Any

# # # --- GUVI Input Format ---
# # class MessageItem(BaseModel):
# #     sender: str  # "scammer" or "user" (agent)
# #     text: str
# #     timestamp: Optional[str] = "" # Made Optional for safety

# # class IncomingMessage(BaseModel):
# #     sessionId: str
# #     message: MessageItem
# #     # CRITICAL FIX: Made Optional with default empty list to prevent 422 on simple pings
# #     conversationHistory: Optional[List[MessageItem]] = [] 
# #     metadata: Optional[dict] = {}

# # # --- GUVI Output Format ---
# # class EngagementMetrics(BaseModel):
# #     engagementDurationSeconds: int = 0
# #     totalMessagesExchanged: int = 0

# # class ExtractedIntelligence(BaseModel):
# #     bankAccounts: List[str] = []
# #     upiIds: List[str] = []
# #     phishingLinks: List[str] = []
# #     phoneNumbers: List[str] = []
# #     suspiciousKeywords: List[str] = []

# # class AgentResponse(BaseModel):
# #     status: str = "success"
# #     scamDetected: bool
# #     engagementMetrics: Optional[EngagementMetrics] = None
# #     extractedIntelligence: Optional[ExtractedIntelligence] = None
# #     agentNotes: Optional[str] = None
# #     # Note: "message" (the actual text reply) isn't explicitly asked for 
# #     # in the PDF's *JSON Response* section (Page 10), 
# #     # but logically we MUST return the text reply to continue the chat.
# #     # We will include it to be safe, or headers if the API expects it differently.
# #     response_text: str = Field(..., description="The agent's reply text")

# from pydantic import BaseModel, Field
# from typing import List, Optional, Any, Union

# # --- GUVI Input Format ---
# class MessageItem(BaseModel):
#     sender: str  # "scammer" or "user" (agent)
#     text: str
#     # FIX: Allow both String (ISO format) AND Integer (Unix timestamp)
#     timestamp: Union[str, int, float] 

# class IncomingMessage(BaseModel):
#     sessionId: str
#     message: MessageItem
#     # Keep this optional/default empty to be safe
#     conversationHistory: Optional[List[MessageItem]] = []
#     metadata: Optional[dict] = {}

# # --- GUVI Output Format ---
# class EngagementMetrics(BaseModel):
#     engagementDurationSeconds: int = 0
#     totalMessagesExchanged: int = 0

# class ExtractedIntelligence(BaseModel):
#     bankAccounts: List[str] = []
#     upiIds: List[str] = []
#     phishingLinks: List[str] = []
#     phoneNumbers: List[str] = []
#     suspiciousKeywords: List[str] = []

# #------------------------------------------------------------------------------------------------------------------

# # class AgentResponse(BaseModel):
# #     status: str = "success"
# #     scamDetected: bool
# #     engagementMetrics: Optional[EngagementMetrics] = None
# #     extractedIntelligence: Optional[ExtractedIntelligence] = None
# #     agentNotes: Optional[str] = None
# #     response_text: str = Field(..., description="The agent's reply text")



# # ... (Keep MessageItem, IncomingMessage, EngagementMetrics, ExtractedIntelligence as they are) ...

# # REPLACE ONLY THE AgentResponse CLASS
# class AgentResponse(BaseModel):
#     status: str = "success"
#     reply: str = Field(..., description="The agent's reply text")
    
#     # REMOVED: scamDetected, engagementMetrics, extractedIntelligence, agentNotes
#     # REASON: These belong in the Callback, not the Chat Response.
#     # RENAMED: response_text -> reply (Per Email Requirement)


# #-----------------------------------------------------------------------------------------------------------------

#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#-------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------



# # from pydantic import BaseModel, Field
# # from typing import List, Optional, Any

# # # --- GUVI Input Format ---
# # class MessageItem(BaseModel):
# #     sender: str  # "scammer" or "user" (agent)
# #     text: str
# #     timestamp: str

# # class IncomingMessage(BaseModel):
# #     sessionId: str
# #     message: MessageItem
# #     conversationHistory: List[MessageItem]
# #     metadata: Optional[dict] = {}

# # # --- GUVI Output Format ---
# # class EngagementMetrics(BaseModel):
# #     engagementDurationSeconds: int = 0
# #     totalMessagesExchanged: int = 0

# # class ExtractedIntelligence(BaseModel):
# #     bankAccounts: List[str] = []
# #     upiIds: List[str] = []
# #     phishingLinks: List[str] = []
# #     phoneNumbers: List[str] = []
# #     suspiciousKeywords: List[str] = []

# # class AgentResponse(BaseModel):
# #     status: str = "success"
# #     scamDetected: bool
# #     engagementMetrics: Optional[EngagementMetrics] = None
# #     extractedIntelligence: Optional[ExtractedIntelligence] = None
# #     agentNotes: Optional[str] = None
# #     # Note: "message" (the actual text reply) isn't explicitly asked for 
# #     # in the PDF's *JSON Response* section (Page 10), 
# #     # but logically we MUST return the text reply to continue the chat.
# #     # We will include it to be safe, or headers if the API expects it differently.
# #     response_text: str = Field(..., description="The agent's reply text")

# from pydantic import BaseModel, Field
# from typing import List, Optional, Any

# # --- GUVI Input Format ---
# class MessageItem(BaseModel):
#     sender: str  # "scammer" or "user" (agent)
#     text: str
#     timestamp: Optional[str] = "" # Made Optional for safety

# class IncomingMessage(BaseModel):
#     sessionId: str
#     message: MessageItem
#     # CRITICAL FIX: Made Optional with default empty list to prevent 422 on simple pings
#     conversationHistory: Optional[List[MessageItem]] = [] 
#     metadata: Optional[dict] = {}

# # --- GUVI Output Format ---
# class EngagementMetrics(BaseModel):
#     engagementDurationSeconds: int = 0
#     totalMessagesExchanged: int = 0

# class ExtractedIntelligence(BaseModel):
#     bankAccounts: List[str] = []
#     upiIds: List[str] = []
#     phishingLinks: List[str] = []
#     phoneNumbers: List[str] = []
#     suspiciousKeywords: List[str] = []

# class AgentResponse(BaseModel):
#     status: str = "success"
#     scamDetected: bool
#     engagementMetrics: Optional[EngagementMetrics] = None
#     extractedIntelligence: Optional[ExtractedIntelligence] = None
#     agentNotes: Optional[str] = None
#     # Note: "message" (the actual text reply) isn't explicitly asked for 
#     # in the PDF's *JSON Response* section (Page 10), 
#     # but logically we MUST return the text reply to continue the chat.
#     # We will include it to be safe, or headers if the API expects it differently.
#     response_text: str = Field(..., description="The agent's reply text")

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

#------------------------------------------------------------------------------------------------------------------

# class AgentResponse(BaseModel):
#     status: str = "success"
#     scamDetected: bool
#     engagementMetrics: Optional[EngagementMetrics] = None
#     extractedIntelligence: Optional[ExtractedIntelligence] = None
#     agentNotes: Optional[str] = None
#     response_text: str = Field(..., description="The agent's reply text")



# ... (Keep MessageItem, IncomingMessage, EngagementMetrics, ExtractedIntelligence as they are) ...

# REPLACE ONLY THE AgentResponse CLASS
class AgentResponse(BaseModel):
    status: str = "success"
    reply: str = Field(..., description="The agent's reply text")
    
    # REMOVED: scamDetected, engagementMetrics, extractedIntelligence, agentNotes
    # REASON: These belong in the Callback, not the Chat Response.
    # RENAMED: response_text -> reply (Per Email Requirement)


#-----------------------------------------------------------------------------------------------------------------
