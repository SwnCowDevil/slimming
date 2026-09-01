import assert from "node:assert/strict";
import { createRequire } from "node:module";
import test from "node:test";

const require = createRequire(import.meta.url);
const { buildWeightOptions, buildCalorieOptions, buildPregnancyWeightOptions, buildPregnancyCalorieOptions } = require("../components/health-chart/options.js");

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

test("pregnancy weight chart needs two points and never adds a calorie budget", () => {
  assert.equal(buildPregnancyWeightOptions([{ date: "08/19", weight_kg: 62 }], 320, 190), null);
  const options = buildPregnancyWeightOptions([{ date: "08/19", weight_kg: 62, moving_average_7d: 62 }, { date: "08/26", weight_kg: 62.4, moving_average_7d: 62.2 }], 320, 190);
  assert.equal(options.type, "line");
  assert.equal(options.series[0].color, "#86B6DC");
  assert.equal("budgetLine" in options, false);
});

test("pregnancy calorie chart uses daily columns and preserves missing days", () => {
  const options = buildPregnancyCalorieOptions([
    { date: "08/18", consumed_kcal: null },
    { date: "08/19", consumed_kcal: 486 },
  ], 320, 190);
  assert.equal(options.type, "column");
  assert.deepEqual(options.categories, ["08/18", "08/19"]);
  assert.deepEqual(options.series[0].data, [null, 486]);
  assert.equal(options.series[0].color, "#F2B66D");
  assert.equal("budgetLine" in options, false);
});

test("pregnancy calorie chart scrolls long daily ranges", () => {
  const points = Array.from({ length: 30 }, (_, index) => ({
    date: `08/${String(index + 1).padStart(2, "0")}`,
    consumed_kcal: index % 2 ? 500 : null,
  }));
  const options = buildPregnancyCalorieOptions(points, 320, 190);
  assert.equal(options.enableScroll, true);
});

test("pregnancy calorie chart stays empty when no meal was recorded", () => {
  assert.equal(buildPregnancyCalorieOptions([
    { date: "08/18", consumed_kcal: null },
    { date: "08/19", consumed_kcal: null },
  ], 320, 190), null);
});
