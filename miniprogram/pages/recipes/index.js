const {recipes:inspiration}=require("../../data/recipes");
const {listRecipes}=require("../../api/recipes");
const {applyRecipeFilters,normalizeRecipe,searchRecipes}=require("../../utils/recipe-filter");

function filterOptions(active){
  const opts={};
  if(active==="quick")opts.maxMinutes=15;
  if(active==="protein")opts.highProtein=true;
  if(active==="vegetarian")opts.tag="vegetarian";
  return opts;
}

Page({
  data:{active:"all",query:"",searching:false,recipes:inspiration,visible:inspiration,filters:[{key:"all",label:"全部"},{key:"quick",label:"15分钟快手"},{key:"protein",label:"高蛋白"},{key:"vegetarian",label:"轻素食"}]},
  onShow(){this.load();},
  async load(){try{const remote=await listRecipes();if(remote.length){const recipes=remote.map((item,index)=>normalizeRecipe(item,index,inspiration));this.setData({recipes},()=>this.refresh());}}catch(error){console.warn("recipes",error);}},
  refresh(){const filtered=applyRecipeFilters(this.data.recipes,filterOptions(this.data.active));this.setData({visible:searchRecipes(filtered,this.data.query)});},
  choose(e){this.setData({active:e.currentTarget.dataset.key},()=>this.refresh());},
  open(e){wx.setStorageSync("recipes.selected",e.detail.recipe);wx.navigateTo({url:`/pages/recipe-detail/index?id=${e.detail.recipe.id}`});},
  toggleSearch(){this.setData({searching:!this.data.searching,query:""},()=>this.refresh());},
  inputSearch(e){this.setData({query:e.detail.value},()=>this.refresh());},
  clearSearch(){this.setData({query:""},()=>this.refresh());}
});
