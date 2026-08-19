const environments = {
  develop: { apiBaseUrl: "http://127.0.0.1:8000" },
  trial: { apiBaseUrl: "https://api.example.com" },
  release: { apiBaseUrl: "https://api.example.com" },
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
