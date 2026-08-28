const { getCurrentPregnancy, listMealSchedules, updateMealSchedule, getWellbeing, saveWellbeing } = require("../../api/pregnancy");
const { getMealPlan } = require("../../api/meal-plans");
const { listMeals } = require("../../api/meals");
const { saveWeight } = require("../../api/profile");
const { localDateKey } = require("../../utils/date");
const { buildMealSections, buildPregnancyTodayModel, buildTodayMealView } = require("../../utils/meal-plan");

Page({
  data:{dateLabel:"",pregnancy:null,gestationLabel:"",currentWeightKg:null,sections:[],focusSection:null,otherSections:[],completedMealCount:0,totalMealCount:0,feelingCodes:[],wellbeingOptions:[{code:"normal",label:"状态还好"},{code:"nausea",label:"有些恶心"},{code:"reflux",label:"反酸"},{code:"constipation",label:"便秘"},{code:"low_appetite",label:"胃口较低"}],aiTip:"只基于已确认记录提供有限回顾。"},
  onLoad(){const now=new Date();this.setData({dateLabel:`${now.getMonth()+1}月${now.getDate()}日 · 今天`});},onShow(){this.load();},
  async load(){const today=localDateKey();try{const [pregnancy,plan,meals,schedules,wellbeing]=await Promise.all([getCurrentPregnancy(),getMealPlan(today),listMeals(today),listMealSchedules(),getWellbeing(today)]);const model=buildPregnancyTodayModel(pregnancy,plan),codes=wellbeing.feeling_codes||[],sections=buildMealSections(plan,meals,schedules),mealView=buildTodayMealView(sections);this.setData({pregnancy,gestationLabel:model.gestationLabel,currentWeightKg:model.currentWeightKg,sections,focusSection:mealView.focusSection,otherSections:mealView.otherSections,completedMealCount:mealView.completedCount,totalMealCount:mealView.totalCount,feelingCodes:codes,wellbeingOptions:this.data.wellbeingOptions.map(item=>({...item,selected:codes.indexOf(item.code)>=0})),aiTip:meals.items&&meals.items.length?"今天的记录已纳入周期回顾，所有营养数值来自已确认食物。":"先记录一餐，周期回顾只会总结你已确认的数据。"});}catch(error){if(error&&error.statusCode===404)wx.reLaunch({url:"/pages/onboarding/welcome/index"});else console.warn("load pregnancy today",error);}},
  addMeal(e){const s=e.detail.section;wx.navigateTo({url:`/pages/food-search/index?date=${localDateKey()}&scheduleId=${s.scheduleId}&mealType=${s.mealType||"snack"}&mealName=${encodeURIComponent(s.title)}`});},
  addCompactMeal(e){const s=e.currentTarget.dataset.section;wx.navigateTo({url:`/pages/food-search/index?date=${localDateKey()}&scheduleId=${s.scheduleId}&mealType=${s.mealType||"snack"}&mealName=${encodeURIComponent(s.title)}`});},
  editCompactTime(e){this.showTimeEditor(e.currentTarget.dataset.section);},
  editTime(e){this.showTimeEditor(e.detail.section);},
  showTimeEditor(s){wx.showModal({title:`修改${s.title}时间`,content:s.time,editable:true,placeholderText:"例如 08:00",success:async(result)=>{if(!result.confirm)return;if(!/^([01]\d|2[0-3]):[0-5]\d$/.test(result.content))return wx.showToast({title:"请输入 HH:mm 格式",icon:"none"});try{await updateMealSchedule(s.scheduleId,{scheduled_time:result.content});this.load();}catch(error){wx.showToast({title:"保存失败",icon:"none"});}}});},
  toggleFeeling(e){const code=e.currentTarget.dataset.code;let next=this.data.feelingCodes.indexOf(code)>=0?this.data.feelingCodes.filter(x=>x!==code):[...this.data.feelingCodes,code];if(code==="normal"&&next.indexOf(code)>=0)next=["normal"];else next=next.filter(x=>x!=="normal");this.setData({feelingCodes:next,wellbeingOptions:this.data.wellbeingOptions.map(item=>({...item,selected:next.indexOf(item.code)>=0}))});clearTimeout(this.feelingTimer);this.feelingTimer=setTimeout(()=>saveWellbeing(localDateKey(),{feeling_codes:next}).catch(()=>wx.showToast({title:"感受保存失败",icon:"none"})),250);},
  scanFood(){wx.navigateTo({url:"/pages/photo-recognition/index"});},
  recordWeight(){wx.showModal({title:"记录今天体重",editable:true,placeholderText:"例如 62.5",success:async(result)=>{if(!result.confirm)return;const value=Number(result.content);if(value<30||value>300)return wx.showToast({title:"请输入有效体重",icon:"none"});try{await saveWeight(localDateKey(),value);this.setData({currentWeightKg:value});wx.showToast({title:"已记录"});}catch(error){wx.showToast({title:"记录失败",icon:"none"});}}});},
  openAi(){wx.navigateTo({url:"/pages/ai-coach/index"});},
});
