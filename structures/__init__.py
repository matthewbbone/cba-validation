from __future__ import annotations

from typing import Literal, TypeAlias

from .common import BaseProvisionExtraction
from .complex import WageBaseRateExtraction
from .complex import GrievanceProcedureExtraction
from .complex import ArbitrationExtraction
from .complex import LeaveHolidaysExtraction
from .complex import PremiumOvertimeExtraction
from .complex import UnionAccessBusinessExtraction
from .binary import DisciplineJustCauseExtraction
from .complex import WageIncreasesColaExtraction
from .quantitative import HealthMedicalActiveContributionExtraction
from .complex import LeaveVacationExtraction
from .complex import SafetyPpeUnsafeWorkExtraction
from .complex import PremiumCallInReportingExtraction
from .complex import RetirementPensionExtraction
from .quantitative import PremiumShiftExtraction
from .complex import JobSecurityLayoffOrderExtraction
from .complex import TimeRegularScheduleExtraction
from .complex import UnionSecurityDuesCheckoffExtraction
from .complex import WageProgressionExtraction
from .complex import LeaveSickExtraction
from .quantitative import LeavePersonalMiscExtraction
from .complex import JobSecurityRecallExtraction
from .complex import TimeRestMealPeriodsExtraction
from .complex import PremiumResponsibilitySpecialtyExtraction
from .quantitative import RetirementSavingsAnnuityExtraction
from .complex import RecognitionCoverageScopeExtraction
from .complex import HealthDentalExtraction
from .complex import LeaveParentalFamilyExtraction
from .complex import TrainingTuitionCertificationExtraction
from .complex import JobSecuritySeveranceExtraction
from .complex import HealthMedicalActiveExtraction
from .complex import HealthLifeAdDExtraction
from .complex import DisciplineProgressiveExtraction
from .complex import HealthMedicalActivePlanDesignExtraction
from .quantitative import PremiumStandbyOnCallExtraction
from .quantitative import UniformClothingAllowanceExtraction
from .binary import LaborManagementCommitteeExtraction
from .complex import HiringHallDispatchExtraction
from .complex import DisciplineInvestigationAppealExtraction
from .complex import HealthDisabilityIncomeExtraction
from .complex import JobSecurityBenefitContinuationExtraction
from .complex import HealthRetireeExtraction
from .complex import SubcontractingWorkPreservationExtraction
from .complex import WorkloadClassSizeStaffingExtraction
from .complex import SenioritySystemExtraction
from .quantitative import TimeScheduleNoticeChangeExtraction
from .complex import PremiumZoneSubsistenceExtraction
from .complex import HealthVisionExtraction
from .quantitative import LegalServicesFundExtraction
from .complex import JobPostingBiddingTransferExtraction
from .complex import SafetyAssaultViolenceExtraction
from .complex import RetirementIncentiveExtraction
from .complex import JobSecurityLayoffRecallExtraction
from .complex import JobSecuritySubIncomeBridgeExtraction
from .quantitative import ChildDependentCareExtraction
from .quantitative import HealthEmployerContributionExtraction
from .complex import HealthActiveExtraction
from .quantitative import JobSecurityLayoffExtraction
from .complex import WageGeneralIncreaseExtraction
from .complex import TimeNoCancellationSecurityExtraction
from .complex import JobSecuritySeniorityExtraction
from .quantitative import TransitCommuterBenefitExtraction
from .complex import WageApprenticeExtraction
from .complex import WageScheduledIncreaseExtraction
from .complex import PremiumSundayHolidayExtraction
from .complex import LightDutyAccommodationExtraction
from .binary import HealthLifeInsuranceExtraction
from .quantitative import PremiumForemanExtraction
from .quantitative import HealthActiveContributionExtraction
from .quantitative import LeaveBereavementExtraction
from .binary import JobSecuritySubcontractingExtraction
from .complex import JobSecurityRifLayoffExtraction
from .complex import HealthExternalFundExtraction
from .quantitative import PremiumHazardExtraction
from .complex import HealthActivePlanDesignExtraction
from .binary import UnionSecurityExtraction
from .complex import WageIncreaseExtraction
from .complex import WageLongevityExtraction
from .complex import UnionDuesCheckoffExtraction
from .complex import HealthPlanDesignExtraction
from .complex import WageMeritStepExtraction
from .complex import DisciplineProbationExtraction
from .complex import SafetyDrugTestingExtraction
from .binary import JobSecurityBumpingExtraction
from .quantitative import HealthInsuranceBuyoutExtraction
from .binary import JobSecurityNoContractingOutExtraction
from .quantitative import WageSavingsExtraction
from .quantitative import WageVacationSuppExtraction
from .quantitative import WageAccrualVacationExtraction
from .quantitative import PremiumLeadmanExtraction
from .quantitative import LeavePersonalExtraction
from .quantitative import HealthWelfareFundExtraction
from .quantitative import LeaveSubsistenceExtraction
from .quantitative import HealthDisabilityExtraction
from .complex import PremiumGroupLeaderExtraction
from .quantitative import LeaveJuryDutyExtraction
from .complex import WageIncentiveExtraction
from .binary import PremiumStandbyExtraction
from .complex import HealthPrescriptionDrugExtraction
from .binary import HealthBenefitsExtraction


