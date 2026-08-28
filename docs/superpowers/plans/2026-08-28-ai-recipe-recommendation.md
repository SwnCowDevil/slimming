# AI Recipe Recommendation and Private Favorites Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a production-safe DeepSeek recipe recommendation flow, 27 owned platform recipes, private favorites, scoped search, nutrition provenance, and meal-record confirmation to the existing pregnancy mini-program.

**Architecture:** Keep reviewed platform recipes and saved private AI recipes in the existing recipe aggregate, while short-lived AI candidates live in user-scoped recommendation sessions. A provider-neutral backend adapter calls the official DeepSeek API, then deterministic schema, allergy, pregnancy-safety, deduplication, and TKA enrichment stages decide what the mini-program may display or save.

**Tech Stack:** Python 3.12, FastAPI 0.116, SQLAlchemy 2, Alembic 1.16, Pydantic 2, HTTPX 0.28, pytest 8, native WeChat Mini Program JavaScript/WXML/WXSS, Node test runner.

**Spec:** `docs/superpowers/specs/2026-08-28-ai-recipe-recommendation-design.md`

## Global Constraints

- Production must not call TheMealDB or copy its images, descriptions, instructions, or API payloads.
- The 27 platform recipes must be original Chinese content with project-owned or already documented legal image assets.
- The mini-program calls only the FastAPI backend; only the backend calls `https://api.deepseek.com`.
- The first provider is DeepSeek through a provider-neutral interface; default model is `deepseek-v4-flash` and remains environment-configurable.
- Never send WeChat openid, nickname, exact due date, weight history, or unrelated health data to the model.
- AI candidates are private, user-scoped, and expire after 24 hours unless saved.
- Saved AI recipes remain visible only to their owner; no public user-generated recipe feed is in scope.
- Any candidate matching an allergy or pregnancy hard-risk rule is discarded as a whole and never displayed.
- AI-estimated nutrition must be labeled; recipes with unmatched ingredients require ingredient and weight confirmation before meal recording.
- All API keys and production secrets stay outside Git and outside mini-program code.
- Preserve the existing recipe Tab card style and the current user-owned dirty changes in `miniprogram/tests/recipe-filter.test.mjs` and `miniprogram/utils/recipe-filter.js`.

## File Structure

### Backend files to create

- `backend/alembic/versions/0012_ai_recipe_library.py` — schema migration for recipe ownership, favorites, richer items, and recommendation sessions.
- `backend/app/ai_recipes/__init__.py` — package marker.
- `backend/app/ai_recipes/models.py` — `AiRecommendationSession` and `AiRecipeRequestEvent` ORM models.
- `backend/app/ai_recipes/schemas.py` — request, candidate, filter, batch, and save schemas.
- `backend/app/ai_recipes/provider.py` — provider protocol and provider dependency factory.
- `backend/app/ai_recipes/deepseek.py` — official DeepSeek HTTP adapter and JSON decoding.
- `backend/app/ai_recipes/validation.py` — ingredient normalization, hard-risk rules, schema post-validation, and fingerprinting.
- `backend/app/ai_recipes/nutrition.py` — TKA matching, totals, and nutrition provenance.
- `backend/app/ai_recipes/service.py` — session orchestration, retries, dedupe, fallback, save, and expiry logic.
- `backend/app/ai_recipes/router.py` — recommendation, next-batch, and save endpoints.
- `backend/app/ai_recipes/cleanup.py` — bounded deletion of expired, unsaved recommendation sessions.
- `backend/app/recipes/importer.py` — versioned idempotent platform recipe importer.
- `backend/data/imports/platform-recipes-v1.json` — 27 original platform recipe records.
- `backend/tests/ai_recipes/test_deepseek_provider.py` — provider contract tests.
- `backend/tests/ai_recipes/test_validation.py` — safety, allergy, and fingerprint tests.
- `backend/tests/ai_recipes/test_nutrition.py` — TKA/mixed/estimated provenance tests.
- `backend/tests/ai_recipes/test_recommendations.py` — session, retry, next-batch, fallback, and expiry tests.
- `backend/tests/recipes/test_recipe_favorites.py` — private saving, duplicate handling, archive, and ownership tests.
- `backend/tests/recipes/test_platform_recipe_import.py` — 27-record importer tests.
- `scripts/cleanup-ai-recipe-sessions.sh` — deployable cleanup command for expired AI candidate sessions.

### Backend files to modify

- `backend/app/core/config.py` — provider, timeout, retry, and session TTL settings.
- `backend/.env.example` — DeepSeek configuration contract with blank secret.
- `backend/app/db/base.py` — import `ai_recipes.models` into metadata.
- `backend/app/main.py` — register AI recipe router and provider dependency.
- `backend/app/recipes/models.py` — ownership, source, provenance, fingerprint, item details, and favorite relationships.
- `backend/app/meals/models.py` — allow recipe-derived estimated snapshots and persist nutrition provenance.
- `backend/app/meals/schemas.py` — expose meal-entry nutrition provenance.
- `backend/app/meals/service.py` — create immutable AI-estimated meal-entry snapshots after explicit confirmation.
- `backend/app/recipes/schemas.py` — richer read/search/favorite/record-confirmation schemas.
- `backend/app/recipes/service.py` — ownership-aware listing, search, favorites, and archive behavior.
- `backend/app/recipes/router.py` — search scope and favorite endpoints.
- `backend/app/ai_coach/safety.py` — allow the bounded `recipe_recommendation` workflow.
- `backend/README.md` — model configuration, import, migration, and verification commands.
- `miniprogram/assets/SOURCES.md` — document the project-owned image reuse for platform recipes.

### Mini-program files to create

- `miniprogram/api/ai-recipes.js` — recommend, next batch, and save candidate calls.
- `miniprogram/utils/ai-recipe.js` — candidate normalization, labels, and request-building helpers.
- `miniprogram/pages/ai-recipes/index.js` — filter state, generation, next batch, and saving behavior.
- `miniprogram/pages/ai-recipes/index.wxml` — lightweight filters, natural-language input, results, and states.
- `miniprogram/pages/ai-recipes/index.wxss` — light visual treatment consistent with the current recipe Tab.
- `miniprogram/pages/ai-recipes/index.json` — page title and recipe-card dependency.
- `miniprogram/pages/recipe-confirm/index.js` — ingredient and gram confirmation before recording mixed/estimated recipes.
- `miniprogram/pages/recipe-confirm/index.wxml` — confirmation list and provenance disclosure.
- `miniprogram/pages/recipe-confirm/index.wxss` — confirmation page styling.
- `miniprogram/pages/recipe-confirm/index.json` — confirmation page title.
- `miniprogram/tests/ai-recipe.test.mjs` — helper and state tests.
- `miniprogram/tests/recipe-api-contract.test.mjs` — endpoint contract assertions.

