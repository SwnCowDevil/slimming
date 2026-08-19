import test from "node:test";
import assert from "node:assert/strict";
import { createRequire } from "node:module";

const require = createRequire(import.meta.url);

test("authenticated requests wait for the app login promise", async () => {
  const { clearSession } = require("../state/session.js");
  clearSession();
  let release;
  const loginReady = new Promise((resolve) => { release = resolve; });
  global.getApp = () => ({ loginReady });
  delete require.cache[require.resolve("../api/client.js")];
  const { waitForAuthenticatedSession } = require("../api/client.js");

  let resolved = false;
  const waiting = waitForAuthenticatedSession(true).then(() => { resolved = true; });
  await Promise.resolve();
  assert.equal(resolved, false);
  release({ token: "token", userId: "user" });
  await waiting;
  assert.equal(resolved, true);
  delete global.getApp;
});
