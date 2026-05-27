from typing import Protocol

from app.schemas.safety import SafetyAssessment


class SafetyClassifierPort(Protocol):
    async def classify(self, query: str) -> SafetyAssessment:
        ...
