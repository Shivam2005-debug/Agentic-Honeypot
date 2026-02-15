# # # # # from agno.agent import Agent
# # # # # from agno.models.groq import Groq
# # # # # from app.models.api_schemas import ExtractedIntelligence

# # # # # def get_extractor_agent():
# # # # #     return Agent(
# # # # #         model=Groq(id="llama3-70b-8192"),
# # # # #         description="You are a forensic intelligence extractor.",
# # # # #         instructions=[
# # # # #             "Analyze the text for financial and contact details.",
# # # # #             "Extract Indian mobile numbers (10 digits).",
# # # # #             "Extract UPI IDs (format: name@bank).",
# # # # #             "Extract Bank Account numbers (often 9-18 digits).",
# # # # #             "Extract Phishing URLs.",
# # # # #             "Extract Suspicious Keywords (urgency, threats).",
# # # # #             "Be aggressive in extraction. If a number is written as text (nine-eight...), convert it.",
# # # # #         ],
# # # # #         response_model=ExtractedIntelligence,
# # # # #         structured_outputs=True,
# # # # #         markdown=False,
# # # # #     )

# # # # from agno.agent import Agent
# # # # from agno.models.groq import Groq

# # # # def get_extractor_agent():
# # # #     return Agent(
# # # #         model=Groq(id="llama3-70b-8192"),
# # # #         description="You are a forensic intelligence extractor.",
# # # #         instructions=[
# # # #             "Analyze the text for financial and contact details.",
# # # #             "Extract: bankAccounts, upiIds, phishingLinks, phoneNumbers, suspiciousKeywords.",
# # # #             "Return a valid JSON object strictly in this format:",
# # # #             '{ "bankAccounts": [], "upiIds": [], "phishingLinks": [], "phoneNumbers": [], "suspiciousKeywords": [] }',
# # # #             "Be aggressive. Convert text-numbers to digits.",
# # # #             "Do NOT output markdown code blocks. Output raw JSON only."
# # # #         ],
# # # #         markdown=False,
# # # #     )

# # # from agno.agent import Agent
# # # from agno.models.groq import Groq

# # # def get_extractor_agent():
# # #     return Agent(
# # #         # USES SMARTEST MODEL
# # #         model=Groq(id="llama-3.3-70b-versatile"),
# # #         description="You are a forensic intelligence extractor.",
# # #         instructions=[
# # #             "Analyze the text for financial and contact details.",
# # #             "Extract: bankAccounts, upiIds, phishingLinks, phoneNumbers, suspiciousKeywords.",
# # #             "Return a valid JSON object strictly in this format:",
# # #             '{ "bankAccounts": [], "upiIds": [], "phishingLinks": [], "phoneNumbers": [], "suspiciousKeywords": [] }',
# # #             "Be aggressive. Convert text-numbers to digits.",
# # #             "Do NOT output markdown code blocks. Output raw JSON only."
# # #         ],
# # #         markdown=False,
# # #     )

# # from agno.agent import Agent
# # from agno.models.groq import Groq

# # def get_extractor_agent():
# #     return Agent(
# #         model=Groq(id="llama-3.3-70b-versatile"),
# #         description="You are a forensic intelligence extractor. Your job is to ignore the victim's data and extract ONLY the scammer's data.",
# #         instructions=[
# #             "Analyze the text for financial and contact details provided by the SENDER.",
# #             "### EXTRACTION RULES",
# #             "1. **Bank Accounts:** Extract only if they look like full account numbers (usually >9 digits). IGNORE partial numbers like '8822xxxx'. IGNORE the victim's own account numbers if mentioned.",
# #             "2. **UPI IDs:** Extract valid UPI handles (e.g., 'name@bank', '99999@paytm'). IGNORE the victim's own UPI IDs if mentioned.",
# #             "3. **Phone Numbers:** Extract 10-digit mobile numbers. IGNORE short codes or OTPs (6 digits). IGNORE the victim's own mobile numbers if mentioned.",
# #             "4. **Phishing Links:** Extract full URLs.",
# #             "",
# #             "### OUTPUT FORMAT",
# #             "Return a valid JSON object strictly in this format:",
# #             '{ "bankAccounts": [], "upiIds": [], "phishingLinks": [], "phoneNumbers": [], "suspiciousKeywords": [] }',
# #             "Do NOT output markdown code blocks. Output raw JSON only."
# #         ],
# #         markdown=False,

# #     )

# #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------
# #--------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# # # # from agno.agent import Agent
# # # # from agno.models.groq import Groq
# # # # from app.models.api_schemas import ExtractedIntelligence

