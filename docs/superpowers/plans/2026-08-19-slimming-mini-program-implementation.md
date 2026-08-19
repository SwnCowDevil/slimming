# 健康减重管理小程序 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 按 `superdesign/` 设计稿交付可运行的原生微信小程序、FastAPI 后端、TKA 食品数据适配层，以及本地启动、服务器部署和微信预览/上传脚本。

**Architecture:** 前端使用原生微信小程序页面和聚焦职责的自定义组件，所有网络访问通过统一 API 客户端；日历由 `@lspriv/wx-calendar@1.8.4` 承担，图表由项目内固定版本的 `wx-charts` 通过 `health-chart` 包装组件承担。后端使用模块化 FastAPI + SQLAlchemy + Alembic，本地 SQLite、生产 PostgreSQL；食品数据通过 `FoodCompositionProvider` 导入经许可的数据文件并建立本地索引，业务请求不实时抓取 TKA/TAP 网页。

**Tech Stack:** 微信小程序基础库 ≥ 3.0.0、TypeScript/JavaScript、`@lspriv/wx-calendar@1.8.4`、vendored `xiaolin3303/wx-charts`、Python 3.12、FastAPI 0.116.1、Pydantic Settings 2.x、SQLAlchemy 2.x、Alembic 1.16+、pytest 8.x、SQLite/PostgreSQL、Docker Compose。

**Spec:** `docs/superpowers/specs/2026-08-19-slimming-mini-program-design.md`

## Global Constraints

- 视觉以 `superdesign/*.html` 和 `superdesign/design-system.md` 为唯一设计基准；不重新发明版式、色板或信息层级。
- 页面整体使用浅绿、浅蓝、浅黄、浅橙；不得出现大面积深绿、纯黑背景或超大字号。
- 页面左右边距 18px，模块间距 20–24px，卡片圆角 20–24px，按钮圆角 14–16px。
- 正文默认 14px、卡片标题 16–17px、说明 12px、图表标签不得小于 11px；非必要不使用粗体。
- 底部导航固定为今日、记录、食谱、分析、我的；AI 只嵌入页面和右上角入口，不增加独立 Tab。
- `wx-calendar` 固定使用 `1.8.4`，默认周视图；`wx-charts` 固定本地文件并由 `health-chart` 统一包装。
- TKA/TAP 不在用户请求链路中实时抓取；只导入已确认有权使用的数据。
- AI 只能生成草稿；正式营养值必须来自来源可追溯的食物记录或用户确认的自定义食物。
- 开发与测试不得依赖真实微信 AppSecret、AI Key、服务器密码或微信上传私钥。
- 所有密钥只从 `.env.local`、`backend/.env` 或部署环境读取；`superdesign/config.json` 永不进入版本控制。
- 每个任务先写失败测试，再写最小实现，再运行验证并单独提交。

## Planned File Structure

```text
backend/
  app/
    main.py                    # FastAPI 组装、生命周期和健康检查
    core/config.py             # 环境配置
    db/base.py                 # ORM Base
    db/session.py              # engine/session 工厂
    auth/                      # 微信登录与开发态身份
    profiles/                  # 建档、BMI/BMR、热量目标
    foods/                     # TKA provider、导入、搜索、别名
    meals/                     # 餐次与营养快照
    weights/                   # 体重记录
    analytics/                 # 7/30/90 天聚合
    recipes/                   # 食谱、收藏、一键记录
    ai_coach/                  # 草稿、安全规则、生成日志
    dietitians/                # 营养师展示与匹配申请
    media/                     # 图片上传元数据与识别任务
  alembic/                     # 数据库迁移
  tests/                       # pytest 单元和 API 测试
miniprogram/
  app.ts app.json app.wxss     # 小程序入口、路由、全局令牌
  api/                         # 统一请求与领域 API
  components/                  # calorie-card、meal-card、health-chart 等
  pages/                       # onboarding、today、record、recipes、analysis、profile
  assets/                      # 本地食物图、图标、tab 图标和来源清单
  vendor/wx-charts/            # 固定版本 wxcharts.js 与来源说明
scripts/                       # 本地服务、数据导入、构建、部署和上传
deploy/                        # Docker、Compose、Caddy、systemd 示例
```

---

### Task 1: 安全基线与项目骨架

**Files:**
- Create: `.gitignore`
- Create: `.env.example`
- Create: `backend/pyproject.toml`
- Create: `backend/.env.example`
- Create: `miniprogram/package.json`
- Create: `miniprogram/project.config.example.json`
- Create: `miniprogram/tsconfig.json`
- Create: `scripts/tests/security-baseline.sh`
- Modify: `README.md`

**Interfaces:**
- Produces: Python 包环境、微信 npm 环境、忽略规则和不包含真实密钥的示例配置。
- Consumes: 无。