### Mini-program files to modify

- `miniprogram/app.json` — register the two non-tab pages.
- `miniprogram/api/recipes.js` — query/scope, favorite removal, and confirmed recording.
- `miniprogram/pages/recipes/index.js` — remote search, favorites scope, AI entry, and refresh after save.
- `miniprogram/pages/recipes/index.wxml` — lightweight AI input and existing-style filters/cards.
- `miniprogram/pages/recipes/index.wxss` — light spacing and source badges without changing card hierarchy.
- `miniprogram/components/recipe-card/index.js` — save/open event support.
- `miniprogram/components/recipe-card/index.wxml` — AI/provenance/favorite affordances.
- `miniprogram/components/recipe-card/index.wxss` — compact badges and favorite button.
- `miniprogram/pages/recipe-detail/index.js` — favorite state and confirmation routing.
- `miniprogram/pages/recipe-detail/index.wxml` — ingredients, steps, provenance, and disclosure.
- `miniprogram/pages/recipe-detail/index.wxss` — detail sections aligned with existing visual style.
- `miniprogram/utils/recipe-filter.js` — normalize source, ownership, ingredients, and favorite state while preserving current dirty edits.
- `miniprogram/tests/recipe-normalize.test.mjs` — provenance and favorite normalization coverage.
- `miniprogram/pages/privacy/index.wxml` — DeepSeek and AI content disclosure.
- `miniprogram/pages/data-sources/index.wxml` — platform recipe, TKA, and AI source explanation.

---

### Task 1: Add persistent recipe ownership and recommendation-session schema

**Files:**
- Create: `backend/alembic/versions/0012_ai_recipe_library.py`
- Create: `backend/app/ai_recipes/__init__.py`
- Create: `backend/app/ai_recipes/models.py`
- Modify: `backend/app/recipes/models.py`
- Modify: `backend/app/meals/models.py`
- Modify: `backend/app/db/base.py`
- Test: `backend/tests/recipes/test_recipe_favorites.py`

**Interfaces:**
- Produces: `Recipe.owner_user_id`, `Recipe.source_type`, `Recipe.visibility`, `Recipe.nutrition_source`, `Recipe.content_fingerprint`, `Recipe.prompt_version`, `Recipe.safety_rule_version`, `RecipeFavorite`, `AiRecommendationSession`, and `AiRecipeRequestEvent` for every later task.
- Produces: nullable `MealEntry.food_id` plus `MealEntry.nutrition_source` and `MealEntry.source_recipe_id` for confirmed estimated snapshots.
- Produces: `utcnow() -> datetime` in `app.ai_recipes.models`.

- [ ] **Step 1: Write the failing ORM ownership test**

```python
def test_recipe_models_support_platform_private_favorites_and_sessions(db_session):
    user = User(openid="owner-openid")
    db_session.add(user)
    db_session.flush()
    recipe = Recipe(
        title="番茄鸡蛋汤",
        source_type="ai",
        visibility="private",
        owner_user_id=user.id,
        content_fingerprint="fp-owner-recipe",
        nutrition_source="mixed",
        nutrition_confidence="medium",
    )
    recipe.items.append(RecipeItem(
        ingredient_name_zh="番茄",
        original_measure="1个",
        grams=180,
        source_food_id=None,
        nutrition_source="ai_estimated",
    ))
    recipe.favorites.append(RecipeFavorite(user_id=user.id))
    recommendation_session = AiRecommendationSession(
        user_id=user.id,
        filters={"meal_type": "dinner"},
        query_text="清淡晚餐",
        displayed_fingerprints=[],
        candidates=[],
        expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
    )
    db_session.add_all([recipe, recommendation_session])
    db_session.flush()
    request_event = AiRecipeRequestEvent(
        session_id=recommendation_session.id,
        user_id=user.id,
        request_kind="initial",
        request_ip_hash="ip-hash",
        idempotency_key="initial-request",
        response_payload={"mode": "ai", "candidates": []},
        provider_call_count=1,
    )
    db_session.add(request_event)
    db_session.commit()
    assert recipe.owner_user_id == user.id
    assert recipe.items[0].source_food_id is None
    assert recipe.favorites[0].user_id == user.id
```

- [ ] **Step 2: Run the test and verify the new fields/classes are missing**

Run: `cd backend && .venv/bin/pytest tests/recipes/test_recipe_favorites.py::test_recipe_models_support_platform_private_favorites_and_sessions -v`

Expected: FAIL during import or model construction because `RecipeFavorite`, `AiRecommendationSession`, or the new mapped fields do not exist.

- [ ] **Step 3: Implement focused ORM models**

Add `RecipeFavorite` with a unique constraint on `(user_id, recipe_id)`, nullable `Recipe.owner_user_id`, indexed `source_type`, `visibility`, `content_fingerprint`, `nutrition_source`, and `nutrition_confidence`, plus `Recipe.original_query`, `Recipe.model_name`, nullable `Recipe.prompt_version`, and nullable `Recipe.safety_rule_version`. Preserve the existing `content_status` field for published/archived state. Expand `RecipeItem` with `ingredient_name_zh`, `original_measure`, nullable `source_food_id`, `nutrition_source`, and nullable per-100g AI estimate fields for energy, protein, fat, carbohydrate, and fiber. Add this session model:

```python
class AiRecommendationSession(Base):
    __tablename__ = "ai_recommendation_sessions"

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    filters: Mapped[dict] = mapped_column(JSON, default=dict)
    query_text: Mapped[str] = mapped_column(Text, default="")
    displayed_fingerprints: Mapped[list[str]] = mapped_column(JSON, default=list)
    candidates: Mapped[list[dict]] = mapped_column(JSON, default=list)
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow)

class AiRecipeRequestEvent(Base):
    __tablename__ = "ai_recipe_request_events"
    __table_args__ = (
        UniqueConstraint("user_id", "idempotency_key", name="uq_ai_recipe_event_user_idempotency"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=lambda: str(uuid4()))
    session_id: Mapped[str] = mapped_column(
        ForeignKey("ai_recommendation_sessions.id", ondelete="CASCADE"), index=True
    )
    user_id: Mapped[str] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    request_kind: Mapped[str] = mapped_column(String(16))
    request_ip_hash: Mapped[str] = mapped_column(String(64), index=True)
    idempotency_key: Mapped[str] = mapped_column(String(128))
    response_payload: Mapped[dict] = mapped_column(JSON)
    provider_call_count: Mapped[int] = mapped_column(Integer, default=0)
    provider_model: Mapped[str | None] = mapped_column(String(128), nullable=True)
    prompt_version: Mapped[str | None] = mapped_column(String(64), nullable=True)
    provider_latency_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    input_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    output_tokens: Mapped[int | None] = mapped_column(Integer, nullable=True)
    rejected_count: Mapped[int] = mapped_column(Integer, default=0)
    fallback_reason: Mapped[str | None] = mapped_column(String(64), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utcnow, index=True)
```

