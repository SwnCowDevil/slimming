import assert from "node:assert/strict";
import { createRequire } from "node:module";
import test from "node:test";

const require = createRequire(import.meta.url);
const { formatGestation, sortSchedules, actorLabel } = require("../utils/pregnancy.js");

test("pregnancy helpers format gestation and custom schedule order", () => {
  assert.equal(formatGestation({ week: 20, day: 3 }), "孕 20 周 3 天");
  assert.deepEqual(
    sortSchedules([
      { id: "late", position: 3 },
      { id: "early", position: 0 },
    ]).map((item) => item.id),
    ["early", "late"]
  );
});

test("actor label distinguishes self and family records", () => {
  assert.equal(actorLabel({ created_by_user_id: "u1" }, "u1"), "我记录");
  assert.equal(actorLabel({ created_by_user_id: "u2" }, "u1"), "家人记录");
});