# # # # def get_extractor_agent():
# # # #     return Agent(
# # # #         model=Groq(id="llama3-70b-8192"),
# # # #         description="You are a forensic intelligence extractor.",
# # # #         instructions=[
# # # #             "Analyze the text for financial and contact details.",
# # # #             "Extract Indian mobile numbers (10 digits).",
# # # #             "Extract UPI IDs (format: name@bank).",
# # # #             "Extract Bank Account numbers (often 9-18 digits).",
# # # #             "Extract Phishing URLs.",
# # # #             "Extract Suspicious Keywords (urgency, threats).",
# # # #             "Be aggressive in extraction. If a number is written as text (nine-eight...), convert it.",
# # # #         ],
# # # #         response_model=ExtractedIntelligence,
# # # #         structured_outputs=True,
# # # #         markdown=False,
# # # #     )

# # # from agno.agent import Agent
# # # from agno.models.groq import Groq

# # # def get_extractor_agent():
# # #     return Agent(
# # #         model=Groq(id="llama3-70b-8192"),
# # #         description="You are a forensic intelligence extractor.",
# # #         instructions=[
# # #             "Analyze the text for financial and contact details.",
# # #             "Extract: bankAccounts, upiIds, phishingLinks, phoneNumbers, suspiciousKeywords.",
# # #             "Return a valid JSON object strictly in this format:",
# # #             '{ "bankAccounts": [], "upiIds": [], "phishingLinks": [], "phoneNumbers": [], "suspiciousKeywords": [] }',
# # #             "Be aggressive. Convert text-numbers to digits.",
# # #             "Do NOT output markdown code blocks. Output raw JSON only."
# # #         ],
# # #         markdown=False,
# # #     )

# # from agno.agent import Agent
# # from agno.models.groq import Groq

# # def get_extractor_agent():
# #     return Agent(
# #         # USES SMARTEST MODEL
# #         model=Groq(id="llama-3.3-70b-versatile"),
# #         description="You are a forensic intelligence extractor.",
# #         instructions=[
# #             "Analyze the text for financial and contact details.",
# #             "Extract: bankAccounts, upiIds, phishingLinks, phoneNumbers, suspiciousKeywords.",
# #             "Return a valid JSON object strictly in this format:",
# #             '{ "bankAccounts": [], "upiIds": [], "phishingLinks": [], "phoneNumbers": [], "suspiciousKeywords": [] }',
# #             "Be aggressive. Convert text-numbers to digits.",
# #             "Do NOT output markdown code blocks. Output raw JSON only."
# #         ],
# #         markdown=False,
# #     )

# from agno.agent import Agent
# from agno.models.groq import Groq

# def get_extractor_agent():
#     return Agent(
#         model=Groq(id="llama-3.3-70b-versatile"),
#         description="You are a forensic intelligence extractor. Your job is to ignore the victim's data and extract ONLY the scammer's data.",
#         instructions=[
#             "Analyze the text for financial and contact details provided by the SENDER.",
#             "### EXTRACTION RULES",
#             "1. **Bank Accounts:** Extract only if they look like full account numbers (usually >9 digits). IGNORE partial numbers like '8822xxxx'. IGNORE the victim's own account numbers if mentioned.",
#             "2. **UPI IDs:** Extract valid UPI handles (e.g., 'name@bank', '99999@paytm'). IGNORE the victim's own UPI IDs if mentioned.",
#             "3. **Phone Numbers:** Extract 10-digit mobile numbers. IGNORE short codes or OTPs (6 digits). IGNORE the victim's own mobile numbers if mentioned.",
#             "4. **Phishing Links:** Extract full URLs.",
#             "5. **Suspicious Keywords:** Extract trigger words explicitly present in the text indicating scam intent (e.g., 'KYC', 'OTP', 'verify', 'blocked', 'suspend', 'urgent', 'refund', 'reward', 'lottery', 'update', 'click link'). Keep them short and specific.",
#             "",
#             "### OUTPUT FORMAT",
#             "Return a valid JSON object strictly in this format:",
#             '{ "bankAccounts": [], "upiIds": [], "phishingLinks": [], "phoneNumbers": [], "suspiciousKeywords": [] }',
#             "Do NOT output markdown code blocks. Output raw JSON only."
#         ],
#         markdown=False,
#     )

#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------
#--------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# # # from agno.agent import Agent
# # # from agno.models.groq import Groq
# # # from app.models.api_schemas import ExtractedIntelligence

