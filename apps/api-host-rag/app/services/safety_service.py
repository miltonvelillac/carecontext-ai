from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

from app.ports.llm import LlmProvider, LlmRequest
from app.schemas.safety import SafetyAction, SafetyAssessment, SafetyRiskLevel

EDUCATIONAL_DISCLAIMER = "Educational information only. Not medical advice."
SENSITIVE_MEDICAL_DISCLAIMER = (
    "Educational information only. This is not a diagnosis or treatment plan. "
    "For personal medical decisions, consult a qualified health professional."
)
GENERIC_SAFETY_REDIRECT_MESSAGE = (
    "I cannot safely answer this request. If this may involve immediate danger, "
    "contact emergency services now. For personal medical or mental health concerns, "
    "contact a qualified professional or a trusted person nearby."
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


async def classify_query_safety(query: str, llm_provider: LlmProvider) -> SafetyAssessment:
    try:
        messages = SAFETY_PROMPT_TEMPLATE.format_messages(
            format_instructions=SAFETY_OUTPUT_PARSER.get_format_instructions(),
            query=query,
        )
        response = await llm_provider.generate(
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


def crisis_response(safety: SafetyAssessment) -> str:
    return (
        "I cannot safely answer this request. "
        f"{safety.escalation_message or GENERIC_SAFETY_REDIRECT_MESSAGE}"
    )


def apply_safety_caveat(answer: str, safety: SafetyAssessment) -> str:
    if safety.action != SafetyAction.CAVEAT:
        return answer
    return f"{safety.disclaimer} {answer}"


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
