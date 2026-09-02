import assert from "node:assert/strict";
import { createRequire } from "node:module";
import test from "node:test";

const require = createRequire(import.meta.url);

for (const envVersion of ["trial", "release"]) {
  test(`${envVersion} requests use the production slimming API`, async () => {
    let requestedUrl = "";
    global.wx = {
      getStorageSync() { return null; },
      getAccountInfoSync() { return { miniProgram: { envVersion } }; },
      request(options) {
        requestedUrl = options.url;
        options.success({ statusCode: 200, data: { status: "ok" } });
      },
    };

    delete require.cache[require.resolve("../config/env.js")];
    delete require.cache[require.resolve("../api/client.js")];
    const { request } = require("../api/client.js");

    await request({ url: "/health", authenticated: false });

    assert.equal(requestedUrl, "https://slimming.sunks.cc/health");
    delete global.wx;
  });
}
