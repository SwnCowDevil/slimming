import assert from "node:assert/strict";
import { createRequire } from "node:module";
import test from "node:test";

const require = createRequire(import.meta.url);
const { calendarTheme, calendarConfig, markForDay } = require("../components/record-calendar/theme.js");

test("calendar stays compact and uses light semantic colors", () => {
  assert.equal(calendarTheme["--wc-primary"], "#9BCDB2");
  assert.equal(calendarTheme["--wc-date-size"], "28rpx");
  assert.equal(calendarConfig.view, "week");
  assert.equal(calendarConfig.weekstart, 1);
  assert.equal(markForDay("attention").color, "#F3A58E");
});
