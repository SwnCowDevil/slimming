const { request } = require("./client");

function getCurrentPregnancy() { return request({ url: "/api/v1/pregnancies/current" }); }
function createPregnancy(payload) { return request({ url: "/api/v1/pregnancies", method: "POST", data: payload }); }
function updatePregnancy(payload) { return request({ url: "/api/v1/pregnancies/current", method: "PATCH", data: payload }); }
function endPregnancy() { return request({ url: "/api/v1/pregnancies/current/end", method: "POST" }); }
function listMealSchedules() { return request({ url: "/api/v1/meal-schedules" }); }
function updateMealSchedule(id, payload) { return request({ url: `/api/v1/meal-schedules/${id}`, method: "PATCH", data: payload }); }
function getWellbeing(date) { return request({ url: `/api/v1/wellbeing/${date}` }); }
function saveWellbeing(date, payload) { return request({ url: `/api/v1/wellbeing/${date}`, method: "PUT", data: payload }); }

module.exports = { getCurrentPregnancy, createPregnancy, updatePregnancy, endPregnancy, listMealSchedules, updateMealSchedule, getWellbeing, saveWellbeing };
