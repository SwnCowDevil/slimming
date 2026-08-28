const { recommendRecipes, nextRecipeBatch, saveAiCandidate } = require("../../api/ai-recipes");
const { buildRecommendationPayload, normalizeCandidate, appendUniqueCandidates } = require("../../utils/ai-recipe");
const { requestErrorMessage } = require("../../utils/errors");

function requestKey(prefix) { return `${prefix}-${Date.now()}-${Math.random().toString(36).slice(2, 9)}`; }

Page({
  data: {
    status: "idle", loading: false, sessionId: "", candidates: [], notice: "",
    mealType: "dinner", maxMinutes: 30, flavors: ["light"], recipeTypes: [],
    availableIngredientsText: "", dislikedIngredientsText: "", query: "",
    mealTypes: [{ value: "breakfast", label: "早餐" }, { value: "lunch", label: "午餐" }, { value: "dinner", label: "晚餐" }, { value: "snack", label: "加餐" }],
    durations: [15, 30, 60],
    flavorOptions: [{ value: "light", label: "清淡" }, { value: "sweet-sour", label: "酸甜" }, { value: "mild-spicy", label: "微辣" }, { value: "home-style", label: "家常" }],
  },
  chooseMeal(e) { this.setData({ mealType: e.currentTarget.dataset.value }); },
  chooseDuration(e) { this.setData({ maxMinutes: Number(e.currentTarget.dataset.value) }); },
  chooseFlavor(e) { this.setData({ flavors: [e.currentTarget.dataset.value] }); },
  inputAvailable(e) { this.setData({ availableIngredientsText: e.detail.value }); },
  inputDisliked(e) { this.setData({ dislikedIngredientsText: e.detail.value }); },
  inputQuery(e) { this.setData({ query: e.detail.value }); },
  async recommend() {
    if (this.data.loading) return;
    this.setData({ loading: true, status: "loading", candidates: [] });
    try {
      const result = await recommendRecipes(buildRecommendationPayload(this.data), requestKey("recipe-initial"));
      const candidates = (result.candidates || []).map(normalizeCandidate);
      this.setData({
        loading: false, sessionId: result.session_id, candidates, notice: result.notice || "",
        status: candidates.length ? (result.mode === "fallback" ? "fallback" : "results") : "empty",
      });
    } catch (error) {
      this.setData({ loading: false, status: "error", errorMessage: requestErrorMessage(error) });
    }
  },
  async nextBatch() {
    if (this.data.loading || !this.data.sessionId) return;
    this.setData({ loading: true });
    try {
      const result = await nextRecipeBatch(this.data.sessionId, requestKey("recipe-next"));
      const next = (result.candidates || []).map(normalizeCandidate);
      this.setData({ loading: false, candidates: appendUniqueCandidates(this.data.candidates, next), status: result.mode === "fallback" ? "fallback" : "results" });
    } catch (error) {
      this.setData({ loading: false });
      wx.showToast({ title: requestErrorMessage(error), icon: "none" });
    }
  },
  adjust() { this.setData({ status: "idle", candidates: [], sessionId: "" }); wx.pageScrollTo({ scrollTop: 0, duration: 250 }); },
  async save(e) {
    const target = e.detail.recipe;
    if (!target.candidateId || target.saved || target.saving) return;
    this.setData({ candidates: this.data.candidates.map((item) => item.id === target.id ? { ...item, saving: true } : item) });
    try {
      const savedRecipe = await saveAiCandidate(target.candidateId);
      this.setData({ candidates: this.data.candidates.map((item) => item.id === target.id ? { ...item, saving: false, saved: true, savedRecipe } : item) });
      wx.showToast({ title: "已加入我的食谱" });
    } catch (error) {
      this.setData({ candidates: this.data.candidates.map((item) => item.id === target.id ? { ...item, saving: false } : item) });
      wx.showToast({ title: requestErrorMessage(error), icon: "none" });
    }
  },
  open(e) {
    const recipe = e.detail.recipe.savedRecipe;
    if (!recipe) { wx.showToast({ title: "收藏后可查看完整食谱", icon: "none" }); return; }
    wx.setStorageSync("recipes.selected", recipe);
    wx.navigateTo({ url: `/pages/recipe-detail/index?id=${recipe.id}` });
  },
});
