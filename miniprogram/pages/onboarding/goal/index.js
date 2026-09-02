Page({
  data: { goal: "", options: [
    { value: "lose", label: "健康减脂", desc: "建立温和、可持续的热量差" },
    { value: "maintain", label: "保持体重", desc: "稳定饮食结构和日常节奏" },
    { value: "improve", label: "改善饮食", desc: "优先关注营养搭配与习惯" },
  ] },
  select(event) { this.setData({ goal: event.currentTarget.dataset.value }); },
  next() { wx.setStorageSync("onboarding.goal", this.data.goal); wx.navigateTo({ url: "/pages/onboarding/body/index" }); },
});
