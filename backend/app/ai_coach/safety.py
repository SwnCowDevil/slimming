from app.ai_coach.schemas import AiContext, SafetyResult


def evaluate_safety(context: AiContext) -> SafetyResult:
    if context.pregnancy:
        return SafetyResult(action="refer_professional", reason="pregnancy")
    if context.eating_disorder_risk:
        return SafetyResult(action="refer_professional", reason="eating_disorder_risk")
    if context.serious_symptoms:
        return SafetyResult(action="refer_professional", reason="serious_symptoms")
    return SafetyResult(action="allow")