The migration must backfill existing recipes as `source_type='platform'`, `visibility='platform'`, `nutrition_source='tka'`, and make existing `recipe_items.source_food_id` nullable using Alembic batch mode for SQLite. It must also make `meal_entries.food_id` nullable and add nullable `source_recipe_id` plus non-null `nutrition_source='tka'` so estimated snapshots remain traceable without inventing a TKA food row. The request-event foreign key must cascade when an expired recommendation session is purged.

- [ ] **Step 4: Run model and migration tests**

Run: `cd backend && .venv/bin/pytest tests/recipes/test_recipe_favorites.py::test_recipe_models_support_platform_private_favorites_and_sessions -v && .venv/bin/alembic upgrade head`

Expected: PASS and Alembic reaches `0012_ai_recipe_library`.

- [ ] **Step 5: Commit the schema unit**

```bash
git add backend/alembic/versions/0012_ai_recipe_library.py backend/app/ai_recipes/__init__.py backend/app/ai_recipes/models.py backend/app/recipes/models.py backend/app/meals/models.py backend/app/db/base.py backend/tests/recipes/test_recipe_favorites.py
git commit -m "feat: add private AI recipe persistence"
```

### Task 2: Make recipe listing, search, and favorites ownership-safe

**Files:**
- Modify: `backend/app/recipes/schemas.py`
- Modify: `backend/app/recipes/service.py`
- Modify: `backend/app/recipes/router.py`
- Test: `backend/tests/recipes/test_recipe_listing.py`
- Test: `backend/tests/recipes/test_recipe_favorites.py`
- Test: `backend/tests/e2e/test_user_isolation.py`

**Interfaces:**
- Consumes: ownership and favorite models from Task 1.
- Produces: `list_visible_recipes(session, user_id, query=None, scope="all", meal_type=None, max_minutes=None, limit=20, offset=0) -> list[Recipe]`.
- Produces: `favorite_recipe(session, user_id, recipe_id) -> Recipe` and `remove_favorite(session, user_id, recipe_id) -> None`.

- [ ] **Step 1: Add failing API tests for scoped search and favorites**

```python
def test_recipe_search_returns_platform_and_current_users_private_recipe(client, auth_headers):
    # Seed one platform recipe, one private recipe for current user, and one for another user.
    response = client.get("/api/v1/recipes?query=番茄&scope=all", headers=auth_headers)
    assert response.status_code == 200
    assert {item["title"] for item in response.json()} == {"平台番茄汤", "我的番茄面"}

def test_platform_favorite_can_be_added_and_removed(client, auth_headers):
    saved = client.post("/api/v1/recipes/platform-1/favorite", headers=auth_headers)
    assert saved.status_code == 200
    assert saved.json()["is_favorite"] is True
    removed = client.delete("/api/v1/recipes/platform-1/favorite", headers=auth_headers)
    assert removed.status_code == 204
```

Also add a two-user test proving user A gets 404 for user B's private recipe ID.

- [ ] **Step 2: Run the focused tests and verify endpoint/query failures**

Run: `cd backend && .venv/bin/pytest tests/recipes/test_recipe_listing.py tests/recipes/test_recipe_favorites.py tests/e2e/test_user_isolation.py -v`

Expected: FAIL because `query`, `scope`, favorite endpoints, and private visibility do not exist.

- [ ] **Step 3: Implement the visible-recipe predicate and endpoints**

Use one server-owned predicate in every list/detail/favorite/record query:

```python
def visible_recipe_clause(user_id: str):
    return and_(
        Recipe.content_status == "published",
        or_(
            Recipe.visibility == "platform",
            and_(Recipe.visibility == "private", Recipe.owner_user_id == user_id),
        ),
    )
```

Search `Recipe.title`, `Recipe.description`, `Recipe.original_query`, serialized tags, and `RecipeItem.ingredient_name_zh`. `scope=favorites` joins `RecipeFavorite` on the current user. Return `is_favorite`, source, nutrition provenance, confidence, and normalized ingredient reads.

- [ ] **Step 4: Run focused tests and existing recipe regression tests**

Run: `cd backend && .venv/bin/pytest tests/recipes tests/e2e/test_user_isolation.py -v`

Expected: PASS; existing reviewed filters, pagination, and recording stay green.

- [ ] **Step 5: Commit ownership-safe recipes**

```bash
git add backend/app/recipes/schemas.py backend/app/recipes/service.py backend/app/recipes/router.py backend/tests/recipes/test_recipe_listing.py backend/tests/recipes/test_recipe_favorites.py backend/tests/e2e/test_user_isolation.py
git commit -m "feat: add private recipe search and favorites"
```

### Task 3: Add the provider-neutral DeepSeek adapter

**Files:**
- Create: `backend/app/ai_recipes/schemas.py`
- Create: `backend/app/ai_recipes/provider.py`
- Create: `backend/app/ai_recipes/deepseek.py`
- Modify: `backend/app/core/config.py`
- Modify: `backend/.env.example`
- Modify: `backend/app/main.py`
- Test: `backend/tests/ai_recipes/test_deepseek_provider.py`
- Test: `backend/tests/test_production_settings.py`

**Interfaces:**
- Produces: `RecipeGenerationRequest`, `RecipeCandidate`, `ProviderUsage`, `ProviderGenerationResult`, and `AiRecipeProvider.generate_recipes(request) -> ProviderGenerationResult`.
- Produces: `get_ai_recipe_provider(request: Request) -> AiRecipeProvider`.

- [ ] **Step 1: Write failing provider contract tests with HTTPX MockTransport**

```python
def test_deepseek_provider_requests_json_and_parses_candidates():
    transport = httpx.MockTransport(lambda request: httpx.Response(200, json={
        "choices": [{"message": {"content": json.dumps({"recipes": [candidate_payload()]}, ensure_ascii=False)}}]
    }))
    provider = DeepSeekRecipeProvider(
        api_key="test-key",
        model="deepseek-v4-flash",
        client=httpx.Client(transport=transport, base_url="https://api.deepseek.com"),
    )
    result = provider.generate_recipes(generation_request())
    assert result.candidates[0].title == "番茄鸡丁饭"
    assert result.model == "deepseek-v4-flash"
```

Add tests for empty content, truncated/invalid JSON, 401, 402, 429, 500, and 503 mapping to typed provider errors.

- [ ] **Step 2: Run provider tests and verify missing imports**

Run: `cd backend && .venv/bin/pytest tests/ai_recipes/test_deepseek_provider.py tests/test_production_settings.py -v`

Expected: FAIL because the provider package and settings do not exist.

- [ ] **Step 3: Implement provider protocol, schemas, adapter, and dependency**