# # # def get_extractor_agent():
# # #     return Agent(
# # #         model=Groq(id="llama3-70b-8192"),
# # #         description="You are a forensic intelligence extractor.",
# # #         instructions=[
# # #             "Analyze the text for financial and contact details.",
# # #             "Extract Indian mobile numbers (10 digits).",
# # #             "Extract UPI IDs (format: name@bank).",
# # #             "Extract Bank Account numbers (often 9-18 digits).",
# # #             "Extract Phishing URLs.",
# # #             "Extract Suspicious Keywords (urgency, threats).",
# # #             "Be aggressive in extraction. If a number is written as text (nine-eight...), convert it.",
# # #         ],
# # #         response_model=ExtractedIntelligence,
# # #         structured_outputs=True,
# # #         markdown=False,
# # #     )

# # from agno.agent import Agent
# # from agno.models.groq import Groq

# # def get_extractor_agent():
# #     return Agent(
# #         model=Groq(id="llama3-70b-8192"),
# #         description="You are a forensic intelligence extractor.",
# #         instructions=[
# #             "Analyze the text for financial and contact details.",
# #             "Extract: bankAccounts, upiIds, phishingLinks, phoneNumbers, suspiciousKeywords.",
# #             "Return a valid JSON object strictly in this format:",
# #             '{ "bankAccounts": [], "upiIds": [], "phishingLinks": [], "phoneNumbers": [], "suspiciousKeywords": [] }',
# #             "Be aggressive. Convert text-numbers to digits.",
# #             "Do NOT output markdown code blocks. Output raw JSON only."
# #         ],
# #         markdown=False,
# #     )

# from agno.agent import Agent
# from agno.models.groq import Groq

# def get_extractor_agent():
#     return Agent(
#         # USES SMARTEST MODEL
#         model=Groq(id="llama-3.3-70b-versatile"),
#         description="You are a forensic intelligence extractor.",
#         instructions=[
#             "Analyze the text for financial and contact details.",
#             "Extract: bankAccounts, upiIds, phishingLinks, phoneNumbers, suspiciousKeywords.",
#             "Return a valid JSON object strictly in this format:",
#             '{ "bankAccounts": [], "upiIds": [], "phishingLinks": [], "phoneNumbers": [], "suspiciousKeywords": [] }',
#             "Be aggressive. Convert text-numbers to digits.",
#             "Do NOT output markdown code blocks. Output raw JSON only."
#         ],
#         markdown=False,
#     )

from agno.agent import Agent
from agno.models.groq import Groq

def get_extractor_agent():
    return Agent(
        model=Groq(id="llama-3.3-70b-versatile"),
        description="You are a forensic intelligence extractor. Your job is to ignore the victim's data and extract ONLY the scammer's data.",
        instructions=[
            "Analyze the text for financial and contact details provided by the SENDER.",
            "### EXTRACTION RULES",
            "1. **Bank Accounts:** Extract only if they look like full account numbers (usually >9 digits). IGNORE partial numbers like '8822xxxx'. IGNORE the victim's own account numbers if mentioned.",
            "2. **UPI IDs:** Extract valid UPI handles (e.g., 'name@bank', '99999@paytm'). IGNORE the victim's own UPI IDs if mentioned.",
            "3. **Phone Numbers:** Extract 10-digit mobile numbers. IGNORE short codes or OTPs (6 digits). IGNORE the victim's own mobile numbers if mentioned.",
            "4. **Phishing Links:** Extract full URLs.",
            "5. **Email Addresses:** Extract valid emails (e.g., 'support@gmail.com'). CRITICAL: Must have a Top-Level Domain (.com, .in, .org). If it ends in a bank handle (e.g., @okicici, @ybl) without a TLD, it is a UPI ID, NOT an email.",
            "6. **Suspicious Keywords:** Extract trigger words explicitly present in the text indicating scam intent (e.g., 'KYC', 'OTP', 'verify', 'blocked', 'suspend', 'urgent', 'refund', 'reward', 'lottery', 'update', 'click link'). Keep them short and specific.",
            "",
            "### OUTPUT FORMAT",
            "Return a valid JSON object strictly in this format:",
            # '{ "bankAccounts": [], "upiIds": [], "phishingLinks": [], "phoneNumbers": [], "suspiciousKeywords": [] }',
            '{ "bankAccounts": [], "upiIds": [], "phishingLinks": [], "phoneNumbers": [], "emailAddresses": [], "suspiciousKeywords": [] }',
            "Do NOT output markdown code blocks. Output raw JSON only."
        ],
        markdown=False,
    )
