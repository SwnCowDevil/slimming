const { formatGestation } = require("./pregnancy");

function buildMealSections(plan, meals) {
  const records = (meals && meals.items) || meals || [];
  return [...((plan && plan.items) || [])]
    .sort((a, b) => a.position - b.position)
    .map((item) => {
      const rows = records.filter((record) => record.meal_schedule_id === item.meal_schedule_id);
      return {
        id: item.id,
        scheduleId: item.meal_schedule_id,
        title: item.meal_name_snapshot,
        time: item.scheduled_time_snapshot,
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