Use Chat Completions with `response_format={"type": "json_object"}`, a timeout from settings, no streaming, and a system prompt containing the literal word `json` plus the required example schema. Define typed exceptions:

```python
class AiProviderError(RuntimeError):
    """Base error safe for service-level mapping."""

class AiProviderUnavailable(AiProviderError):
    """Retryable provider availability or rate-limit error."""

class AiProviderConfigurationError(AiProviderError):
    """Missing or rejected provider configuration."""

class AiProviderResponseError(AiProviderError):
    """Provider returned content that violates the JSON contract."""
```

`ProviderGenerationResult` must contain `candidates`, `model`, `prompt_version`, `latency_ms`, and optional `input_tokens` / `output_tokens`, allowing the orchestration layer to record cost metadata without storing prompts or raw responses.

Define bounded Pydantic contracts rather than accepting free-form dictionaries: recommendation `query` is at most 300 characters; available/disliked ingredients are at most 20 items of 40 characters each; filter values are enums; every candidate has exactly 1–2 servings, 1–120 minutes, 1–30 ingredients, 1–20 steps, positive gram weights, and per-serving nutrient fields. Each ingredient carries its AI estimate per 100g until TKA enrichment replaces it. Reject unknown top-level fields. The system prompt must treat the user's text as data, never as instructions that can override JSON, pregnancy-safety, or privacy rules.

Add settings with exact defaults:

```python
ai_provider: Literal["deepseek"] = "deepseek"
ai_base_url: str = "https://api.deepseek.com"
ai_model: str = "deepseek-v4-flash"
ai_api_key: str = ""
ai_timeout_seconds: float = 25.0
ai_max_retries: int = 2
ai_recipe_session_ttl_hours: int = 24
ai_recipe_user_limit_per_hour: int = 20
ai_recipe_ip_limit_per_hour: int = 60
```

In production, require a non-empty AI key only when the AI recipe feature is enabled; introduce `ai_recipe_enabled: bool = False` so deployments can safely start before the key is configured.

- [ ] **Step 4: Run provider and settings tests**

Run: `cd backend && .venv/bin/pytest tests/ai_recipes/test_deepseek_provider.py tests/test_production_settings.py -v`

Expected: PASS with no real network request.

- [ ] **Step 5: Commit the provider adapter**

```bash
git add backend/app/ai_recipes/schemas.py backend/app/ai_recipes/provider.py backend/app/ai_recipes/deepseek.py backend/app/core/config.py backend/.env.example backend/app/main.py backend/tests/ai_recipes/test_deepseek_provider.py backend/tests/test_production_settings.py
git commit -m "feat: add DeepSeek recipe provider"
```

### Task 4: Implement deterministic pregnancy safety and deduplication

**Files:**
- Create: `backend/app/ai_recipes/validation.py`
- Modify: `backend/app/ai_coach/safety.py`
- Test: `backend/tests/ai_recipes/test_validation.py`
- Test: `backend/tests/ai_coach/test_safety.py`

**Interfaces:**
- Consumes: `RecipeCandidate` from Task 3.
- Produces: `ValidationResult(allowed: bool, reason: str | None, normalized_candidate: RecipeCandidate | None)` and `validate_candidate(candidate, allergens, avoidances) -> ValidationResult`.
- Produces: `recipe_fingerprint(candidate) -> str`.

- [ ] **Step 1: Write table-driven failing safety tests**

```python
@pytest.mark.parametrize("ingredient", ["料理酒", "生鸡蛋", "生鱼片", "鲨鱼", "未巴氏杀菌鲜奶"])
def test_pregnancy_hard_risks_discard_whole_candidate(ingredient):
    candidate = candidate_with(ingredient=ingredient, instructions=["拌匀后食用"])
    result = validate_candidate(candidate, allergens=set(), avoidances=set())
    assert result.allowed is False

def test_user_allergen_discards_candidate():
    result = validate_candidate(candidate_with(ingredient="花生"), allergens={"peanut"}, avoidances=set())
    assert result.reason == "allergen:peanut"

def test_fingerprint_ignores_ingredient_order_and_whitespace():
    assert recipe_fingerprint(candidate_a()) == recipe_fingerprint(candidate_b_reordered())
```

Include allowed cooked-egg/meat cases so the rule is not a naive substring block.

- [ ] **Step 2: Run tests and confirm missing validator failures**

Run: `cd backend && .venv/bin/pytest tests/ai_recipes/test_validation.py tests/ai_coach/test_safety.py -v`

Expected: FAIL because validation functions and `recipe_recommendation` allowlist entry are missing.

- [ ] **Step 3: Implement versioned rules and normalized fingerprinting**

Define `SAFETY_RULE_VERSION = "pregnancy-recipe-v1"`, normalized alias sets, allergen mapping, forbidden ingredient categories, and required-cook checks. Return structured reasons for logs, but never include rejected content in API responses. Add `recipe_recommendation` to `PREGNANCY_ALLOWED_WORKFLOWS` while retaining serious-symptom, medication/disease, and eating-disorder referral behavior.

- [ ] **Step 4: Run focused safety tests**

Run: `cd backend && .venv/bin/pytest tests/ai_recipes/test_validation.py tests/ai_coach/test_safety.py -v`

Expected: PASS for hard rejection, safe cooked cases, deterministic fingerprints, and existing safety referrals.

- [ ] **Step 5: Commit deterministic safety**

```bash
git add backend/app/ai_recipes/validation.py backend/app/ai_coach/safety.py backend/tests/ai_recipes/test_validation.py backend/tests/ai_coach/test_safety.py
git commit -m "feat: validate pregnancy recipe candidates"
```

### Task 5: Enrich candidate nutrition from TKA with explicit provenance

**Files:**
- Create: `backend/app/ai_recipes/nutrition.py`
- Modify: `backend/app/foods/tka_provider.py`
- Test: `backend/tests/ai_recipes/test_nutrition.py`

**Interfaces:**
- Consumes: normalized candidate ingredients and `TkaProvider`.
- Produces: `enrich_candidate_nutrition(session, candidate) -> RecipeCandidate`.
- Produces: `TkaProvider.match_exact(name, locale="zh-CN") -> Food | None`.

- [ ] **Step 1: Write failing provenance tests**

```python
def test_all_tka_matches_replace_model_totals_and_mark_tka(db_session, seeded_foods):
    enriched = enrich_candidate_nutrition(db_session, fully_matchable_candidate())
    assert enriched.nutrition_source == "tka"
    assert enriched.nutrition_confidence == "high"
    assert all(item.nutrition_source == "tka" for item in enriched.ingredients)

def test_partial_match_keeps_estimate_only_for_unmatched_items(db_session, seeded_foods):
    enriched = enrich_candidate_nutrition(db_session, partly_matchable_candidate())
    assert enriched.nutrition_source == "mixed"
    assert enriched.nutrition_confidence == "medium"
    assert {item.nutrition_source for item in enriched.ingredients} == {"tka", "ai_estimated"}
```

