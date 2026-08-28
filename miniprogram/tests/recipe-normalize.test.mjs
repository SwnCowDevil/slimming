import assert from "node:assert/strict";
import { createRequire } from "node:module";
import test from "node:test";

const require = createRequire(import.meta.url);
const { normalizeRecipe } = require("../utils/recipe-filter.js");

test("recipe normalization prefers reviewed backend metadata and safe fallbacks", () => {
  const result = normalizeRecipe(
    {
      id: "reviewed",
      title: "已复核食谱",
      minutes: 18,
      energy_kcal: "412.00",
      subtitle: "18 分钟 · 食材已复核",
      tags: null,
      image_url: null,
      safety_summary: "食材信息已复核",
    },
    0,
    [{ image: "/assets/recipes/fallback.jpg" }]
  );

  assert.equal(result.image, "/assets/recipes/fallback.jpg");
  assert.equal(result.kcalLabel, "412 kcal");
  assert.equal(result.subtitle, "18 分钟 · 食材已复核");
  assert.deepEqual(result.tags, []);
  assert.equal(result.recordable, true);
});
