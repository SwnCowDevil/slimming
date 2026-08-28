# 孕食记 FastAPI 后端

## 本地环境

从仓库根目录执行：

```sh
python3.12 -m venv backend/.venv
backend/.venv/bin/pip install -e 'backend[dev]'
cp backend/.env.example backend/.env
./scripts/start-local.sh
```

启动脚本会先执行 `alembic upgrade head`，再启动单进程 Uvicorn。健康检查为 `GET /health`，开发接口文档为 `/docs`。

## 配置契约

`backend/.env` 仅在本机或服务器创建，不纳入 Git。必需配置：

- `SLIMMING_DATABASE_URL`：数据库连接；变量名前缀为兼容旧部署保留。
- `SLIMMING_JWT_SECRET`：至少 32 个随机字符。
- `SLIMMING_WECHAT_APP_ID`、`SLIMMING_WECHAT_APP_SECRET`：微信登录换取 openid。
- `SLIMMING_ADMIN_IMPORT_KEY`：食品数据导入独立管理密钥。
- `SLIMMING_ENABLE_DEV_AUTH=false`：生产环境必须关闭开发登录。

AI 配置为可选项；未配置时不得伪造模型结果。日志和文档示例不得包含真实密钥。

## 数据库迁移

当前孕期版迁移链：

1. `0006_pregnancy_core`
2. `0007_tracking_ownership`
3. `0008_family_collaboration`
4. `0009_meal_plans`
5. `0010_pregnancy_guidance`
6. `0011_ai_policy`

生产发布前备份数据库，并在生产副本上验证升级。发布顺序是：构建新镜像 → 运行迁移 → 迁移成功后启动新服务 → 验证健康检查 → 发布小程序。服务回滚前必须确认旧版本可读取升级后的兼容字段；若必须回退数据库，先停写并从备份恢复或按已验证的 Alembic downgrade 执行。

## 验证

```sh
backend/.venv/bin/pytest -q backend/tests
```
