# Pregnancy Product Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Upgrade the existing native WeChat mini program and FastAPI service from slimming semantics to a pregnancy-only household meal-management product without destroying legacy data.

**Architecture:** Add pregnancy, meal-schedule, family, meal-plan, consent, recipe-guidance, and ownership capabilities through additive SQLAlchemy models and Alembic migrations. Keep WeChat identity and food/meal snapshot foundations, expose pregnancy-aware APIs, then replace the native mini-program Today, Record, Analysis, and Profile/Family flows while preserving the existing Recipes tab structure and visual design.

**Tech Stack:** Native WeChat Mini Program (WXML/WXSS/JavaScript), `@lspriv/wx-calendar`, project-wrapped `wx-charts`, FastAPI 0.116, Pydantic 2, SQLAlchemy 2, Alembic, Pytest, Node test runner.

**Spec:** `docs/superpowers/specs/2026-08-27-pregnancy-product-data-architecture-design.md`

## Global Constraints

- Formal frontend work is limited to `miniprogram/`; `prototype/` is reference-only and must not enter the production build.
- Current release scope is pregnancy only; no preconception or postpartum product flow.
- Recipes keeps the existing native page structure and single-column large-card visual design from `docs/superpowers/specs/2026-08-27-pregnancy-recipe-tab-redesign.md`.
- Today, Record, Trend, and Family use the later light pregnancy design: no large dark green, dark blue-gray, black cards, or heavy gradients.
- Pregnancy mode never calls the legacy calorie-deficit or target-weight algorithm.
- WeChat users retain internal UUID identity; partner access is independently authenticated and server-authorized on every request.
- Data ownership (`subject_user_id`) and actor (`created_by_user_id`) are distinct for partner-entered records.
- AI is not a standalone tab, cannot generate authoritative nutrition numbers, and cannot directly mutate formal records.
- TKA/TAP-derived food composition is separate from versioned pregnancy guidance and reviewed recipe-safety content.
- All schema changes use additive Alembic migrations with legacy-data backfill and downgrade support.

---

### Task 1: Pregnancy Core Domain and Profile API

**Files:**
- Create: `backend/app/pregnancies/__init__.py`
- Create: `backend/app/pregnancies/models.py`
- Create: `backend/app/pregnancies/schemas.py`
- Create: `backend/app/pregnancies/service.py`
- Create: `backend/app/pregnancies/router.py`
- Create: `backend/tests/pregnancies/test_profile_api.py`
- Create: `backend/alembic/versions/0006_pregnancy_core.py`
- Modify: `backend/app/auth/models.py`
- Modify: `backend/app/db/base.py`
- Modify: `backend/app/main.py`

**Interfaces:**
- Produces: `PregnancyEpisode`, `PregnancyPreference`, `MealSchedule`, `DailyWellbeingLog` ORM models.
- Produces: `derive_gestation(due_date: date, today: date) -> GestationRead`.
- Produces: `POST /api/v1/pregnancies`, `GET/PATCH /api/v1/pregnancies/current`, `POST /api/v1/pregnancies/current/end`.
- Produces: `GET/POST/PATCH /api/v1/meal-schedules` and `GET/PUT /api/v1/wellbeing/{date}`.

- [ ] **Step 1: Write failing pregnancy profile tests**

Create API tests that assert a logged-in user can create one active pregnancy profile, receives a server-derived gestational week, gets `product_mode="pregnancy"`, cannot create a second active episode, and can end the current episode without entering postpartum mode.

- [ ] **Step 2: Verify the tests fail for missing routes**

Run: `backend/.venv/bin/pytest -q backend/tests/pregnancies/test_profile_api.py`

Expected: FAIL because `/api/v1/pregnancies` is not registered.

- [ ] **Step 3: Add pregnancy models, validation, and service logic**

Implement `derive_gestation` from due date and local date, input validation for a plausible due-date window, one active episode per user, preference persistence, and an atomic update of `User.product_mode` when creating the episode.

- [ ] **Step 4: Register routes and write migration 0006**

Add `users.product_mode` with server default `legacy_slimming`; create pregnancy episodes, preferences, meal schedules, and wellbeing logs with indexes and uniqueness constraints. Import models in `db/base.py` and include the router in `main.py`.

