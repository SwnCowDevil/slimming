# 孕食记原生微信小程序

客户端使用 WXML、WXSS 和 JavaScript。`wx-calendar` 固定为 `@lspriv/wx-calendar@1.8.4`，趋势图统一通过本地 `wx-charts` 包装组件绘制。

## 开发

```sh
npm install --prefix miniprogram
./scripts/start-local.sh
./scripts/open-wechat-devtools.sh
```

在微信开发者工具中执行“工具 → 构建 npm”，或运行：

```sh
./scripts/preview-miniprogram.sh --execute
```

开发、体验和正式环境 API 地址在 `config/env.js` 中分开配置。体验版与正式版必须使用已备案的 HTTPS 域名，并在微信公众平台配置 request 合法域名；不要把 AppSecret 放入小程序代码。

微信身份流程为 `wx.login()` → 后端 `/api/v1/auth/wechat` → JWT。后端根据 `(AppID, openid)` 创建稳定内部用户 UUID，业务数据按该 UUID、孕期档案所有者和操作人保存。昵称、头像只在用户主动授权后同步。

## 页面约束

- Tab：今日、记录、食谱、趋势、家庭。
- 今日与记录按可编辑餐次展示，餐间使用独立浅色卡片与间距。
- 食谱沿用原生小程序既有布局和样式。
- 趋势只展示孕期事实、饮食多样性和体重记录，不展示减重热量预算。
- 家庭权限由后端返回的角色与 scope 决定，前端不得自行伪造角色。

## 测试与发布

```sh
npm test --prefix miniprogram
export WECHAT_APP_ID='wx...'
./scripts/upload-miniprogram.sh --version 0.2.0 --description '孕期版' --execute
```

上传脚本会核对环境 AppID 与 `project.config.json`，并拒绝 `touristappid`。发布前按 `qa/acceptance-checklist.md` 在真机验证授权、弱网、撤权和敏感文案。
