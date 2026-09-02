import assert from "node:assert/strict";
import { createRequire } from "node:module";
import test from "node:test";

const require = createRequire(import.meta.url);
const { applyRecipeFilters, searchRecipes } = require("../utils/recipe-filter.js");

test("recipe filters combine duration and tags", () => {
  const recipes = [
    { id: "quick-chicken-bowl", minutes: 12, tags: ["high-protein"] },
    { id: "slow-chicken", minutes: 30, tags: ["high-protein"] },
    { id: "quick-soup", minutes: 10, tags: ["vegetarian"] },
  ];
  assert.deepEqual(applyRecipeFilters(recipes, { maxMinutes: 15, highProtein: true }).map((item) => item.id), ["quick-chicken-bowl"]);
});

test("recipe search matches titles and descriptive food terms", () => {
  const recipes = [
    { id: "chicken", title: "鸡胸藜麦轻食碗", subtitle: "蛋白质充足", description: "鸡胸肉搭配藜麦" },
    { id: "soup", title: "番茄蘑菇燕麦汤", subtitle: "暖胃高纤", description: "番茄和蘑菇" },
  ];

  assert.deepEqual(searchRecipes(recipes, "鸡胸").map((item) => item.id), ["chicken"]);
  assert.deepEqual(searchRecipes(recipes, "  蘑菇 ").map((item) => item.id), ["soup"]);
  assert.deepEqual(searchRecipes(recipes, ""), recipes);
});
