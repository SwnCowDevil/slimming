import assert from "node:assert/strict";
import { createRequire } from "node:module";
import test from "node:test";

const require = createRequire(import.meta.url);
const { nextStep, canSubmitBody, isTargetCompatible, validatePregnancySetup, normalizePregnancyPayload } = require("../utils/onboarding.js");
const { shouldReuseSession } = require("../state/session.js");

test("onboarding advances only when the current step is valid", () => {
  assert.deepEqual(nextStep({ step: "goal", valid: true }), { step: "body" });
  assert.deepEqual(nextStep({ step: "goal", valid: false }), { step: "goal" });
});

test("body measurements reject impossible values", () => {
  assert.equal(canSubmitBody({ heightCm: 168, weightKg: 82 }), true);
  assert.equal(canSubmitBody({ heightCm: 0, weightKg: 82 }), false);
});

test("non-weight-loss goals may keep the current weight", () => {
  assert.equal(isTargetCompatible("lose", 68, 68), false);
  assert.equal(isTargetCompatible("maintain", 68, 68), true);
  assert.equal(isTargetCompatible("improve", 68, 68), true);
});

test("session is reused only while safely unexpired", () => {
  assert.equal(shouldReuseSession({ token: "jwt", userId: "uuid", expiresAt: Date.now() + 60_000 }), true);
  assert.equal(shouldReuseSession({ expiresAt: Date.now() - 1 }), false);
});

test("pregnancy setup validates due date and required current measurements", () => {
  const today = "2026-08-28";
  assert.equal(validatePregnancySetup({ dueDate: "2027-01-15", heightCm: 165, currentWeightKg: 62 }, today), true);
  assert.equal(validatePregnancySetup({ dueDate: "2027-08-15", heightCm: 165, currentWeightKg: 62 }, today), false);
  assert.equal(validatePregnancySetup({ dueDate: "2027-01-15", heightCm: 165, currentWeightKg: "" }, today), false);
});

test("pregnancy payload keeps optional pre-pregnancy weight and no slimming targets", () => {
  const payload = normalizePregnancyPayload({ dueDate: "2027-01-15", heightCm: "165", prePregnancyWeightKg: "", currentWeightKg: "62.5", activityLevel: "light", allergens: "花生, 牛奶", avoidances: "生食", dietaryPreferences: "清淡" });
  assert.equal(payload.pre_pregnancy_weight_kg, undefined);
  assert.equal(payload.current_weight_kg, 62.5);
  assert.deepEqual(payload.allergens, ["花生", "牛奶"]);
  assert.equal("goal" in payload, false);
  assert.equal("target_weight_kg" in payload, false);
  assert.equal("daily_kcal" in payload, false);
});