Add invalid estimate tests rejecting negative nutrients, more than 2,500 kcal per serving, or macros whose calories materially exceed the stated total.

- [ ] **Step 2: Run tests and verify enrichment is absent**

Run: `cd backend && .venv/bin/pytest tests/ai_recipes/test_nutrition.py -v`

Expected: FAIL because exact matching and enrichment are missing.

- [ ] **Step 3: Implement exact alias matching and weighted totals**

`match_exact` must compare normalized `FoodAlias.name`, `Food.name_en`, and synonyms without using broad substring matches. TKA values replace model estimates for matched items. Unmatched items preserve validated AI estimates and remain visibly marked. Compute recipe totals per serving from ingredient grams and serving count.

- [ ] **Step 4: Run nutrition and existing food tests**

Run: `cd backend && .venv/bin/pytest tests/ai_recipes/test_nutrition.py tests/foods -v`

Expected: PASS and existing TKA imports/search remain green.

- [ ] **Step 5: Commit nutrition enrichment**

```bash
git add backend/app/ai_recipes/nutrition.py backend/app/foods/tka_provider.py backend/tests/ai_recipes/test_nutrition.py
git commit -m "feat: enrich AI recipes with TKA nutrition"
```

### Task 6: Build recommendation sessions, retries, next batch, and fallback

**Files:**
- Create: `backend/app/ai_recipes/service.py`
- Create: `backend/app/ai_recipes/router.py`
- Create: `backend/app/ai_recipes/cleanup.py`
- Create: `scripts/cleanup-ai-recipe-sessions.sh`
- Modify: `backend/app/main.py`
- Test: `backend/tests/ai_recipes/test_recommendations.py`

**Interfaces:**
- Consumes: provider, validator, nutrition enrichment, session model, and visible recipe listing.
- Produces: `create_recommendation_session(session, user, filters, query_text, idempotency_key, client_ip, provider) -> RecommendationBatch`.
- Produces: `next_recommendation_batch(session, user, session_id, idempotency_key, client_ip, provider) -> RecommendationBatch`.

- [ ] **Step 1: Write failing endpoint tests**

```python
def test_recommendation_uses_minimal_profile_and_returns_three_valid_candidates(client, auth_headers, fake_provider):
    response = client.post("/api/v1/ai/recipe-recommendations", headers=auth_headers, json={
        "filters": {"meal_type": "dinner", "max_minutes": 30, "flavors": ["light"]},
        "query": "冰箱里有鸡蛋和番茄",
    })
    assert response.status_code == 201
    assert response.json()["mode"] == "ai"
    assert len(response.json()["candidates"]) == 3
    sent = fake_provider.last_request.model_dump()
    assert "openid" not in sent
    assert "exact_due_date" not in sent

def test_next_batch_excludes_previously_displayed_fingerprints(client, auth_headers, fake_provider):
    first = create_batch(client, auth_headers)
    second = client.post(f"/api/v1/ai/recipe-recommendations/{first['session_id']}/next", headers=auth_headers)
    assert fingerprints(first).isdisjoint(fingerprints(second.json()))
```

Also test: two supplement attempts, fewer than three valid results, provider 429/500/503, disabled/missing key, expired session, another user's session, user/IP hourly limits, repeated idempotency keys, and fallback content.

- [ ] **Step 2: Run tests and verify missing service/router**

Run: `cd backend && .venv/bin/pytest tests/ai_recipes/test_recommendations.py -v`

Expected: FAIL with 404 or import errors.

- [ ] **Step 3: Implement orchestration with bounded retries and request controls**

Build generation input from `derive_gestation()` plus `PregnancyPreference.allergens`, `avoidances`, and `disliked_foods`. Do not include exact due date or weight. Generate a backend `candidate_id` for each accepted candidate. Use at most `ai_max_retries` supplement calls, maintain displayed fingerprints in the session, and set expiry using `ai_recipe_session_ttl_hours`.

Require `Idempotency-Key` on initial and next-batch requests. In one transaction, reserve an `AiRecipeRequestEvent` using the `(user_id, idempotency_key)` unique constraint; if it already exists, return its `response_payload` instead of calling the provider. Calculate `request_ip_hash` with HMAC-SHA256 using the server JWT secret; never persist the raw IP. Before reserving a new event, count request events in the previous hour by `user_id` and by the current `request_ip_hash`, returning 429 when the configured limit is reached. Store the finalized API response and provider-call count on that event.

Return `mode="fallback"` and reviewed visible recipes when the feature is disabled, provider configuration is missing, or the provider is unavailable. Do not leak raw provider messages.

After each provider call, persist only operational metadata on the request event: configured model, prompt version, latency, token counts when supplied by DeepSeek, rejected-candidate count, and a bounded fallback reason code. Never log or persist the complete prompt, raw model response, openid, nickname, exact due date, or weight history.

Create `purge_expired_sessions(session, now, limit=500) -> int` and a `python -m app.ai_recipes.cleanup` entry point. The cleanup command must delete only expired recommendation sessions in bounded batches; the service may also purge a small batch opportunistically before creating a session.

- [ ] **Step 4: Run recommendation and safety regression tests**

Run: `cd backend && .venv/bin/pytest tests/ai_recipes/test_recommendations.py tests/ai_coach -v`

Expected: PASS with deterministic fake-provider behavior and no network.

- [ ] **Step 5: Commit recommendation orchestration**

```bash
git add backend/app/ai_recipes/service.py backend/app/ai_recipes/router.py backend/app/ai_recipes/cleanup.py backend/app/main.py backend/tests/ai_recipes/test_recommendations.py scripts/cleanup-ai-recipe-sessions.sh
git commit -m "feat: add AI recipe recommendation sessions"
```

### Task 7: Save AI candidates transactionally and require record confirmation

**Files:**
- Modify: `backend/app/ai_recipes/service.py`
- Modify: `backend/app/ai_recipes/router.py`
- Modify: `backend/app/meals/models.py`
- Modify: `backend/app/meals/schemas.py`
- Modify: `backend/app/meals/service.py`
- Modify: `backend/app/recipes/schemas.py`
- Modify: `backend/app/recipes/router.py`
- Modify: `backend/app/recipes/service.py`
- Test: `backend/tests/recipes/test_recipe_favorites.py`
- Test: `backend/tests/recipes/test_recipe_recording.py`

**Interfaces:**
- Produces: `save_candidate(session, user_id, candidate_id) -> Recipe`.
- Produces: `ConfirmedRecipeItem(item_id: str, ingredient_name_zh: str, grams: float)` and `RecipeRecordRequest.confirmed_items: list[ConfirmedRecipeItem] | None`.
- Produces: `create_estimated_meal_entry(session, user_id, recipe, item, grams, meal_date, meal_type) -> MealEntry`.

