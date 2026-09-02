const { recordRecipe } = require("../../api/recipes");
const { localDateKey } = require("../../utils/date");
const { requestErrorMessage } = require("../../utils/errors");

Page({
  data: {
    recipe: null, items: [], mealType: "dinner", submitting: false,
    mealTypes: [{value:"breakfast",label:"早餐"},{value:"lunch",label:"午餐"},{value:"dinner",label:"晚餐"},{value:"snack",label:"加餐"}],
  },
  onLoad() {
    const recipe = wx.getStorageSync("recipes.confirm");
    if (!recipe || !recipe.id) { wx.showToast({ title: "食谱已失效", icon: "none" }); return; }
    const items = (recipe.ingredients || recipe.items || []).map((item) => ({
      itemId: item.id,
      name: item.ingredient_name_zh || item.name_zh,
      grams: Number(item.grams),
      sourceLabel: item.nutrition_source === "tka" ? "TKA 数据" : "AI 估算",
    }));
    this.setData({ recipe, items });
  },
  chooseMeal(e) { this.setData({ mealType: e.currentTarget.dataset.value }); },
  editGrams(e) {
    const index = Number(e.currentTarget.dataset.index);
    this.setData({ [`items[${index}].grams`]: e.detail.value });
  },
  async submit() {
    if (this.data.submitting) return;
    const confirmedItems = this.data.items.map((item) => ({
      item_id: item.itemId,
      ingredient_name_zh: item.name,
      grams: Number(item.grams),
    }));
    if (!confirmedItems.length || confirmedItems.some((item) => !item.item_id || !Number.isFinite(item.grams) || item.grams <= 0)) {
      wx.showToast({ title: "请填写有效的食材克数", icon: "none" }); return;
    }
    this.setData({ submitting: true });
    const date = localDateKey();
    try {
      await recordRecipe(
        this.data.recipe.id,
        { meal_date: date, meal_type: this.data.mealType, confirmed_items: confirmedItems },
        `recipe-confirm-${this.data.recipe.id}-${date}-${this.data.mealType}-${Date.now()}`,
      );
      wx.showToast({ title: "已记录" });
      setTimeout(() => wx.switchTab({ url: "/pages/record/index" }), 500);
    } catch (error) {
      this.setData({ submitting: false });
      wx.showToast({ title: requestErrorMessage(error), icon: "none" });
    }
  },
});
