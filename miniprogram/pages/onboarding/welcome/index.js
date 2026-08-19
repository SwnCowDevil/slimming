const {getProfile}=require("../../../api/profile");
Page({
  data:{checking:true},
  async onLoad(){
    try{await getProfile();wx.setStorageSync("onboarding.completed",true);wx.switchTab({url:"/pages/today/index"});}
    catch(error){this.setData({checking:false});}
  },
  start() { wx.navigateTo({ url: "/pages/onboarding/goal/index" }); }
});
