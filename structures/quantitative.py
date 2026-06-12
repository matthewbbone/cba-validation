from __future__ import annotations

from typing import ClassVar, Literal

from .templates import QuantitativeProvisionExtraction


# Provisions whose comparison target is a single normalized value; value is None when absent.


class HealthMedicalActiveContributionExtraction(QuantitativeProvisionExtraction):
    """H&W Fund contribution."""
    concept_id: ClassVar[Literal['C_HEALTH_MEDICAL_ACTIVE_CONTRIBUTION']] = 'C_HEALTH_MEDICAL_ACTIVE_CONTRIBUTION'
    category: ClassVar[Literal['Healthcare']] = 'Healthcare'


class PremiumShiftExtraction(QuantitativeProvisionExtraction):
    """Shift differentials and night/weekend premiums."""
    concept_id: ClassVar[Literal['C_PREMIUM_SHIFT']] = 'C_PREMIUM_SHIFT'
    category: ClassVar[Literal['Compensation']] = 'Compensation'


class LeavePersonalMiscExtraction(QuantitativeProvisionExtraction):
    """Bereavement/compassionate leave."""
    concept_id: ClassVar[Literal['C_LEAVE_PERSONAL_MISC']] = 'C_LEAVE_PERSONAL_MISC'
    category: ClassVar[Literal['Leave']] = 'Leave'


class RetirementSavingsAnnuityExtraction(QuantitativeProvisionExtraction):
    """Annuity Fund (CT Carpenters) contributions."""
    concept_id: ClassVar[Literal['C_RETIREMENT_SAVINGS_ANNUITY']] = 'C_RETIREMENT_SAVINGS_ANNUITY'
    category: ClassVar[Literal['Ancillary']] = 'Ancillary'


class PremiumStandbyOnCallExtraction(QuantitativeProvisionExtraction):
    """Standby pay."""
    concept_id: ClassVar[Literal['C_PREMIUM_STANDBY_ON_CALL']] = 'C_PREMIUM_STANDBY_ON_CALL'
    category: ClassVar[Literal['Compensation']] = 'Compensation'


class UniformClothingAllowanceExtraction(QuantitativeProvisionExtraction):
    """Safety shoe program."""
    concept_id: ClassVar[Literal['C_UNIFORM_CLOTHING_ALLOWANCE']] = 'C_UNIFORM_CLOTHING_ALLOWANCE'
    category: ClassVar[Literal['Compensation']] = 'Compensation'


class TimeScheduleNoticeChangeExtraction(QuantitativeProvisionExtraction):
    """Schedule changes."""
    concept_id: ClassVar[Literal['C_TIME_SCHEDULE_NOTICE_CHANGE']] = 'C_TIME_SCHEDULE_NOTICE_CHANGE'
    category: ClassVar[Literal['Scheduling']] = 'Scheduling'


class LegalServicesFundExtraction(QuantitativeProvisionExtraction):
    """Group legal services fund."""
    concept_id: ClassVar[Literal['C_LEGAL_SERVICES_FUND']] = 'C_LEGAL_SERVICES_FUND'
    category: ClassVar[Literal['Ancillary']] = 'Ancillary'


class ChildDependentCareExtraction(QuantitativeProvisionExtraction):
    """Fellowships for Day Care."""
    concept_id: ClassVar[Literal['C_CHILD_DEPENDENT_CARE']] = 'C_CHILD_DEPENDENT_CARE'
    category: ClassVar[Literal['Ancillary']] = 'Ancillary'


class HealthEmployerContributionExtraction(QuantitativeProvisionExtraction):
    """IAFF VEBA health benefit fund."""
    concept_id: ClassVar[Literal['C_HEALTH_EMPLOYER_CONTRIBUTION']] = 'C_HEALTH_EMPLOYER_CONTRIBUTION'
    category: ClassVar[Literal['Healthcare']] = 'Healthcare'


class JobSecurityLayoffExtraction(QuantitativeProvisionExtraction):
    """Dismissal pay."""
    concept_id: ClassVar[Literal['C_JOB_SECURITY_LAYOFF']] = 'C_JOB_SECURITY_LAYOFF'
    category: ClassVar[Literal['Security']] = 'Security'


class TransitCommuterBenefitExtraction(QuantitativeProvisionExtraction):
    """Transit subsidy per SMC 4.20.370."""
    concept_id: ClassVar[Literal['C_TRANSIT_COMMUTER_BENEFIT']] = 'C_TRANSIT_COMMUTER_BENEFIT'
    category: ClassVar[Literal['Ancillary']] = 'Ancillary'