- [ ] **Step 1: Write failing save and confirmation tests**

```python
def test_saving_candidate_creates_private_recipe_and_is_idempotent(client, auth_headers, recommendation):
    url = f"/api/v1/ai/recipe-candidates/{recommendation['candidate_id']}/save"
    first = client.post(url, headers=auth_headers)
    second = client.post(url, headers=auth_headers)
    assert first.status_code == 201
    assert second.status_code == 200
    assert first.json()["id"] == second.json()["id"]
    assert first.json()["visibility"] == "private"
    assert first.json()["is_favorite"] is True

def test_mixed_recipe_requires_confirmed_items_before_recording(client, auth_headers, private_recipe):
    rejected = client.post(
        f"/api/v1/recipes/{private_recipe.id}/record",
        headers={**auth_headers, "Idempotency-Key": "mixed-unconfirmed"},
        json={"meal_date": "2026-08-28", "meal_type": "dinner"},
    )
    assert rejected.status_code == 422
    assert rejected.json()["detail"]["action"] == "confirm_ingredients"
```

Add tests for expired candidates, safety-version recheck failure, rollback on item failure, archive on private unfavorite, and historical meal preservation.

- [ ] **Step 2: Run tests and verify save/confirm behavior is absent**

Run: `cd backend && .venv/bin/pytest tests/recipes/test_recipe_favorites.py tests/recipes/test_recipe_recording.py -v`

Expected: FAIL because candidate saving and confirmed items are unsupported.

- [ ] **Step 3: Implement the transactional save and confirmed recording flow**

Never create a recipe from a full candidate payload sent by the client. Resolve `candidate_id` inside the current user's unexpired server session, revalidate it, calculate fingerprint, reuse an existing same-owner fingerprint, then write the recipe, items, and favorite in one transaction. Persist only a bounded normalized summary of the request in `Recipe.original_query`; do not copy arbitrary prompt text into logs or public fields.

For `mixed` or `ai_estimated` recipes, require confirmed ingredient names and positive grams. Re-run TKA exact matching. Matched ingredients use the existing TKA meal-entry path. Unmatched ingredients create immutable `MealEntry` snapshots with `food_id=None`, `source_food_id="ai:" + recipe_item.id`, `provider="ai_estimated"`, `dataset_version=recipe.prompt_version`, scaled nutrient snapshots, `nutrition_source="ai_estimated"`, and `source_recipe_id=recipe.id`. This preserves the confirmed meal without inventing a TKA food row.

- [ ] **Step 4: Run recipe tests**

Run: `cd backend && .venv/bin/pytest tests/recipes -v`

Expected: PASS for existing one-click TKA recipes and new confirmation-required recipes.

- [ ] **Step 5: Commit saving and recording**

```bash
git add backend/app/ai_recipes/service.py backend/app/ai_recipes/router.py backend/app/meals/models.py backend/app/meals/schemas.py backend/app/meals/service.py backend/app/recipes/schemas.py backend/app/recipes/router.py backend/app/recipes/service.py backend/tests/recipes/test_recipe_favorites.py backend/tests/recipes/test_recipe_recording.py
git commit -m "feat: save and record private AI recipes"
```

### Task 8: Add the original 27-recipe platform dataset and idempotent importer

**Files:**
- Create: `backend/app/recipes/importer.py`
- Create: `backend/data/imports/platform-recipes-v1.json`
- Create: `backend/tests/recipes/test_platform_recipe_import.py`
- Modify: `backend/app/recipes/router.py`
- Modify: `backend/app/main.py`
- Modify: `miniprogram/assets/SOURCES.md`
- Create: `scripts/import-platform-recipes.sh`

**Interfaces:**
- Produces: `PlatformRecipeImporter.import_file(path, version, dry_run=False) -> ImportReport`.
- Produces: `POST /api/v1/admin/recipes/import`, protected by `X-Admin-Import-Key`.

- [ ] **Step 1: Write the failing importer tests**

```python
def test_platform_dataset_contains_exactly_27_owned_recipes():
    payload = json.loads(DATASET.read_text(encoding="utf-8"))
    assert payload["provider"] == "slimming-platform"
    assert payload["version"] == "platform-recipes-v1"
    assert len(payload["recipes"]) == 27
    assert all(item["source_type"] == "platform" for item in payload["recipes"])
    assert all(item["ingredients"] and item["steps"] for item in payload["recipes"])
    assert all(item["image_url"].startswith("/assets/recipes/") for item in payload["recipes"])

def test_platform_import_is_idempotent(client, auth_headers):
    first = import_dataset(client, auth_headers)
    second = import_dataset(client, auth_headers)
    assert first["imported"] == 27
    assert second["unchanged"] == 27
```

Also assert no record contains `themealdb.com`, English copied instructions, missing safety summary, or an undocumented image path.

- [ ] **Step 2: Run tests and verify dataset/importer are missing**

Run: `cd backend && .venv/bin/pytest tests/recipes/test_platform_recipe_import.py -v`

Expected: FAIL because the data file and importer do not exist.

- [ ] **Step 3: Author the dataset and importer**

Author original content for these 27 familiar dish directions without copying TheMealDB text: 鸡肉粥、番茄炒蛋、蛋花汤、牛肉西兰花、鸡肉炒饭、鸡肉杂菜焖饭、凉拌黄瓜、麻婆豆腐孕期温和版、鲜虾荷兰豆、虾仁河粉、豆腐麻酱拌菜、地三鲜少油版、清炒长豆角、完熟鸡蛋汤面、少油春卷、牛肉炒面、鸡肉炒面、番茄鸡丁、少辣宫保鸡丁、全熟虾仁拌面、甜酸鸡丁、甜酸里脊少糖版、青椒牛肉微辣版、家常豆腐、白菜虾皮汤、鸡肉小馄饨、蔬菜蛋饼。

Use the three existing project-owned ImageGen assets as documented category imagery in v1; distribute them by primary ingredient and document that deliberate reuse in `miniprogram/assets/SOURCES.md`. Every item must contain 1–2 servings, ingredient grams, original steps, `pregnancy_safety="safe"`, allergens, provenance, and content version.

Implement hash-based idempotent upsert mirroring `TkaProvider.import_dataset`; the importer must update changed records, preserve unchanged records, and support dry-run rollback. Create a separate `admin_router = APIRouter(prefix="/api/v1/admin/recipes")` for the protected import endpoint, retain the public recipe router unchanged, and register both routers explicitly in `backend/app/main.py`.

- [ ] **Step 4: Run importer, listing, and authorization tests**

