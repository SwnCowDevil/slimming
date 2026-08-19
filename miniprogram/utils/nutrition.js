function round(value, digits = 2) {
  const factor = 10 ** digits;
  return Math.round((Number(value) + Number.EPSILON) * factor) / factor;
}

function scaleNutrients(per100g, grams) {
  const ratio = Number(grams) / 100;
  return Object.fromEntries(Object.entries(per100g).map(([key, value]) => [key, round(Number(value) * ratio)]));
}

module.exports = { scaleNutrients, round };
