const {listMeals}=require("../../api/meals");
const {getMealPlan}=require("../../api/meal-plans");
const {listMealSchedules}=require("../../api/pregnancy");
const {localDateKey}=require("../../utils/date");
const {buildMealSections,buildRecordTimeline}=require("../../utils/meal-plan");

function key(day){return `${day.year}-${String(day.month).padStart(2,"0")}-${String(day.day).padStart(2,"0")}`;}

Page({
  data:{selectedDate:localDateKey(),timelineGroups:[],recordCount:0,totalKcal:0,marks:[]},
  onShow(){this.load();},
  async load(){
    try{
      const [meals,plan,schedules]=await Promise.all([listMeals(this.data.selectedDate),getMealPlan(this.data.selectedDate),listMealSchedules()]);
      const items=meals.items||[];
      const timeline=buildRecordTimeline(buildMealSections(plan,meals,schedules));
      this.setData({timelineGroups:timeline.groups,recordCount:timeline.recordCount,totalKcal:timeline.totalKcal,marks:items.length?[{date:this.data.selectedDate,type:"festival",text:"●",style:"color:#9BCDB2"}]:[]});
    }catch(error){console.warn("load record",error);}
  },
  dateChange(e){const selected=key(e.detail.checked);clearTimeout(this.timer);this.timer=setTimeout(()=>this.setData({selectedDate:selected},()=>this.load()),180);},
  viewChange(){},
  addToGroup(e){const s=e.currentTarget.dataset.section;wx.navigateTo({url:`/pages/food-search/index?date=${this.data.selectedDate}&scheduleId=${s.scheduleId}&mealType=${s.mealType||"snack"}&mealName=${encodeURIComponent(s.title)}`});},
  search(){wx.navigateTo({url:`/pages/food-search/index?date=${this.data.selectedDate}`});},
  recent(){wx.showToast({title:"最近食物将在搜索页展示",icon:"none"});},
  estimateFood(){wx.navigateTo({url:`/pages/food-estimate/index?date=${this.data.selectedDate}`});}
});
