import assert from "node:assert/strict";
import fs from "node:fs";
import test from "node:test";

const read = (path) => fs.readFileSync(new URL(path, import.meta.url), "utf8");

test("the mini program presents a pregnancy product instead of a weight-loss product", () => {
  const app = JSON.parse(read("../app.json"));
  const profile = read("../pages/profile/index.wxml");
  const profileLogic = read("../pages/profile/index.js");
  const recipeDetail = read("../pages/recipe-detail/index.wxml");

  assert.equal(app.window.navigationBarTitleText, "孕食记");
  assert.equal(app.tabBar.selectedColor, "#86B6DC");
  assert.doesNotMatch(profile, /目标体重|target_weight/);
  assert.doesNotMatch(profileLogic, /getProfile/);
  assert.match(profileLogic, /preferences\.current_weight_kg/);
  assert.doesNotMatch(recipeDetail, /剩余目标|热量预算/);
});

test("privacy copy explains pregnancy data and revocable family access", () => {
  const privacy = read("../pages/privacy/index.wxml");
  const settings = read("../pages/settings/index.wxml");

  for (const required of ["预产期", "体重", "饮食", "身体感受", "随时撤销", "删除账户"]) {
    assert.match(privacy, new RegExp(required));
  }
  assert.doesNotMatch(privacy, /诊断|治疗方案/);
  assert.match(settings, /删除账户/);
});

test("data-source copy distinguishes imported TKA data from TAP tooling", () => {
  const source = read("../pages/data-sources/index.wxml");

  assert.match(source, /TKA/);
  assert.match(source, /TAP/);
  assert.match(source, /不会实时抓取/);
});
