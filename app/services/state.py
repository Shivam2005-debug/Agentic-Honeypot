# import json
# from typing import Optional
# from redis import Redis
# from app.core.config import settings
# from app.models.api_schemas import ExtractedIntelligence, IncomingMessage

# class StateService:
#     def __init__(self):
#         # Initialize Redis connection (Sync is fine for simple K/V, but we use strict decoding)
#         self.redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
#         self.ttl = 3600  # 1 hour expiration for sessions

#     def _get_intel_key(self, session_id: str) -> str:
#         return f"session:{session_id}:intel"

#     def _get_status_key(self, session_id: str) -> str:
#         return f"session:{session_id}:status"

#     def get_extracted_intelligence(self, session_id: str) -> ExtractedIntelligence:
#         """
#         Retrieve existing intelligence for this session from Redis.
#         If none exists, return an empty object.
#         """
#         data = self.redis.get(self._get_intel_key(session_id))
#         if data:
#             try:
#                 return ExtractedIntelligence(**json.loads(data))
#             except json.JSONDecodeError:
#                 return ExtractedIntelligence()
#         return ExtractedIntelligence()

#     def update_intelligence(self, session_id: str, new_intel: ExtractedIntelligence) -> ExtractedIntelligence:
#         """
#         Merge new intelligence with existing intelligence (Deduplicate).
#         Save back to Redis.
#         """
#         current = self.get_extracted_intelligence(session_id)

#         # Merge Logic: Use sets to remove duplicates, then convert back to lists
#         merged_intel = ExtractedIntelligence(
#             bankAccounts=list(set(current.bankAccounts + new_intel.bankAccounts)),
#             upiIds=list(set(current.upiIds + new_intel.upiIds)),
#             phishingLinks=list(set(current.phishingLinks + new_intel.phishingLinks)),
#             phoneNumbers=list(set(current.phoneNumbers + new_intel.phoneNumbers)),
#             suspiciousKeywords=list(set(current.suspiciousKeywords + new_intel.suspiciousKeywords))
#         )

#         # Save to Redis
#         self.redis.setex(
#             self._get_intel_key(session_id),
#             self.ttl,
#             merged_intel.model_dump_json()
#         )
#         return merged_intel

#     def get_scam_status(self, session_id: str) -> bool:
#         """
#         Check if we have already flagged this session as a SCAM.
#         """
#         status = self.redis.get(self._get_status_key(session_id))
#         return status == "true"

#     def set_scam_status(self, session_id: str, is_scam: bool):
#         """
#         Persist the scam detection verdict.
#         """
#         # Only set if True (once a scam, always a scam)
#         if is_scam:
#             self.redis.setex(self._get_status_key(session_id), self.ttl, "true")

#     def mark_conversation_complete(self, session_id: str):
#         """
#         Mark session as 'reported' so we don't fire the callback twice.
#         """
#         self.redis.setex(f"session:{session_id}:completed", self.ttl, "true")

#     def is_conversation_complete(self, session_id: str) -> bool:

#         return self.redis.get(f"session:{session_id}:completed") == "true"

import json
from typing import Optional
from redis import Redis
from app.core.config import settings
from app.models.api_schemas import ExtractedIntelligence, IncomingMessage

class StateService:
    def __init__(self):
        # Initialize Redis connection (Sync is fine for simple K/V, but we use strict decoding)
        self.redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.ttl = 3600  # 1 hour expiration for sessions

    def _get_intel_key(self, session_id: str) -> str:
        return f"session:{session_id}:intel"

    def _get_status_key(self, session_id: str) -> str:
        return f"session:{session_id}:status"

    def get_extracted_intelligence(self, session_id: str) -> ExtractedIntelligence:
        """
        Retrieve existing intelligence for this session from Redis.
        If none exists, return an empty object.
        """
        data = self.redis.get(self._get_intel_key(session_id))
        if data:
            try:
                return ExtractedIntelligence(**json.loads(data))
            except json.JSONDecodeError:
                return ExtractedIntelligence()
        return ExtractedIntelligence()

    def update_intelligence(self, session_id: str, new_intel: ExtractedIntelligence) -> ExtractedIntelligence:
        """
        Merge new intelligence with existing intelligence (Deduplicate).
        Save back to Redis.
        """
        current = self.get_extracted_intelligence(session_id)

        # Merge Logic: Use sets to remove duplicates, then convert back to lists
        merged_intel = ExtractedIntelligence(
            bankAccounts=list(set(current.bankAccounts + new_intel.bankAccounts)),
            upiIds=list(set(current.upiIds + new_intel.upiIds)),
            phishingLinks=list(set(current.phishingLinks + new_intel.phishingLinks)),
            phoneNumbers=list(set(current.phoneNumbers + new_intel.phoneNumbers)),
            emailAddresses=list(set(current.emailAddresses + new_intel.emailAddresses)), # <--- ADD THIS
            suspiciousKeywords=list(set(current.suspiciousKeywords + new_intel.suspiciousKeywords))
        )

        # Save to Redis
        self.redis.setex(
            self._get_intel_key(session_id),
            self.ttl,
            merged_intel.model_dump_json()
        )
        return merged_intel

    def get_scam_status(self, session_id: str) -> bool:
        """
        Check if we have already flagged this session as a SCAM.
        """
        status = self.redis.get(self._get_status_key(session_id))
        return status == "true"

    def set_scam_status(self, session_id: str, is_scam: bool):
        """
        Persist the scam detection verdict.
        """
        # Only set if True (once a scam, always a scam)
        if is_scam:
            self.redis.setex(self._get_status_key(session_id), self.ttl, "true")

    def mark_conversation_complete(self, session_id: str):
        """
        Mark session as 'reported' so we don't fire the callback twice.
        """
        self.redis.setex(f"session:{session_id}:completed", self.ttl, "true")

    def is_conversation_complete(self, session_id: str) -> bool:
        return self.redis.get(f"session:{session_id}:completed") == "true"
