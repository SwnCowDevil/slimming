const { request } = require("./client");

function getMealPlan(date) { return request({ url: `/api/v1/meal-plans/${date}` }); }
function updateMealPlanItem(id, payload) { return request({ url: `/api/v1/meal-plans/items/${id}`, method: "PATCH", data: payload }); }

module.exports = { getMealPlan, updateMealPlanItem };
