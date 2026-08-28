const { recipes } = require("../../data/recipes");
const { favoriteRecipe, recordRecipe, unfavoriteRecipe } = require("../../api/recipes");
const { localDateKey } = require("../../utils/date");
const { requestErrorMessage } = require("../../utils/errors");
const TYPES = [{label:"早餐",value:"breakfast"},{label:"午餐",value:"lunch"},{label:"晚餐",value:"dinner"},{label:"加餐",value:"snack"}];

function presentRecipe(recipe) {
  const kcal = Number(recipe.energy_kcal || recipe.kcal);
  const sourceType = recipe.source_type || "platform";
  const nutritionSource = recipe.nutrition_source || "tka";
  return {
    ...recipe,
    image: recipe.image || recipe.image_url || "",
    ingredients: recipe.items || recipe.ingredients || [],
    steps: recipe.steps || [],
    kcalLabel: Number.isFinite(kcal) ? `${Math.round(kcal)} kcal` : (recipe.kcalLabel || "营养待确认"),
    sourceLabel: sourceType === "ai" ? "AI 推荐" : "平台食谱",
    nutritionLabel: nutritionSource === "tka" ? "TKA 营养数据" : "含 AI 估算",
    isFavorite: Boolean(recipe.is_favorite),
    allergenLabel: (recipe.allergen_codes || []).join("、"),
  };
}

Page({
  data:{recipe:null,buttonText:"查找并记录食材",favoriteBusy:false},
  onLoad(q){
    const selected=wx.getStorageSync("recipes.selected");
    const raw=selected&&selected.id===q.id?selected:(recipes.find(x=>x.id===q.id)||recipes[0]);
    const recipe=presentRecipe(raw);
    this.setData({recipe,buttonText:recipe.recordable===false?"查找并记录食材":"记录这份食谱"});
  },
  async toggleFavorite(){
    const recipe=this.data.recipe;if(!recipe.id||this.data.favoriteBusy)return;
    this.setData({favoriteBusy:true});
    try{
      if(recipe.isFavorite)await unfavoriteRecipe(recipe.id);else await favoriteRecipe(recipe.id);
      this.setData({"recipe.isFavorite":!recipe.isFavorite,favoriteBusy:false});
    }catch(error){this.setData({favoriteBusy:false});wx.showToast({title:requestErrorMessage(error),icon:"none"});}
  },
  record(){
    const recipe=this.data.recipe;
    if(recipe.recordable===false){const keyword=recipe.searchKeyword||recipe.title;wx.navigateTo({url:`/pages/food-search/index?q=${encodeURIComponent(keyword)}`});return;}
    if(recipe.nutrition_source==="mixed"||recipe.nutrition_source==="ai_estimated"){
      wx.setStorageSync("recipes.confirm",recipe);
      wx.navigateTo({url:`/pages/recipe-confirm/index?id=${recipe.id}`});
      return;
    }
    wx.showActionSheet({itemList:TYPES.map(x=>x.label),success:async({tapIndex})=>{try{await recordRecipe(recipe.id,{meal_date:localDateKey(),meal_type:TYPES[tapIndex].value},`recipe-${recipe.id}-${localDateKey()}-${TYPES[tapIndex].value}`);wx.showToast({title:"已记录"});setTimeout(()=>wx.switchTab({url:"/pages/record/index"}),500);}catch(error){wx.showToast({title:requestErrorMessage(error),icon:"none"});}}});
  }
});