ProvisionFormat: TypeAlias = Literal["binary", "quantitative", "complex"]
ProvisionExtractionType: TypeAlias = type[BaseProvisionExtraction]

PROVISION_EXTRACTION_REGISTRY: dict[str, ProvisionExtractionType] = {
    'C_WAGE_BASE_RATE': WageBaseRateExtraction,
    'C_GRIEVANCE_PROCEDURE': GrievanceProcedureExtraction,
    'C_ARBITRATION': ArbitrationExtraction,
    'C_LEAVE_HOLIDAYS': LeaveHolidaysExtraction,
    'C_PREMIUM_OVERTIME': PremiumOvertimeExtraction,
    'C_UNION_ACCESS_BUSINESS': UnionAccessBusinessExtraction,
    'C_DISCIPLINE_JUST_CAUSE': DisciplineJustCauseExtraction,
    'C_WAGE_INCREASES_COLA': WageIncreasesColaExtraction,
    'C_HEALTH_MEDICAL_ACTIVE_CONTRIBUTION': HealthMedicalActiveContributionExtraction,
    'C_LEAVE_VACATION': LeaveVacationExtraction,
    'C_SAFETY_PPE_UNSAFE_WORK': SafetyPpeUnsafeWorkExtraction,
    'C_PREMIUM_CALL_IN_REPORTING': PremiumCallInReportingExtraction,
    'C_RETIREMENT_PENSION': RetirementPensionExtraction,
    'C_PREMIUM_SHIFT': PremiumShiftExtraction,
    'C_JOB_SECURITY_LAYOFF_ORDER': JobSecurityLayoffOrderExtraction,
    'C_TIME_REGULAR_SCHEDULE': TimeRegularScheduleExtraction,
    'C_UNION_SECURITY_DUES_CHECKOFF': UnionSecurityDuesCheckoffExtraction,
    'C_WAGE_PROGRESSION': WageProgressionExtraction,
    'C_LEAVE_SICK': LeaveSickExtraction,
    'C_LEAVE_PERSONAL_MISC': LeavePersonalMiscExtraction,
    'C_JOB_SECURITY_RECALL': JobSecurityRecallExtraction,
    'C_TIME_REST_MEAL_PERIODS': TimeRestMealPeriodsExtraction,
    'C_PREMIUM_RESPONSIBILITY_SPECIALTY': PremiumResponsibilitySpecialtyExtraction,
    'C_RETIREMENT_SAVINGS_ANNUITY': RetirementSavingsAnnuityExtraction,
    'C_RECOGNITION_COVERAGE_SCOPE': RecognitionCoverageScopeExtraction,
    'C_HEALTH_DENTAL': HealthDentalExtraction,
    'C_LEAVE_PARENTAL_FAMILY': LeaveParentalFamilyExtraction,
    'C_TRAINING_TUITION_CERTIFICATION': TrainingTuitionCertificationExtraction,
    'C_JOB_SECURITY_SEVERANCE': JobSecuritySeveranceExtraction,
    'C_HEALTH_MEDICAL_ACTIVE': HealthMedicalActiveExtraction,
    'C_HEALTH_LIFE_AD_D': HealthLifeAdDExtraction,
    'C_DISCIPLINE_PROGRESSIVE': DisciplineProgressiveExtraction,
    'C_HEALTH_MEDICAL_ACTIVE_PLAN_DESIGN': HealthMedicalActivePlanDesignExtraction,
    'C_PREMIUM_STANDBY_ON_CALL': PremiumStandbyOnCallExtraction,
    'C_UNIFORM_CLOTHING_ALLOWANCE': UniformClothingAllowanceExtraction,
    'C_LABOR_MANAGEMENT_COMMITTEE': LaborManagementCommitteeExtraction,
    'C_HIRING_HALL_DISPATCH': HiringHallDispatchExtraction,
    'C_DISCIPLINE_INVESTIGATION_APPEAL': DisciplineInvestigationAppealExtraction,
    'C_HEALTH_DISABILITY_INCOME': HealthDisabilityIncomeExtraction,
    'C_JOB_SECURITY_BENEFIT_CONTINUATION': JobSecurityBenefitContinuationExtraction,
    'C_HEALTH_RETIREE': HealthRetireeExtraction,
    'C_SUBCONTRACTING_WORK_PRESERVATION': SubcontractingWorkPreservationExtraction,
    'C_WORKLOAD_CLASS_SIZE_STAFFING': WorkloadClassSizeStaffingExtraction,
    'C_SENIORITY_SYSTEM': SenioritySystemExtraction,
    'C_TIME_SCHEDULE_NOTICE_CHANGE': TimeScheduleNoticeChangeExtraction,
    'C_PREMIUM_ZONE_SUBSISTENCE': PremiumZoneSubsistenceExtraction,
    'C_HEALTH_VISION': HealthVisionExtraction,
    'C_LEGAL_SERVICES_FUND': LegalServicesFundExtraction,
    'C_JOB_POSTING_BIDDING_TRANSFER': JobPostingBiddingTransferExtraction,
    'C_SAFETY_ASSAULT_VIOLENCE': SafetyAssaultViolenceExtraction,
    'C_RETIREMENT_INCENTIVE': RetirementIncentiveExtraction,
    'C_JOB_SECURITY_LAYOFF_RECALL': JobSecurityLayoffRecallExtraction,
    'C_JOB_SECURITY_SUB_INCOME_BRIDGE': JobSecuritySubIncomeBridgeExtraction,
    'C_CHILD_DEPENDENT_CARE': ChildDependentCareExtraction,
    'C_HEALTH_EMPLOYER_CONTRIBUTION': HealthEmployerContributionExtraction,
    'C_HEALTH_ACTIVE': HealthActiveExtraction,
    'C_JOB_SECURITY_LAYOFF': JobSecurityLayoffExtraction,
    'C_WAGE_GENERAL_INCREASE': WageGeneralIncreaseExtraction,
    'C_TIME_NO_CANCELLATION_SECURITY': TimeNoCancellationSecurityExtraction,
    'C_JOB_SECURITY_SENIORITY': JobSecuritySeniorityExtraction,
    'C_TRANSIT_COMMUTER_BENEFIT': TransitCommuterBenefitExtraction,
    'C_WAGE_APPRENTICE': WageApprenticeExtraction,
    'C_WAGE_SCHEDULED_INCREASE': WageScheduledIncreaseExtraction,
    'C_PREMIUM_SUNDAY_HOLIDAY': PremiumSundayHolidayExtraction,
    'C_LIGHT_DUTY_ACCOMMODATION': LightDutyAccommodationExtraction,
    'C_HEALTH_LIFE_INSURANCE': HealthLifeInsuranceExtraction,
    'C_PREMIUM_FOREMAN': PremiumForemanExtraction,
    'C_HEALTH_ACTIVE_CONTRIBUTION': HealthActiveContributionExtraction,
    'C_LEAVE_BEREAVEMENT': LeaveBereavementExtraction,
    'C_JOB_SECURITY_SUBCONTRACTING': JobSecuritySubcontractingExtraction,
    'C_JOB_SECURITY_RIF_LAYOFF': JobSecurityRifLayoffExtraction,
    'C_HEALTH_EXTERNAL_FUND': HealthExternalFundExtraction,
    'C_PREMIUM_HAZARD': PremiumHazardExtraction,
    'C_HEALTH_ACTIVE_PLAN_DESIGN': HealthActivePlanDesignExtraction,
    'C_UNION_SECURITY': UnionSecurityExtraction,
    'C_WAGE_INCREASE': WageIncreaseExtraction,
    'C_WAGE_LONGEVITY': WageLongevityExtraction,
    'C_UNION_DUES_CHECKOFF': UnionDuesCheckoffExtraction,
    'C_HEALTH_PLAN_DESIGN': HealthPlanDesignExtraction,
    'C_WAGE_MERIT_STEP': WageMeritStepExtraction,
    'C_DISCIPLINE_PROBATION': DisciplineProbationExtraction,
    'C_SAFETY_DRUG_TESTING': SafetyDrugTestingExtraction,
    'C_JOB_SECURITY_BUMPING': JobSecurityBumpingExtraction,
    'C_HEALTH_INSURANCE_BUYOUT': HealthInsuranceBuyoutExtraction,
    'C_JOB_SECURITY_NO_CONTRACTING_OUT': JobSecurityNoContractingOutExtraction,
    'C_WAGE_SAVINGS': WageSavingsExtraction,
    'C_WAGE_VACATION_SUPP': WageVacationSuppExtraction,
    'C_WAGE_ACCRUAL_VACATION': WageAccrualVacationExtraction,
    'C_PREMIUM_LEADMAN': PremiumLeadmanExtraction,
    'C_LEAVE_PERSONAL': LeavePersonalExtraction,
    'C_HEALTH_WELFARE_FUND': HealthWelfareFundExtraction,
    'C_LEAVE_SUBSISTENCE': LeaveSubsistenceExtraction,
    'C_HEALTH_DISABILITY': HealthDisabilityExtraction,
    'C_PREMIUM_GROUP_LEADER': PremiumGroupLeaderExtraction,
    'C_LEAVE_JURY_DUTY': LeaveJuryDutyExtraction,
    'C_WAGE_INCENTIVE': WageIncentiveExtraction,
    'C_PREMIUM_STANDBY': PremiumStandbyExtraction,
    'C_HEALTH_PRESCRIPTION_DRUG': HealthPrescriptionDrugExtraction,
    'C_HEALTH_BENEFITS': HealthBenefitsExtraction,
}