- [ ] **Step 1: 写安全基线失败测试**

```sh
#!/bin/sh
set -eu
test -f .gitignore
grep -q '^superdesign/config.json$' .gitignore
grep -q '^backend/.env$' .gitignore
grep -q '^miniprogram/private\.' .gitignore
! git ls-files --error-unmatch superdesign/config.json >/dev/null 2>&1
```

- [ ] **Step 2: 运行测试并确认失败**

Run: `sh scripts/tests/security-baseline.sh`

Expected: FAIL，因为 `.gitignore` 尚不存在或未覆盖敏感文件。

- [ ] **Step 3: 创建最小骨架与固定依赖**

`backend/pyproject.toml` 至少包含：

```toml
[project]
name = "slimming-api"
version = "0.1.0"
requires-python = ">=3.12"
dependencies = [
  "fastapi==0.116.1", "uvicorn[standard]>=0.35,<1",
  "pydantic-settings>=2.10,<3", "sqlalchemy>=2.0,<3",
  "alembic>=1.16,<2", "httpx>=0.28,<1", "PyJWT>=2.10,<3",
  "python-multipart>=0.0.20,<1", "openpyxl>=3.1,<4"
]

[project.optional-dependencies]
dev = ["pytest>=8.4,<9", "pytest-asyncio>=1.1,<2"]
```

`miniprogram/package.json` 固定：

```json
{
  "private": true,
  "dependencies": {"@lspriv/wx-calendar": "1.8.4"},
  "devDependencies": {"miniprogram-api-typings": "^4.0.0"}
}
```

- [ ] **Step 4: 运行安全测试与配置解析检查**

Run: `sh scripts/tests/security-baseline.sh && cd backend && python3.12 -m pip install -e '.[dev]' --dry-run`

Expected: PASS；pip 能解析全部依赖且不安装。

- [ ] **Step 5: 提交骨架**

```bash
git add .gitignore .env.example README.md backend miniprogram scripts/tests/security-baseline.sh
git commit -m "chore: scaffold secure slimming project"
```

### Task 2: FastAPI 配置、数据库和健康检查

**Files:**
- Create: `backend/app/__init__.py`
- Create: `backend/app/main.py`
- Create: `backend/app/core/config.py`
- Create: `backend/app/db/base.py`
- Create: `backend/app/db/session.py`
- Create: `backend/app/auth/schemas.py`
- Create: `backend/app/auth/service.py`
- Create: `backend/app/auth/router.py`
- Create: `backend/alembic.ini`
- Create: `backend/alembic/env.py`
- Create: `backend/alembic/versions/0001_initial.py`
- Create: `backend/tests/conftest.py`
- Create: `backend/tests/test_health.py`
- Create: `backend/tests/auth/test_wechat_auth.py`

**Interfaces:**
- Produces: `create_app() -> FastAPI`、`get_session() -> Iterator[Session]`、`GET /health`、`POST /api/v1/auth/wechat`、`get_current_user() -> User`。
- Consumes: Task 1 的配置和依赖。

- [ ] **Step 1: 写健康检查失败测试**

```python
def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "service": "slimming-api"}

def test_dev_auth_is_only_available_when_enabled(client, settings):
    settings.enable_dev_auth = False
    assert client.post("/api/v1/auth/dev", json={"user_id": "demo"}).status_code == 404
```

- [ ] **Step 2: 运行测试并确认失败**

Run: `cd backend && pytest tests/test_health.py -v`

Expected: FAIL with `ModuleNotFoundError: app.main`。

- [ ] **Step 3: 实现配置、session 和应用工厂**

```python
def create_app() -> FastAPI:
    app = FastAPI(title="Slimming API", version="0.1.0")

    @app.get("/health")
    def health() -> dict[str, str]:
        return {"status": "ok", "service": "slimming-api"}

    return app

app = create_app()
```

配置字段使用 `SLIMMING_` 前缀：`DATABASE_URL`、`JWT_SECRET`、`WECHAT_APP_ID`、`WECHAT_APP_SECRET`、`ENABLE_DEV_AUTH`、`AI_BASE_URL`、`AI_MODEL`、`AI_API_KEY`、`MEDIA_ROOT`。微信登录服务用 `httpx` 调用 `jscode2session`，只存 `openid`/`unionid` 和内部用户 ID；开发态身份接口只有 `ENABLE_DEV_AUTH=true` 时注册。

- [ ] **Step 4: 创建空初始迁移并验证**

Run: `cd backend && alembic upgrade head && pytest tests/test_health.py tests/auth/test_wechat_auth.py -v`

Expected: migration success；health and auth tests passed；invalid WeChat code maps to 401 without exposing upstream body。

- [ ] **Step 5: 提交后端基础设施**

