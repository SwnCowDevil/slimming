const calendarTheme = {
  "--wc-primary": "#78A992",
  "--wc-primary-2": "#EAF4ED",
  "--wc-bg-light": "#FFFFFF",
  "--wc-title-color-light": "#47515A",
  "--wc-title-sub-color-light": "#8B9A90",
  "--wc-week-color-light": "#8B9A90",
  "--wc-date-color-light": "#47515A",
  "--wc-checked-color-light": "#47515A",
  "--wc-checked-bg-light": "#DDEFE7",
  "--wc-checked-today-color-light": "#47515A",
  "--wc-checked-today-bg-light": "#FDE8C9",
  "--wc-today-color-light": "#E8862D",
  "--wc-title-size": "30rpx",
  "--wc-title-sub-size": "22rpx",
  "--wc-week-size": "22rpx",
  "--wc-date-size": "28rpx",
  "--wc-mark-size": "20rpx",
  "--wc-corner-size": "18rpx",
  "--wc-panel-height": "112rpx",
};
const calendarStyle = Object.entries(calendarTheme).map(([key, value]) => `${key}:${value}`).join(";");
const calendarConfig = { view: "week", weekstart: 1, sameChecked: true, darkmode: false };
const markStyles = {
  full: { color: "#78A992", text: "●" },
  partial: { color: "#F2B66D", text: "●" },
  "over-budget": { color: "#F3A58E", text: "!" },
};
function markForDay(status) { return markStyles[status] || markStyles.partial; }

module.exports = { calendarTheme, calendarStyle, calendarConfig, markForDay };