PROVISION_FORMAT_REGISTRY: dict[str, ProvisionFormat] = {
    'C_WAGE_BASE_RATE': 'complex',
    'C_GRIEVANCE_PROCEDURE': 'complex',
    'C_ARBITRATION': 'complex',
    'C_LEAVE_HOLIDAYS': 'complex',
    'C_PREMIUM_OVERTIME': 'complex',
    'C_UNION_ACCESS_BUSINESS': 'complex',
    'C_DISCIPLINE_JUST_CAUSE': 'binary',
    'C_WAGE_INCREASES_COLA': 'complex',
    'C_HEALTH_MEDICAL_ACTIVE_CONTRIBUTION': 'quantitative',
    'C_LEAVE_VACATION': 'complex',
    'C_SAFETY_PPE_UNSAFE_WORK': 'complex',
    'C_PREMIUM_CALL_IN_REPORTING': 'complex',
    'C_RETIREMENT_PENSION': 'complex',
    'C_PREMIUM_SHIFT': 'quantitative',
    'C_JOB_SECURITY_LAYOFF_ORDER': 'complex',
    'C_TIME_REGULAR_SCHEDULE': 'complex',
    'C_UNION_SECURITY_DUES_CHECKOFF': 'complex',
    'C_WAGE_PROGRESSION': 'complex',
    'C_LEAVE_SICK': 'complex',
    'C_LEAVE_PERSONAL_MISC': 'quantitative',
    'C_JOB_SECURITY_RECALL': 'complex',
    'C_TIME_REST_MEAL_PERIODS': 'complex',
    'C_PREMIUM_RESPONSIBILITY_SPECIALTY': 'complex',
    'C_RETIREMENT_SAVINGS_ANNUITY': 'quantitative',
    'C_RECOGNITION_COVERAGE_SCOPE': 'complex',
    'C_HEALTH_DENTAL': 'complex',
    'C_LEAVE_PARENTAL_FAMILY': 'complex',
    'C_TRAINING_TUITION_CERTIFICATION': 'complex',
    'C_JOB_SECURITY_SEVERANCE': 'complex',
    'C_HEALTH_MEDICAL_ACTIVE': 'complex',
    'C_HEALTH_LIFE_AD_D': 'complex',
    'C_DISCIPLINE_PROGRESSIVE': 'complex',
    'C_HEALTH_MEDICAL_ACTIVE_PLAN_DESIGN': 'complex',
    'C_PREMIUM_STANDBY_ON_CALL': 'quantitative',
    'C_UNIFORM_CLOTHING_ALLOWANCE': 'quantitative',
    'C_LABOR_MANAGEMENT_COMMITTEE': 'binary',
    'C_HIRING_HALL_DISPATCH': 'complex',
    'C_DISCIPLINE_INVESTIGATION_APPEAL': 'complex',
    'C_HEALTH_DISABILITY_INCOME': 'complex',
    'C_JOB_SECURITY_BENEFIT_CONTINUATION': 'complex',
    'C_HEALTH_RETIREE': 'complex',
    'C_SUBCONTRACTING_WORK_PRESERVATION': 'complex',
    'C_WORKLOAD_CLASS_SIZE_STAFFING': 'complex',
    'C_SENIORITY_SYSTEM': 'complex',
    'C_TIME_SCHEDULE_NOTICE_CHANGE': 'quantitative',
    'C_PREMIUM_ZONE_SUBSISTENCE': 'complex',
    'C_HEALTH_VISION': 'complex',
    'C_LEGAL_SERVICES_FUND': 'quantitative',
    'C_JOB_POSTING_BIDDING_TRANSFER': 'complex',
    'C_SAFETY_ASSAULT_VIOLENCE': 'complex',
    'C_RETIREMENT_INCENTIVE': 'complex',
    'C_JOB_SECURITY_LAYOFF_RECALL': 'complex',
    'C_JOB_SECURITY_SUB_INCOME_BRIDGE': 'complex',
    'C_CHILD_DEPENDENT_CARE': 'quantitative',
    'C_HEALTH_EMPLOYER_CONTRIBUTION': 'quantitative',
    'C_HEALTH_ACTIVE': 'complex',
    'C_JOB_SECURITY_LAYOFF': 'quantitative',
    'C_WAGE_GENERAL_INCREASE': 'complex',
    'C_TIME_NO_CANCELLATION_SECURITY': 'complex',
    'C_JOB_SECURITY_SENIORITY': 'complex',
    'C_TRANSIT_COMMUTER_BENEFIT': 'quantitative',
    'C_WAGE_APPRENTICE': 'complex',
    'C_WAGE_SCHEDULED_INCREASE': 'complex',
    'C_PREMIUM_SUNDAY_HOLIDAY': 'complex',
    'C_LIGHT_DUTY_ACCOMMODATION': 'complex',
    'C_HEALTH_LIFE_INSURANCE': 'binary',
    'C_PREMIUM_FOREMAN': 'quantitative',
    'C_HEALTH_ACTIVE_CONTRIBUTION': 'quantitative',
    'C_LEAVE_BEREAVEMENT': 'quantitative',
    'C_JOB_SECURITY_SUBCONTRACTING': 'binary',
    'C_JOB_SECURITY_RIF_LAYOFF': 'complex',
    'C_HEALTH_EXTERNAL_FUND': 'complex',
    'C_PREMIUM_HAZARD': 'quantitative',
    'C_HEALTH_ACTIVE_PLAN_DESIGN': 'complex',
    'C_UNION_SECURITY': 'binary',
    'C_WAGE_INCREASE': 'complex',
    'C_WAGE_LONGEVITY': 'complex',
    'C_UNION_DUES_CHECKOFF': 'complex',
    'C_HEALTH_PLAN_DESIGN': 'complex',
    'C_WAGE_MERIT_STEP': 'complex',
    'C_DISCIPLINE_PROBATION': 'complex',
    'C_SAFETY_DRUG_TESTING': 'complex',
    'C_JOB_SECURITY_BUMPING': 'binary',
    'C_HEALTH_INSURANCE_BUYOUT': 'quantitative',
    'C_JOB_SECURITY_NO_CONTRACTING_OUT': 'binary',
    'C_WAGE_SAVINGS': 'quantitative',
    'C_WAGE_VACATION_SUPP': 'quantitative',
    'C_WAGE_ACCRUAL_VACATION': 'quantitative',
    'C_PREMIUM_LEADMAN': 'quantitative',
    'C_LEAVE_PERSONAL': 'quantitative',
    'C_HEALTH_WELFARE_FUND': 'quantitative',
    'C_LEAVE_SUBSISTENCE': 'quantitative',
    'C_HEALTH_DISABILITY': 'quantitative',
    'C_PREMIUM_GROUP_LEADER': 'complex',
    'C_LEAVE_JURY_DUTY': 'quantitative',
    'C_WAGE_INCENTIVE': 'complex',
    'C_PREMIUM_STANDBY': 'binary',
    'C_HEALTH_PRESCRIPTION_DRUG': 'complex',
    'C_HEALTH_BENEFITS': 'binary',
}

