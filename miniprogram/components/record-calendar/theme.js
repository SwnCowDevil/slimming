const calendarTheme = {
  "--wc-primary": "#9BCDB2",
  "--wc-primary-2": "#EAF6EF",
  "--wc-bg-light": "#FFFFFF",
  "--wc-title-color-light": "#59645E",
  "--wc-title-sub-color-light": "#98A39D",
  "--wc-week-color-light": "#98A39D",
  "--wc-date-color-light": "#59645E",
  "--wc-checked-color-light": "#59645E",
  "--wc-checked-bg-light": "#EAF6EF",
  "--wc-checked-today-color-light": "#59645E",
  "--wc-checked-today-bg-light": "#FDE8C9",
  "--wc-today-color-light": "#E8862D",
  "--wc-title-size": "30rpx",
  "--wc-title-sub-size": "22rpx",
  "--wc-week-size": "22rpx",
  "--wc-date-size": "28rpx",
  "--wc-mark-size": "20rpx",
  "--wc-corner-size": "18rpx",
};
const calendarStyle = [
  "width:100%",
  "max-width:100%",
  ...Object.entries(calendarTheme).map(([key, value]) => `${key}:${value}`),
].join(";");
const calendarConfig = { view: "week", weekstart: 1, sameChecked: true, darkmode: false };
const markStyles = {
  full: { color: "#9BCDB2", text: "●" },
  partial: { color: "#F2B66D", text: "●" },
  attention: { color: "#F3A58E", text: "!" },
};
function markForDay(status) { return markStyles[status] || markStyles.partial; }

module.exports = { calendarTheme, calendarStyle, calendarConfig, markForDay };