- [ ] **Step 5: Run focused and baseline backend tests**

Run: `backend/.venv/bin/pytest -q backend/tests/pregnancies/test_profile_api.py backend/tests/auth backend/tests/profiles`

Expected: all selected tests pass and legacy profile calculations remain unchanged for legacy mode.

- [ ] **Step 6: Commit**

```bash
git add backend/app/pregnancies backend/app/auth/models.py backend/app/db/base.py backend/app/main.py backend/alembic/versions/0006_pregnancy_core.py backend/tests/pregnancies
git commit -m "feat: add pregnancy profile core"
```

### Task 2: Custom Meal Schedules and Wellbeing Records

**Files:**
- Modify: `backend/app/pregnancies/router.py`
- Modify: `backend/app/pregnancies/schemas.py`
- Modify: `backend/app/pregnancies/service.py`
- Create: `backend/tests/pregnancies/test_meal_schedules.py`
- Create: `backend/tests/pregnancies/test_wellbeing.py`

**Interfaces:**
- Consumes: `PregnancyEpisode`, `MealSchedule`, `DailyWellbeingLog` from Task 1.
- Produces: `MealScheduleRead` with `id`, `code`, `display_name`, `scheduled_time`, `position`, and `enabled`.
- Produces: `WellbeingRead` with date, selected feeling codes, and optional note.

- [ ] **Step 1: Write failing schedule and wellbeing API tests**

Test default five-meal creation, `HH:mm` validation, custom time persistence, stable ordering, disabled schedules, and one wellbeing record per date with update semantics.

- [ ] **Step 2: Verify failures identify missing behavior**

Run: `backend/.venv/bin/pytest -q backend/tests/pregnancies/test_meal_schedules.py backend/tests/pregnancies/test_wellbeing.py`

Expected: FAIL on missing routes or empty default schedules.

- [ ] **Step 3: Implement minimal service and routes**

Create default breakfast, morning snack, lunch, afternoon snack, and dinner schedules when an episode is created. Validate schedule ownership and return wellbeing data only to its owner.

- [ ] **Step 4: Run focused tests**

Run: `backend/.venv/bin/pytest -q backend/tests/pregnancies`

