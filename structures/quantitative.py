from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import Field

from .templates import QuantitativeProvisionExtraction


# Provisions whose comparison target is a single normalized value; value is None when absent.


class HealthMedicalActiveContributionExtraction(QuantitativeProvisionExtraction):
    """H&W Fund contribution."""
    concept_id: ClassVar[Literal['C_HEALTH_MEDICAL_ACTIVE_CONTRIBUTION']] = 'C_HEALTH_MEDICAL_ACTIVE_CONTRIBUTION'
    category: ClassVar[Literal['Healthcare']] = 'Healthcare'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('coverage_tiers', 'eligible_employee_groups')
    coverage_tiers: list[str] = Field(default_factory=list)
    eligible_employee_groups: list[str] = Field(default_factory=list)


class PremiumShiftExtraction(QuantitativeProvisionExtraction):
    """Shift differentials and night/weekend premiums."""
    concept_id: ClassVar[Literal['C_PREMIUM_SHIFT']] = 'C_PREMIUM_SHIFT'
    category: ClassVar[Literal['Compensation']] = 'Compensation'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('covered_employee_groups',)
    covered_employee_groups: list[str] = Field(default_factory=list)


class LeavePersonalMiscExtraction(QuantitativeProvisionExtraction):
    """Bereavement/compassionate leave."""
    concept_id: ClassVar[Literal['C_LEAVE_PERSONAL_MISC']] = 'C_LEAVE_PERSONAL_MISC'
    category: ClassVar[Literal['Leave']] = 'Leave'
    string_detail_fields: ClassVar[tuple[str, ...]] = ()


class RetirementSavingsAnnuityExtraction(QuantitativeProvisionExtraction):
    """Annuity Fund (CT Carpenters) contributions."""
    concept_id: ClassVar[Literal['C_RETIREMENT_SAVINGS_ANNUITY']] = 'C_RETIREMENT_SAVINGS_ANNUITY'
    category: ClassVar[Literal['Ancillary']] = 'Ancillary'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('eligible_employee_groups', 'vesting_terms')
    eligible_employee_groups: list[str] = Field(default_factory=list)
    vesting_terms: list[str] = Field(default_factory=list)


class PremiumStandbyOnCallExtraction(QuantitativeProvisionExtraction):
    """Standby pay."""
    concept_id: ClassVar[Literal['C_PREMIUM_STANDBY_ON_CALL']] = 'C_PREMIUM_STANDBY_ON_CALL'
    category: ClassVar[Literal['Compensation']] = 'Compensation'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('covered_employee_groups',)
    covered_employee_groups: list[str] = Field(default_factory=list)


class UniformClothingAllowanceExtraction(QuantitativeProvisionExtraction):
    """Safety shoe program."""
    concept_id: ClassVar[Literal['C_UNIFORM_CLOTHING_ALLOWANCE']] = 'C_UNIFORM_CLOTHING_ALLOWANCE'
    category: ClassVar[Literal['Compensation']] = 'Compensation'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('covered_employee_groups',)
    covered_employee_groups: list[str] = Field(default_factory=list)


class TimeScheduleNoticeChangeExtraction(QuantitativeProvisionExtraction):
    """Schedule changes."""
    concept_id: ClassVar[Literal['C_TIME_SCHEDULE_NOTICE_CHANGE']] = 'C_TIME_SCHEDULE_NOTICE_CHANGE'
    category: ClassVar[Literal['Scheduling']] = 'Scheduling'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('notice_trigger_terms', 'affected_employee_groups')
    notice_trigger_terms: list[str] = Field(default_factory=list)
    affected_employee_groups: list[str] = Field(default_factory=list)


class LegalServicesFundExtraction(QuantitativeProvisionExtraction):
    """Group legal services fund."""
    concept_id: ClassVar[Literal['C_LEGAL_SERVICES_FUND']] = 'C_LEGAL_SERVICES_FUND'
    category: ClassVar[Literal['Ancillary']] = 'Ancillary'
    string_detail_fields: ClassVar[tuple[str, ...]] = ()


