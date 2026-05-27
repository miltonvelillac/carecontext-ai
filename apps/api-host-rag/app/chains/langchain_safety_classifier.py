from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.ports.llm import LlmProvider, LlmRequest
from app.schemas.safety import SafetyAction, SafetyAssessment, SafetyRiskLevel
from app.services.safety_service import (
    EDUCATIONAL_DISCLAIMER,
    GENERIC_SAFETY_REDIRECT_MESSAGE,
    SENSITIVE_MEDICAL_DISCLAIMER,
)

SAFETY_SYSTEM_PROMPT = (
    "You are a safety classifier for an educational health and psychology RAG assistant. "
    "Classify the user's query. Return only valid JSON with keys: risk_level, action, "
    "disclaimer, reasons, escalation_message. risk_level must be one of low, medium, "
    "high, crisis. action must be one of allow, caveat, redirect. Use redirect for "
    "self-harm, harm-to-others, crisis, or requests that cannot be safely answered. "
    "Use caveat for sensitive medical questions involving diagnosis, medication, dosage, "
    "or treatment decisions. Use allow for ordinary educational questions."
)
SAFETY_OUTPUT_PARSER = PydanticOutputParser(pydantic_object=SafetyAssessment)
SAFETY_PROMPT_TEMPLATE = ChatPromptTemplate.from_messages(
    [
        ("system", SAFETY_SYSTEM_PROMPT),
        (
            "human",
            "Classify this user query for safety.\n\n"
            "{format_instructions}\n\n"
            "User query: {query}",
        ),
    ]
)


class LangChainSafetyClassifier:
    def __init__(self, llm_provider: LlmProvider) -> None:
        self.llm_provider = llm_provider

    async def classify(self, query: str) -> SafetyAssessment:
        try:
            messages = SAFETY_PROMPT_TEMPLATE.format_messages(
                format_instructions=SAFETY_OUTPUT_PARSER.get_format_instructions(),
                query=query,
            )
            response = await self.llm_provider.generate(
                LlmRequest(
                    system_prompt=SAFETY_SYSTEM_PROMPT,
                    prompt="\n\n".join(str(message.content) for message in messages),
                    language="auto",
                )
            )
            safety = _parse_safety_response(response.text)
        except Exception:
            return _fail_closed_safety_assessment()

        if safety.action == SafetyAction.REDIRECT and not safety.escalation_message:
            return safety.model_copy(update={"escalation_message": GENERIC_SAFETY_REDIRECT_MESSAGE})
        if safety.action == SafetyAction.CAVEAT and safety.disclaimer == EDUCATIONAL_DISCLAIMER:
            return safety.model_copy(update={"disclaimer": SENSITIVE_MEDICAL_DISCLAIMER})
        return safety


def _parse_safety_response(raw_text: str) -> SafetyAssessment:
    safety = SAFETY_OUTPUT_PARSER.parse(raw_text)
    if safety.risk_level in {SafetyRiskLevel.HIGH, SafetyRiskLevel.CRISIS}:
        return safety.model_copy(update={"action": SafetyAction.REDIRECT})
    return safety


def _fail_closed_safety_assessment() -> SafetyAssessment:
    return SafetyAssessment(
        risk_level=SafetyRiskLevel.HIGH,
        action=SafetyAction.REDIRECT,
        disclaimer=EDUCATIONAL_DISCLAIMER,
        reasons=["safety_classifier_failed"],
        escalation_message=GENERIC_SAFETY_REDIRECT_MESSAGE,
    )
