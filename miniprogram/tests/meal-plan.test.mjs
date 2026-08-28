import assert from "node:assert/strict";
import { createRequire } from "node:module";
import test from "node:test";

const require = createRequire(import.meta.url);
const { buildMealSections, buildPregnancyTodayModel } = require("../utils/meal-plan.js");

test("daily plan groups records by persisted schedule snapshots", () => {
  const sections = buildMealSections(
    {
      items: [
        { id: "p2", meal_schedule_id: "s2", meal_name_snapshot: "上午加餐", scheduled_time_snapshot: "10:15", position: 1 },
        { id: "p1", meal_schedule_id: "s1", meal_name_snapshot: "早餐", scheduled_time_snapshot: "07:45", position: 0 },
      ],
    },
    [{ id: "m1", meal_schedule_id: "s1", energy_kcal: "120.00" }]
  );

  assert.equal(sections[0].title, "早餐");
  assert.equal(sections[0].time, "07:45");
  assert.equal(sections[0].items[0].id, "m1");
  assert.equal(sections[1].items.length, 0);
});

test("pregnancy today model does not expose calorie deficit fields", () => {
  const model = buildPregnancyTodayModel(
    { gestation: { week: 18, day: 2 }, preferences: { current_weight_kg: 62 } },
    { items: [] },
    { daily_kcal: 1650, target_weight_kg: 55 }
  );

  assert.equal(model.gestationLabel, "孕 18 周 2 天");
  assert.equal(model.currentWeightKg, 62);
  assert.equal("dailyKcal" in model, false);
  assert.equal("targetWeightKg" in model, false);
});
