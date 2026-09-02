import test from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { localDateKey } = require("../utils/date.js");

test("local date key keeps the user's local calendar day", () => {
  assert.equal(localDateKey(new Date(2026, 7, 20, 0, 30, 0)), "2026-08-20");
});
