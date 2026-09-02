const {getCurrentPregnancy}=require("../../../api/pregnancy");
Page({
  data:{checking:true},
  async onLoad(){
    try{await getCurrentPregnancy();wx.setStorageSync("pregnancy.onboarding.completed",true);wx.switchTab({url:"/pages/today/index"});}
    catch(error){this.setData({checking:false});}
  },
  start() { wx.navigateTo({ url: "/pages/onboarding/pregnancy/index" }); }
});
