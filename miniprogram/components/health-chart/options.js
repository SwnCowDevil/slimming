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

function buildPregnancyCalorieOptions(days, width, height) {
  if (!days || !days.some((day) => day.consumed_kcal !== null && typeof day.consumed_kcal !== "undefined")) return null;
  return {
    ...base(width, height),
    type: "column",
    enableScroll: days.length > 14,
    categories: days.map((day) => day.date),
    series: [
      { name: "摄入", color: palette.orange, data: days.map((day) => day.consumed_kcal) },
    ],
    yAxis: { ...base(width, height).yAxis, format: (value) => `${Math.round(value)}` },
    extra: { column: { width: 14 } },
  };
}

module.exports = { palette, buildWeightOptions, buildCalorieOptions, buildPregnancyWeightOptions, buildPregnancyCalorieOptions };
