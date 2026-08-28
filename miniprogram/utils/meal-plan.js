const { formatGestation } = require("./pregnancy");

function buildMealSections(plan, meals, schedules) {
  const records = (meals && meals.items) || meals || [];
  const scheduleMap = new Map((schedules || []).map((item) => [item.id, item]));
  return [...((plan && plan.items) || [])]
    .sort((a, b) => a.position - b.position)
    .map((item) => {
      const schedule = scheduleMap.get(item.meal_schedule_id);
      const code = schedule && schedule.code;
      const rows = records.filter((record) => record.meal_schedule_id === item.meal_schedule_id || (!record.meal_schedule_id && (record.meal_type === code || (record.meal_type === "snack" && code && code.startsWith("snack")))));
      return {
        id: item.id,
        scheduleId: item.meal_schedule_id,
        mealType: code && code.startsWith("snack") ? "snack" : code,
        title: schedule ? schedule.display_name : item.meal_name_snapshot,
        time: schedule ? schedule.scheduled_time : item.scheduled_time_snapshot,
        state: item.state,
        items: rows,
        kcal: Math.round(rows.reduce((sum, record) => sum + Number(record.energy_kcal || 0), 0)),
      };
    });
}

function buildPregnancyTodayModel(pregnancy, plan) {
  return {
    gestationLabel: formatGestation(pregnancy && pregnancy.gestation),
    currentWeightKg:
      pregnancy && pregnancy.preferences ? pregnancy.preferences.current_weight_kg : null,
    mealCount: ((plan && plan.items) || []).length,
  };
}

module.exports = { buildMealSections, buildPregnancyTodayModel };
