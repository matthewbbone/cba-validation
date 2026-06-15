from __future__ import annotations

import csv
from pathlib import Path
from typing import get_args, get_origin

import pytest

from structures import (
    PROVISION_EXTRACTION_REGISTRY,
    PROVISION_FORMAT_REGISTRY,
    PROVISION_METADATA_REGISTRY,
    PROVISION_STRING_FIELD_REGISTRY,
)
from structures.common import MoneyAmount, QuantitativeValue
from structures.complex import (
    ArbitrationFlags,
    DisciplineJustCauseFlags,
    WageBaseRateExtraction,
)


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


def test_extraction_string_fields_are_lists_except_summarize() -> None:
    for concept_id, model_cls in PROVISION_EXTRACTION_REGISTRY.items():
        instance = model_cls(summarize="No matching provision appears.", exists=False)
        for field_name, field in model_cls.model_fields.items():
            annotation = field.annotation
            if field_name == "summarize":
                assert annotation is str, concept_id
                continue
            if field_name in model_cls.string_detail_fields:
                assert get_origin(annotation) is list, (concept_id, field_name)
                assert get_args(annotation) == (str,), (concept_id, field_name)
                assert getattr(instance, field_name) == [], (concept_id, field_name)
            else:
                assert annotation is not str, (concept_id, field_name)


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


def test_discipline_just_cause_is_complex_and_requires_detail() -> None:
    model_cls = PROVISION_EXTRACTION_REGISTRY["C_DISCIPLINE_JUST_CAUSE"]
    assert PROVISION_FORMAT_REGISTRY["C_DISCIPLINE_JUST_CAUSE"] == "complex"
    with pytest.raises(ValueError):
        model_cls(
            summarize="The agreement requires just cause for discipline.",
            exists=True,
        )

    extraction = model_cls(
        summarize="The agreement requires just cause for discipline.",
        exists=True,
        flags=DisciplineJustCauseFlags(has_just_cause_standard=True),
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


def test_metadata_registry_covers_all_provisions() -> None:
    assert set(PROVISION_METADATA_REGISTRY) == set(PROVISION_EXTRACTION_REGISTRY)


def test_string_field_registry_covers_all_provisions() -> None:
    assert set(PROVISION_STRING_FIELD_REGISTRY) == set(PROVISION_EXTRACTION_REGISTRY)


def test_representative_string_fields_are_exposed() -> None:
    assert {
        "occupation_names",
        "classification_names",
        "effective_dates",
    }.issubset(PROVISION_STRING_FIELD_REGISTRY["C_WAGE_BASE_RATE"])
    assert {
        "coverage_tiers",
        "eligible_employee_groups",
    }.issubset(
        PROVISION_STRING_FIELD_REGISTRY[
        "C_HEALTH_MEDICAL_ACTIVE_CONTRIBUTION"
        ]
    )
    assert {
        "bargaining_unit_descriptions",
        "included_employee_groups",
        "excluded_employee_groups",
    }.issubset(PROVISION_STRING_FIELD_REGISTRY["C_RECOGNITION_COVERAGE_SCOPE"])


def test_label_and_broad_eligibility_string_fields_are_not_exposed() -> None:
    removed_fields = {
        "certification_names",
        "covered_service_names",
        "eligibility_terms",
        "fund_names",
        "plan_names",
        "step_names",
        "union_names",
    }
    for concept_id, fields in PROVISION_STRING_FIELD_REGISTRY.items():
        assert not (set(fields) & removed_fields), concept_id


def test_complex_existing_extraction_accepts_string_detail_only() -> None:
    model_cls = PROVISION_EXTRACTION_REGISTRY["C_RECOGNITION_COVERAGE_SCOPE"]
    extraction = model_cls(
        summarize="The agreement identifies the covered bargaining unit.",
        exists=True,
        bargaining_unit_descriptions=["production and maintenance employees"],
    )
    assert extraction.has_normalized_detail()


def test_absent_extraction_rejects_string_detail() -> None:
    model_cls = PROVISION_EXTRACTION_REGISTRY["C_WAGE_BASE_RATE"]
    with pytest.raises(ValueError):
        model_cls(
            summarize="No wage schedule appears.",
            exists=False,
            occupation_names=["mechanic"],
        )


def test_quantitative_existing_extraction_accepts_string_detail_without_value() -> None:
    model_cls = PROVISION_EXTRACTION_REGISTRY["C_PREMIUM_SHIFT"]
    extraction = model_cls(
        summarize="The agreement limits shift premium eligibility to covered mechanics.",
        exists=True,
        covered_employee_groups=["mechanics"],
    )
    assert extraction.value is None
    assert extraction.has_string_detail()


def test_ranked_core_metadata_matches_deep_research_priorities() -> None:
    expected = {
        "C_WAGE_BASE_RATE": 1,
        "C_PREMIUM_OVERTIME": 2,
        "C_GRIEVANCE_PROCEDURE": 3,
        "C_ARBITRATION": 3,
        "C_RECOGNITION_COVERAGE_SCOPE": 4,
        "C_JOB_SECURITY_LAYOFF_ORDER": 5,
        "C_JOB_SECURITY_RECALL": 5,
        "C_HEALTH_MEDICAL_ACTIVE_CONTRIBUTION": 6,
        "C_RETIREMENT_PENSION": 7,
        "C_LEAVE_VACATION": 8,
        "C_SENIORITY_SYSTEM": 9,
        "C_DISCIPLINE_JUST_CAUSE": 10,
        "C_LEAVE_HOLIDAYS": 11,
        "C_SAFETY_PPE_UNSAFE_WORK": 12,
        "C_LEAVE_SICK": 14,
    }
    for concept_id, rank in expected.items():
        meta = PROVISION_METADATA_REGISTRY[concept_id]
        assert meta.priority_tier == "core", concept_id
        assert meta.rank == rank, concept_id


def test_conditional_and_advanced_metadata() -> None:
    assert (
        PROVISION_METADATA_REGISTRY["C_UNION_SECURITY_DUES_CHECKOFF"].priority_tier
        == "conditional_core"
    )
    assert (
        PROVISION_METADATA_REGISTRY[
            "C_HEALTH_MEDICAL_ACTIVE_PLAN_DESIGN"
        ].priority_tier
        == "advanced"
    )
    assert (
        PROVISION_METADATA_REGISTRY["C_LABOR_MANAGEMENT_COMMITTEE"].priority_tier
        == "advanced"
    )
