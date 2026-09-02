# API 使用说明

业务接口位于 `/api/v1`。除健康检查和微信登录外，接口必须携带 `Authorization: Bearer <token>`。服务端从令牌读取内部用户 UUID；客户端不得把任意用户 ID 当作授权依据。

## 微信身份

1. 小程序调用 `wx.login()` 获取一次性 code。
2. `POST /api/v1/auth/wechat` 由后端向微信换取 openid。
3. 后端按 `(AppID, openid)` 查找或创建稳定内部 UUID，并签发 JWT。
4. 餐食、体重等记录同时保存数据所有者、实际操作人和孕期档案关联。
5. 昵称与头像仅在用户主动授权后通过 `PATCH /api/v1/auth/me/wechat-profile` 保存。
6. `DELETE /api/v1/auth/me` 永久删除当前账户及关联记录，旧 JWT 随即失效。

## 孕期与餐次

- `POST /pregnancies`：创建当前孕期档案。
- `GET|PATCH /pregnancies/current`：读取或修正当前孕期。
- `POST /pregnancies/current/end`：结束当前孕期。
- `GET|POST /meal-schedules`、`PATCH /meal-schedules/{id}`：管理默认或自定义餐次时间。
- `GET|PUT /wellbeing/{date}`：读取或保存当日身体感受。
- `GET /meal-plans/{date}`：按餐次生成当日餐单。

## 记录、趋势与食谱

- `GET|POST /meals`：读取或记录饮食；写入要求幂等键并保存营养快照。
- `GET|POST /weights`：读取或记录体重，保存所有者与操作人。
- `GET /analytics/summary?period=7|30|90`：孕期模式返回事实卡、饮食多样性与体重趋势，不返回减重预算。
- `GET /recipes`：按孕期阶段、过敏原、审核状态等筛选食谱。
- `POST /recipes/{id}/record`：以食谱营养快照记入指定餐次。

## 家庭协作

- `POST /family/invitations`、`POST /family/invitations/accept`：创建或接受一次性邀请。
- `GET /family/members`：按服务端身份返回档案所有者或家属视图。
- `PATCH /family/members/{id}/permissions`：由档案所有者调整 scope。
- `DELETE /family/members/{id}`：撤销共享并写入授权事件。
- `GET|POST /family/tasks`、`PATCH /family/tasks/{id}`：采购或准备任务。

明文邀请码不入库；家属每次访问都重新经过后端授权检查，撤销后不再具备读取或写入权限。

## AI 白名单

- `POST /ai/drafts`：食物候选草稿。
- `POST /ai/weekly-reflections`：周记录整理。
- `POST /ai/recipe-swaps`：已审核食谱范围内的替换解释。
- `POST /ai/drafts/{id}/confirm`：用户确认草稿。

高风险上下文返回固定转介文案，不生成个体化医疗结论。交互式接口文档在开发环境的 `/docs`。
