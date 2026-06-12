from __future__ import annotations

from typing import ClassVar, Literal

from .templates import BinaryProvisionExtraction


# Provisions where the stable comparison target is whether the clause exists.


class DisciplineJustCauseExtraction(BinaryProvisionExtraction):
    """Just cause and substantive discipline/discharge standard."""
    concept_id: ClassVar[Literal['C_DISCIPLINE_JUST_CAUSE']] = 'C_DISCIPLINE_JUST_CAUSE'
    category: ClassVar[Literal['Disputes']] = 'Disputes'


class LaborManagementCommitteeExtraction(BinaryProvisionExtraction):
    """Labor-Management Cooperation Committee (LMCC)."""
    concept_id: ClassVar[Literal['C_LABOR_MANAGEMENT_COMMITTEE']] = 'C_LABOR_MANAGEMENT_COMMITTEE'
    category: ClassVar[Literal['Safety']] = 'Safety'


class HealthLifeInsuranceExtraction(BinaryProvisionExtraction):
    """Life insurance Board-provided."""
    concept_id: ClassVar[Literal['C_HEALTH_LIFE_INSURANCE']] = 'C_HEALTH_LIFE_INSURANCE'
    category: ClassVar[Literal['Healthcare']] = 'Healthcare'


class JobSecuritySubcontractingExtraction(BinaryProvisionExtraction):
    """Subcontracting at company discretion."""
    concept_id: ClassVar[Literal['C_JOB_SECURITY_SUBCONTRACTING']] = 'C_JOB_SECURITY_SUBCONTRACTING'
    category: ClassVar[Literal['Security']] = 'Security'


class UnionSecurityExtraction(BinaryProvisionExtraction):
    """Union membership required as condition of employment."""
    concept_id: ClassVar[Literal['C_UNION_SECURITY']] = 'C_UNION_SECURITY'
    category: ClassVar[Literal['Recognition']] = 'Recognition'


class JobSecurityBumpingExtraction(BinaryProvisionExtraction):
    """Bumping rights to former classification."""
    concept_id: ClassVar[Literal['C_JOB_SECURITY_BUMPING']] = 'C_JOB_SECURITY_BUMPING'
    category: ClassVar[Literal['Security']] = 'Security'


class JobSecurityNoContractingOutExtraction(BinaryProvisionExtraction):
    """Subcontracting limitation."""
    concept_id: ClassVar[Literal['C_JOB_SECURITY_NO_CONTRACTING_OUT']] = 'C_JOB_SECURITY_NO_CONTRACTING_OUT'
    category: ClassVar[Literal['Security']] = 'Security'


class PremiumStandbyExtraction(BinaryProvisionExtraction):
    """Standby provision."""
    concept_id: ClassVar[Literal['C_PREMIUM_STANDBY']] = 'C_PREMIUM_STANDBY'
    category: ClassVar[Literal['Compensation']] = 'Compensation'


class HealthBenefitsExtraction(BinaryProvisionExtraction):
    """Health and welfare benefits."""
    concept_id: ClassVar[Literal['C_HEALTH_BENEFITS']] = 'C_HEALTH_BENEFITS'
    category: ClassVar[Literal['Healthcare']] = 'Healthcare'
