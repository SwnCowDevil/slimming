const {request}=require("../../api/client");
const {createMeal}=require("../../api/meals");
const {localDateKey}=require("../../utils/date");
const MEAL_TYPES=[{label:"早餐",value:"breakfast"},{label:"午餐",value:"lunch"},{label:"晚餐",value:"dinner"},{label:"加餐",value:"snack"}];
Page({
  data:{query:"",items:[],loading:false,searched:false,mealDate:localDateKey()},
  onLoad(query){this.setData({mealDate:query.date||localDateKey(),query:query.q||""},()=>{if(this.data.query)this.search();});},
  input(e){this.setData({query:e.detail.value});},
  async search(){const q=this.data.query.trim();if(!q)return;this.setData({loading:true});try{const r=await request({url:`/api/v1/foods/search?q=${encodeURIComponent(q)}&locale=zh-CN`});this.setData({items:r.items||[],searched:true});}catch(e){wx.showToast({title:"搜索失败",icon:"none"});}finally{this.setData({loading:false});}},
  choose(e){
    const item=e.currentTarget.dataset.item;
    wx.showActionSheet({itemList:MEAL_TYPES.map(x=>x.label),success:({tapIndex})=>{
      const meal=MEAL_TYPES[tapIndex];
      wx.showModal({title:`记录到${meal.label}`,content:"100",editable:true,placeholderText:"输入克数",confirmText:"确认记录",success:async(result)=>{
        if(!result.confirm)return;
        const grams=Number(result.content);
        if(!Number.isFinite(grams)||grams<=0||grams>5000)return wx.showToast({title:"请输入有效克数",icon:"none"});
        try{
          await createMeal({meal_date:this.data.mealDate,meal_type:meal.value,source_food_id:item.source_food_id,grams},`${this.data.mealDate}-${meal.value}-${item.source_food_id}-${Date.now()}`);
          wx.showToast({title:"已记录"});
          setTimeout(()=>wx.switchTab({url:"/pages/record/index"}),500);
        }catch(error){wx.showToast({title:"记录失败",icon:"none"});}
      }});
    }});
  }
});
