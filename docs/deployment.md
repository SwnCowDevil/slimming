# 部署与发布

## 1. 本地开发

```sh
cp backend/.env.example backend/.env
./scripts/start-local.sh
./scripts/status-local.sh
./scripts/open-wechat-devtools.sh
```

本地后端默认监听 `http://127.0.0.1:8000`。端口冲突时使用 `LOCAL_PORT=18080 ./scripts/start-local.sh`，并将 `miniprogram/config/env.js` 的 develop 地址改为同一端口。停止与状态命令也应携带相同的 `LOCAL_PORT`。体验版与正式版固定访问 `https://slimming.sunks.cc`。

`prototype/` 和 `superdesign/` 是视觉参考，不参与小程序构建、上传或后端部署。

## 2. 生产配置

```sh
sudo install -d -m 700 /etc/slimming
sudo install -m 600 deploy/backend.env.example /etc/slimming/slimming-api.env
```

必须在服务器安全配置并定期轮换：

- `SLIMMING_JWT_SECRET`
- `SLIMMING_WECHAT_APP_ID`
- `SLIMMING_WECHAT_APP_SECRET`
- `SLIMMING_ADMIN_IMPORT_KEY`
- 可选的 AI 提供方地址、模型与密钥

`/etc/slimming/slimming-api.env` 只保存在服务器，不能放入项目目录或提交 Git。生产环境必须关闭开发登录，API 必须经 HTTPS 暴露。小程序代码中只能配置 API 地址，不能存放 AppSecret 或其他服务端密钥。

## 3. 数据库迁移与后端部署

当前迁移头为 `0015_ai_coach_rate_limit`。发布顺序：

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
DEPLOY_HOST=服务器地址 \
DEPLOY_USER=deploy \
DEPLOY_DIR=/opt/slimming \
DEPLOY_SSH_KEY=.local/slimming-deploy-key \
./scripts/deploy-backend.sh --execute
```

目标服务器需预先准备可执行的 `/opt/slimming/.runtime/python3.12/bin/python3.12`。运行时独立保存在 slimming 目录，不随每次代码包上传，也不共享 travelling 的容器、配置或数据。构建基础系统镜像来自阿里云镜像仓库，Python 依赖通过阿里云 PyPI 镜像安装，因此不依赖目标服务器访问 Docker Hub。

生产容器监听宿主机 `127.0.0.1:8001`，与 travelling 使用的 `127.0.0.1:8000` 隔离。SQLite 和媒体目录保存在 `/opt/slimming/backend/data`。将 `deploy/Caddyfile.example` 中的站点块合并到服务器 Caddyfile 后，先执行 `caddy validate`，再平滑重载。阿里云 DNS 还需添加 `slimming.sunks.cc` 指向服务器公网 IP 的 A 记录，解析生效后验证 `https://slimming.sunks.cc/health`。

横向扩展前应迁移到独立 PostgreSQL。服务回滚必须先确认旧后端兼容新 schema；无法确认时停止写入并从发布前备份恢复，不能在活跃写入期间直接降级数据库。

## 4. 微信预览与上传

先登录微信开发者工具，并在“设置 → 安全”开启服务端口：

```sh
export WECHAT_APP_ID='wx...'
./scripts/preview-miniprogram.sh --execute
./scripts/upload-miniprogram.sh --version 0.2.0 --description '孕期版' --execute
```

脚本会先构建 npm，再调用微信 CLI。上传脚本校验 AppID 一致性；未加 `--execute` 时不会连接或上传。体验版和正式版自动使用 `https://slimming.sunks.cc`；还需在微信公众平台将该地址加入 request 合法域名。
