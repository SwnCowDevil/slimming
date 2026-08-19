const { request } = require("./client");
const { readSession, saveSession, shouldReuseSession } = require("../state/session");

function wxLoginCode() {
  return new Promise((resolve, reject) => {
    wx.login({ success: ({ code }) => (code ? resolve(code) : reject(new Error("微信登录未返回 code"))), fail: reject });
  });
}

async function loginWithWechat() {
  const existing = readSession();
  if (shouldReuseSession(existing)) return existing;
  const code = await wxLoginCode();
  const payload = await request({ url: "/api/v1/auth/wechat", method: "POST", data: { code }, authenticated: false });
  return saveSession({
    token: payload.access_token,
    userId: payload.user_id,
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

module.exports = { loginWithWechat, syncWechatProfile };
