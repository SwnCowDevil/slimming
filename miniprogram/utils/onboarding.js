const STEP_ORDER = ["goal", "body", "life", "plan"];

function nextStep({ step, valid }) {
  if (!valid) return { step };
  const index = STEP_ORDER.indexOf(step);
  return { step: STEP_ORDER[Math.min(index + 1, STEP_ORDER.length - 1)] };
}

function canSubmitBody({ heightCm, weightKg }) {
  return heightCm >= 120 && heightCm <= 230 && weightKg >= 30 && weightKg <= 300;
}

function isTargetCompatible(goal, weightKg, targetWeightKg) {
  if (targetWeightKg < 30 || targetWeightKg > 300) return false;
  if (goal === "lose") return targetWeightKg < weightKg;
  return true;
}

module.exports = { STEP_ORDER, nextStep, canSubmitBody, isTargetCompatible };
