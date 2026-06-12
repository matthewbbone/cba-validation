from __future__ import annotations

import csv
from pathlib import Path
from typing import Any

import pytest

from structures import PROVISION_EXTRACTION_REGISTRY, PROVISION_FORMAT_REGISTRY
from structures.common import MoneyAmount, QuantitativeValue
from structures.complex import ArbitrationFlags, WageBaseRateExtraction


def test_registry_matches_provision_dictionary() -> None:
    dictionary_path = (
        Path(__file__).resolve().parents[1]
        / "data"
        / "cba_meta"
        / "cba_provision_dictionary.csv"
    )
    rows = list(csv.DictReader(dictionary_path.open(newline="")))
    assert len(rows) == 99
    assert set(PROVISION_EXTRACTION_REGISTRY) == {row["concept_id"] for row in rows}
    assert set(PROVISION_FORMAT_REGISTRY) == {row["concept_id"] for row in rows}


def test_extraction_schemas_only_have_summarize_string_field() -> None:
    def walk_schema(schema: dict[str, Any]) -> list[str]:
        string_paths: list[str] = []

        def walk(value: Any, path: tuple[str, ...]) -> None:
            if isinstance(value, dict):
                if value.get("type") == "string":
                    string_paths.append(".".join(path))
                for key, child in value.items():
                    if key == "description":
                        continue
                    walk(child, (*path, key))
            elif isinstance(value, list):
                for index, child in enumerate(value):
                    walk(child, (*path, str(index)))

        walk(schema, ())
        return string_paths

    for concept_id, model_cls in PROVISION_EXTRACTION_REGISTRY.items():
        string_paths = walk_schema(model_cls.model_json_schema())
        assert string_paths == ["properties.summarize"], concept_id


def test_extraction_schemas_have_short_descriptions() -> None:
    for concept_id, model_cls in PROVISION_EXTRACTION_REGISTRY.items():
        description = model_cls.model_json_schema().get("description")
        assert isinstance(description, str), concept_id
        assert 0 < len(description) <= 100, concept_id


def test_complex_absent_extraction_allows_empty_details() -> None:
    model_cls = PROVISION_EXTRACTION_REGISTRY["C_GRIEVANCE_PROCEDURE"]
    extraction = model_cls(summarize="No grievance procedure appears.", exists=False)
    assert extraction.concept_id == "C_GRIEVANCE_PROCEDURE"
    assert extraction.values == []
    assert extraction.flags is None


def test_complex_existing_extraction_requires_detail() -> None:
    model_cls = PROVISION_EXTRACTION_REGISTRY["C_GRIEVANCE_PROCEDURE"]
    with pytest.raises(ValueError):
        model_cls(summarize="The agreement describes a grievance process.", exists=True)


def test_complex_existing_extraction_accepts_boolean_detail() -> None:
    model_cls = PROVISION_EXTRACTION_REGISTRY["C_ARBITRATION"]
    extraction = model_cls(
        summarize="The agreement provides final and binding arbitration.",
        exists=True,
        flags=ArbitrationFlags(final_and_binding=True, has_arbitration=True),
    )
    assert extraction.exists is True


def test_safety_ppe_flags_are_provision_specific() -> None:
    model_cls = PROVISION_EXTRACTION_REGISTRY["C_SAFETY_PPE_UNSAFE_WORK"]
    flags_schema = model_cls.model_json_schema()["$defs"]["SafetyPpeUnsafeWorkFlags"]
    assert set(flags_schema["properties"]) == {
        "has_ppe_requirement",
        "has_unsafe_work_right",
        "has_safety_standards",
        "has_hazard_response",
        "has_safety_committee",
    }


def test_binary_existing_extraction_allows_indicator_only() -> None:
    model_cls = PROVISION_EXTRACTION_REGISTRY["C_DISCIPLINE_JUST_CAUSE"]
    extraction = model_cls(
        summarize="The agreement requires just cause for discipline.",
        exists=True,
    )
    assert extraction.exists is True


def test_quantitative_existing_extraction_requires_value() -> None:
    model_cls = PROVISION_EXTRACTION_REGISTRY["C_PREMIUM_SHIFT"]
    with pytest.raises(ValueError):
        model_cls(summarize="The agreement includes shift premium pay.", exists=True)


def test_quantitative_absent_extraction_requires_no_value() -> None:
    model_cls = PROVISION_EXTRACTION_REGISTRY["C_PREMIUM_SHIFT"]
    value = QuantitativeValue(money=MoneyAmount(amount=1.00))
    with pytest.raises(ValueError):
        model_cls(
            summarize="No shift premium appears.",
            exists=False,
            value=value,
        )


def test_quantitative_existing_extraction_accepts_value() -> None:
    model_cls = PROVISION_EXTRACTION_REGISTRY["C_PREMIUM_SHIFT"]
    value = QuantitativeValue(money=MoneyAmount(amount=1.00))
    extraction = model_cls(
        summarize="The agreement provides a one-dollar shift premium.",
        exists=True,
        value=value,
    )
    assert extraction.value == value


def test_wage_base_rate_uses_quantitative_values() -> None:
    extraction = WageBaseRateExtraction(
        summarize="The agreement lists a 25 dollar base wage.",
        exists=True,
        values=[QuantitativeValue(money=MoneyAmount(amount=25.00))],
    )
    assert extraction.values[0].money is not None
    assert extraction.values[0].money.amount == 25.00
