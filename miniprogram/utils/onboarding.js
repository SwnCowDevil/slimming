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

function parseList(value) {
  return String(value || "").split(/[,，]/).map((item) => item.trim()).filter(Boolean);
}

function validatePregnancySetup(data, todayKey) {
  const due = new Date(`${data.dueDate}T00:00:00`);
  const today = new Date(`${todayKey}T00:00:00`);
  const days = Math.round((due.getTime() - today.getTime()) / 86400000);
  const pre = data.prePregnancyWeightKg;
  return Number.isFinite(due.getTime()) && days >= -14 && days <= 294 &&
    Number(data.heightCm) >= 120 && Number(data.heightCm) <= 230 &&
    Number(data.currentWeightKg) >= 30 && Number(data.currentWeightKg) <= 300 &&
    (pre === "" || pre == null || (Number(pre) >= 30 && Number(pre) <= 300));
}

function normalizePregnancyPayload(data) {
  const payload = {
    due_date: data.dueDate,
    due_date_source: "user_entered",
    height_cm: Number(data.heightCm),
    current_weight_kg: Number(data.currentWeightKg),
    activity_level: data.activityLevel,
    dietary_preferences: parseList(data.dietaryPreferences),
    allergens: parseList(data.allergens),
    avoidances: parseList(data.avoidances),
    disliked_foods: parseList(data.dislikedFoods),
    timezone: "Asia/Shanghai",
  };
  if (data.prePregnancyWeightKg !== "" && data.prePregnancyWeightKg != null) {
    payload.pre_pregnancy_weight_kg = Number(data.prePregnancyWeightKg);
  }
  return payload;
}

module.exports = { STEP_ORDER, nextStep, canSubmitBody, isTargetCompatible, validatePregnancySetup, normalizePregnancyPayload };
