import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";

const read = (path) => fs.readFileSync(new URL(path, import.meta.url), "utf8");

test("global buttons vertically center their labels", () => {
  const styles = read("../app.wxss");
  assert.match(styles, /button\s*\{[^}]*display\s*:\s*flex/i);
  assert.match(styles, /button\s*\{[^}]*align-items\s*:\s*center/i);
  assert.match(styles, /button\s*\{[^}]*justify-content\s*:\s*center/i);
  assert.match(styles, /button\s*\{[^}]*line-height\s*:\s*1\.2/i);
});

test("record page is a history timeline instead of another meal-plan page", () => {
  const markup = read("../pages/record/index.wxml");
  const config = JSON.parse(read("../pages/record/index.json"));

  assert.doesNotMatch(markup, /<pregnancy-meal/);
  assert.match(markup, /timelineGroups/);
  assert.equal("pregnancy-meal" in config.usingComponents, false);
  assert.doesNotMatch(markup, /点击时间可修改/);
});

test("food search decodes route keywords before encoding the API request", () => {
  const logic = read("../pages/food-search/index.js");

  assert.match(logic, /query\s*:\s*decodeURIComponent\(query\.q\s*\|\|\s*["']{2}\)/);
});

test("fallback recipes open food search with a searchable ingredient keyword", () => {
  const detailLogic = read("../pages/recipe-detail/index.js");
  const fallbackRecipes = read("../data/recipes.js");

  assert.match(detailLogic, /recipe\.searchKeyword\s*\|\|\s*recipe\.title/);
  assert.match(fallbackRecipes, /searchKeyword\s*:\s*["']鸡胸肉["']/);
});
