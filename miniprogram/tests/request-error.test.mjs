import test from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);
const { requestErrorMessage } = require("../utils/errors.js");

test("request errors expose the backend detail instead of a generic onboarding toast", () => {
  assert.equal(
    requestErrorMessage({ statusCode: 401, data: { detail: "微信登录失败，请重试" } }),
    "微信登录失败，请重试",
  );
});

test("network failures keep a useful fallback", () => {
  assert.equal(requestErrorMessage({ errMsg: "request:fail" }), "网络连接失败，请检查后端服务");
});
