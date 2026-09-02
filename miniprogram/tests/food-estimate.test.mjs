import assert from "node:assert/strict";
import { createRequire } from "node:module";
import { readFileSync } from "node:fs";
import test from "node:test";

const require = createRequire(import.meta.url);

function loadPage(modulePath) {
  let definition;
  global.Page = (page) => { definition = page; };
  delete require.cache[require.resolve(modulePath)];
  require(modulePath);
  delete global.Page;
  return definition;
}

function mountPage(definition, data = {}) {
  return {
    ...definition,
    data: { ...definition.data, ...data },
    setData(update, callback) {
      Object.assign(this.data, update);
      if (callback) callback();
    },
  };
}

test("food estimate filters practical references and recalculates half portions", () => {
  const page = mountPage(loadPage("../pages/food-estimate/index.js"));

  page.selectCategory({ currentTarget: { dataset: { key: "fruit" } } });
  assert.deepEqual(page.data.visibleItems.map((item) => item.name), ["苹果", "香蕉"]);

  page.adjust({ currentTarget: { dataset: { id: "apple", delta: 1 } } });
  const apple = page.data.visibleItems.find((item) => item.id === "apple");
  assert.equal(apple.portions, 1.5);
  assert.equal(apple.gramsLabel, "约 225–300 克");
});

test("food estimate carries its date and keyword into confirmed food search", () => {
  const navigations = [];
  global.wx = { navigateTo: ({ url }) => navigations.push(url) };
  const page = mountPage(loadPage("../pages/food-estimate/index.js"), { mealDate: "2026-08-31" });

  page.record({ currentTarget: { dataset: { keyword: "苹果" } } });

  assert.deepEqual(navigations, ["/pages/food-search/index?date=2026-08-31&q=%E8%8B%B9%E6%9E%9C"]);
  delete global.wx;
});

test("today and record entries open food estimate instead of photo recognition", () => {
  const navigations = [];
  global.wx = { navigateTo: ({ url }) => navigations.push(url) };

  const today = mountPage(loadPage("../pages/today/index.js"));
  today.estimateFood();
  const record = mountPage(loadPage("../pages/record/index.js"), { selectedDate: "2026-08-30" });
  record.estimateFood();

  assert.match(navigations[0], /^\/pages\/food-estimate\/index\?date=\d{4}-\d{2}-\d{2}$/);
  assert.equal(navigations[1], "/pages/food-estimate/index?date=2026-08-30");
  delete global.wx;
});

test("the shipped mini program no longer registers the photo recognition page", () => {
  const appConfig = JSON.parse(readFileSync(new URL("../app.json", import.meta.url), "utf8"));

  assert.equal(appConfig.pages.includes("pages/photo-recognition/index"), false);
  assert.equal(appConfig.pages.includes("pages/food-estimate/index"), true);
});
