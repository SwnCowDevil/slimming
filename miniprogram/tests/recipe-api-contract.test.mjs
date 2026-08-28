import assert from "node:assert/strict";
import { createRequire } from "node:module";
import test from "node:test";

const require = createRequire(import.meta.url);

function stubClient(calls) {
  const clientPath = require.resolve("../api/client.js");
  require.cache[clientPath] = {
    id: clientPath,
    filename: clientPath,
    loaded: true,
    exports: { request(options) { calls.push(options); return Promise.resolve({}); } },
  };
}

test("AI recipe API sends exact endpoints and idempotency headers", async () => {
  const calls = [];
  stubClient(calls);
  delete require.cache[require.resolve("../api/ai-recipes.js")];
  const api = require("../api/ai-recipes.js");

  await api.recommendRecipes({ query: "清淡" }, "initial-key");
  await api.nextRecipeBatch("session-1", "next-key");
  await api.saveAiCandidate("candidate-1");

  assert.deepEqual(calls, [
    { url: "/api/v1/ai/recipe-recommendations", method: "POST", data: { query: "清淡" }, headers: { "Idempotency-Key": "initial-key" } },
    { url: "/api/v1/ai/recipe-recommendations/session-1/next", method: "POST", headers: { "Idempotency-Key": "next-key" } },
    { url: "/api/v1/ai/recipe-candidates/candidate-1/save", method: "POST" },
  ]);
});

test("recipe API supports search, favorites and confirmed recording", async () => {
  const calls = [];
  stubClient(calls);
  delete require.cache[require.resolve("../api/recipes.js")];
  const api = require("../api/recipes.js");

  await api.listRecipes({ query: "番茄", scope: "favorites" });
  await api.favoriteRecipe("recipe-1");
  await api.unfavoriteRecipe("recipe-1");

  assert.equal(calls[0].url, "/api/v1/recipes?query=%E7%95%AA%E8%8C%84&scope=favorites");
  assert.deepEqual(calls[1], { url: "/api/v1/recipes/recipe-1/favorite", method: "POST" });
  assert.deepEqual(calls[2], { url: "/api/v1/recipes/recipe-1/favorite", method: "DELETE" });
});
