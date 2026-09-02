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

test("recipe tab keeps its card flow and offers a lightweight AI entry", () => {
  const markup = read("../pages/recipes/index.wxml");
  const logic = read("../pages/recipes/index.js");

  assert.match(markup, /告诉我今天想吃什么/);
  assert.match(markup, /帮我推荐/);
  assert.match(markup, /recipe-card/);
  assert.match(logic, /options\.query/);
  assert.match(logic, /scope\s*=\s*["']favorites["']/);
  assert.match(logic, /onReachBottom/);
});

test("recipe recommendation button stays on one line without being squeezed", () => {
  const styles = read("../pages/recipes/index.wxss");
  const buttonRule = styles.match(/\.ai-entry button\s*\{([^}]*)\}/)?.[1] || "";

  assert.match(buttonRule, /white-space\s*:\s*nowrap/i);
  assert.match(buttonRule, /flex-shrink\s*:\s*0/i);
  assert.match(buttonRule, /width\s*:\s*auto/i);
  assert.doesNotMatch(buttonRule, /(?:^|;)width\s*:\s*142rpx/i);
});

test("AI recipe page has filters, free text, next batch and adjustment actions", () => {
  const markup = read("../pages/ai-recipes/index.wxml");
  const logic = read("../pages/ai-recipes/index.js");
  for (const required of ["餐次", "烹饪时长", "口味", "已有食材", "换一批", "调整条件"]) {
    assert.match(markup, new RegExp(required));
  }
  assert.match(logic, /!item\.candidateId\s*&&\s*item\.id/);
});

test("mixed or estimated recipes route through ingredient confirmation", () => {
  const detail = read("../pages/recipe-detail/index.js");
  assert.match(detail, /nutrition_source/);
  assert.match(detail, /recipe-confirm/);
});

test("recipe confirmation displays grams and source labels", () => {
  const markup = read("../pages/recipe-confirm/index.wxml");
  assert.match(markup, /确认食材与份量/);
  assert.match(markup, /克/);
  assert.match(markup, /AI 估算/);
});
