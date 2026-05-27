from app.schemas.safety import SafetyAction, SafetyAssessment

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


def crisis_response(safety: SafetyAssessment) -> str:
    return (
        "I cannot safely answer this request. "
        f"{safety.escalation_message or GENERIC_SAFETY_REDIRECT_MESSAGE}"
    )


def apply_safety_caveat(answer: str, safety: SafetyAssessment) -> str:
    if safety.action != SafetyAction.CAVEAT:
        return answer
    return f"{safety.disclaimer} {answer}"
