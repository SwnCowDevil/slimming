# 部署与发布

## 1. 本地开发

```sh
cp backend/.env.example backend/.env
./scripts/start-local.sh
./scripts/status-local.sh
./scripts/open-wechat-devtools.sh
```

本地后端默认监听 `http://127.0.0.1:8000`。端口冲突时使用 `LOCAL_PORT=18080 ./scripts/start-local.sh`，并将 `miniprogram/config/env.js` 的 develop 地址改为同一端口。停止与状态命令也应携带相同的 `LOCAL_PORT`。

`prototype/` 和 `superdesign/` 是视觉参考，不参与小程序构建、上传或后端部署。

## 2. 生产配置

```sh
cp deploy/backend.env.example deploy/backend.env
```

必须在服务器安全配置并定期轮换：

- `SLIMMING_JWT_SECRET`
- `SLIMMING_WECHAT_APP_ID`
- `SLIMMING_WECHAT_APP_SECRET`
- `SLIMMING_ADMIN_IMPORT_KEY`
- 可选的 AI 提供方地址、模型与密钥

`deploy/backend.env` 已被 Git 忽略。生产环境必须关闭开发登录，API 必须经 HTTPS 暴露。小程序代码中只能配置 API 地址，不能存放 AppSecret 或其他服务端密钥。

## 3. 数据库迁移与后端部署

当前迁移头为 `0011_ai_policy`。发布顺序：

1. 备份数据库及媒体目录。
2. 在生产数据副本执行 `alembic upgrade head` 并验证。
3. 构建后端镜像。
4. 使用一次性容器执行迁移。
5. 只有迁移成功后才启动新服务。
6. 检查 `/health`、登录、孕期档案和家庭授权。
7. 最后发布依赖新接口的小程序。

脚本默认仅显示计划：

```sh
./scripts/deploy-backend.sh --dry-run
DEPLOY_HOST=example.com DEPLOY_USER=deploy DEPLOY_DIR=/opt/slimming ./scripts/deploy-backend.sh --execute
```

单实例默认使用 Compose 具名卷中的 SQLite。横向扩展前应迁移到独立 PostgreSQL。服务回滚必须先确认旧后端兼容新 schema；无法确认时停止写入并从发布前备份恢复，不能在活跃写入期间直接降级数据库。

## 4. 微信预览与上传

先登录微信开发者工具，并在“设置 → 安全”开启服务端口：

```sh
export WECHAT_APP_ID='wx...'
./scripts/preview-miniprogram.sh --execute
./scripts/upload-miniprogram.sh --version 0.2.0 --description '孕期版' --execute
```

脚本会先构建 npm，再调用微信 CLI。上传脚本校验 AppID 一致性；未加 `--execute` 时不会连接或上传。体验版和正式版发布前，必须把 `miniprogram/config/env.js` 中对应 API 地址替换为真实 HTTPS 域名。
