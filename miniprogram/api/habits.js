const { request } = require("./client");
function saveHabits(date, payload) { return request({ url: `/api/v1/habits/${date}`, method: "PUT", data: payload }); }
module.exports = { saveHabits };