Run: `cd backend && .venv/bin/pytest tests/recipes/test_platform_recipe_import.py tests/recipes/test_recipe_listing.py tests/foods/test_import_authorization.py -v`

Expected: PASS with exactly 27 platform recipes and an authorization failure without the admin key.

- [ ] **Step 5: Commit the platform dataset**

```bash
git add backend/app/recipes/importer.py backend/data/imports/platform-recipes-v1.json backend/tests/recipes/test_platform_recipe_import.py backend/app/recipes/router.py backend/app/main.py miniprogram/assets/SOURCES.md scripts/import-platform-recipes.sh
git commit -m "feat: add reviewed platform recipe dataset"
```

### Task 9: Add mini-program API contracts and pure state helpers

**Files:**
- Create: `miniprogram/api/ai-recipes.js`
- Create: `miniprogram/utils/ai-recipe.js`
- Create: `miniprogram/tests/ai-recipe.test.mjs`
- Create: `miniprogram/tests/recipe-api-contract.test.mjs`
- Modify: `miniprogram/api/recipes.js`
- Modify: `miniprogram/utils/recipe-filter.js`
- Modify: `miniprogram/tests/recipe-normalize.test.mjs`

**Interfaces:**
- Produces: `recommendRecipes(payload, key)`, `nextRecipeBatch(sessionId, key)`, and `saveAiCandidate(candidateId)`.
- Produces: `buildRecommendationPayload(state)`, `normalizeCandidate(item)`, and `appendUniqueCandidates(current, next)`.

- [ ] **Step 1: Write failing Node tests for request and normalization contracts**

```javascript
test("recommendation payload sends only the current request", () => {
  const payload = buildRecommendationPayload(state());
  assert.deepEqual(payload.filters, {
    meal_type: "dinner",
    max_minutes: 30,
    flavors: ["light"],
    available_ingredients: ["番茄", "鸡蛋"],
  });
  assert.equal(payload.query, "想吃清淡的家常菜");
  assert.equal("profile" in payload, false);
  assert.equal("openid" in payload, false);
  assert.equal("due_date" in payload, false);
  assert.equal("weight_history" in payload, false);
});

test("candidate normalization exposes provenance and favorite state", () => {
  const item = normalizeCandidate(candidatePayload());
  assert.equal(item.sourceLabel, "AI 推荐");
  assert.equal(item.nutritionLabel, "含 AI 估算");
  assert.equal(item.isFavorite, false);
});
```

The API-contract test must stub `wx.request` and assert exact methods, URLs, and `Idempotency-Key` headers.

- [ ] **Step 2: Run tests and verify modules/functions are missing**

Run: `node --test miniprogram/tests/ai-recipe.test.mjs miniprogram/tests/recipe-api-contract.test.mjs miniprogram/tests/recipe-normalize.test.mjs`

Expected: FAIL on missing modules/exports.

- [ ] **Step 3: Implement pure helpers and API wrappers**

Preserve the current uncommitted `recipe-filter.js` edits by reading and patching around them rather than replacing the file. Extend normalization with `source_type`, `nutrition_source`, `nutrition_confidence`, `is_favorite`, `ingredients`, and badges. API wrappers must delegate to the existing authenticated `request()` client. The mini-program sends only filters and current free text; the FastAPI backend derives pregnancy stage, allergens, and avoidances from the authenticated user's stored profile.

- [ ] **Step 4: Run all mini-program pure tests**

Run: `node --test miniprogram/tests/*.test.mjs`

Expected: PASS.

- [ ] **Step 5: Commit API and helper logic without sweeping unrelated dirty files**

```bash
git add miniprogram/api/ai-recipes.js miniprogram/api/recipes.js miniprogram/utils/ai-recipe.js miniprogram/utils/recipe-filter.js miniprogram/tests/ai-recipe.test.mjs miniprogram/tests/recipe-api-contract.test.mjs miniprogram/tests/recipe-normalize.test.mjs
git commit -m "feat: add mini-program AI recipe client"
```

Before committing, inspect `git diff --cached` and confirm the pre-existing recipe-filter changes are understood and intentionally included; otherwise split them into a prior user-change commit only with explicit user approval.

### Task 10: Build the lightweight AI recommendation page and recipe Tab entry

**Files:**
- Create: `miniprogram/pages/ai-recipes/index.js`
- Create: `miniprogram/pages/ai-recipes/index.wxml`
- Create: `miniprogram/pages/ai-recipes/index.wxss`
- Create: `miniprogram/pages/ai-recipes/index.json`
- Modify: `miniprogram/app.json`
- Modify: `miniprogram/pages/recipes/index.js`
- Modify: `miniprogram/pages/recipes/index.wxml`
- Modify: `miniprogram/pages/recipes/index.wxss`
- Modify: `miniprogram/components/recipe-card/index.js`
- Modify: `miniprogram/components/recipe-card/index.wxml`
- Modify: `miniprogram/components/recipe-card/index.wxss`
- Test: `miniprogram/tests/ui-contract.test.mjs`
- Test: `miniprogram/tests/pregnancy-surface.test.mjs`

**Interfaces:**
- Consumes: APIs and pure helpers from Task 9.
- Produces: `/pages/ai-recipes/index` and card events `save` / `open`.

- [ ] **Step 1: Extend failing UI contract tests**

```javascript
test("recipe tab keeps existing card flow and offers a lightweight AI entry", () => {
  const wxml = read("pages/recipes/index.wxml");
  assert.match(wxml, /告诉我今天想吃什么/);
  assert.match(wxml, /帮我推荐/);
  assert.match(wxml, /recipe-card/);
});

test("AI recipe page has filters, free text, next batch and adjustment actions", () => {
  const wxml = read("pages/ai-recipes/index.wxml");
  for (const text of ["餐次", "烹饪时长", "口味", "已有食材", "换一批", "调整条件"]) {
    assert.match(wxml, new RegExp(text));
  }
});
```

- [ ] **Step 2: Run UI tests and verify missing page/markup**

Run: `node --test miniprogram/tests/ui-contract.test.mjs miniprogram/tests/pregnancy-surface.test.mjs`

Expected: FAIL because the new page and entry are missing.

- [ ] **Step 3: Implement UI while preserving the existing recipe design**

Keep the existing top title, search button, horizontal pills, section header, and recipe-card hierarchy. Add a light input row below the title rather than a dark hero card. Use the project's light blue, light mint, pale yellow, and pale orange palette; do not add deep green surfaces or excessive borders.

The AI page state must represent `idle`, `loading`, `results`, `fallback`, `empty`, and `error`. Disable the recommend/next button while a request is in flight. Save each candidate independently and replace its action with “已加入我的食谱” on success.

- [ ] **Step 4: Run all mini-program tests**

Run: `node --test miniprogram/tests/*.test.mjs`

Expected: PASS.

- [ ] **Step 5: Commit the recommendation UI**

