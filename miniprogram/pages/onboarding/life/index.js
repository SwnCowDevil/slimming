Page({
  data: { activity:"light", eatingIndex:1, eatingLabels:["很少外食","偶尔外食","经常外食"], activities:[
    {value:"sedentary",label:"久坐为主",desc:"日常步行较少"},{value:"light",label:"轻度活动",desc:"每周活动 1–3 次"},{value:"moderate",label:"中度活动",desc:"每周活动 3–5 次"},{value:"active",label:"高活动量",desc:"多数天都有运动"}
  ]},
  select(e){ this.setData({activity:e.currentTarget.dataset.value}); }, changeEating(e){this.setData({eatingIndex:Number(e.detail.value)});},
  next(){wx.setStorageSync("onboarding.life",{activity:this.data.activity,eating:["rarely","sometimes","often"][this.data.eatingIndex]});wx.navigateTo({url:"/pages/onboarding/plan/index"});}
});
