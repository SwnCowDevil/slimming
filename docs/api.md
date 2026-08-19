# API 使用说明

所有业务接口位于 `/api/v1`。除健康检查和微信登录外，接口都必须携带 `Authorization: Bearer <token>`；服务端从令牌读取内部用户 UUID，客户端不得自行传入用户 ID。

## 登录与用户身份

1. 小程序调用 `wx.login()` 获取一次性 `code`。
2. `POST /api/v1/auth/wechat` 将 `code` 交给后端。
3. 后端调用微信 `jscode2session`，按 `(app_id, openid)` 查找或创建内部用户 UUID，并返回 JWT。
4. 再次登录同一微信用户会得到同一个内部 UUID。
5. 昵称和头像只在用户主动点击“使用微信资料”后，通过 `PATCH /api/v1/auth/me/wechat-profile` 保存。

## 核心资源

- `POST /profiles/onboarding`：保存建档资料并计算 BMI、BMR、热量与宏量营养目标。
- `GET /foods/search?q=`：搜索已导入的 TKA 食物数据。
- `POST /admin/foods/import`：食品库运维接口，同时要求普通登录 JWT 与独立的 `X-Admin-Import-Key`，小程序用户不能调用。
- `POST /meals`：记录一项食物，必须携带 `Idempotency-Key`；营养数据以快照保存。
- `GET /meals?date=YYYY-MM-DD`：读取某日饮食。
- `POST /weights`：记录体重。
- `PUT /habits/YYYY-MM-DD`：保存喝水、步数等日习惯。
- `GET /analytics/summary?period=7|30|90`：读取体重、热量和营养趋势。
- `GET /recipes` 与 `POST /recipes/{id}/record`：食谱查询与一键记录。
- `POST /ai/drafts`：创建 AI 建议草稿；只有再次确认后才改变状态或写入餐食。
- `GET /dietitians` 与 `POST /dietitians/requests`：营养师筛选和服务申请。

交互式接口文档在开发环境的 `/docs`。