Expected: all pregnancy tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/pregnancies backend/tests/pregnancies
git commit -m "feat: support pregnancy meal schedules"
```

### Task 3: Tracking Ownership Migration

**Files:**
- Modify: `backend/app/meals/models.py`
- Modify: `backend/app/meals/schemas.py`
- Modify: `backend/app/meals/service.py`
- Modify: `backend/app/meals/router.py`
- Modify: `backend/app/weights/models.py`
- Modify: `backend/app/weights/router.py`
- Create: `backend/alembic/versions/0007_tracking_ownership.py`
- Create: `backend/tests/meals/test_record_ownership.py`
- Modify: `backend/tests/meals/test_meal_snapshot.py`
- Modify: `backend/tests/e2e/test_user_isolation.py`

**Interfaces:**
- Consumes: current user, current pregnancy episode, optional `meal_schedule_id`.
- Produces: meal/weight records with nullable `pregnancy_episode_id`, `subject_user_id`, and required `created_by_user_id` after application-level backfill.
- Keeps: legacy `user_id` and existing idempotency behavior during transition.

- [ ] **Step 1: Write a failing ownership test**

Assert a self-recorded meal returns the same UUID for `subject_user_id` and `created_by_user_id`, links the active episode, keeps source nutrition snapshot values, and rejects another user's `subject_user_id` without family permission.

- [ ] **Step 2: Verify the ownership test fails**

Run: `backend/.venv/bin/pytest -q backend/tests/meals/test_record_ownership.py`

Expected: FAIL because ownership fields are absent.

- [ ] **Step 3: Implement additive ORM/schema/service changes**

Default self-recording ownership on the server. Accept a schedule ID only when it belongs to the subject's active episode. Continue deriving nutrition from the food catalog and retain idempotency.

- [ ] **Step 4: Add migration and backfill**

Add nullable columns, backfill `subject_user_id` and `created_by_user_id` from `user_id`, then add indexes and foreign keys supported by both SQLite and PostgreSQL batch migration behavior.

- [ ] **Step 5: Run meal, weight, and isolation tests**

Run: `backend/.venv/bin/pytest -q backend/tests/meals backend/tests/e2e/test_user_isolation.py backend/tests/habits`

Expected: all selected tests pass.

- [ ] **Step 6: Commit**

```bash
git add backend/app/meals backend/app/weights backend/alembic/versions/0007_tracking_ownership.py backend/tests/meals backend/tests/e2e/test_user_isolation.py
git commit -m "feat: separate health data owner and actor"
```

### Task 4: Family Invitation, Permission, and Revocation

**Files:**
- Create: `backend/app/family/__init__.py`
- Create: `backend/app/family/models.py`
- Create: `backend/app/family/schemas.py`
- Create: `backend/app/family/service.py`
- Create: `backend/app/family/router.py`
- Create: `backend/alembic/versions/0008_family_collaboration.py`
- Modify: `backend/app/db/base.py`
- Modify: `backend/app/main.py`
- Modify: `backend/app/meals/router.py`
- Create: `backend/tests/family/test_permissions.py`
- Create: `backend/tests/family/test_partner_meal_entry.py`

**Interfaces:**
- Produces: `authorize_subject(session, actor_user_id, subject_user_id, scope) -> PregnancyEpisode`.
- Produces: invitation creation/acceptance, member listing, permission update, revocation, and family-task APIs.
- Consumes: meal ownership fields from Task 3.

- [ ] **Step 1: Write failing multi-user authorization tests**

Use two WeChat identities to assert default scopes, single-use/expiry behavior, inability to self-accept, partner read access, denied meal entry before `meal_entry:write_for_owner`, accepted meal entry afterward, and immediate denial after revocation.

- [ ] **Step 2: Verify tests fail because family routes do not exist**

Run: `backend/.venv/bin/pytest -q backend/tests/family`

Expected: FAIL with missing route responses.

- [ ] **Step 3: Implement family models and authorization service**

Store only invitation token hashes. Make membership status and permission scopes server authoritative. Record immutable consent events for invite, accept, permission change, and revoke.

- [ ] **Step 4: Register routes and integrate meal authorization**

Resolve subject ownership through `authorize_subject`; never trust a frontend-supplied role. Record partner-entered meals with subject as owner and current user as actor.

- [ ] **Step 5: Add migration 0008 and run tests**

Run: `backend/.venv/bin/pytest -q backend/tests/family backend/tests/meals backend/tests/e2e`

Expected: all selected tests pass, including cross-user isolation.

- [ ] **Step 6: Commit**

```bash
git add backend/app/family backend/app/meals backend/app/db/base.py backend/app/main.py backend/alembic/versions/0008_family_collaboration.py backend/tests/family
git commit -m "feat: add consent-based family collaboration"
```

### Task 5: Meal Plans and Household Tasks

**Files:**
- Create: `backend/app/meal_plans/__init__.py`
- Create: `backend/app/meal_plans/models.py`
- Create: `backend/app/meal_plans/schemas.py`
- Create: `backend/app/meal_plans/router.py`
- Create: `backend/app/meal_plans/service.py`
- Create: `backend/alembic/versions/0009_meal_plans.py`
- Modify: `backend/app/db/base.py`
- Modify: `backend/app/main.py`
- Create: `backend/tests/meal_plans/test_daily_plan.py`
- Create: `backend/tests/family/test_tasks.py`

**Interfaces:**
- Produces: `GET /api/v1/meal-plans/{date}` and status/update endpoints.
- Produces: `GET/POST/PATCH /api/v1/family/tasks` with assignee and status.
- Consumes: active pregnancy, custom schedules, recipes, and family authorization.

- [ ] **Step 1: Write failing daily-plan and task tests**

Assert a new day returns one plan item per enabled schedule, plan times reflect persisted custom schedules, partner cooking updates require scope, and task completion records the acting user.

- [ ] **Step 2: Verify tests fail**

Run: `backend/.venv/bin/pytest -q backend/tests/meal_plans backend/tests/family/test_tasks.py`

Expected: FAIL because the service and tables are absent.

- [ ] **Step 3: Implement deterministic plan materialization and tasks**

Materialize empty daily rows from enabled schedules without inventing nutrition or recipes. Persist plan item title snapshots, state, assignee, and audit actor.

- [ ] **Step 4: Run focused tests**

Run: `backend/.venv/bin/pytest -q backend/tests/meal_plans backend/tests/family`

Expected: all selected tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/meal_plans backend/app/family backend/app/db/base.py backend/app/main.py backend/alembic/versions/0009_meal_plans.py backend/tests/meal_plans backend/tests/family/test_tasks.py
git commit -m "feat: add daily meal plans and family tasks"
```

