import assert from "node:assert/strict";
import { createRequire } from "node:module";
import test from "node:test";

const require = createRequire(import.meta.url);
const { applyRecipeFilters } = require("../utils/recipe-filter.js");

test("recipe filters combine duration and tags", () => {
  const recipes = [
    { id: "quick-chicken-bowl", minutes: 12, tags: ["high-protein"] },
    { id: "slow-chicken", minutes: 30, tags: ["high-protein"] },
    { id: "quick-soup", minutes: 10, tags: ["vegetarian"] },
  ];
  assert.deepEqual(applyRecipeFilters(recipes, { maxMinutes: 15, highProtein: true }).map((item) => item.id), ["quick-chicken-bowl"]);
});
