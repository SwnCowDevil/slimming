import assert from "node:assert/strict";
import { createRequire } from "node:module";
import test from "node:test";

const require = createRequire(import.meta.url);
const { calendarTheme, calendarStyle, calendarConfig, markForDay } = require("../components/record-calendar/theme.js");

function parseInlineStyle(style) {
  return Object.fromEntries(
    style
      .split(";")
      .filter(Boolean)
      .map((entry) => entry.split(":")),
  );
}

test("calendar stays compact and uses light semantic colors", () => {
  assert.equal(calendarTheme["--wc-primary"], "#9BCDB2");
  assert.equal(calendarTheme["--wc-date-size"], "28rpx");
  assert.equal(calendarConfig.view, "week");
  assert.equal(calendarConfig.weekstart, 1);
  assert.equal(markForDay("attention").color, "#F3A58E");
});

test("calendar fills its padded card instead of using the viewport width", () => {
  const style = parseInlineStyle(calendarStyle);

  assert.equal(style.width, "100%");
  assert.equal(style["max-width"], "100%");
});