### Task 6: Reviewed Recipe Nutrition and Existing Tab Contract

**Files:**
- Modify: `backend/app/recipes/models.py`
- Modify: `backend/app/recipes/schemas.py`
- Modify: `backend/app/recipes/router.py`
- Create: `backend/app/recipes/service.py`
- Create: `backend/alembic/versions/0010_pregnancy_guidance.py`
- Create: `backend/tests/recipes/test_recipe_listing.py`
- Modify: `backend/tests/recipes/test_recipe_recording.py`
- Modify: `miniprogram/utils/recipe-filter.js`
- Modify: `miniprogram/pages/recipes/index.js`
- Create: `miniprogram/tests/recipe-normalize.test.mjs`

**Interfaces:**
- Produces recipe list fields: `energy_kcal`, `subtitle`, `safety_summary`, `content_version`, and existing fields.
- Produces query filters: `max_minutes`, `tag`, `high_protein`, `limit`, `offset`.
- Preserves the current WXML/WXSS Recipes layout.

- [ ] **Step 1: Write failing backend recipe-list contract tests**

Assert only published recipes are returned, filters work, nutrition totals are calculated from reviewed ingredients, unsafe/allergen-matching recipes are excluded, and pagination is stable.

- [ ] **Step 2: Verify backend tests fail**

Run: `backend/.venv/bin/pytest -q backend/tests/recipes/test_recipe_listing.py`

Expected: FAIL because fields and filters are missing.

- [ ] **Step 3: Implement reviewed recipe models, migration, and list service**

Add content status/version, nutrition snapshots, and safety labels. Calculate and persist snapshot values from food data; never accept authoritative nutrition totals from the client.

- [ ] **Step 4: Write and verify a failing mini-program normalization test**

Test missing tags, backend kcal/subtitle preference, local-image fallback, and preserved four-filter behavior.

Run: `npm test --prefix miniprogram`

Expected: the new normalization test fails against the current inline normalizer.

- [ ] **Step 5: Export normalization helper and keep existing Recipes UI**

Move the normalizer to a testable utility and update only recipe data mapping/copy. Do not add the React prototype science strip, AI panel, double-column grid, or floating bookmark controls.

- [ ] **Step 6: Run recipe backend and mini-program tests**

Run: `backend/.venv/bin/pytest -q backend/tests/recipes && npm test --prefix miniprogram`

Expected: all selected tests pass.

- [ ] **Step 7: Commit**

```bash
git add backend/app/recipes backend/alembic/versions/0010_pregnancy_guidance.py backend/tests/recipes miniprogram/pages/recipes/index.js miniprogram/utils/recipe-filter.js miniprogram/tests/recipe-normalize.test.mjs
git commit -m "feat: add reviewed pregnancy recipe metadata"
```

### Task 7: Pregnancy Trend Analytics

**Files:**
- Modify: `backend/app/analytics/schemas.py`
- Modify: `backend/app/analytics/service.py`
- Create: `backend/tests/analytics/test_pregnancy_summary.py`
- Modify: `backend/tests/analytics/test_period_summary.py`

**Interfaces:**
- Produces pregnancy summary fields: weight points, recorded-day count, food-category diversity, and explainable facts.
- Keeps legacy summary behavior only when `product_mode=legacy_slimming`.
- Never uses `BodyProfile.daily_kcal` for pregnancy mode.

- [ ] **Step 1: Write failing pregnancy-summary tests**

Assert pregnancy summaries omit calorie-budget conclusions, count distinct reviewed food categories, preserve weight moving averages, and return no inferred trend with fewer than two points.

- [ ] **Step 2: Verify tests fail on legacy-only schema**

Run: `backend/.venv/bin/pytest -q backend/tests/analytics/test_pregnancy_summary.py`

Expected: FAIL because diversity and product-aware responses are missing.

- [ ] **Step 3: Implement product-aware analytics**

