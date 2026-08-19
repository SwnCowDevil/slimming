const { loginWithWechat } = require("./api/auth");

App({
  globalData: { session: null },
  onLaunch() {
    this.loginReady = loginWithWechat()
      .then((session) => {
        this.globalData.session = session;
        return session;
      })
      .catch((error) => {
        console.warn("微信身份初始化失败", error);
        this.loginError = error;
        return null;
      });
  },
});
