const { getEnvironment } = require("../config/env");
const { readSession, clearSession } = require("../state/session");

function waitForAuthenticatedSession(authenticated) {
  const session = readSession();
  if (!authenticated || session) return Promise.resolve(session);
  if (typeof getApp === "function") {
    const app = getApp();
    if (app && app.loginReady) return app.loginReady;
  }
  return Promise.resolve(null);
}

async function request({ url, method = "GET", data, headers = {}, authenticated = true }) {
  const session = await waitForAuthenticatedSession(authenticated);
  const authorization = authenticated && session ? { Authorization: `Bearer ${session.token}` } : {};
  return new Promise((resolve, reject) => {
    wx.request({
      url: `${getEnvironment().apiBaseUrl}${url}`,
      method,
      data,
      header: { "content-type": "application/json", ...authorization, ...headers },
      success(response) {
        if (response.statusCode === 401) clearSession();
        if (response.statusCode >= 200 && response.statusCode < 300) resolve(response.data);
        else reject({ statusCode: response.statusCode, data: response.data });
      },
      fail: reject,
    });
  });
}

module.exports = { request, waitForAuthenticatedSession };
