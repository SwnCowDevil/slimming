const {createDraft,confirmDraft}=require("../../api/ai");
const {localDateKey}=require("../../utils/date");
Page({
  data:{
    draft:null,
    draftText:"",
    prompts:[
      {text:"看看今天怎么调整",kind:"today_tip",copy:"先补齐尚未记录的一餐，再根据全天营养进度微调份量。"},
      {text:"解释本周趋势",kind:"weekly_explanation",copy:"趋势解释只基于你已确认的记录；连续记录 7 天后会更有参考价值。"}
    ]
  },
  async choose(e){
    const item=e.currentTarget.dataset.item;
    try{
      const draft=await createDraft({kind:item.kind,context:{pregnancy:false},input_data_range:{end:localDateKey(),days:item.kind==="weekly_explanation"?7:1}});
      this.setData({draft,draftText:item.copy});
    }catch(e){wx.showToast({title:"暂时无法生成",icon:"none"});}
  },
  async confirm(){
    try{
      await confirmDraft(this.data.draft.id,`ai-${this.data.draft.id}`);
      wx.showToast({title:"已收下建议"});
      this.setData({draft:null,draftText:""});
    }catch(e){wx.showToast({title:"确认失败",icon:"none"});}
  }
});
