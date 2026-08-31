import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { readFileSync } from "node:fs";
import test from "node:test";

const require = createRequire(import.meta.url);

function loadPage() {
  let definition;
  global.Page = (page) => { definition = page; };
  delete require.cache[require.resolve("../pages/ai-coach/index.js")];
  require("../pages/ai-coach/index.js");
  delete global.Page;
  return definition;
}

function mountPage(definition) {
  return {
    ...definition,
    data: { ...definition.data },
    setData(update) { Object.assign(this.data, update); },
  };
}

test("AI review displays the weekly reflection returned by the backend", async () => {
  const api = require("../api/ai.js");
  const original = api.createWeeklyReflection;
  const requestedPeriods = [];
  api.createWeeklyReflection = async (period) => {
    requestedPeriods.push(period);
    return {
      id: "reflection-1",
      response_text: "这一周已经记录了两天，继续按真实情况记录即可。",
      model_name: "deepseek-v4-flash",
      prompt_version: "pregnancy-reflection-v1",
    };
  };
  global.wx = { showToast() {} };
  const page = mountPage(loadPage());

  await page.generate({ currentTarget: { dataset: { period: 7 } } });

  assert.deepEqual(requestedPeriods, [7]);
  assert.equal(page.data.draftText, "这一周已经记录了两天，继续按真实情况记录即可。");
  assert.equal(page.data.loading, false);

  await page.generate({ currentTarget: { dataset: { period: 30 } } });
  await page.generate({ currentTarget: { dataset: { period: page.data.currentPeriod } } });

  assert.deepEqual(requestedPeriods, [7, 30, 30]);
  api.createWeeklyReflection = original;
  delete global.wx;
});

test("AI review shows loading only on the button that was tapped", async () => {
  const api = require("../api/ai.js");
  const original = api.createWeeklyReflection;
  let resolveRequest;
  api.createWeeklyReflection = () => new Promise((resolve) => { resolveRequest = resolve; });
  global.wx = { showToast() {} };
  const page = mountPage(loadPage());

  const pending = page.generate({
    currentTarget: { dataset: { period: 7, loadingKey: "prompt-7" } },
  });

  assert.equal(page.data.loading, true);
  assert.equal(page.data.loadingKey, "prompt-7");
  const markup = readFileSync(new URL("../pages/ai-coach/index.wxml", import.meta.url), "utf8");
  assert.match(markup, /loading="\{\{loadingKey===item\.loadingKey\}\}"/);
  assert.match(markup, /loading="\{\{loadingKey==='regenerate'\}\}"/);

  resolveRequest({ response_text: "回顾完成。", model_name: "test", prompt_version: "v1" });
  await pending;
  assert.equal(page.data.loading, false);
  assert.equal(page.data.loadingKey, "");
  api.createWeeklyReflection = original;
  delete global.wx;
});
