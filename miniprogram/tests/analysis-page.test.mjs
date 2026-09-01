import assert from "node:assert/strict";
import { createRequire } from "node:module";
import test from "node:test";

const require = createRequire(import.meta.url);

function loadPage() {
  let definition;
  global.Page = (config) => {
    definition = config;
  };
  delete require.cache[require.resolve("../pages/analysis/index.js")];
  require("../pages/analysis/index.js");
  delete global.Page;
  return definition;
}

test("selecting a trend end date updates the day and reloads the period", () => {
  const definition = loadPage();

  let reloads = 0;
  const context = {
    data: { endDate: "2026-09-01" },
    setData(patch, callback) {
      Object.assign(this.data, patch);
      if (callback) callback();
    },
    load() {
      reloads += 1;
    },
  };

  definition.changeEndDate.call(context, { detail: { value: "2026-08-19" } });

  assert.equal(context.data.endDate, "2026-08-19");
  assert.equal(reloads, 1);
});

test("period reflection uses the selected trend end date", async () => {
  const api = require("../api/ai.js");
  const original = api.createWeeklyReflection;
  const requests = [];
  api.createWeeklyReflection = async (period, endDate) => {
    requests.push({ period, endDate });
    return { response_text: "历史周期回顾" };
  };
  const definition = loadPage();
  const context = {
    ...definition,
    data: { ...definition.data, period: 30, endDate: "2026-08-19" },
    setData(patch) {
      Object.assign(this.data, patch);
    },
  };

  await definition.reflect.call(context);

  assert.deepEqual(requests, [{ period: 30, endDate: "2026-08-19" }]);
  assert.equal(context.data.insight, "历史周期回顾");
  api.createWeeklyReflection = original;
});
