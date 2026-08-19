import assert from "node:assert/strict";
import { createRequire } from "node:module";
import test from "node:test";

const require = createRequire(import.meta.url);
const { nextStep, canSubmitBody, isTargetCompatible } = require("../utils/onboarding.js");
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