```bash
git add backend/app backend/alembic backend/alembic.ini backend/tests
git commit -m "feat: add FastAPI health and database foundation"
```

### Task 3: 用户建档、BMI/BMR 与热量目标

**Files:**
- Create: `backend/app/profiles/models.py`
- Create: `backend/app/profiles/schemas.py`
- Create: `backend/app/profiles/service.py`
- Create: `backend/app/profiles/router.py`
- Create: `backend/tests/profiles/test_calculations.py`
- Create: `backend/tests/profiles/test_profile_api.py`
- Modify: `backend/app/main.py`
- Modify: `backend/alembic/versions/0001_initial.py`

**Interfaces:**
- Produces: `calculate_bmi(weight_kg: Decimal, height_cm: Decimal) -> Decimal`；`calculate_bmr(profile: BodyProfile) -> Decimal`；`calculate_targets(profile: BodyProfile) -> NutritionTargets`；`POST /api/v1/profiles/onboarding`；`GET /api/v1/profiles/me`。
- Consumes: `get_session()`。

- [ ] **Step 1: 写计算失败测试**

```python
def test_bmi_rounds_to_one_decimal():
    assert calculate_bmi(Decimal("82"), Decimal("168")) == Decimal("29.1")

def test_calorie_target_stays_inside_safe_range():
    target = calculate_targets(sample_profile(goal="lose"))
    assert target.minimum_kcal <= target.daily_kcal <= target.maximum_kcal
```

- [ ] **Step 2: 运行测试并确认函数未定义**

Run: `cd backend && pytest tests/profiles/test_calculations.py -v`

Expected: FAIL with import error for `calculate_bmi`。

- [ ] **Step 3: 实现纯函数和建档模型**

```python
def calculate_bmi(weight_kg: Decimal, height_cm: Decimal) -> Decimal:
    metres = height_cm / Decimal("100")
    return (weight_kg / (metres * metres)).quantize(Decimal("0.1"))
```

`BodyProfile` 保存目标、出生日期/年龄、性别、身高、当前/目标体重、活动量、偏好、过敏源和外食频率；`NutritionTargets` 保存 BMR、建议热量范围和宏量营养目标。

- [ ] **Step 4: 增加 API 测试并运行领域测试**

Run: `cd backend && pytest tests/profiles -v`

Expected: BMI 29.1；建档返回 201；读取当前建档返回同一用户数据。

- [ ] **Step 5: 提交建档领域**

```bash
git add backend/app/profiles backend/app/main.py backend/alembic backend/tests/profiles
git commit -m "feat: add onboarding and nutrition target calculations"
```

### Task 4: TKA 数据适配、导入校验和本地检索

**Files:**
- Create: `backend/app/foods/provider.py`
- Create: `backend/app/foods/tka_provider.py`
- Create: `backend/app/foods/models.py`
- Create: `backend/app/foods/schemas.py`
- Create: `backend/app/foods/importer.py`
- Create: `backend/app/foods/service.py`
- Create: `backend/app/foods/router.py`
- Create: `backend/app/foods/cli.py`
- Create: `backend/tests/foods/fixtures/tka_sample.json`
- Create: `backend/tests/foods/test_tka_import.py`
- Create: `backend/tests/foods/test_food_search_api.py`
- Modify: `backend/app/main.py`
- Create: `backend/alembic/versions/0002_food_catalog.py`

**Interfaces:**
- Produces: `FoodCompositionProvider.import_dataset(path: Path, version: str) -> ImportReport`；`search(query: str, locale: str, limit: int) -> list[FoodHit]`；`get_food(source_food_id: str) -> FoodDetail | None`；`POST /api/v1/admin/foods/import`；`GET /api/v1/foods/search`；`GET /api/v1/foods/{food_id}`。
- Consumes: database session and `SLIMMING_TKA_IMPORT_ROOT`。

- [ ] **Step 1: 写导入失败测试**

```python
def test_import_preserves_source_and_normalizes_per_100g(session, fixture_path):
    report = TkaProvider(session).import_dataset(fixture_path, "fixture-2026-08")
    food = session.scalar(select(Food).where(Food.source_food_id == "8535"))
    assert report.imported == 1
    assert food.source_url == "https://tka.nutridata.ee/en/foods/3"
    assert food.energy_kcal_100g == Decimal("162")
    assert food.dataset_version == "fixture-2026-08"
```

- [ ] **Step 2: 运行测试并确认 provider 缺失**

Run: `cd backend && pytest tests/foods/test_tka_import.py -v`

Expected: FAIL with import error for `TkaProvider`。

- [ ] **Step 3: 实现标准化模型与事务导入**

```python
class FoodCompositionProvider(Protocol):
    def import_dataset(self, path: Path, version: str) -> ImportReport: ...
    def search(self, query: str, locale: str = "zh-CN", limit: int = 20) -> list[FoodHit]: ...
    def get_food(self, source_food_id: str) -> FoodDetail | None: ...
```

