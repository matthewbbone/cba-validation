from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import Field

from .templates import BinaryProvisionExtraction


# Provisions where the stable comparison target is whether the clause exists.


class LaborManagementCommitteeExtraction(BinaryProvisionExtraction):
    """Labor-Management Cooperation Committee (LMCC)."""
    concept_id: ClassVar[Literal['C_LABOR_MANAGEMENT_COMMITTEE']] = 'C_LABOR_MANAGEMENT_COMMITTEE'
    category: ClassVar[Literal['Safety']] = 'Safety'
    string_detail_fields: ClassVar[tuple[str, ...]] = ()


class HealthLifeInsuranceExtraction(BinaryProvisionExtraction):
    """Life insurance Board-provided."""
    concept_id: ClassVar[Literal['C_HEALTH_LIFE_INSURANCE']] = 'C_HEALTH_LIFE_INSURANCE'
    category: ClassVar[Literal['Healthcare']] = 'Healthcare'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('coverage_tiers', 'eligible_employee_groups')
    coverage_tiers: list[str] = Field(default_factory=list)
    eligible_employee_groups: list[str] = Field(default_factory=list)


class JobSecuritySubcontractingExtraction(BinaryProvisionExtraction):
    """Subcontracting at company discretion."""
    concept_id: ClassVar[Literal['C_JOB_SECURITY_SUBCONTRACTING']] = 'C_JOB_SECURITY_SUBCONTRACTING'
    category: ClassVar[Literal['Security']] = 'Security'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('protected_work_terms', 'subcontracting_exception_terms', 'notice_recipient_names')
    protected_work_terms: list[str] = Field(default_factory=list)
    subcontracting_exception_terms: list[str] = Field(default_factory=list)
    notice_recipient_names: list[str] = Field(default_factory=list)


class UnionSecurityExtraction(BinaryProvisionExtraction):
    """Union membership required as condition of employment."""
    concept_id: ClassVar[Literal['C_UNION_SECURITY']] = 'C_UNION_SECURITY'
    category: ClassVar[Literal['Recognition']] = 'Recognition'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('excluded_employee_groups',)
    excluded_employee_groups: list[str] = Field(default_factory=list)


class JobSecurityBumpingExtraction(BinaryProvisionExtraction):
    """Bumping rights to former classification."""
    concept_id: ClassVar[Literal['C_JOB_SECURITY_BUMPING']] = 'C_JOB_SECURITY_BUMPING'
    category: ClassVar[Literal['Security']] = 'Security'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('affected_employee_groups', 'exception_terms')
    affected_employee_groups: list[str] = Field(default_factory=list)
    exception_terms: list[str] = Field(default_factory=list)


class JobSecurityNoContractingOutExtraction(BinaryProvisionExtraction):
    """Subcontracting limitation."""
    concept_id: ClassVar[Literal['C_JOB_SECURITY_NO_CONTRACTING_OUT']] = 'C_JOB_SECURITY_NO_CONTRACTING_OUT'
    category: ClassVar[Literal['Security']] = 'Security'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('protected_work_terms', 'subcontracting_exception_terms', 'notice_recipient_names')
    protected_work_terms: list[str] = Field(default_factory=list)
    subcontracting_exception_terms: list[str] = Field(default_factory=list)
    notice_recipient_names: list[str] = Field(default_factory=list)


class PremiumStandbyExtraction(BinaryProvisionExtraction):
    """Standby provision."""
    concept_id: ClassVar[Literal['C_PREMIUM_STANDBY']] = 'C_PREMIUM_STANDBY'
    category: ClassVar[Literal['Compensation']] = 'Compensation'
    string_detail_fields: ClassVar[tuple[str, ...]] = ()


class HealthBenefitsExtraction(BinaryProvisionExtraction):
    """Health and welfare benefits."""
    concept_id: ClassVar[Literal['C_HEALTH_BENEFITS']] = 'C_HEALTH_BENEFITS'
    category: ClassVar[Literal['Healthcare']] = 'Healthcare'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('coverage_tiers', 'eligible_employee_groups')
    coverage_tiers: list[str] = Field(default_factory=list)
    eligible_employee_groups: list[str] = Field(default_factory=list)
