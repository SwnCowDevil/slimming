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

AI 食谱配置：

- `SLIMMING_AI_RECIPE_ENABLED`：默认 `false`，用于渐进启用。
- `SLIMMING_AI_PROVIDER=deepseek`、`SLIMMING_AI_BASE_URL=https://api.deepseek.com`：生产环境只允许官方域名。
- `SLIMMING_AI_MODEL`、`SLIMMING_AI_API_KEY`：模型名和服务端密钥；密钥只保存在部署环境，客户端和日志不得出现。
- `SLIMMING_AI_TIMEOUT_SECONDS`、`SLIMMING_AI_MAX_RETRIES`：单次上游超时与有限重试。
- `SLIMMING_AI_RECIPE_SESSION_TTL_HOURS`：未收藏候选的临时保存时间。
- `SLIMMING_AI_RECIPE_USER_LIMIT_PER_HOUR`、`SLIMMING_AI_RECIPE_IP_LIMIT_PER_HOUR`：用户和散列 IP 的小时限流。

DeepSeek 只接收粗粒度孕期阶段、已保存的过敏/忌口和本次推荐条件，不接收 openid、预产期原值、体重历史或既往饮食。上游关闭、配置缺失、超时或报错时，推荐接口回退到已审核平台食谱。轮换密钥时先在服务端更新环境变量并重启单实例验证，旧密钥确认无调用后再撤销。

## 数据库迁移

当前孕期版迁移链：

1. `0006_pregnancy_core`
2. `0007_tracking_ownership`
3. `0008_family_collaboration`
4. `0009_meal_plans`
5. `0010_pregnancy_guidance`
6. `0011_ai_policy`
7. `0012_ai_recipe_library`
8. `0013_recipe_steps`

生产发布前备份数据库，并在生产副本上验证升级。发布顺序是：构建新镜像 → 运行迁移 → 迁移成功后启动新服务 → 验证健康检查 → 发布小程序。服务回滚前必须确认旧版本可读取升级后的兼容字段；若必须回退数据库，先停写并从备份恢复或按已验证的 Alembic downgrade 执行。

## 验证

```sh
backend/.venv/bin/pytest -q backend/tests
```

## 基础食谱与临时候选运维

先导入合法获得的 TKA 数据，再导入 27 条平台食谱，以便后续食材尽可能匹配可追溯营养数据：

```sh
./scripts/import-tka-dataset.sh /absolute/path/to/tka-export.json DATASET_VERSION --execute
./scripts/import-platform-recipes.sh --execute
```

两个导入脚本默认均支持 dry-run；平台食谱导入按内容哈希幂等更新。生产执行前需确保数据文件位于 `SLIMMING_TKA_IMPORT_ROOT` 允许目录且后端已启动。

推荐会话是短期数据，不是收藏食谱或饮食历史。建议由部署调度器每天执行一次：

```sh
./scripts/cleanup-ai-recipe-sessions.sh
```

该命令分批删除已过期的临时推荐会话及其请求事件，不删除已收藏食谱、收藏关系或饮食记录。

完整发布顺序：备份数据库 → `alembic upgrade head` → 导入 TKA → 导入平台食谱 → 启动 API → 检查 `/health` → 小流量开启 AI 食谱开关 → 发布小程序。
