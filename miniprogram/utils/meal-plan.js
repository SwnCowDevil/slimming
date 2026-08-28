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

function timeToMinutes(value) {
  const match = /^(\d{2}):(\d{2})$/.exec(value || "");
  return match ? Number(match[1]) * 60 + Number(match[2]) : Number.MAX_SAFE_INTEGER;
}

function buildTodayMealView(sections, currentMinutes) {
  const rows = sections || [];
  const now = Number.isFinite(currentMinutes)
    ? currentMinutes
    : new Date().getHours() * 60 + new Date().getMinutes();
  const incomplete = rows.filter((section) => !(section.items || []).length);
  const focusSection =
    incomplete.find((section) => timeToMinutes(section.time) >= now) ||
    incomplete[0] ||
    rows[rows.length - 1] ||
    null;
  return {
    focusSection,
    otherSections: focusSection ? rows.filter((section) => section.id !== focusSection.id) : [],
    completedCount: rows.filter((section) => (section.items || []).length > 0).length,
    totalCount: rows.length,
  };
}

function buildRecordTimeline(sections) {
  const groups = (sections || []).filter((section) => (section.items || []).length > 0);
  return {
    groups,
    recordCount: groups.reduce((sum, section) => sum + section.items.length, 0),
    totalKcal: Math.round(groups.reduce((sum, section) => sum + Number(section.kcal || 0), 0)),
  };
}

module.exports = {
  buildMealSections,
  buildPregnancyTodayModel,
  buildTodayMealView,
  buildRecordTimeline,
};
