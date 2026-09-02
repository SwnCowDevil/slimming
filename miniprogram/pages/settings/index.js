const { deleteAccount } = require("../../api/auth");
const { clearSession } = require("../../state/session");

Page({
  async deleteAccount() {
    const confirmation = await new Promise((resolve) => {
      wx.showModal({
        title: "删除账户与全部记录",
        content: "此操作无法恢复。请输入“删除”后确认。",
        editable: true,
        placeholderText: "请输入 删除",
        confirmText: "永久删除",
        confirmColor: "#C77967",
        success: resolve,
        fail: () => resolve({ confirm: false }),
      });
    });
    if (!confirmation.confirm || String(confirmation.content || "").trim() !== "删除") {
      if (confirmation.confirm) wx.showToast({ title: "输入不正确，未删除", icon: "none" });
      return;
    }
    try {
      wx.showLoading({ title: "正在删除", mask: true });
      await deleteAccount();
      clearSession();
      wx.clearStorageSync();
      wx.hideLoading();
      wx.reLaunch({ url: "/pages/onboarding/welcome/index" });
    } catch (error) {
      wx.hideLoading();
      wx.showToast({ title: "删除失败，请重试", icon: "none" });
    }
  },
});
