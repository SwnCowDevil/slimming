import assert from "node:assert/strict";
import { createRequire } from "node:module";
import test from "node:test";

const require = createRequire(import.meta.url);
const { buildRecommendationPayload, normalizeCandidate, appendUniqueCandidates } = require("../utils/ai-recipe.js");

test("recommendation payload sends only current filters and free text", () => {
  const payload = buildRecommendationPayload({
    mealType: "dinner",
    maxMinutes: 30,
    flavors: ["light"],
    recipeTypes: ["soup"],
    availableIngredientsText: "番茄、鸡蛋",
    dislikedIngredientsText: "香菜",
    query: "想吃清淡的家常菜",
    profile: { dueDate: "2026-12-20" },
    openid: "must-not-leak",
  });

  assert.deepEqual(payload.filters, {
    meal_type: "dinner",
    max_minutes: 30,
    flavors: ["light"],
    recipe_types: ["soup"],
    available_ingredients: ["番茄", "鸡蛋"],
    disliked_ingredients: ["香菜"],
  });
  assert.equal(payload.query, "想吃清淡的家常菜");
  assert.equal("profile" in payload, false);
  assert.equal("openid" in payload, false);
});

test("candidate normalization exposes provenance and favorite state", () => {
  const item = normalizeCandidate({
    candidate_id: "candidate-1",
    title: "番茄鸡丁",
    summary: "清淡家常",
    nutrition_source: "mixed",
    nutrition_confidence: "medium",
    nutrition_per_serving: { energy_kcal: 328.4 },
    ingredients: [],
  });

  assert.equal(item.id, "candidate-1");
  assert.equal(item.sourceLabel, "AI 推荐");
  assert.equal(item.nutritionLabel, "含 AI 估算");
  assert.equal(item.kcalLabel, "328 kcal");
  assert.equal(item.isFavorite, false);
});

test("next batch appends only unseen candidates", () => {
  const items = appendUniqueCandidates([{ id: "a" }], [{ id: "a" }, { id: "b" }]);
  assert.deepEqual(items.map((item) => item.id), ["a", "b"]);
});