Branch on server-side `product_mode`, calculate facts from persisted snapshots, and keep schemas explicit instead of overloading legacy calorie fields with pregnancy meanings.

- [ ] **Step 4: Run analytics tests**

Run: `backend/.venv/bin/pytest -q backend/tests/analytics`

Expected: pregnancy and legacy tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/analytics backend/tests/analytics
git commit -m "feat: add pregnancy-aware trend analytics"
```

### Task 8: Pregnancy AI Allowlist and Fixed Safety Responses

**Files:**
- Modify: `backend/app/ai_coach/schemas.py`
- Modify: `backend/app/ai_coach/safety.py`
- Modify: `backend/app/ai_coach/models.py`
- Modify: `backend/app/ai_coach/router.py`
- Modify: `backend/tests/ai_coach/test_safety.py`
- Create: `backend/tests/ai_coach/test_pregnancy_allowlist.py`
- Modify: `backend/alembic/versions/0010_pregnancy_guidance.py`

**Interfaces:**
- Produces actions: `allow`, `allow_limited`, `refer_professional`, `emergency_guidance`.
- Allows only reviewed recipe swaps, confirmed-record explanations, and weekly fact reflections.
- Emergency response uses fixed reviewed text and never invokes a generative model.

- [ ] **Step 1: Write failing allowlist tests**

Assert pregnancy recipe-swap and weekly-reflection requests return limited drafts, serious symptoms return fixed emergency guidance, medication/disease requests refer, and meal-number generation is rejected.

- [ ] **Step 2: Verify tests fail against pregnancy-wide rejection**

Run: `backend/.venv/bin/pytest -q backend/tests/ai_coach`

Expected: pregnancy allowlist cases fail because current safety always returns `refer_professional`.

- [ ] **Step 3: Implement deterministic safety policy and draft metadata**

Store policy/rule version and input data range. Use server-computed candidates and facts only. Retain user confirmation before any allowed state change.

- [ ] **Step 4: Run AI and recipe tests**

Run: `backend/.venv/bin/pytest -q backend/tests/ai_coach backend/tests/recipes`

Expected: all selected tests pass.

- [ ] **Step 5: Commit**

```bash
git add backend/app/ai_coach backend/tests/ai_coach backend/alembic/versions/0010_pregnancy_guidance.py
git commit -m "feat: restrict pregnancy AI to reviewed workflows"
```

### Task 9: Mini-Program Pregnancy API and State Utilities

**Files:**
- Create: `miniprogram/api/pregnancy.js`
- Create: `miniprogram/api/family.js`
- Create: `miniprogram/api/meal-plans.js`
- Modify: `miniprogram/api/meals.js`
- Modify: `miniprogram/api/analytics.js`
- Create: `miniprogram/utils/pregnancy.js`
- Create: `miniprogram/utils/meal-plan.js`
- Create: `miniprogram/tests/pregnancy.test.mjs`
- Create: `miniprogram/tests/meal-plan.test.mjs`

**Interfaces:**
- Produces API functions for current pregnancy, schedules, wellbeing, family, daily plans, and pregnancy analytics.
- Produces pure view-model helpers for gestation labels, meal grouping, actor labels, and empty states.

- [ ] **Step 1: Write failing pure-function tests**

Test gestation-label formatting from API values, custom schedule ordering, plan/record grouping, partner actor labels, and no use of calorie-deficit fields.

- [ ] **Step 2: Verify tests fail because utilities do not exist**

Run: `npm test --prefix miniprogram`

Expected: FAIL on missing utility modules.

- [ ] **Step 3: Implement minimal API wrappers and pure utilities**

Keep request/auth handling in the existing client. Do not compute authoritative gestation or nutrition values on the device.

- [ ] **Step 4: Run mini-program tests**

Run: `npm test --prefix miniprogram`

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add miniprogram/api miniprogram/utils miniprogram/tests
git commit -m "feat: add pregnancy mini program data clients"
```

### Task 10: Pregnancy Onboarding

**Files:**
- Create: `miniprogram/pages/onboarding/pregnancy/index.js`
- Create: `miniprogram/pages/onboarding/pregnancy/index.json`
- Create: `miniprogram/pages/onboarding/pregnancy/index.wxml`
- Create: `miniprogram/pages/onboarding/pregnancy/index.wxss`
- Modify: `miniprogram/pages/onboarding/welcome/index.js`
- Modify: `miniprogram/pages/onboarding/welcome/index.wxml`
- Modify: `miniprogram/app.json`
- Modify: `miniprogram/utils/onboarding.js`
- Modify: `miniprogram/tests/onboarding.test.mjs`

