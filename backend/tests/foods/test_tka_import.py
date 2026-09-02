from decimal import Decimal
import json
from pathlib import Path

import pytest
from sqlalchemy import select

from app.foods.models import Food
from app.foods.tka_provider import TkaProvider


FIXTURE = Path(__file__).parent / "fixtures" / "tka_sample.json"


def test_import_preserves_source_and_normalizes_per_100g(db_session):
    report = TkaProvider(db_session).import_dataset(FIXTURE, "fixture-2026-08")
    food = db_session.scalar(select(Food).where(Food.source_food_id == "8535"))

    assert report.imported == 1
    assert food.source_url == "https://tka.nutridata.ee/en/foods/3"
    assert food.energy_kcal_100g == Decimal("162.00")
    assert food.dataset_version == "fixture-2026-08"
    assert food.raw_sha256


def test_import_is_idempotent_for_provider_source_and_version(db_session):
    provider = TkaProvider(db_session)
    first = provider.import_dataset(FIXTURE, "fixture-2026-08")
    second = provider.import_dataset(FIXTURE, "fixture-2026-08")

    assert first.imported == 1
    assert second.imported == 0
    assert second.unchanged == 1


def test_import_rejects_missing_dataset_version(db_session):
    with pytest.raises(ValueError, match="数据版本"):
        TkaProvider(db_session).import_dataset(FIXTURE, "")


def test_chinese_alias_and_english_name_are_searchable(db_session):
    provider = TkaProvider(db_session)
    provider.import_dataset(FIXTURE, "fixture-2026-08")

    assert provider.search("琼脂粉")[0].source_food_id == "8535"
    assert provider.search("agar", locale="en")[0].name == "Agar, powder"


def test_official_synonyms_are_searchable(db_session):
    provider = TkaProvider(db_session)
    provider.import_dataset(FIXTURE, "fixture-2026-08")

    assert provider.search("Chinese grass", locale="en")[0].source_food_id == "8535"


def test_import_updates_aliases_when_only_local_aliases_change(db_session, tmp_path):
    provider = TkaProvider(db_session)
    provider.import_dataset(FIXTURE, "fixture-2026-08")
    payload = json.loads(FIXTURE.read_text(encoding="utf-8"))
    payload["aliases_zh"]["8535"] = ["琼脂", "寒天"]
    changed_fixture = tmp_path / "tka_alias_update.json"
    changed_fixture.write_text(json.dumps(payload, ensure_ascii=False), encoding="utf-8")

    report = provider.import_dataset(changed_fixture, "fixture-2026-08")

    assert report.updated == 1
    assert report.unchanged == 0
    assert provider.search("寒天")[0].source_food_id == "8535"


def test_import_merges_reviewed_local_chinese_aliases(db_session):
    provider = TkaProvider(db_session)
    provider.import_dataset(FIXTURE, "fixture-2026-08")

    assert provider.search("大菜粉")[0].source_food_id == "8535"
