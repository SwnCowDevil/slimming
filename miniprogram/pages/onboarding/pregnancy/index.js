const { createPregnancy } = require("../../../api/pregnancy");
const { loginWithWechat } = require("../../../api/auth");
const { localDateKey } = require("../../../utils/date");
const { requestErrorMessage } = require("../../../utils/errors");
const { validatePregnancySetup, normalizePregnancyPayload } = require("../../../utils/onboarding");

function futureDate(days) {
  const value = new Date();
  value.setDate(value.getDate() + days);
  return localDateKey(value);
}

Page({
  data: {
    dueDate: futureDate(140), heightCm: "165", prePregnancyWeightKg: "", currentWeightKg: "",
    activityLevel: "light", activityIndex: 1, activityLabels: ["久坐为主", "轻度活动", "中度活动", "较高活动"],
    dietaryPreferences: "", allergens: "", avoidances: "", dislikedFoods: "", submitting: false,
  },
  input(e) { this.setData({ [e.currentTarget.dataset.field]: e.detail.value }); },
  dueDateChange(e) { this.setData({ dueDate: e.detail.value }); },
  activityChange(e) { const index=Number(e.detail.value);this.setData({ activityIndex:index, activityLevel:["sedentary","light","moderate","active"][index] }); },
  async submit() {
    if (!validatePregnancySetup(this.data, localDateKey())) return wx.showToast({ title: "请检查预产期、身高和体重", icon: "none" });
    this.setData({ submitting: true });
    try {
      await loginWithWechat();
      await createPregnancy(normalizePregnancyPayload(this.data));
      wx.setStorageSync("pregnancy.onboarding.completed", true);
      wx.switchTab({ url: "/pages/today/index" });
    } catch (error) {
      wx.showToast({ title: requestErrorMessage(error), icon: "none" });
    } finally {
      this.setData({ submitting: false });
    }
  },
});
