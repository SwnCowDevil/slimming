function splitIngredients(value) {
  return String(value || "")
    .split(/[,，、\n]+/)
    .map((item) => item.trim())
    .filter(Boolean)
    .slice(0, 20);
}

function buildRecommendationPayload(state = {}) {
  return {
    filters: {
      meal_type: state.mealType || null,
      max_minutes: state.maxMinutes || null,
      flavors: Array.isArray(state.flavors) ? state.flavors : [],
      recipe_types: Array.isArray(state.recipeTypes) ? state.recipeTypes : [],
      available_ingredients: splitIngredients(state.availableIngredientsText),
      disliked_ingredients: splitIngredients(state.dislikedIngredientsText),
    },
    query: String(state.query || "").trim().slice(0, 300),
  };
}

function normalizeCandidate(item = {}) {
  const kcal = Number(item.nutrition_per_serving?.energy_kcal ?? item.energy_kcal);
  const id = item.candidate_id || item.id;
  const sourceType = item.source_type || (item.candidate_id ? "ai" : "platform");
  const nutritionSource = item.nutrition_source || "ai_estimated";
  return {
    ...item,
    id,
    candidateId: item.candidate_id || null,
    sourceType,
    sourceLabel: sourceType === "ai" ? "AI 推荐" : "平台食谱",
    nutritionLabel: nutritionSource === "tka" ? "TKA 营养数据" : "含 AI 估算",
    kcal: Number.isFinite(kcal) ? Math.round(kcal) : null,
    kcalLabel: Number.isFinite(kcal) ? `${Math.round(kcal)} kcal` : "营养待确认",
    ingredients: Array.isArray(item.ingredients) ? item.ingredients : (item.items || []),
    isFavorite: Boolean(item.is_favorite),
  };
}

function appendUniqueCandidates(current = [], next = []) {
  const seen = new Set(current.map((item) => item.id || item.candidate_id));
  return current.concat(next.filter((item) => {
    const id = item.id || item.candidate_id;
    if (!id || seen.has(id)) return false;
    seen.add(id);
    return true;
  }));
}

module.exports = { splitIngredients, buildRecommendationPayload, normalizeCandidate, appendUniqueCandidates };
