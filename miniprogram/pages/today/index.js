const { request } = require("../../api/client");
const { listMeals } = require("../../api/meals");
function dateKey(date=new Date()){return `${date.getFullYear()}-${String(date.getMonth()+1).padStart(2,"0")}-${String(date.getDate()).padStart(2,"0")}`;}
function groupMeals(items){const defs=[['breakfast','早餐'],['lunch','午餐'],['dinner','晚餐'],['snack','加餐']];return defs.map(([type,title])=>{const rows=items.filter(x=>x.meal_type===type);return{type,title,time:"",items:rows,kcal:Math.round(rows.reduce((n,x)=>n+Number(x.energy_kcal),0))};});}
Page({
  data:{dateLabel:"",nickname:"朋友",budget:1650,consumed:0,nutrients:[],mealGroups:groupMeals([]),mealCount:0,aiTip:"记录第一餐后，我会根据已确认的数据给你一条具体建议。"},
  onLoad(){const now=new Date();this.setData({dateLabel:`${now.getFullYear()}年${now.getMonth()+1}月${now.getDate()}日`});},
  onShow(){this.load();},
  async load(){const today=dateKey();try{const [profile,meals]=await Promise.all([request({url:"/api/v1/profiles/me"}),listMeals(today)]);const items=meals.items||[],consumed=Math.round(items.reduce((n,x)=>n+Number(x.energy_kcal),0));const sums={protein:0,carbs:0,fat:0};items.forEach(x=>{sums.protein+=Number(x.protein_g);sums.carbs+=Number(x.carbohydrate_g);sums.fat+=Number(x.fat_g);});const nutrients=[['蛋白质',sums.protein,profile.protein_g],['碳水',sums.carbs,profile.carbohydrate_g],['脂肪',sums.fat,profile.fat_g]].map(([label,value,goal])=>({label,value:Math.round(value),goal,percent:Math.min(100,Math.round(value/goal*100))}));this.setData({budget:profile.daily_kcal,consumed,nutrients,mealGroups:groupMeals(items),mealCount:new Set(items.map(x=>x.meal_type)).size,aiTip:items.length?"今天的记录已纳入分析。晚餐优先补足当前进度较低的营养项。":"记录第一餐后，我会根据已确认的数据给你一条具体建议。"});}catch(e){console.warn("load today",e);}},
  recordMeal(){wx.switchTab({url:"/pages/record/index"});},scanFood(){wx.navigateTo({url:"/pages/photo-recognition/index"});},recordWeight(){wx.switchTab({url:"/pages/profile/index"});},openAi(){wx.navigateTo({url:"/pages/ai-coach/index"});}
});
