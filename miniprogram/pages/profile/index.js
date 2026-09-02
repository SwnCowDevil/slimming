const { syncWechatProfile } = require("../../api/auth");
const { getCurrentPregnancy } = require("../../api/pregnancy");
const { saveWeight } = require("../../api/profile");
const { readSession } = require("../../state/session");
const { localDateKey } = require("../../utils/date");

Page({
  data: {
    nickname: "微信用户",
    userIdShort: "",
    pregnancy: { gestation: {} },
    currentWeight: null,
    weight: "",
  },
  onShow() {
    this.load();
    const session = readSession();
    this.setData({ userIdShort: session ? session.userId.slice(0, 8) : "未登录" });
  },
  async load() {
    try {
      const pregnancy = await getCurrentPregnancy();
      const currentWeight = pregnancy.preferences.current_weight_kg;
      this.setData({
        pregnancy,
        currentWeight,
        weight: currentWeight == null ? "" : String(currentWeight),
      });
    } catch (error) {
      console.warn("load profile", error);
    }
  },
  useWechatProfile() {
    wx.getUserProfile({
      desc: "用于在孕食记中显示你的头像和昵称",
      success: async ({ userInfo }) => {
        try {
          await syncWechatProfile({ nickName: userInfo.nickName, avatarUrl: userInfo.avatarUrl });
          this.setData({ nickname: userInfo.nickName });
          wx.showToast({ title: "已保存" });
        } catch (error) {
          wx.showToast({ title: "保存失败", icon: "none" });
        }
      },
    });
  },
  weightInput(event) {
    this.setData({ weight: event.detail.value });
  },
  async saveWeight() {
    const value = Number(this.data.weight);
    if (value < 30 || value > 300) {
      return wx.showToast({ title: "请输入有效体重", icon: "none" });
    }
    try {
      await saveWeight(localDateKey(), value);
      wx.showToast({ title: "已记录" });
      this.load();
    } catch (error) {
      wx.showToast({ title: "记录失败", icon: "none" });
    }
  },
});
