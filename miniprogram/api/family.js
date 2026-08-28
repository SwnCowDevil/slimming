const { request } = require("./client");

function createInvitation() { return request({ url: "/api/v1/family/invitations", method: "POST" }); }
function acceptInvitation(token) { return request({ url: "/api/v1/family/invitations/accept", method: "POST", data: { token } }); }
function listMembers() { return request({ url: "/api/v1/family/members" }); }
function updatePermissions(id, permissionScopes) { return request({ url: `/api/v1/family/members/${id}/permissions`, method: "PATCH", data: { permission_scopes: permissionScopes } }); }
function revokeMember(id) { return request({ url: `/api/v1/family/members/${id}`, method: "DELETE" }); }
function listTasks(date, subjectUserId) { const subject = subjectUserId ? `&subject_user_id=${encodeURIComponent(subjectUserId)}` : ""; return request({ url: `/api/v1/family/tasks?date=${date}${subject}` }); }
function createTask(payload) { return request({ url: "/api/v1/family/tasks", method: "POST", data: payload }); }
function updateTask(id, payload) { return request({ url: `/api/v1/family/tasks/${id}`, method: "PATCH", data: payload }); }

module.exports = { createInvitation, acceptInvitation, listMembers, updatePermissions, revokeMember, listTasks, createTask, updateTask };