```bash
git add miniprogram/pages/ai-recipes miniprogram/app.json miniprogram/pages/recipes/index.js miniprogram/pages/recipes/index.wxml miniprogram/pages/recipes/index.wxss miniprogram/components/recipe-card miniprogram/tests/ui-contract.test.mjs miniprogram/tests/pregnancy-surface.test.mjs
git commit -m "feat: add AI recipe recommendation UI"
```

### Task 11: Add recipe detail, favorite behavior, and ingredient confirmation

**Files:**
- Create: `miniprogram/pages/recipe-confirm/index.js`
- Create: `miniprogram/pages/recipe-confirm/index.wxml`
- Create: `miniprogram/pages/recipe-confirm/index.wxss`
- Create: `miniprogram/pages/recipe-confirm/index.json`
- Modify: `miniprogram/app.json`
- Modify: `miniprogram/pages/recipe-detail/index.js`
- Modify: `miniprogram/pages/recipe-detail/index.wxml`
- Modify: `miniprogram/pages/recipe-detail/index.wxss`
- Modify: `miniprogram/pages/privacy/index.wxml`
- Modify: `miniprogram/pages/data-sources/index.wxml`
- Test: `miniprogram/tests/ui-contract.test.mjs`
- Test: `miniprogram/tests/pregnancy-surface.test.mjs`

**Interfaces:**
- Consumes: confirmed recording API from Task 7 and mini client from Task 9.
- Produces: `/pages/recipe-confirm/index` and complete AI/provenance disclosures.

- [ ] **Step 1: Add failing detail and confirmation UI tests**

```javascript
test("mixed or estimated recipes route through ingredient confirmation", () => {
  const detail = read("pages/recipe-detail/index.js");
  assert.match(detail, /nutrition_source/);
  assert.match(detail, /recipe-confirm/);
});

test("recipe confirmation displays grams and source labels", () => {
  const wxml = read("pages/recipe-confirm/index.wxml");
  assert.match(wxml, /确认食材与份量/);
  assert.match(wxml, /克/);
  assert.match(wxml, /AI 估算/);
});
```

- [ ] **Step 2: Run focused UI tests and verify failure**

Run: `node --test miniprogram/tests/ui-contract.test.mjs miniprogram/tests/pregnancy-surface.test.mjs`

Expected: FAIL because confirmation and detail provenance are missing.

- [ ] **Step 3: Implement detail and confirmation flow**

Show ingredients, steps, allergen summary, safety summary, source badge, nutrition source, and the fixed disclaimer: “AI 推荐仅供饮食安排参考，不替代医生建议。” `tka` recipes retain one-click record. `mixed` and `ai_estimated` recipes navigate to confirmation, allow positive gram edits, and submit `confirmed_items` with a fresh idempotency key. Preserve the existing light card styling and normal font sizes.

Update privacy/data-source pages to state that DeepSeek receives only minimized pregnancy stage/preferences, AI output is labeled, and nutrition may be TKA, mixed, or estimated.

- [ ] **Step 4: Run all mini-program tests**

Run: `node --test miniprogram/tests/*.test.mjs`

Expected: PASS.

- [ ] **Step 5: Commit the completed recipe experience**

```bash
git add miniprogram/pages/recipe-confirm miniprogram/app.json miniprogram/pages/recipe-detail miniprogram/pages/privacy/index.wxml miniprogram/pages/data-sources/index.wxml miniprogram/tests/ui-contract.test.mjs miniprogram/tests/pregnancy-surface.test.mjs
git commit -m "feat: confirm and disclose AI recipe nutrition"
```

### Task 12: Document operations and run full verification

**Files:**
- Modify: `backend/README.md`
- Modify: `README.md`
- Test: all backend and mini-program tests.

**Interfaces:**
- Consumes: all completed tasks.
- Produces: documented local setup, import, provider configuration, and production rollout sequence.

- [ ] **Step 1: Add documentation assertions to existing contract tests**

Extend `backend/tests/test_production_settings.py` to assert production rejects an enabled AI recipe feature without an API key and accepts a disabled feature without one. Extend `miniprogram/tests/ui-contract.test.mjs` to assert AI disclosure copy exists.

- [ ] **Step 2: Run the full suite before documentation changes**

Run: `cd backend && .venv/bin/pytest -q tests`

Run: `node --test miniprogram/tests/*.test.mjs`

Expected: settings/disclosure assertions fail until configuration and documentation surfaces are final; all earlier behavior remains green.

- [ ] **Step 3: Document exact operational commands**

Document these commands and their purpose:

```bash
cd backend
.venv/bin/alembic upgrade head
cd ..
./scripts/import-platform-recipes.sh backend/data/imports/platform-recipes-v1.json platform-recipes-v1
./scripts/cleanup-ai-recipe-sessions.sh
./scripts/start-local.sh
```

Document `SLIMMING_AI_RECIPE_ENABLED`, `SLIMMING_AI_PROVIDER`, `SLIMMING_AI_BASE_URL`, `SLIMMING_AI_MODEL`, `SLIMMING_AI_API_KEY`, timeout/retry/TTL and hourly user/IP limit settings, official-domain requirement, secret rotation, and fallback behavior. State that platform recipes must be imported after TKA data so nutrition matching can succeed. Document running the bounded cleanup command daily in the deployment scheduler and state that it deletes only expired temporary recommendation sessions, never saved recipes or meal history.

- [ ] **Step 4: Run migrations and all automated verification**

Run: `cd backend && .venv/bin/alembic upgrade head && .venv/bin/pytest -q tests`

Expected: Alembic reaches head and all backend tests pass.

Run: `node --test miniprogram/tests/*.test.mjs`

Expected: all mini-program tests pass.

Run: `git diff --check`

Expected: no whitespace errors.

- [ ] **Step 5: Perform local smoke verification**

Run: `./scripts/stop-local.sh`

Run: `./scripts/start-local.sh`

Verify:

```bash
curl -fsS http://127.0.0.1:8000/health
```

Expected: `{"status":"ok","service":"slimming-api"}`.

With AI disabled, verify recommendation returns `mode="fallback"`. With a locally configured DeepSeek key, verify one request returns only labeled, user-scoped, safety-checked candidates; never print the key or complete sensitive prompt in logs.

- [ ] **Step 6: Review the staged diff and commit documentation/verification changes**

```bash
git add backend/README.md README.md backend/tests/test_production_settings.py miniprogram/tests/ui-contract.test.mjs
git diff --cached --check
git commit -m "docs: document AI recipe operations"
```

- [ ] **Step 7: Run final branch verification and record evidence**

Run: `git status --short && git log --oneline --decorate -15`

Expected: only known pre-existing user-owned files remain uncommitted; every implementation task has its own commit. Record the exact backend test count, mini-program test count, migration head, and smoke-test response in the final handoff.
