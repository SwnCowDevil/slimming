function applyRecipeFilters(recipes, filters = {}) {
  return recipes.filter((recipe) => {
    if (filters.maxMinutes && recipe.minutes > filters.maxMinutes) return false;
    if (filters.highProtein && !(recipe.tags || []).includes("high-protein")) return false;
    if (filters.tag && !(recipe.tags || []).includes(filters.tag)) return false;
    return true;
  });
}
module.exports = { applyRecipeFilters };
