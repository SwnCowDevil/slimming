import test from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { buildLoginRequest } = require("../api/auth.js");

test("development login uses the stable local user id", () => {
  assert.deepEqual(buildLoginRequest("dev", "unused-code", "local-user-1"), {
    url: "/api/v1/auth/dev",
    data: { user_id: "local-user-1" },
  });
});

test("trial and release login keep the real WeChat code exchange", () => {
  assert.deepEqual(buildLoginRequest("wechat", "wx-code", "unused-local-id"), {
    url: "/api/v1/auth/wechat",
    data: { code: "wx-code" },
  });
});
