const { getSummary } = require("../../api/analytics");
const { createWeeklyReflection } = require("../../api/ai");
const { localDateKey } = require("../../utils/date");

function short(value) {
  return value.slice(5).replace("-", "/");
}

const today = localDateKey();

Page({
  data: {
    period: 7,
    periods: [7, 30, 90],
    today,
    endDate: today,
    weightPoints: [],
    caloriePoints: [],
    facts: [],
    insight: "",
    reflecting: false,
  },
  onShow() {
    this.load();
  },
  changePeriod(event) {
    this.setData({ period: Number(event.currentTarget.dataset.period) }, () => this.load());
  },
  changeEndDate(event) {
    this.setData({ endDate: event.detail.value }, () => this.load());
  },
  async load() {
    try {
      const result = await getSummary(this.data.period, this.data.endDate);
      this.setData({
        weightPoints: (result.weight_points || []).map((item) => ({ ...item, date: short(item.date) })),
        caloriePoints: (result.calorie_days || []).map((item) => ({ ...item, date: short(item.date) })),
        facts: result.facts || [],
        insight: result.insight || "记录达到两次后，再结合产检建议观察变化。",
      });
    } catch (error) {
      console.warn("pregnancy analytics", error);
    }
  },
  async reflect() {
    this.setData({ reflecting: true });
    try {
      const draft = await createWeeklyReflection(this.data.period, this.data.endDate);
      this.setData({ insight: draft.response_text || this.data.insight });
    } catch (error) {
      wx.showToast({ title: "暂时无法生成回顾", icon: "none" });
    } finally {
      this.setData({ reflecting: false });
    }
  },
});