__all__ = [
    "BaseProvisionExtraction",
    "PROVISION_EXTRACTION_REGISTRY",
    "PROVISION_FORMAT_REGISTRY",
    "ProvisionExtractionType",
    "ProvisionFormat",
    "WageBaseRateExtraction",
    "GrievanceProcedureExtraction",
    "ArbitrationExtraction",
    "LeaveHolidaysExtraction",
    "PremiumOvertimeExtraction",
    "UnionAccessBusinessExtraction",
    "DisciplineJustCauseExtraction",
    "WageIncreasesColaExtraction",
    "HealthMedicalActiveContributionExtraction",
    "LeaveVacationExtraction",
    "SafetyPpeUnsafeWorkExtraction",
    "PremiumCallInReportingExtraction",
    "RetirementPensionExtraction",
    "PremiumShiftExtraction",
    "JobSecurityLayoffOrderExtraction",
    "TimeRegularScheduleExtraction",
    "UnionSecurityDuesCheckoffExtraction",
    "WageProgressionExtraction",
    "LeaveSickExtraction",
    "LeavePersonalMiscExtraction",
    "JobSecurityRecallExtraction",
    "TimeRestMealPeriodsExtraction",
    "PremiumResponsibilitySpecialtyExtraction",
    "RetirementSavingsAnnuityExtraction",
    "RecognitionCoverageScopeExtraction",
    "HealthDentalExtraction",
    "LeaveParentalFamilyExtraction",
    "TrainingTuitionCertificationExtraction",
    "JobSecuritySeveranceExtraction",
    "HealthMedicalActiveExtraction",
    "HealthLifeAdDExtraction",
    "DisciplineProgressiveExtraction",
    "HealthMedicalActivePlanDesignExtraction",
    "PremiumStandbyOnCallExtraction",
    "UniformClothingAllowanceExtraction",
    "LaborManagementCommitteeExtraction",
    "HiringHallDispatchExtraction",
    "DisciplineInvestigationAppealExtraction",
    "HealthDisabilityIncomeExtraction",
    "JobSecurityBenefitContinuationExtraction",
    "HealthRetireeExtraction",
    "SubcontractingWorkPreservationExtraction",
    "WorkloadClassSizeStaffingExtraction",
    "SenioritySystemExtraction",
    "TimeScheduleNoticeChangeExtraction",
    "PremiumZoneSubsistenceExtraction",
    "HealthVisionExtraction",
    "LegalServicesFundExtraction",
    "JobPostingBiddingTransferExtraction",
    "SafetyAssaultViolenceExtraction",
    "RetirementIncentiveExtraction",
    "JobSecurityLayoffRecallExtraction",
    "JobSecuritySubIncomeBridgeExtraction",
    "ChildDependentCareExtraction",
    "HealthEmployerContributionExtraction",
    "HealthActiveExtraction",
    "JobSecurityLayoffExtraction",
    "WageGeneralIncreaseExtraction",
    "TimeNoCancellationSecurityExtraction",
    "JobSecuritySeniorityExtraction",
    "TransitCommuterBenefitExtraction",
    "WageApprenticeExtraction",
    "WageScheduledIncreaseExtraction",
    "PremiumSundayHolidayExtraction",
    "LightDutyAccommodationExtraction",
    "HealthLifeInsuranceExtraction",
    "PremiumForemanExtraction",
    "HealthActiveContributionExtraction",
    "LeaveBereavementExtraction",
    "JobSecuritySubcontractingExtraction",
    "JobSecurityRifLayoffExtraction",
    "HealthExternalFundExtraction",
    "PremiumHazardExtraction",
    "HealthActivePlanDesignExtraction",
    "UnionSecurityExtraction",
    "WageIncreaseExtraction",
    "WageLongevityExtraction",
    "UnionDuesCheckoffExtraction",
    "HealthPlanDesignExtraction",
    "WageMeritStepExtraction",
    "DisciplineProbationExtraction",
    "SafetyDrugTestingExtraction",
    "JobSecurityBumpingExtraction",
    "HealthInsuranceBuyoutExtraction",
    "JobSecurityNoContractingOutExtraction",
    "WageSavingsExtraction",
    "WageVacationSuppExtraction",
    "WageAccrualVacationExtraction",
    "PremiumLeadmanExtraction",
    "LeavePersonalExtraction",
    "HealthWelfareFundExtraction",
    "LeaveSubsistenceExtraction",
    "HealthDisabilityExtraction",
    "PremiumGroupLeaderExtraction",
    "LeaveJuryDutyExtraction",
    "WageIncentiveExtraction",
    "PremiumStandbyExtraction",
    "HealthPrescriptionDrugExtraction",
    "HealthBenefitsExtraction",
]