class ChildDependentCareExtraction(QuantitativeProvisionExtraction):
    """Fellowships for Day Care."""
    concept_id: ClassVar[Literal['C_CHILD_DEPENDENT_CARE']] = 'C_CHILD_DEPENDENT_CARE'
    category: ClassVar[Literal['Ancillary']] = 'Ancillary'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('eligible_dependent_terms',)
    eligible_dependent_terms: list[str] = Field(default_factory=list)


class HealthEmployerContributionExtraction(QuantitativeProvisionExtraction):
    """IAFF VEBA health benefit fund."""
    concept_id: ClassVar[Literal['C_HEALTH_EMPLOYER_CONTRIBUTION']] = 'C_HEALTH_EMPLOYER_CONTRIBUTION'
    category: ClassVar[Literal['Healthcare']] = 'Healthcare'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('coverage_tiers', 'eligible_employee_groups')
    coverage_tiers: list[str] = Field(default_factory=list)
    eligible_employee_groups: list[str] = Field(default_factory=list)


class JobSecurityLayoffExtraction(QuantitativeProvisionExtraction):
    """Dismissal pay."""
    concept_id: ClassVar[Literal['C_JOB_SECURITY_LAYOFF']] = 'C_JOB_SECURITY_LAYOFF'
    category: ClassVar[Literal['Security']] = 'Security'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('affected_employee_groups', 'exception_terms')
    affected_employee_groups: list[str] = Field(default_factory=list)
    exception_terms: list[str] = Field(default_factory=list)


class TransitCommuterBenefitExtraction(QuantitativeProvisionExtraction):
    """Transit subsidy per SMC 4.20.370."""
    concept_id: ClassVar[Literal['C_TRANSIT_COMMUTER_BENEFIT']] = 'C_TRANSIT_COMMUTER_BENEFIT'
    category: ClassVar[Literal['Ancillary']] = 'Ancillary'
    string_detail_fields: ClassVar[tuple[str, ...]] = ()


class PremiumForemanExtraction(QuantitativeProvisionExtraction):
    """Foreman and General Foreman premium."""
    concept_id: ClassVar[Literal['C_PREMIUM_FOREMAN']] = 'C_PREMIUM_FOREMAN'
    category: ClassVar[Literal['Compensation']] = 'Compensation'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('classification_names',)
    classification_names: list[str] = Field(default_factory=list)


class HealthActiveContributionExtraction(QuantitativeProvisionExtraction):
    """Active health."""
    concept_id: ClassVar[Literal['C_HEALTH_ACTIVE_CONTRIBUTION']] = 'C_HEALTH_ACTIVE_CONTRIBUTION'
    category: ClassVar[Literal['Healthcare']] = 'Healthcare'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('coverage_tiers', 'eligible_employee_groups')
    coverage_tiers: list[str] = Field(default_factory=list)
    eligible_employee_groups: list[str] = Field(default_factory=list)


class LeaveBereavementExtraction(QuantitativeProvisionExtraction):
    """Bereavement leave."""
    concept_id: ClassVar[Literal['C_LEAVE_BEREAVEMENT']] = 'C_LEAVE_BEREAVEMENT'
    category: ClassVar[Literal['Leave']] = 'Leave'
    string_detail_fields: ClassVar[tuple[str, ...]] = ()


class PremiumHazardExtraction(QuantitativeProvisionExtraction):
    """Hazardous work differential."""
    concept_id: ClassVar[Literal['C_PREMIUM_HAZARD']] = 'C_PREMIUM_HAZARD'
    category: ClassVar[Literal['Compensation']] = 'Compensation'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('covered_employee_groups',)
    covered_employee_groups: list[str] = Field(default_factory=list)


