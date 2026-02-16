# # # from agno.agent import Agent
# # # from agno.models.groq import Groq
# # # from pydantic import BaseModel, Field

# # # class ScamDetectionResult(BaseModel):
# # #     is_scam: bool = Field(..., description="True if the message indicates a scam attempt")
# # #     confidence: float = Field(..., description="Confidence score between 0.0 and 1.0")
# # #     reasoning: str = Field(..., description="Brief explanation")

# # # def get_detector_agent():
# # #     return Agent(
# # #         model=Groq(id="llama-3-8b-8192"),
# # #         description="You are a high-speed scam detection system.",
# # #         instructions=[
# # #             "Analyze the incoming message for scam intent.",
# # #             "Look for keywords: blocked, KYC, expiry, OTP, refund, APK, verify immediately.",
# # #             "If the user is threatening account blockage or asking for money/OTP, it is a SCAM.",
# # #             "Return JSON only."
# # #         ],
# # #         response_model=ScamDetectionResult,
# # #         structured_outputs=True, # Enforces strict JSON
# # #         markdown=False,
# # #     )

# # from agno.agent import Agent
# # from agno.models.groq import Groq

# # def get_detector_agent():
# #     return Agent(
# #         model=Groq(id="llama-3-8b-8192"),
# #         description="You are a high-speed scam detection system.",
# #         instructions=[
# #             "Analyze the incoming message for scam intent.",
# #             "Look for keywords: blocked, KYC, expiry, OTP, refund, APK, verify immediately.",
# #             "If the user is threatening account blockage or asking for money/OTP, it is a SCAM.",
# #             "Return a valid JSON object strictly in this format:",
# #             '{"is_scam": boolean, "confidence": float, "reasoning": "string"}',
# #             "Do NOT output markdown code blocks (```json). Output raw JSON only."
# #         ],
# #         markdown=False,
# #     )

# from agno.agent import Agent
# from agno.models.groq import Groq

# from agno.agent import Agent
# from agno.models.groq import Groq

# def get_detector_agent():
#     return Agent(
#         # USES SMARTEST MODEL
#         model=Groq(id="llama-3.3-70b-versatile"), 
#         description="You are a cyber-security expert detecting financial scams.",
#         instructions=[
#             "Analyze the message for scam intent.",
#             "Triggers: 'blocked', 'KYC', 'expiry', 'OTP', 'refund', 'account closed', 'urgent'.",
#             "Logic: If the sender asks for money, OTP, or threatens account closure, is_scam = true.",
#             "Logic: If it looks like a normal hello, is_scam = false.",
#             "Return JSON strictly: {\"is_scam\": boolean, \"confidence\": float, \"reasoning\": \"string\"}",
#             "NO markdown. NO explanations outside JSON."
#         ],
#         markdown=False,
#     )

from agno.agent import Agent
from agno.models.groq import Groq

def get_detector_agent():
    return Agent(
        model=Groq(id="llama-3.3-70b-versatile"), 
        description="You are a cyber-security expert analyzing conversation logs.",
        instructions=[
            "Analyze the incoming message for scam intent.",
            "Triggers: 'blocked', 'KYC', 'expiry', 'OTP', 'refund', 'account closed', 'urgent'.",
            "Task 1: Determine is_scam (boolean).",
            "Task 2: Generate 'behavior_summary' (string). A succinct (5-10 words) description of the tactic used.",
            "   - Bad Example: 'Engaging...'",
            "   - Good Example: 'Scammer used urgency tactics and threatened account closure.'",
            "   - Good Example: 'Scammer requested UPI payment via social engineering.'",
            "Return JSON strictly: {\"is_scam\": boolean, \"confidence\": float, \"reasoning\": \"string\", \"behavior_summary\": \"string\"}",
            "NO markdown. NO explanations outside JSON."
        ],
        markdown=False,

    )
