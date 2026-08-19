const { request } = require("../../../api/client");
const { loginWithWechat } = require("../../../api/auth");
Page({
  data:{submitting:false},
  async finish(){
    this.setData({submitting:true});
    try {
      await loginWithWechat();
      const goal=wx.getStorageSync("onboarding.goal")||"lose", body=wx.getStorageSync("onboarding.body"), life=wx.getStorageSync("onboarding.life");
      await request({url:"/api/v1/profiles/onboarding",method:"POST",data:{goal,sex:body.sex,age:body.age,height_cm:body.heightCm,current_weight_kg:body.weightKg,target_weight_kg:body.targetWeightKg,activity_level:life.activity,dietary_preferences:[],allergens:[],eating_out_frequency:life.eating}});
      wx.setStorageSync("onboarding.completed",true); wx.switchTab({url:"/pages/today/index"});
    } catch(e) { wx.showToast({title:"暂时无法保存，请重试",icon:"none"}); }
    finally { this.setData({submitting:false}); }
  }
});
