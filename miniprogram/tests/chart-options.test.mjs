import assert from "node:assert/strict";
import { createRequire } from "node:module";
import test from "node:test";

const require = createRequire(import.meta.url);
const { buildWeightOptions, buildCalorieOptions } = require("../components/health-chart/options.js");

test("weight chart uses line series and light accessible palette", () => {
  const options = buildWeightOptions([{ date: "08/19", weight_kg: 68.2, moving_average_7d: 68.4 }], 320, 190);
  assert.equal(options.type, "line");
  assert.deepEqual(options.series.map((item) => item.name), ["体重", "7日均线"]);
  assert.equal(options.series[0].color, "#6FA8D6");
  assert.equal(options.enableScroll, false);
});

test("calorie chart uses columns and exposes budget as a line series", () => {
  const options = buildCalorieOptions([{ date: "周一", consumed_kcal: 1400, budget_kcal: 1650 }], 320, 190);
  assert.equal(options.type, "column");
  assert.equal(options.series[0].name, "摄入");
  assert.deepEqual(options.budgetLine, [1650]);
});
