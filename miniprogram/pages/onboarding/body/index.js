const { canSubmitBody, isTargetCompatible } = require("../../../utils/onboarding");
Page({
  data: { goal: "lose", sex: "female", age: "30", heightCm: "168", weightKg: "68", targetWeightKg: "60" },
  onLoad() { const goal=wx.getStorageSync("onboarding.goal")||"lose"; this.setData({goal,targetWeightKg:goal==="lose"?"60":"68"}); },
  selectSex(event) { this.setData({ sex: event.currentTarget.dataset.value }); },
  input(event) { this.setData({ [event.currentTarget.dataset.field]: event.detail.value }); },
  next() {
    const body = { sex: this.data.sex, age: Number(this.data.age), heightCm: Number(this.data.heightCm), weightKg: Number(this.data.weightKg), targetWeightKg: Number(this.data.targetWeightKg) };
    if (!canSubmitBody(body) || !isTargetCompatible(this.data.goal,body.weightKg,body.targetWeightKg)) return wx.showToast({ title: "请检查身高体重", icon: "none" });
    wx.setStorageSync("onboarding.body", body); wx.navigateTo({ url: "/pages/onboarding/life/index" });
  },
});
