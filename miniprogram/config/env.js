const environments = {
  develop: { apiBaseUrl: "http://127.0.0.1:8000", authMode: "wechat" },
  trial: { apiBaseUrl: "https://slimming.sunks.cc", authMode: "wechat" },
  release: { apiBaseUrl: "https://slimming.sunks.cc", authMode: "wechat" },
};

function getEnvironment() {
  try {
    const envVersion = wx.getAccountInfoSync().miniProgram.envVersion || "develop";
    return environments[envVersion] || environments.develop;
  } catch (_) {
    return environments.develop;
  }
}

module.exports = { environments, getEnvironment };