导入器拒绝未知单位、重复来源 ID、负营养值和缺少数据版本的文件；保存 `provider`、来源 URL、FoodEx2、方法/来源 ID、更新时间、原始记录 SHA-256。中文别名进入 `food_aliases`，不覆盖英文或爱沙尼亚语来源名。

- [ ] **Step 4: 验证导入、检索和无结果行为**

Run: `cd backend && pytest tests/foods -v`

Expected: fixture import passed；中文别名与英文同义词均可搜索；无结果返回空列表而非伪造数据。

- [ ] **Step 5: 提交食品目录**

```bash
git add backend/app/foods backend/alembic/versions/0002_food_catalog.py backend/tests/foods
git commit -m "feat: add traceable TKA food catalog adapter"
```

### Task 5: 饮食、体重和分析 API

**Files:**
- Create: `backend/app/meals/models.py`
- Create: `backend/app/meals/schemas.py`
- Create: `backend/app/meals/service.py`
- Create: `backend/app/meals/router.py`
- Create: `backend/app/weights/models.py`
- Create: `backend/app/weights/router.py`
- Create: `backend/app/habits/models.py`
- Create: `backend/app/habits/router.py`
- Create: `backend/app/analytics/schemas.py`
- Create: `backend/app/analytics/service.py`
- Create: `backend/app/analytics/router.py`
- Create: `backend/alembic/versions/0003_tracking.py`
- Create: `backend/tests/meals/test_meal_snapshot.py`
- Create: `backend/tests/habits/test_daily_habits.py`
- Create: `backend/tests/analytics/test_period_summary.py`
- Modify: `backend/app/main.py`

**Interfaces:**
- Produces: `create_meal_entry(command: MealEntryCreate) -> MealEntryRead`；`POST/GET/PATCH/DELETE /api/v1/meals`；`POST/GET /api/v1/weights`；`PUT/GET /api/v1/habits/{date}`（饮水和步数）；`GET /api/v1/analytics/summary?period=7|30|90`。
- Consumes: FoodDetail from Task 4 and NutritionTargets from Task 3.

- [ ] **Step 1: 写营养快照和移动平均失败测试**

```python
def test_meal_snapshot_does_not_change_after_catalog_update(session):
    entry = create_entry(session, grams=Decimal("150"), kcal_100g=Decimal("100"))
    update_catalog_food(session, kcal_100g=Decimal("120"))
    assert entry.energy_kcal == Decimal("150.0")

def test_seven_day_average_ignores_missing_days():
    points = build_weight_series([("2026-08-18", 68.4), ("2026-08-19", 68.2)])
    assert points[-1].moving_average_7d == Decimal("68.3")

def test_daily_habits_upsert_is_scoped_to_user(client):
    client.put("/api/v1/habits/2026-08-19", json={"water_ml": 1200, "steps": 6400})
    assert client.get("/api/v1/habits/2026-08-19").json()["water_ml"] == 1200
```

- [ ] **Step 2: 运行领域测试并确认失败**

Run: `cd backend && pytest tests/meals tests/habits tests/analytics -v`

Expected: FAIL because tracking services do not exist。

- [ ] **Step 3: 实现记录、幂等和服务端聚合**

营养快照保存来源、数据集版本、克数、换算依据和所有宏量营养值；创建接口接受 `Idempotency-Key`，同一用户与键重复提交返回原记录。分析响应固定包含：

```python
class AnalyticsSummary(BaseModel):
    period: Literal[7, 30, 90]
    weight_points: list[WeightPoint]
    calorie_days: list[CalorieDay]
    macro_achievement: MacroAchievement
    insight: PeriodInsight | None
```

- [ ] **Step 4: 运行跟踪 API 测试**

Run: `cd backend && pytest tests/meals tests/habits tests/analytics -v`

Expected: snapshots remain stable；duplicate idempotency key does not duplicate rows；water/steps upsert by user and date；7/30/90 responses validate。

- [ ] **Step 5: 提交核心跟踪闭环**

```bash
git add backend/app/meals backend/app/weights backend/app/habits backend/app/analytics backend/alembic backend/tests/meals backend/tests/habits backend/tests/analytics
git commit -m "feat: add meal weight and analytics tracking"
```

### Task 6: 食谱、AI 草稿、营养师和媒体边界

**Files:**
- Create: `backend/app/recipes/models.py`
- Create: `backend/app/recipes/router.py`
- Create: `backend/app/ai_coach/models.py`
- Create: `backend/app/ai_coach/safety.py`
- Create: `backend/app/ai_coach/service.py`
- Create: `backend/app/ai_coach/router.py`
- Create: `backend/app/dietitians/models.py`
- Create: `backend/app/dietitians/router.py`
- Create: `backend/app/media/models.py`
- Create: `backend/app/media/router.py`
- Create: `backend/alembic/versions/0004_guidance.py`
- Create: `backend/tests/ai_coach/test_safety.py`
- Create: `backend/tests/recipes/test_recipe_recording.py`
- Create: `backend/tests/dietitians/test_matching_request.py`
- Modify: `backend/app/main.py`

