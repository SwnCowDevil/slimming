const { request } = require("./client");
const { readSession, saveSession, shouldReuseSession } = require("../state/session");
const { getEnvironment } = require("../config/env");

const DEV_USER_KEY = "slimming.dev-user-id.v1";

function wxLoginCode() {
  return new Promise((resolve, reject) => {
    wx.login({ success: ({ code }) => (code ? resolve(code) : reject(new Error("微信登录未返回 code"))), fail: reject });
  });
}

function getOrCreateDevUserId() {
  const existing = wx.getStorageSync(DEV_USER_KEY);
  if (existing) return existing;
  const created = `local-${Date.now()}-${Math.random().toString(36).slice(2, 10)}`;
  wx.setStorageSync(DEV_USER_KEY, created);
  return created;
}

function buildLoginRequest(authMode, code, devUserId) {
  if (authMode === "dev") return { url: "/api/v1/auth/dev", data: { user_id: devUserId } };
  return { url: "/api/v1/auth/wechat", data: { code } };
}

async function loginWithWechat() {
  const environment = getEnvironment();
  const existing = readSession();
  if (shouldReuseSession(existing) && existing.apiBaseUrl === environment.apiBaseUrl && existing.authMode === environment.authMode) return existing;
  const code = environment.authMode === "wechat" ? await wxLoginCode() : "";
  const loginRequest = buildLoginRequest(environment.authMode, code, environment.authMode === "dev" ? getOrCreateDevUserId() : "");
  const payload = await request({ ...loginRequest, method: "POST", authenticated: false });
  return saveSession({
    token: payload.access_token,
    userId: payload.user_id,
    apiBaseUrl: environment.apiBaseUrl,
    authMode: environment.authMode,
    expiresAt: Date.now() + 6.5 * 24 * 60 * 60 * 1000,
  });
}

function syncWechatProfile({ nickName, avatarUrl }) {
  return request({
    url: "/api/v1/auth/me/wechat-profile",
    method: "PATCH",
    data: { nickname: nickName, avatar_url: avatarUrl || null },
  });
}

function deleteAccount() {
  return request({ url: "/api/v1/auth/me", method: "DELETE" });
}

module.exports = { buildLoginRequest, deleteAccount, loginWithWechat, syncWechatProfile };
