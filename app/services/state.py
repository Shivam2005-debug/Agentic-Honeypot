import json
from typing import Optional
from redis import Redis
from app.core.config import settings
from app.models.api_schemas import ExtractedIntelligence, IncomingMessage

class StateService:
    def __init__(self):
        # Initialize Redis connection
        self.redis = Redis.from_url(settings.REDIS_URL, decode_responses=True)
        self.ttl = 3600  # 1 hour expiration for sessions

    def _get_intel_key(self, session_id: str) -> str:
        return f"session:{session_id}:intel"

    def _get_status_key(self, session_id: str) -> str:
        return f"session:{session_id}:status"

    # --- NEW: METADATA KEYS ---
    def _get_metadata_key(self, session_id: str) -> str:
        return f"session:{session_id}:metadata"

    def get_extracted_intelligence(self, session_id: str) -> ExtractedIntelligence:
        data = self.redis.get(self._get_intel_key(session_id))
        if data:
            try:
                return ExtractedIntelligence(**json.loads(data))
            except json.JSONDecodeError:
                return ExtractedIntelligence()
        return ExtractedIntelligence()

    def update_intelligence(self, session_id: str, new_intel: ExtractedIntelligence) -> ExtractedIntelligence:
        current = self.get_extracted_intelligence(session_id)

        merged_intel = ExtractedIntelligence(
            bankAccounts=list(set(current.bankAccounts + new_intel.bankAccounts)),
            upiIds=list(set(current.upiIds + new_intel.upiIds)),
            phishingLinks=list(set(current.phishingLinks + new_intel.phishingLinks)),
            phoneNumbers=list(set(current.phoneNumbers + new_intel.phoneNumbers)),
            emailAddresses=list(set(current.emailAddresses + new_intel.emailAddresses)),
            suspiciousKeywords=list(set(current.suspiciousKeywords + new_intel.suspiciousKeywords)),
            caseIds=list(set(current.caseIds + new_intel.caseIds)),
            policyNumbers=list(set(current.policyNumbers + new_intel.policyNumbers)),
            orderNumbers=list(set(current.orderNumbers + new_intel.orderNumbers))
        )

        self.redis.setex(
            self._get_intel_key(session_id),
            self.ttl,
            merged_intel.model_dump_json()
        )
        return merged_intel

    def get_scam_status(self, session_id: str) -> bool:
        status = self.redis.get(self._get_status_key(session_id))
        return status == "true"

    def set_scam_status(self, session_id: str, is_scam: bool):
        if is_scam:
            self.redis.setex(self._get_status_key(session_id), self.ttl, "true")

    # --- NEW: METADATA METHODS ---
    def set_scam_metadata(self, session_id: str, scam_type: str, confidence: float):
        """Store the type and confidence when scam is first detected."""
        data = json.dumps({"scamType": scam_type, "confidence": confidence})
        self.redis.setex(self._get_metadata_key(session_id), self.ttl, data)

    def get_scam_metadata(self, session_id: str) -> dict:
        """Retrieve type and confidence for the final callback."""
        data = self.redis.get(self._get_metadata_key(session_id))
        if data:
            return json.loads(data)
        # Default fallback if nothing stored
        return {"scamType": "financial_fraud_generic", "confidence": 1.0}

    def mark_conversation_complete(self, session_id: str):
        self.redis.setex(f"session:{session_id}:completed", self.ttl, "true")

    def is_conversation_complete(self, session_id: str) -> bool:
        return self.redis.get(f"session:{session_id}:completed") == "true"
