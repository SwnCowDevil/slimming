import assert from "node:assert/strict";
import { createRequire } from "node:module";
import test from "node:test";

const require = createRequire(import.meta.url);
const { scaleNutrients } = require("../utils/nutrition.js");
const { reconcileDrafts } = require("../state/offline-drafts.js");

test("nutrients scale from per-100g source values", () => {
  assert.deepEqual(scaleNutrients({ kcal: 162, protein: 0.2 }, 150), { kcal: 243, protein: 0.3 });
});

test("newer offline draft wins without silently creating a record", () => {
  assert.equal(reconcileDrafts([{ id: "a", updatedAt: 2 }], [{ id: "a", updatedAt: 1 }])[0].updatedAt, 2);
});