**Interfaces:**
- Produces: `GET /api/v1/recipes`、`POST /api/v1/recipes/{id}/record`、`POST /api/v1/ai/drafts`、`POST /api/v1/ai/drafts/{id}/confirm`、`GET /api/v1/dietitians`、`POST /api/v1/dietitian-requests`、`POST /api/v1/media/uploads`。
- Consumes: meal service, analytics summary and profile safety context.

- [ ] **Step 1: 写安全与草稿隔离失败测试**

```python
def test_pregnancy_context_routes_to_professional():
    result = evaluate_safety(AiContext(pregnancy=True))
    assert result.action == "refer_professional"

def test_ai_draft_never_creates_meal_before_confirmation(client):
    draft = client.post("/api/v1/ai/drafts", json=photo_candidate()).json()
    assert draft["status"] == "draft"
    assert client.get("/api/v1/meals").json()["items"] == []
```

- [ ] **Step 2: 运行测试并确认失败**

Run: `cd backend && pytest tests/ai_coach tests/recipes tests/dietitians -v`

Expected: FAIL because routers and safety service are absent。

- [ ] **Step 3: 实现首版有界能力**

AI 仅实现今日建议、单餐候选和周报解释；生成记录保存输入数据范围、模型、提示版本和安全结果。食谱营养值由现有食物快照汇总；营养师首版只展示资料并提交匹配申请，不实现支付或聊天。

- [ ] **Step 4: 运行边界测试**

Run: `cd backend && pytest tests/ai_coach tests/recipes tests/dietitians -v`

Expected: dangerous contexts return professional referral；draft confirmation creates exactly one meal；recipe one-click recording is idempotent。

- [ ] **Step 5: 提交指导服务**

```bash
git add backend/app/recipes backend/app/ai_coach backend/app/dietitians backend/app/media backend/alembic backend/tests
git commit -m "feat: add recipes AI drafts and dietitian requests"
```

### Task 7: 原生小程序基础、主题、鉴权与建档

**Files:**
- Create: `miniprogram/app.ts`
- Create: `miniprogram/app.json`
- Create: `miniprogram/app.wxss`
- Create: `miniprogram/api/client.ts`
- Create: `miniprogram/api/auth.ts`
- Create: `miniprogram/config/env.ts`
- Create: `miniprogram/styles/tokens.wxss`
- Create: `miniprogram/pages/onboarding/welcome/*`
- Create: `miniprogram/pages/onboarding/goal/*`
- Create: `miniprogram/pages/onboarding/body/*`
- Create: `miniprogram/pages/onboarding/life/*`
- Create: `miniprogram/pages/onboarding/plan/*`
- Create: `miniprogram/tests/onboarding.test.mjs`

**Interfaces:**
- Produces: `request<T>(options: ApiRequestOptions) -> Promise<T>`、本地 token store、五步建档路由和 Design Token。
- Consumes: Task 3 onboarding API；`superdesign/ob-*.html`。

- [ ] **Step 1: 写建档状态机失败测试**

```javascript
assert.deepEqual(nextStep({step: "goal", valid: true}), {step: "body"});
assert.equal(canSubmitBody({heightCm: 168, weightKg: 82}), true);
assert.equal(canSubmitBody({heightCm: 0, weightKg: 82}), false);
```

- [ ] **Step 2: 运行测试并确认模块不存在**

Run: `node --test miniprogram/tests/onboarding.test.mjs`

Expected: FAIL with module not found。

- [ ] **Step 3: 实现路由、请求层和建档页面**

将设计稿 CSS 数值转换为 rpx 时保持 375px 设计宽度；`app.wxss` 只放全局 reset 和 token。图片、图标和头像必须下载为本地许可资产并记录在 `miniprogram/assets/SOURCES.md`，不得运行时依赖 Unsplash、Iconify 或 DiceBear。

- [ ] **Step 4: 构建 npm 并运行静态检查**

Run: `cd miniprogram && npm install && node --test tests/onboarding.test.mjs`

Expected: dependencies locked；tests passed；`miniprogram_npm/@lspriv/wx-calendar` can be generated by WeChat build npm。

- [ ] **Step 5: 提交小程序基础**

```bash
git add miniprogram
git commit -m "feat: add native mini-program onboarding foundation"
```

### Task 8: 今日页、记录页和 `wx-calendar`