**Interfaces:**
- Consumes: `createPregnancy` from Task 9.
- Produces a single pregnancy onboarding flow with due date, height, pre-pregnancy/current weight, activity, allergens, avoidances, and preferences.

- [ ] **Step 1: Extend onboarding tests first**

Test due-date validation, optional pre-pregnancy weight, required current weight, and payload normalization without `goal`, `target_weight_kg`, or calorie fields.

- [ ] **Step 2: Verify tests fail against slimming onboarding**

Run: `npm test --prefix miniprogram`

Expected: new tests fail because pregnancy validation is absent.

- [ ] **Step 3: Build native onboarding page and route**

Use normal font sizes, light backgrounds, explicit sensitive-data explanation, and a single submit action. On success switch to Today; on network failure preserve inputs and show backend detail.

- [ ] **Step 4: Run mini-program tests**

Run: `npm test --prefix miniprogram`

Expected: all tests pass.

- [ ] **Step 5: Commit**

```bash
git add miniprogram/pages/onboarding miniprogram/app.json miniprogram/utils/onboarding.js miniprogram/tests/onboarding.test.mjs
git commit -m "feat: replace slimming onboarding with pregnancy setup"
```

### Task 11: Native Today and Record Tabs

**Files:**
- Modify: `miniprogram/pages/today/index.js`
- Modify: `miniprogram/pages/today/index.wxml`
- Modify: `miniprogram/pages/today/index.wxss`
- Modify: `miniprogram/pages/today/index.json`
- Modify: `miniprogram/pages/record/index.js`
- Modify: `miniprogram/pages/record/index.wxml`
- Modify: `miniprogram/pages/record/index.wxss`
- Modify: `miniprogram/components/record-calendar/*`
- Create: `miniprogram/components/pregnancy-meal/index.js`
- Create: `miniprogram/components/pregnancy-meal/index.json`
- Create: `miniprogram/components/pregnancy-meal/index.wxml`
- Create: `miniprogram/components/pregnancy-meal/index.wxss`
- Create: `miniprogram/tests/pregnancy-meal.test.mjs`

**Interfaces:**
- Consumes: current pregnancy, meal plans, schedules, wellbeing, and meal records.
- Produces: editable meal times, bordered/light-separated meal cards, preparation states, record actor labels, and compact calendar navigation.

- [ ] **Step 1: Write failing meal view-model tests**

Test five default meals, custom names/times, planned/cooking/done labels, empty meal behavior, and partner actor display.

- [ ] **Step 2: Verify test failure**

Run: `npm test --prefix miniprogram`

Expected: new tests fail before the component helper exists.

- [ ] **Step 3: Replace Today page with pregnancy hierarchy**

Remove the calorie-budget hero. Render gestation/date, wellbeing chips, separated meal cards with vertical margins, editable times, preparation summary, and one reviewed daily note.

- [ ] **Step 4: Replace Record page content while preserving calendar wrapper**

Keep compact week/month calendar. Render dated meal records with owner/actor metadata and wellbeing controls; keep search/recent/photo entry points.

- [ ] **Step 5: Run mini-program tests**

