const { request } = require("./client");

function listMeals(date) { return request({ url: `/api/v1/meals?date=${date}` }); }
function createMeal(payload, idempotencyKey) {
  return request({ url: "/api/v1/meals", method: "POST", data: payload, headers: { "Idempotency-Key": idempotencyKey } });
}
module.exports = { listMeals, createMeal };