**Files:**
- Create: `miniprogram/api/meals.ts`
- Create: `miniprogram/api/habits.ts`
- Create: `miniprogram/components/calorie-card/*`
- Create: `miniprogram/components/nutrient-bars/*`
- Create: `miniprogram/components/meal-card/*`
- Create: `miniprogram/components/ai-tip/*`
- Create: `miniprogram/components/record-calendar/*`
- Create: `miniprogram/pages/today/*`
- Create: `miniprogram/pages/record/*`
- Create: `miniprogram/pages/photo-recognition/*`
- Create: `miniprogram/state/offline-drafts.ts`
- Create: `miniprogram/tests/calendar-theme.test.mjs`
- Create: `miniprogram/tests/meal-calculation.test.mjs`

**Interfaces:**
- Produces: `RecordCalendar` events `datechange` and `viewchange`；`scaleNutrients(per100g, grams)`；`saveOfflineDraft(draft)` / `syncOfflineDrafts()`；今日页、记录页和拍照候选确认交互。
- Consumes: Task 5 meal/weight APIs；`@lspriv/wx-calendar@1.8.4`；`superdesign/today.html` and `record.html`。

- [ ] **Step 1: 写日历主题与份量换算失败测试**

```javascript
assert.equal(calendarTheme["--wc-primary"], "#78A992");
assert.equal(calendarTheme["--wc-date-size"], "28rpx");
assert.deepEqual(scaleNutrients({kcal: 162, protein: 0.2}, 150), {kcal: 243, protein: 0.3});
assert.equal(reconcileDrafts([{id: "a", updatedAt: 2}], [{id: "a", updatedAt: 1}])[0].updatedAt, 2);
```

- [ ] **Step 2: 运行测试并确认失败**

Run: `node --test miniprogram/tests/calendar-theme.test.mjs miniprogram/tests/meal-calculation.test.mjs`

Expected: FAIL because theme and calculation modules do not exist。

- [ ] **Step 3: 实现浅色日历包装组件**

`record-calendar` 使用 `view="week"`、`weekstart="1"`、`same-checked="true"`、`darkmode="false"`；保留 `header/title/today/viewbar/dragbar`，隐藏农历。完整记录用浅绿点、部分记录用浅橙点、超预算用浅珊瑚角标；选中态 `#DDEFE7`，今日 `#F7C98B`，周视图高度不超过 264rpx。

- [ ] **Step 4: 实现今日和记录核心交互并验证**

Run: `node --test miniprogram/tests/*.test.mjs`

Expected: date change debounced to one API request；gram adjustment recalculates and persists；network failure saves a local draft；sync requires user confirmation before creating a formal record；empty meal groups show add action。

- [ ] **Step 5: 提交今日与记录页面**

```bash
git add miniprogram/api miniprogram/components miniprogram/pages/today miniprogram/pages/record miniprogram/tests
git commit -m "feat: build today and record flows with wx-calendar"
```

### Task 9: 食谱页、我的页和工具入口

**Files:**
- Create: `miniprogram/api/recipes.ts`
- Create: `miniprogram/api/profile.ts`
- Create: `miniprogram/api/ai.ts`
- Create: `miniprogram/components/recipe-card/*`
- Create: `miniprogram/components/ai-entry/*`
- Create: `miniprogram/pages/recipes/*`
- Create: `miniprogram/pages/recipe-detail/*`
- Create: `miniprogram/pages/profile/*`
- Create: `miniprogram/pages/bmi/*`
- Create: `miniprogram/pages/bmr/*`
- Create: `miniprogram/pages/food-search/*`
- Create: `miniprogram/pages/food-estimate/*`
- Create: `miniprogram/pages/ai-coach/*`
- Create: `miniprogram/pages/dietitians/*`
- Create: `miniprogram/pages/settings/*`
- Create: `miniprogram/pages/privacy/*`
- Create: `miniprogram/pages/data-sources/*`
- Create: `miniprogram/tests/recipe-filter.test.mjs`

**Interfaces:**
- Produces: recipe filters, favorite state, one-click meal draft, BMI/BMR tools, food-estimation guide, TKA food search, AI draft/weekly interpretation and dietitian request UI.
- Consumes: Tasks 3, 4 and 6 APIs；`superdesign/recipes.html` and `profile.html`。

- [ ] **Step 1: 写食谱过滤失败测试**

```javascript
assert.deepEqual(
  applyRecipeFilters(recipes, {maxMinutes: 15, highProtein: true}).map(x => x.id),
  ["quick-chicken-bowl"]
);
```

- [ ] **Step 2: 运行测试并确认失败**

Run: `node --test miniprogram/tests/recipe-filter.test.mjs`

Expected: FAIL because filter module does not exist。

- [ ] **Step 3: 实现页面与共享组件**

