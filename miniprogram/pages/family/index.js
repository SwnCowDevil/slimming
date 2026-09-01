const { getCurrentPregnancy } = require("../../api/pregnancy");
const {
  createInvitation,
  acceptInvitation,
  listMembers,
  updatePermissions,
  revokeMember,
  listTasks,
  createTask,
  updateTask,
} = require("../../api/family");
const { localDateKey } = require("../../utils/date");
const { requestErrorMessage } = require("../../utils/errors");

Page({
  data: {
    mode: "owner",
    pregnancy: null,
    members: [],
    tasks: [],
    invitationToken: "",
    joinInvitationToken: "",
    canJoinFamily: false,
    joining: false,
    loading: true,
  },
  onShow() {
    this.load();
  },
  async load() {
    this.setData({ loading: true });
    try {
      const memberships = await listMembers();
      let pregnancy = null;
      let mode = "partner";
      let subjectUserId = "";
      let activeMembership = null;
      try {
        pregnancy = await getCurrentPregnancy();
        mode = "owner";
        subjectUserId = pregnancy.user_id;
      } catch (error) {
        activeMembership = (memberships.items || []).find((item) => item.status === "active") || null;
        if (activeMembership) subjectUserId = activeMembership.owner_user_id;
      }
      const members = (memberships.items || []).map((item) => ({
        ...item,
        canMeal: item.permission_scopes.indexOf("meal_entry:write_for_owner") >= 0,
        canTask: item.permission_scopes.indexOf("family_task:write") >= 0,
      }));
      const tasks = subjectUserId
        ? (await listTasks(localDateKey(), mode === "partner" ? subjectUserId : "")).items || []
        : [];
      this.setData({
        mode,
        pregnancy,
        members,
        tasks,
        canJoinFamily: mode === "partner" && !activeMembership,
        loading: false,
      });
    } catch (error) {
      console.warn("family", error);
      this.setData({ loading: false });
    }
  },
  inputInvitation(event) {
    this.setData({ joinInvitationToken: event.detail.value });
  },
  async joinFamily() {
    if (this.data.joining) return;
    const token = (this.data.joinInvitationToken || "").trim();
    if (token.length < 16) {
      wx.showToast({ title: "请输入完整的邀请码", icon: "none" });
      return;
    }
    this.setData({ joining: true });
    try {
      await acceptInvitation(token);
      this.setData({ joinInvitationToken: "" });
      wx.showToast({ title: "已加入家庭", icon: "success" });
      await this.load();
    } catch (error) {
      wx.showToast({ title: requestErrorMessage(error), icon: "none" });
    } finally {
      this.setData({ joining: false });
    }
  },
  async invite() {
    try {
      const result = await createInvitation();
      this.setData({ invitationToken: result.token });
      wx.setClipboardData({ data: result.token, title: "邀请码已复制" });
    } catch (error) {
      wx.showToast({ title: "暂时无法创建邀请", icon: "none" });
    }
  },
  async toggleMeal(event) {
    const member = event.currentTarget.dataset.member;
    const scopes = member.permission_scopes.filter((item) => item !== "meal_entry:write_for_owner");
    if (!member.canMeal) scopes.push("meal_entry:write_for_owner");
    try {
      await updatePermissions(member.id, scopes);
      this.load();
    } catch (error) {
      wx.showToast({ title: "权限保存失败", icon: "none" });
    }
  },
  revoke(event) {
    const id = event.currentTarget.dataset.id;
    wx.showModal({
      title: "撤销家属权限",
      content: "撤销后将立即无法查看或代记。",
      success: async (result) => {
        if (result.confirm) {
          await revokeMember(id);
          this.load();
        }
      },
    });
  },
  addTask() {
    wx.showModal({
      title: "添加家庭任务",
      editable: true,
      placeholderText: "例如：准备晚餐食材",
      success: async (result) => {
        if (!result.confirm || !result.content.trim()) return;
        const member = this.data.members.find((item) => item.status === "active");
        try {
          await createTask({
            task_date: localDateKey(),
            task_type: "other",
            title: result.content.trim(),
            assignee_user_id: member && member.member_user_id,
          });
          this.load();
        } catch (error) {
          wx.showToast({ title: "任务保存失败", icon: "none" });
        }
      },
    });
  },
  async completeTask(event) {
    try {
      await updateTask(event.currentTarget.dataset.id, { status: "completed" });
      this.load();
    } catch (error) {
      wx.showToast({ title: "暂无完成权限", icon: "none" });
    }
  },
});
