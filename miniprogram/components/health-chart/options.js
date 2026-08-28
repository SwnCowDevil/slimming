const palette = { blue: "#6FA8D6", blueSoft: "#AFCBE3", orange: "#F2B66D", grid: "#E8EEEA", text: "#7C8780" };

function base(width, height) {
  return { width, height, animation: true, dataLabel: false, enableScroll: false, legend: false, background: "#FFFFFF", xAxis: { disableGrid: true, fontColor: palette.text }, yAxis: { gridColor: palette.grid, fontColor: palette.text, min: 0 } };
}

function buildWeightOptions(points, width, height) {
  return { ...base(width, height), type: "line", categories: points.map((p) => p.date), series: [
    { name: "体重", color: palette.blue, data: points.map((p) => p.weight_kg), format: (v) => `${v}kg` },
    { name: "7日均线", color: palette.blueSoft, data: points.map((p) => p.moving_average_7d), format: (v) => `${v}kg` },
  ], extra: { lineStyle: "curve" } };
}

function buildCalorieOptions(days, width, height) {
  const options = { ...base(width, height), type: "column", categories: days.map((d) => d.date), series: [
    { name: "摄入", color: palette.orange, data: days.map((d) => d.consumed_kcal) },
  ], yAxis: { ...base(width, height).yAxis, format: (v) => `${Math.round(v)}` }, extra: { column: { width: 18 } } };
  options.budgetLine = days.map((d) => d.budget_kcal || 0);
  return options;
}

function buildPregnancyWeightOptions(points, width, height) {
  if (!points || points.length < 2) return null;
  const options = base(width, height);
  return { ...options, type: "line", categories: points.map((p) => p.date), series: [
    { name: "体重记录", color: "#86B6DC", data: points.map((p) => p.weight_kg), format: (v) => `${v}kg` },
    { name: "7日均线", color: "#C7DDEF", data: points.map((p) => p.moving_average_7d), format: (v) => `${v}kg` },
  ], extra: { lineStyle: "curve" } };
}

function buildPregnancyFactsOptions(summary, width, height) {
  const source = Array.isArray(summary) ? summary[0] || {} : summary || {};
  return { ...base(width, height), type: "column", categories: ["记录天数", "食物类别"], series: [
    { name: "周期记录", color: "#F2C48D", data: [source.recorded_day_count || 0, source.food_category_diversity || 0] },
  ], extra: { column: { width: 28 } } };
}

module.exports = { palette, buildWeightOptions, buildCalorieOptions, buildPregnancyWeightOptions, buildPregnancyFactsOptions };