Run: `npm test --prefix miniprogram`

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add miniprogram/pages/today miniprogram/pages/record miniprogram/components/pregnancy-meal miniprogram/components/record-calendar miniprogram/tests/pregnancy-meal.test.mjs
git commit -m "feat: build pregnancy today and record tabs"
```

### Task 12: Native Trend and Family Tabs

**Files:**
- Modify: `miniprogram/pages/analysis/index.js`
- Modify: `miniprogram/pages/analysis/index.wxml`
- Modify: `miniprogram/pages/analysis/index.wxss`
- Modify: `miniprogram/components/health-chart/index.js`
- Modify: `miniprogram/components/health-chart/index.wxml`
- Modify: `miniprogram/components/health-chart/options.js`
- Create: `miniprogram/pages/family/index.js`
- Create: `miniprogram/pages/family/index.json`
- Create: `miniprogram/pages/family/index.wxml`
- Create: `miniprogram/pages/family/index.wxss`
- Modify: `miniprogram/app.json`
- Modify: `miniprogram/styles/tokens.wxss`
- Modify: `miniprogram/tests/chart-options.test.mjs`

**Interfaces:**
- Consumes: pregnancy analytics, family members, permissions, tasks, pregnancy profile, and account settings.
- Produces: light trend charts and owner/partner-specific Family tab.

- [ ] **Step 1: Write failing chart-option tests**

Assert pregnancy trend options omit calorie-budget series, use light blue/apricot tones, return an empty-state result for fewer than two weight points, and build diversity bars from server categories.

- [ ] **Step 2: Verify tests fail against legacy options**

Run: `npm test --prefix miniprogram`

Expected: new chart assertions fail.

- [ ] **Step 3: Implement pregnancy Trend page**

Use 7/30/90-day tabs, weight trend, food diversity, recorded-day facts, and a restrained weekly reflection. Do not show calorie-deficit or macro-budget completion cards.

- [ ] **Step 4: Implement Family page and TabBar replacement**

Replace Profile tab with Family. Render owner invitation/permission/settings views and partner task view from server role, not local assumptions. Keep pregnancy profile, allergies, privacy, data sources, and account actions accessible.

- [ ] **Step 5: Run mini-program tests**

Run: `npm test --prefix miniprogram`

Expected: all tests pass.

- [ ] **Step 6: Commit**

```bash
git add miniprogram/pages/analysis miniprogram/pages/family miniprogram/components/health-chart miniprogram/app.json miniprogram/styles/tokens.wxss miniprogram/tests/chart-options.test.mjs
git commit -m "feat: add pregnancy trend and family tabs"
```

### Task 13: Privacy Copy, Deployment Contract, and Full Verification

**Files:**
- Modify: `miniprogram/pages/privacy/index.wxml`
- Modify: `miniprogram/pages/privacy/index.wxss`
- Modify: `miniprogram/pages/data-sources/index.wxml`
- Modify: `README.md`
- Modify: `backend/README.md`
- Modify: `miniprogram/README.md`
- Test: all backend and mini-program tests

**Interfaces:**
- Documents: pregnancy-sensitive data purpose, partner revocation, deletion, reviewed-content limits, TKA/TAP boundary, migration/deployment order.
- Verifies: backend, migration chain, mini-program tests, and WeChat developer-tool compile/preview command where available.

- [ ] **Step 1: Update user-facing privacy and data-source text**

State what due date, weight, food, wellbeing, and family permissions are used for; explain voluntary WeChat profile authorization and partner revocation; avoid treatment or diagnosis claims.

- [ ] **Step 2: Update developer documentation**

Document migration order, required environment variables without secrets, local startup, production upgrade order, rollback, and the fact that React prototype is reference-only.

- [ ] **Step 3: Run formatting and complete backend tests**

Run: `backend/.venv/bin/pytest -q backend/tests`

Expected: all backend tests pass with zero failures.

- [ ] **Step 4: Run migration upgrade/downgrade smoke test**

Create a temporary SQLite database, run `alembic upgrade head`, inspect current revision, run `alembic downgrade 0005_guidance`, then `alembic upgrade head` again.

Expected: each command exits 0 and the final revision is `0010_pregnancy_guidance`.

- [ ] **Step 5: Run complete mini-program tests**

Run: `npm test --prefix miniprogram`

Expected: all Node tests pass with zero failures.

- [ ] **Step 6: Compile the native mini program**

Run the configured WeChat developer-tools CLI against `miniprogram/` after building npm dependencies.

Expected: compile or preview exits 0 with no missing page/component/dependency error. If the CLI requires an interactive login, record that as a manual verification requirement without claiming it passed.

- [ ] **Step 7: Review the diff against the specification**

Confirm Recipes kept its original page structure, all other tabs use pregnancy design, no pregnancy route calls slimming calorie-deficit targets, no frontend role bypass exists, and no secret is committed.

- [ ] **Step 8: Commit**

```bash
git add miniprogram/pages/privacy miniprogram/pages/data-sources README.md backend/README.md miniprogram/README.md
git commit -m "docs: document pregnancy privacy and deployment"
```
