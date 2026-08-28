function applyRecipeFilters(recipes, filters = {}) {
  return recipes.filter((recipe) => {
    if (filters.maxMinutes && recipe.minutes > filters.maxMinutes) return false;
    if (filters.highProtein && !(recipe.tags || []).includes("high-protein")) return false;
    if (filters.tag && !(recipe.tags || []).includes(filters.tag)) return false;
    return true;
  });
}

function normalizeRecipe(item, index, inspiration) {
  const fallbacks = inspiration || [];
  const fallback = fallbacks.length ? fallbacks[index % fallbacks.length] : {};
  const tags = Array.isArray(item.tags) ? item.tags : [];
  const kcal = Number(item.energy_kcal);
  return {
    ...item,
    tags,
    image: item.image_url || fallback.image || "",
    kcal: Number.isFinite(kcal) ? Math.round(kcal) : null,
    kcalLabel: Number.isFinite(kcal) ? `${Math.round(kcal)} kcal` : "营养信息待完善",
    subtitle:
      item.subtitle ||
      item.safety_summary ||
      (tags.length ? tags.join(" · ") : "食材信息已复核"),
    recordable: true,
  };
}

function searchRecipes(recipes, query) {
  const term = String(query || "").trim().toLocaleLowerCase();
  if (!term) return recipes;
  return recipes.filter((recipe) => {
    const corpus = [
      recipe.title,
      recipe.subtitle,
      recipe.description,
      recipe.safety_summary,
      ...(recipe.tags || []),
    ]
      .filter(Boolean)
      .join(" ")
      .toLocaleLowerCase();
    return corpus.includes(term);
  });
}

module.exports = { applyRecipeFilters, normalizeRecipe, searchRecipes };