class HealthInsuranceBuyoutExtraction(QuantitativeProvisionExtraction):
    """Health insurance opt-out payment $1,200/year."""
    concept_id: ClassVar[Literal['C_HEALTH_INSURANCE_BUYOUT']] = 'C_HEALTH_INSURANCE_BUYOUT'
    category: ClassVar[Literal['Healthcare']] = 'Healthcare'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('eligible_employee_groups',)
    eligible_employee_groups: list[str] = Field(default_factory=list)


class WageSavingsExtraction(QuantitativeProvisionExtraction):
    """Savings/deferred compensation contribution."""
    concept_id: ClassVar[Literal['C_WAGE_SAVINGS']] = 'C_WAGE_SAVINGS'
    category: ClassVar[Literal['Compensation']] = 'Compensation'
    string_detail_fields: ClassVar[tuple[str, ...]] = ()


class WageVacationSuppExtraction(QuantitativeProvisionExtraction):
    """Vacation/Supplemental dues contribution $2.95/hr."""
    concept_id: ClassVar[Literal['C_WAGE_VACATION_SUPP']] = 'C_WAGE_VACATION_SUPP'
    category: ClassVar[Literal['Compensation']] = 'Compensation'
    string_detail_fields: ClassVar[tuple[str, ...]] = ()


class WageAccrualVacationExtraction(QuantitativeProvisionExtraction):
    """Vacation/holiday pay accrual ($0.50/hr)."""
    concept_id: ClassVar[Literal['C_WAGE_ACCRUAL_VACATION']] = 'C_WAGE_ACCRUAL_VACATION'
    category: ClassVar[Literal['Compensation']] = 'Compensation'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('covered_employee_groups',)
    covered_employee_groups: list[str] = Field(default_factory=list)


class PremiumLeadmanExtraction(QuantitativeProvisionExtraction):
    """Leadman premium."""
    concept_id: ClassVar[Literal['C_PREMIUM_LEADMAN']] = 'C_PREMIUM_LEADMAN'
    category: ClassVar[Literal['Compensation']] = 'Compensation'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('classification_names',)
    classification_names: list[str] = Field(default_factory=list)


class LeavePersonalExtraction(QuantitativeProvisionExtraction):
    """Perfect Attendance Days (paid personal time)."""
    concept_id: ClassVar[Literal['C_LEAVE_PERSONAL']] = 'C_LEAVE_PERSONAL'
    category: ClassVar[Literal['Leave']] = 'Leave'
    string_detail_fields: ClassVar[tuple[str, ...]] = ()


class HealthWelfareFundExtraction(QuantitativeProvisionExtraction):
    """Welfare fund employer contributions."""
    concept_id: ClassVar[Literal['C_HEALTH_WELFARE_FUND']] = 'C_HEALTH_WELFARE_FUND'
    category: ClassVar[Literal['Healthcare']] = 'Healthcare'
    string_detail_fields: ClassVar[tuple[str, ...]] = ()


class LeaveSubsistenceExtraction(QuantitativeProvisionExtraction):
    """Subsistence."""
    concept_id: ClassVar[Literal['C_LEAVE_SUBSISTENCE']] = 'C_LEAVE_SUBSISTENCE'
    category: ClassVar[Literal['Leave']] = 'Leave'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('geographic_areas',)
    geographic_areas: list[str] = Field(default_factory=list)


class HealthDisabilityExtraction(QuantitativeProvisionExtraction):
    """Short-term disability $400/week max 26 weeks."""
    concept_id: ClassVar[Literal['C_HEALTH_DISABILITY']] = 'C_HEALTH_DISABILITY'
    category: ClassVar[Literal['Healthcare']] = 'Healthcare'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('waiting_period_terms',)
    waiting_period_terms: list[str] = Field(default_factory=list)


class LeaveJuryDutyExtraction(QuantitativeProvisionExtraction):
    """Jury duty."""
    concept_id: ClassVar[Literal['C_LEAVE_JURY_DUTY']] = 'C_LEAVE_JURY_DUTY'
    category: ClassVar[Literal['Leave']] = 'Leave'
    string_detail_fields: ClassVar[tuple[str, ...]] = ()