class PremiumForemanExtraction(QuantitativeProvisionExtraction):
    """Foreman and General Foreman premium."""
    concept_id: ClassVar[Literal['C_PREMIUM_FOREMAN']] = 'C_PREMIUM_FOREMAN'
    category: ClassVar[Literal['Compensation']] = 'Compensation'


class HealthActiveContributionExtraction(QuantitativeProvisionExtraction):
    """Active health."""
    concept_id: ClassVar[Literal['C_HEALTH_ACTIVE_CONTRIBUTION']] = 'C_HEALTH_ACTIVE_CONTRIBUTION'
    category: ClassVar[Literal['Healthcare']] = 'Healthcare'


class LeaveBereavementExtraction(QuantitativeProvisionExtraction):
    """Bereavement leave."""
    concept_id: ClassVar[Literal['C_LEAVE_BEREAVEMENT']] = 'C_LEAVE_BEREAVEMENT'
    category: ClassVar[Literal['Leave']] = 'Leave'


class PremiumHazardExtraction(QuantitativeProvisionExtraction):
    """Hazardous work differential."""
    concept_id: ClassVar[Literal['C_PREMIUM_HAZARD']] = 'C_PREMIUM_HAZARD'
    category: ClassVar[Literal['Compensation']] = 'Compensation'


class HealthInsuranceBuyoutExtraction(QuantitativeProvisionExtraction):
    """Health insurance opt-out payment $1,200/year."""
    concept_id: ClassVar[Literal['C_HEALTH_INSURANCE_BUYOUT']] = 'C_HEALTH_INSURANCE_BUYOUT'
    category: ClassVar[Literal['Healthcare']] = 'Healthcare'


class WageSavingsExtraction(QuantitativeProvisionExtraction):
    """Savings/deferred compensation contribution."""
    concept_id: ClassVar[Literal['C_WAGE_SAVINGS']] = 'C_WAGE_SAVINGS'
    category: ClassVar[Literal['Compensation']] = 'Compensation'


class WageVacationSuppExtraction(QuantitativeProvisionExtraction):
    """Vacation/Supplemental dues contribution $2.95/hr."""
    concept_id: ClassVar[Literal['C_WAGE_VACATION_SUPP']] = 'C_WAGE_VACATION_SUPP'
    category: ClassVar[Literal['Compensation']] = 'Compensation'


class WageAccrualVacationExtraction(QuantitativeProvisionExtraction):
    """Vacation/holiday pay accrual ($0.50/hr)."""
    concept_id: ClassVar[Literal['C_WAGE_ACCRUAL_VACATION']] = 'C_WAGE_ACCRUAL_VACATION'
    category: ClassVar[Literal['Compensation']] = 'Compensation'


class PremiumLeadmanExtraction(QuantitativeProvisionExtraction):
    """Leadman premium."""
    concept_id: ClassVar[Literal['C_PREMIUM_LEADMAN']] = 'C_PREMIUM_LEADMAN'
    category: ClassVar[Literal['Compensation']] = 'Compensation'


class LeavePersonalExtraction(QuantitativeProvisionExtraction):
    """Perfect Attendance Days (paid personal time)."""
    concept_id: ClassVar[Literal['C_LEAVE_PERSONAL']] = 'C_LEAVE_PERSONAL'
    category: ClassVar[Literal['Leave']] = 'Leave'


class HealthWelfareFundExtraction(QuantitativeProvisionExtraction):
    """Welfare fund employer contributions."""
    concept_id: ClassVar[Literal['C_HEALTH_WELFARE_FUND']] = 'C_HEALTH_WELFARE_FUND'
    category: ClassVar[Literal['Healthcare']] = 'Healthcare'


class LeaveSubsistenceExtraction(QuantitativeProvisionExtraction):
    """Subsistence."""
    concept_id: ClassVar[Literal['C_LEAVE_SUBSISTENCE']] = 'C_LEAVE_SUBSISTENCE'
    category: ClassVar[Literal['Leave']] = 'Leave'


class HealthDisabilityExtraction(QuantitativeProvisionExtraction):
    """Short-term disability $400/week max 26 weeks."""
    concept_id: ClassVar[Literal['C_HEALTH_DISABILITY']] = 'C_HEALTH_DISABILITY'
    category: ClassVar[Literal['Healthcare']] = 'Healthcare'


class LeaveJuryDutyExtraction(QuantitativeProvisionExtraction):
    """Jury duty."""
    concept_id: ClassVar[Literal['C_LEAVE_JURY_DUTY']] = 'C_LEAVE_JURY_DUTY'
    category: ClassVar[Literal['Leave']] = 'Leave'