食谱大图保持自然光俯拍；卡片不叠加深色遮罩。我的页按当前体重/目标/BMI、工具、收藏/计划、营养师和设置分组；AI 入口仅使用右上角小图标和浅色建议卡。

- [ ] **Step 4: 运行测试并在开发者工具检查路由**

Run: `node --test miniprogram/tests/*.test.mjs`

Expected: filters deterministic；favorite and one-click draft states survive page re-entry；all declared pages exist。

- [ ] **Step 5: 提交内容与个人中心**

```bash
git add miniprogram/api miniprogram/components miniprogram/pages miniprogram/tests
git commit -m "feat: add recipes profile tools and dietitian flow"
```

### Task 10: 分析页和 `wx-charts` 包装组件

**Files:**
- Create: `miniprogram/vendor/wx-charts/wxcharts.js`
- Create: `miniprogram/vendor/wx-charts/README.md`
- Create: `miniprogram/components/health-chart/index.ts`
- Create: `miniprogram/components/health-chart/index.json`
- Create: `miniprogram/components/health-chart/index.wxml`
- Create: `miniprogram/components/health-chart/index.wxss`
- Create: `miniprogram/components/chart-legend/*`
- Create: `miniprogram/pages/analysis/*`
- Create: `miniprogram/tests/chart-options.test.mjs`

**Interfaces:**
- Produces: `buildWeightChart(summary, size) -> WxChartOptions`；`buildCalorieChart(summary, size) -> WxChartOptions`；component methods `render(options)` and `dispose()`。
- Consumes: Task 5 analytics API；pinned wx-charts source；`superdesign/analysis.html`。

- [ ] **Step 1: 写图表主题失败测试**

```javascript
const options = buildWeightChart(sampleSummary, {width: 339, height: 200, dpr: 3});
assert.equal(options.type, "line");
assert.equal(options.series[0].color, "#8EBFE8");
assert.equal(options.series[1].color, "#F4B978");
assert.equal(options.legend, false);
assert.ok(options.categories.length <= 7);
```

- [ ] **Step 2: 运行测试并确认失败**

Run: `node --test miniprogram/tests/chart-options.test.mjs`

Expected: FAIL because chart option builders do not exist。

- [ ] **Step 3: 固定并记录 wx-charts 来源**

复制上游 `dist/wxcharts.js` 到 vendor；`README.md` 记录仓库 URL、获取日期、commit SHA 和文件 SHA-256。包装组件统一处理设备 DPR、180–220px 高度、最多 4 条 Y 轴网格、11px 标签、白色 WXML tooltip、空状态和页面卸载时 `dispose()`。

- [ ] **Step 4: 实现 7/30/90 天图表并运行测试**

Run: `node --test miniprogram/tests/chart-options.test.mjs`

Expected: line and column options use light palette；fewer than 2 weight points returns empty state；period switch stops previous animation before redraw。

- [ ] **Step 5: 提交分析页面**

```bash
git add miniprogram/vendor miniprogram/components/health-chart miniprogram/components/chart-legend miniprogram/pages/analysis miniprogram/tests/chart-options.test.mjs
git commit -m "feat: add light analytics charts with wx-charts"
```

### Task 11: 本地启动、TKA 导入、服务器部署和微信上传脚本

**Files:**
- Create: `scripts/local-service-lib.sh`
- Create: `scripts/start-local.sh`
- Create: `scripts/stop-local.sh`
- Create: `scripts/status-local.sh`
- Create: `scripts/restart-backend.sh`
- Create: `scripts/import-tka-dataset.sh`
- Create: `scripts/build-backend-image.sh`
- Create: `scripts/deploy-backend.sh`
- Create: `scripts/open-wechat-devtools.sh`
- Create: `scripts/preview-miniprogram.sh`
- Create: `scripts/upload-miniprogram.sh`
- Create: `scripts/tests/local-service-scripts.sh`
- Create: `scripts/tests/release-scripts.sh`
- Create: `deploy/Dockerfile.backend`
- Create: `deploy/docker-compose.backend.yml`
- Create: `deploy/Caddyfile.example`
- Create: `deploy/slimming-api.service`

**Interfaces:**
- Produces: local PID/log/health workflow；safe data import；Docker build；dry-run deployment；WeChat open/preview/upload commands.
- Consumes: Task 2 health endpoint, Task 4 CLI and WeChat developer tools CLI.

- [ ] **Step 1: 写脚本行为失败测试**

```sh
assert_contains "$(./scripts/deploy-backend.sh --dry-run)" "DRY RUN"
assert_contains "$(./scripts/upload-miniprogram.sh --help)" "WECHAT_PRIVATE_KEY_PATH"
assert_fails ./scripts/upload-miniprogram.sh --version 0.1.0 --description test
```

- [ ] **Step 2: 运行测试并确认脚本缺失**

Run: `sh scripts/tests/local-service-scripts.sh && sh scripts/tests/release-scripts.sh`

