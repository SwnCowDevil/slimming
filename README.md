# 轻减（Slimming）

健康减重管理微信小程序。前端使用原生微信小程序，后端使用 FastAPI；食品成分数据通过可追溯的 TKA 数据导入适配层提供。

设计规格：`docs/superpowers/specs/2026-08-19-slimming-mini-program-design.md`

实施计划：`docs/superpowers/plans/2026-08-19-slimming-mini-program-implementation.md`

真实密钥、微信上传私钥和服务器配置不得提交到仓库。

## 快速开始

```sh
cd backend
python3 -m venv .venv
.venv/bin/pip install -e '.[dev]'
cd ..
cp backend/.env.example backend/.env
./scripts/start-local.sh
./scripts/open-wechat-devtools.sh
```

小程序首次启动通过 `wx.login()` 换取服务端 JWT。后端以 `(微信 AppID, openid)` 创建稳定内部 UUID，餐食、体重、习惯、AI 草稿和营养师申请都按该 UUID 隔离保存；客户端不会自行指定用户 ID。

更多说明：

- [API 与微信身份](docs/api.md)
- [本地启动、后端部署和小程序上传](docs/deployment.md)
- [TKA 数据导入运维](docs/tka-data-operations.md)
- [小程序验收清单](miniprogram/qa/acceptance-checklist.md)
