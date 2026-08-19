# 部署与发布

## 本地开发

```sh
cp backend/.env.example backend/.env
./scripts/start-local.sh
./scripts/status-local.sh
./scripts/open-wechat-devtools.sh
```

本地后端默认监听 `http://127.0.0.1:8000`。若端口已被其他项目占用，可运行 `LOCAL_PORT=18080 ./scripts/start-local.sh`。停止服务运行 `./scripts/stop-local.sh`，只重启后端运行 `./scripts/restart-backend.sh`；使用自定义端口时，停止和查看状态也应带相同的 `LOCAL_PORT`。

## 后端部署

服务器准备好 Docker、Compose 和域名后：

```sh
cp deploy/backend.env.example deploy/backend.env
./scripts/deploy-backend.sh --dry-run
./scripts/deploy-backend.sh --execute
```

`deploy/backend.env` 已被 Git 忽略；部署脚本会将它随部署配置安全复制到服务器，但不会纳入版本库。

部署脚本先上传 `backend/` 与 `deploy/`，再在服务器用 Compose 构建、迁移并启动 FastAPI。默认 Compose 使用具名卷 `slimming_data` 中的 SQLite，适合单实例；需要横向扩展时再把 `DATABASE_URL` 切换到独立 PostgreSQL。HTTPS 由服务器现有 Caddy 承担，可参考 `deploy/Caddyfile.example`。生产环境必须设置随机 `JWT_SECRET`、微信 AppID/AppSecret 和真实 HTTPS 域名。

## 微信预览与上传

先在微信开发者工具“设置 → 安全”中开启服务端口，并登录目标小程序账号。

```sh
export WECHAT_APP_ID='wx...'
./scripts/preview-miniprogram.sh --execute
./scripts/upload-miniprogram.sh --version 0.1.0 --description '首个可测试版本' --execute
```

上传前脚本会校验 `WECHAT_APP_ID` 与本地 `project.config.json` 的 AppID 完全一致，并拒绝 `touristappid`。两个脚本默认只打印计划，只有显式传入 `--execute` 才会调用官方微信开发者工具 CLI。
