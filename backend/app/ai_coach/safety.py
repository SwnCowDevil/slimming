from app.ai_coach.schemas import AiContext, SafetyResult


PREGNANCY_ALLOWED_WORKFLOWS = {
    "recipe_recommendation",
    "recipe_swap",
    "record_explanation",
    "weekly_reflection",
}


def evaluate_safety(context: AiContext, workflow: str | None = None) -> SafetyResult:
    if context.serious_symptoms:
        return SafetyResult(action="emergency_guidance", reason="serious_symptoms")
    if context.medication_or_disease:
        return SafetyResult(action="refer_professional", reason="medical_scope")
    if context.eating_disorder_risk:
        return SafetyResult(action="refer_professional", reason="eating_disorder_risk")
    if context.pregnancy:
        if workflow in PREGNANCY_ALLOWED_WORKFLOWS:
            return SafetyResult(action="allow_limited", reason="pregnancy_allowlist")
        return SafetyResult(action="refer_professional", reason="pregnancy")
    return SafetyResult(action="allow")
