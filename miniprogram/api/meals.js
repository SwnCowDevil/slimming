const { request } = require("./client");

function listMeals(date, subjectUserId) { const subject=subjectUserId?`&subject_user_id=${encodeURIComponent(subjectUserId)}`:"";return request({ url: `/api/v1/meals?date=${date}${subject}` }); }
function createMeal(payload, idempotencyKey) {
  return request({ url: "/api/v1/meals", method: "POST", data: payload, headers: { "Idempotency-Key": idempotencyKey } });
}
module.exports = { listMeals, createMeal };