Expected: FAIL because scripts are absent。

- [ ] **Step 3: 实现 travelling 风格的本地服务脚本**

`start-local.sh` 检查端口 8000、`backend/.venv`、`backend/.env`，执行 Alembic，再以 PID/log 文件启动 Uvicorn，并轮询 `/health`；stop/status/restart 验证 PID 对应命令行，不误杀其他进程。

- [ ] **Step 4: 实现安全发布脚本并验证 dry-run**

后端部署从 `DEPLOY_HOST`、`DEPLOY_USER`、`DEPLOY_DIR` 读取目标；微信上传从 `WECHAT_APP_ID`、`WECHAT_PRIVATE_KEY_PATH`、版本与说明读取参数。没有必需变量时退出非零；所有远端和上传脚本默认 dry-run，只有 `--execute` 才改变外部状态。

Run: `sh scripts/tests/local-service-scripts.sh && sh scripts/tests/release-scripts.sh`

Expected: all tests passed；dry-run 不调用 ssh、docker push 或微信上传。

- [ ] **Step 5: 提交运维脚本**

```bash
git add scripts deploy
git commit -m "feat: add local deployment and WeChat release scripts"
```

### Task 12: 集成测试、视觉 QA 和交付文档

**Files:**
- Create: `backend/tests/e2e/test_user_journey.py`
- Create: `miniprogram/qa/acceptance-checklist.md`
- Create: `docs/api.md`
- Create: `docs/deployment.md`
- Create: `docs/tka-data-operations.md`
- Modify: `README.md`
- Modify: `superdesign/design-system.md`

**Interfaces:**
- Produces: 可重复的端到端验证、设计对照清单、启动/部署/数据运营说明。
- Consumes: Tasks 1–11 的所有接口和设计稿。

- [ ] **Step 1: 写端到端失败测试**

```python
def test_onboard_record_and_analyze(client, imported_food):
    onboard_user(client)
    record_meal(client, imported_food, grams=150)
    record_weight(client, weight_kg=68.2)
    summary = client.get("/api/v1/analytics/summary?period=7").json()
    assert summary["calorie_days"][-1]["consumed_kcal"] > 0
    assert summary["weight_points"][-1]["weight_kg"] == 68.2
```

- [ ] **Step 2: 运行全量自动化测试**

Run: `cd backend && pytest -q && cd ../miniprogram && node --test tests/*.test.mjs && cd .. && sh scripts/tests/security-baseline.sh && sh scripts/tests/local-service-scripts.sh && sh scripts/tests/release-scripts.sh`

Expected: if integration gaps remain, tests fail with exact missing route, field or script behavior。

- [ ] **Step 3: 修复集成差异并完成文档**

`README.md` 提供环境准备、本地启动、微信开发者工具打开方式和测试命令；`docs/tka-data-operations.md` 说明许可门槛、文件格式、dry-run、版本回滚和来源追踪；`docs/deployment.md` 说明 Docker 与 systemd 两种方式以及全部环境变量。

- [ ] **Step 4: 执行设计对照和真机检查**

在用户当前选定的应用内浏览器/微信开发者工具中，以 375px 等效视口逐页对照 `superdesign`：今日、记录、食谱、分析、我的和五个建档页。检查字体、字重、浅色令牌、卡片边距、圆角、图片裁切、日历周/月状态、图表 tooltip、空数据、长文案、iOS/Android 安全区。每个差异记录“参考/实装/修复结果”，修复后再次对照。

- [ ] **Step 5: 运行最终验证并提交交付文档**

Run: `cd backend && pytest -q && cd ../miniprogram && node --test tests/*.test.mjs && cd .. && git diff --check`

Expected: all tests passed；no whitespace errors；acceptance checklist completed without open severity-1 or severity-2 items。

```bash
git add backend/tests/e2e miniprogram/qa docs README.md superdesign/design-system.md
git commit -m "docs: complete slimming app integration handoff"
```

## Final Verification

- [ ] `./scripts/start-local.sh` starts the migrated API and `/health` returns 200.
- [ ] `./scripts/import-tka-dataset.sh --dry-run <fixture>` validates without writing; explicit execute imports traceable records.
- [ ] WeChat developer tools opens the native project and builds npm successfully.
- [ ] Onboarding → food search → meal record → weight record → 7-day analysis works end to end.
- [ ] `wx-calendar` defaults to compact week view and uses the approved light marks and selection styles.
- [ ] `wx-charts` uses the approved light palette, readable labels, custom WXML legend/tooltip, and correct empty states.
- [ ] AI candidates remain drafts until confirmation and safety referral tests pass.
- [ ] No real secrets are tracked; upload and deployment scripts default to dry-run.
- [ ] Full backend, mini-program and script test suites pass from a clean checkout.
