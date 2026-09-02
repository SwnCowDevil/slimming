const { request } = require("./client");

function recommendRecipes(payload, key) {
  return request({
    url: "/api/v1/ai/recipe-recommendations",
    method: "POST",
    data: payload,
    headers: { "Idempotency-Key": key },
  });
}

function nextRecipeBatch(sessionId, key) {
  return request({
    url: `/api/v1/ai/recipe-recommendations/${sessionId}/next`,
    method: "POST",
    headers: { "Idempotency-Key": key },
  });
}

function saveAiCandidate(candidateId) {
  return request({ url: `/api/v1/ai/recipe-candidates/${candidateId}/save`, method: "POST" });
}

module.exports = { recommendRecipes, nextRecipeBatch, saveAiCandidate };
