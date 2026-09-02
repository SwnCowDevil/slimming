const {createWeeklyReflection}=require("../../api/ai");
Page({
  data:{
    draft:null,
    draftText:"",
    currentPeriod:7,
    loading:false,
    loadingKey:"",
    prompts:[
      {text:"回顾最近 7 天",period:7,loadingKey:"prompt-7"},
      {text:"回顾最近 30 天",period:30,loadingKey:"prompt-30"}
    ]
  },
  async generate(e){
    const period=Number(e.currentTarget.dataset.period||7);
    const loadingKey=e.currentTarget.dataset.loadingKey||"";
    this.setData({loading:true,loadingKey});
    try{
      const draft=await createWeeklyReflection(period);
      this.setData({draft,draftText:draft.response_text||"本周期暂无足够记录可供回顾。",currentPeriod:period});
    }catch(error){wx.showToast({title:"暂时无法生成回顾",icon:"none"});}
    finally{this.setData({loading:false,loadingKey:""});}
  }
});
