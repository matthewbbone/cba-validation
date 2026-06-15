from __future__ import annotations

from typing import ClassVar, Literal

from pydantic import Field

from .templates import (
    BooleanFlagModel,
    AncillaryBenefitExtraction,
    HealthBenefitExtraction,
    JobSecurityExtraction,
    LeaveEntitlementExtraction,
    PremiumPayExtraction,
    ProcedureOrStandardExtraction,
    RecognitionExtraction,
    SafetyExtraction,
    SchedulingExtraction,
    WageAdjustmentExtraction,
    WageScaleExtraction,
)


# Provisions needing structured detail beyond one existence flag or one scalar value.


class WageBaseRateFlags(BooleanFlagModel):
    has_base_rate: bool | None = None
    has_rate_table: bool | None = None
    has_classification_rates: bool | None = None
    has_step_rates: bool | None = None
    has_salary_rates: bool | None = None
    has_hourly_rates: bool | None = None


class WageBaseRateExtraction(WageScaleExtraction):
    """Base wage or salary rate."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_WAGE_BASE_RATE']] = 'C_WAGE_BASE_RATE'
    category: ClassVar[Literal['Compensation']] = 'Compensation'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('occupation_names', 'classification_names', 'step_names', 'wage_schedule_names', 'geographic_areas', 'effective_dates')
    occupation_names: list[str] = Field(default_factory=list)
    classification_names: list[str] = Field(default_factory=list)
    step_names: list[str] = Field(default_factory=list)
    wage_schedule_names: list[str] = Field(default_factory=list)
    geographic_areas: list[str] = Field(default_factory=list)
    effective_dates: list[str] = Field(default_factory=list)
    flags: WageBaseRateFlags | None = None


class GrievanceProcedureFlags(BooleanFlagModel):
    has_grievance_steps: bool | None = None
    has_deadlines: bool | None = None
    has_union_representation: bool | None = None
    has_written_grievance: bool | None = None
    has_management_response: bool | None = None


class GrievanceProcedureExtraction(ProcedureOrStandardExtraction):
    """Grievance steps, timelines, representation, and scope."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_GRIEVANCE_PROCEDURE']] = 'C_GRIEVANCE_PROCEDURE'
    category: ClassVar[Literal['Disputes']] = 'Disputes'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('grievance_step_names', 'eligible_filers', 'excluded_claim_types', 'deadline_terms')
    grievance_step_names: list[str] = Field(default_factory=list)
    eligible_filers: list[str] = Field(default_factory=list)
    excluded_claim_types: list[str] = Field(default_factory=list)
    deadline_terms: list[str] = Field(default_factory=list)
    flags: GrievanceProcedureFlags | None = None


class ArbitrationFlags(BooleanFlagModel):
    has_arbitration: bool | None = None
    final_and_binding: bool | None = None
    has_neutral_arbitrator: bool | None = None
    has_shared_costs: bool | None = None
    limits_arbitrator_authority: bool | None = None


class ArbitrationExtraction(ProcedureOrStandardExtraction):
    """Arbitration access, selection, authority, costs, and finality."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_ARBITRATION']] = 'C_ARBITRATION'
    category: ClassVar[Literal['Disputes']] = 'Disputes'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('arbitrator_selection_terms', 'excluded_claim_types', 'forum_names', 'remedy_limit_terms')
    arbitrator_selection_terms: list[str] = Field(default_factory=list)
    excluded_claim_types: list[str] = Field(default_factory=list)
    forum_names: list[str] = Field(default_factory=list)
    remedy_limit_terms: list[str] = Field(default_factory=list)
    flags: ArbitrationFlags | None = None


class LeaveHolidaysFlags(BooleanFlagModel):
    has_paid_holidays: bool | None = None
    has_holiday_premium_pay: bool | None = None
    has_floating_holidays: bool | None = None
    has_observed_holidays: bool | None = None


class LeaveHolidaysExtraction(LeaveEntitlementExtraction):
    """Holidays and holiday pay."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_LEAVE_HOLIDAYS']] = 'C_LEAVE_HOLIDAYS'
    category: ClassVar[Literal['Leave']] = 'Leave'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('holiday_names', 'observed_rule_terms', 'eligibility_terms')
    holiday_names: list[str] = Field(default_factory=list)
    observed_rule_terms: list[str] = Field(default_factory=list)
    eligibility_terms: list[str] = Field(default_factory=list)
    flags: LeaveHolidaysFlags | None = None


class PremiumOvertimeFlags(BooleanFlagModel):
    has_overtime_threshold: bool | None = None
    has_daily_overtime: bool | None = None
    has_weekly_overtime: bool | None = None
    has_premium_multiplier: bool | None = None
    has_double_time: bool | None = None


class PremiumOvertimeExtraction(PremiumPayExtraction):
    """Overtime eligibility thresholds and multipliers."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_PREMIUM_OVERTIME']] = 'C_PREMIUM_OVERTIME'
    category: ClassVar[Literal['Compensation']] = 'Compensation'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('trigger_terms', 'covered_employee_groups', 'excluded_employee_groups', 'premium_names')
    trigger_terms: list[str] = Field(default_factory=list)
    covered_employee_groups: list[str] = Field(default_factory=list)
    excluded_employee_groups: list[str] = Field(default_factory=list)
    premium_names: list[str] = Field(default_factory=list)
    flags: PremiumOvertimeFlags | None = None


class UnionAccessBusinessFlags(BooleanFlagModel):
    has_steward_access: bool | None = None
    has_union_business_time: bool | None = None
    has_bulletin_board_rights: bool | None = None
    has_meeting_rights: bool | None = None
    has_paid_union_time: bool | None = None


class UnionAccessBusinessExtraction(RecognitionExtraction):
    """Steward access, union business time, bulletin boards, and meeting rights."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_UNION_ACCESS_BUSINESS']] = 'C_UNION_ACCESS_BUSINESS'
    category: ClassVar[Literal['Recognition']] = 'Recognition'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('union_role_names', 'access_location_names', 'communication_channel_names')
    union_role_names: list[str] = Field(default_factory=list)
    access_location_names: list[str] = Field(default_factory=list)
    communication_channel_names: list[str] = Field(default_factory=list)
    flags: UnionAccessBusinessFlags | None = None


class DisciplineJustCauseFlags(BooleanFlagModel):
    has_just_cause_standard: bool | None = None
    covers_discipline: bool | None = None
    covers_discharge: bool | None = None
    has_hearing_right: bool | None = None
    has_investigatory_right: bool | None = None
    has_probation_exception: bool | None = None
    has_progressive_discipline: bool | None = None


class DisciplineJustCauseExtraction(ProcedureOrStandardExtraction):
    """Just cause and substantive discipline/discharge standard."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_DISCIPLINE_JUST_CAUSE']] = 'C_DISCIPLINE_JUST_CAUSE'
    category: ClassVar[Literal['Disputes']] = 'Disputes'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('discipline_terms', 'covered_employee_groups', 'excluded_employee_groups', 'offense_terms')
    discipline_terms: list[str] = Field(default_factory=list)
    covered_employee_groups: list[str] = Field(default_factory=list)
    excluded_employee_groups: list[str] = Field(default_factory=list)
    offense_terms: list[str] = Field(default_factory=list)
    flags: DisciplineJustCauseFlags | None = None


class WageIncreasesColaFlags(BooleanFlagModel):
    has_scheduled_increases: bool | None = None
    has_cola: bool | None = None
    has_lump_sum_adjustment: bool | None = None
    has_across_the_board_increase: bool | None = None


class WageIncreasesColaExtraction(WageAdjustmentExtraction):
    """Annual wage increases."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_WAGE_INCREASES_COLA']] = 'C_WAGE_INCREASES_COLA'
    category: ClassVar[Literal['Compensation']] = 'Compensation'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('effective_dates', 'covered_employee_groups', 'adjustment_names', 'cola_index_names')
    effective_dates: list[str] = Field(default_factory=list)
    covered_employee_groups: list[str] = Field(default_factory=list)
    adjustment_names: list[str] = Field(default_factory=list)
    cola_index_names: list[str] = Field(default_factory=list)
    flags: WageIncreasesColaFlags | None = None


class LeaveVacationFlags(BooleanFlagModel):
    has_paid_vacation: bool | None = None
    accrues_with_service: bool | None = None
    has_cashout: bool | None = None
    has_scheduling_rules: bool | None = None
    has_vacation_fund: bool | None = None


class LeaveVacationExtraction(LeaveEntitlementExtraction):
    """Vacation and annual leave."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_LEAVE_VACATION']] = 'C_LEAVE_VACATION'
    category: ClassVar[Literal['Leave']] = 'Leave'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('service_band_names', 'vacation_schedule_terms', 'eligible_employee_groups')
    service_band_names: list[str] = Field(default_factory=list)
    vacation_schedule_terms: list[str] = Field(default_factory=list)
    eligible_employee_groups: list[str] = Field(default_factory=list)
    flags: LeaveVacationFlags | None = None


class SafetyPpeUnsafeWorkFlags(BooleanFlagModel):
    has_ppe_requirement: bool | None = None
    has_unsafe_work_right: bool | None = None
    has_safety_standards: bool | None = None
    has_hazard_response: bool | None = None
    has_safety_committee: bool | None = None


class SafetyPpeUnsafeWorkExtraction(SafetyExtraction):
    """PPE, unsafe-work rights, safety standards, and hazard response."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_SAFETY_PPE_UNSAFE_WORK']] = 'C_SAFETY_PPE_UNSAFE_WORK'
    category: ClassVar[Literal['Safety']] = 'Safety'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('ppe_item_names', 'hazard_names', 'safety_standard_names', 'committee_names')
    ppe_item_names: list[str] = Field(default_factory=list)
    hazard_names: list[str] = Field(default_factory=list)
    safety_standard_names: list[str] = Field(default_factory=list)
    committee_names: list[str] = Field(default_factory=list)
    flags: SafetyPpeUnsafeWorkFlags | None = None


class PremiumCallInReportingFlags(BooleanFlagModel):
    has_call_in_pay: bool | None = None
    has_call_back_pay: bool | None = None
    has_reporting_pay: bool | None = None
    has_minimum_pay_guarantee: bool | None = None


class PremiumCallInReportingExtraction(PremiumPayExtraction):
    """Call-in, call-back, reporting, and minimum-pay guarantees."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_PREMIUM_CALL_IN_REPORTING']] = 'C_PREMIUM_CALL_IN_REPORTING'
    category: ClassVar[Literal['Compensation']] = 'Compensation'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('trigger_terms', 'covered_employee_groups', 'guarantee_names')
    trigger_terms: list[str] = Field(default_factory=list)
    covered_employee_groups: list[str] = Field(default_factory=list)
    guarantee_names: list[str] = Field(default_factory=list)
    flags: PremiumCallInReportingFlags | None = None


class RetirementPensionFlags(BooleanFlagModel):
    has_defined_benefit_pension: bool | None = None
    has_employer_contribution: bool | None = None
    has_employee_contribution: bool | None = None
    has_vesting_requirement: bool | None = None
    has_external_fund: bool | None = None


class RetirementPensionExtraction(AncillaryBenefitExtraction):
    """Pension and retirement plan eligibility/contributions."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_RETIREMENT_PENSION']] = 'C_RETIREMENT_PENSION'
    category: ClassVar[Literal['Ancillary']] = 'Ancillary'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('plan_names', 'fund_names', 'eligible_employee_groups', 'vesting_terms')
    plan_names: list[str] = Field(default_factory=list)
    fund_names: list[str] = Field(default_factory=list)
    eligible_employee_groups: list[str] = Field(default_factory=list)
    vesting_terms: list[str] = Field(default_factory=list)
    flags: RetirementPensionFlags | None = None


class JobSecurityLayoffOrderFlags(BooleanFlagModel):
    has_layoff_notice: bool | None = None
    seniority_based: bool | None = None
    has_bumping_rights: bool | None = None
    has_inverse_seniority_order: bool | None = None
    has_union_notice: bool | None = None


class JobSecurityLayoffOrderExtraction(JobSecurityExtraction):
    """Layoff notification and procedure."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_JOB_SECURITY_LAYOFF_ORDER']] = 'C_JOB_SECURITY_LAYOFF_ORDER'
    category: ClassVar[Literal['Security']] = 'Security'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('layoff_unit_names', 'affected_employee_groups', 'notice_method_terms', 'exception_terms')
    layoff_unit_names: list[str] = Field(default_factory=list)
    affected_employee_groups: list[str] = Field(default_factory=list)
    notice_method_terms: list[str] = Field(default_factory=list)
    exception_terms: list[str] = Field(default_factory=list)
    flags: JobSecurityLayoffOrderFlags | None = None


class TimeRegularScheduleFlags(BooleanFlagModel):
    has_regular_hours: bool | None = None
    has_workweek_definition: bool | None = None
    has_shift_schedule: bool | None = None
    has_flexible_schedule: bool | None = None
    has_guaranteed_hours: bool | None = None


class TimeRegularScheduleExtraction(SchedulingExtraction):
    """Regular hours and schedule structure."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_TIME_REGULAR_SCHEDULE']] = 'C_TIME_REGULAR_SCHEDULE'
    category: ClassVar[Literal['Scheduling']] = 'Scheduling'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('shift_names', 'workweek_definition_terms', 'covered_employee_groups')
    shift_names: list[str] = Field(default_factory=list)
    workweek_definition_terms: list[str] = Field(default_factory=list)
    covered_employee_groups: list[str] = Field(default_factory=list)
    flags: TimeRegularScheduleFlags | None = None


class UnionSecurityDuesCheckoffFlags(BooleanFlagModel):
    has_dues_checkoff: bool | None = None
    has_union_security: bool | None = None
    has_agency_shop: bool | None = None
    has_remittance_deadline: bool | None = None
    has_authorization_requirement: bool | None = None


class UnionSecurityDuesCheckoffExtraction(RecognitionExtraction):
    """Dues checkoff, agency shop, union security, and payroll remittance."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_UNION_SECURITY_DUES_CHECKOFF']] = 'C_UNION_SECURITY_DUES_CHECKOFF'
    category: ClassVar[Literal['Recognition']] = 'Recognition'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('union_names', 'authorization_terms', 'revocation_terms', 'fee_type_names')
    union_names: list[str] = Field(default_factory=list)
    authorization_terms: list[str] = Field(default_factory=list)
    revocation_terms: list[str] = Field(default_factory=list)
    fee_type_names: list[str] = Field(default_factory=list)
    flags: UnionSecurityDuesCheckoffFlags | None = None


class WageProgressionFlags(BooleanFlagModel):
    has_step_progression: bool | None = None
    has_classification_movement: bool | None = None
    has_seniority_progression: bool | None = None
    has_training_progression: bool | None = None
    has_automatic_progression: bool | None = None


class WageProgressionExtraction(WageAdjustmentExtraction):
    """Wage progression, steps, and classification movement."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_WAGE_PROGRESSION']] = 'C_WAGE_PROGRESSION'
    category: ClassVar[Literal['Compensation']] = 'Compensation'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('progression_step_names', 'classification_names', 'occupation_names', 'effective_dates')
    progression_step_names: list[str] = Field(default_factory=list)
    classification_names: list[str] = Field(default_factory=list)
    occupation_names: list[str] = Field(default_factory=list)
    effective_dates: list[str] = Field(default_factory=list)
    flags: WageProgressionFlags | None = None


class LeaveSickFlags(BooleanFlagModel):
    has_paid_sick_leave: bool | None = None
    accrues_with_service: bool | None = None
    has_carryover: bool | None = None
    has_cashout: bool | None = None
    has_medical_certification_requirement: bool | None = None


class LeaveSickExtraction(LeaveEntitlementExtraction):
    """Sick/personal days."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_LEAVE_SICK']] = 'C_LEAVE_SICK'
    category: ClassVar[Literal['Leave']] = 'Leave'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('sick_leave_bank_names', 'eligible_employee_groups', 'permitted_use_terms')
    sick_leave_bank_names: list[str] = Field(default_factory=list)
    eligible_employee_groups: list[str] = Field(default_factory=list)
    permitted_use_terms: list[str] = Field(default_factory=list)
    flags: LeaveSickFlags | None = None


class JobSecurityRecallFlags(BooleanFlagModel):
    has_recall_rights: bool | None = None
    seniority_based: bool | None = None
    has_recall_period_limit: bool | None = None
    has_recall_notice: bool | None = None
    has_preference_over_new_hires: bool | None = None


class JobSecurityRecallExtraction(JobSecurityExtraction):
    """Recall rights."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_JOB_SECURITY_RECALL']] = 'C_JOB_SECURITY_RECALL'
    category: ClassVar[Literal['Security']] = 'Security'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('recall_list_names', 'affected_employee_groups', 'notice_method_terms', 'exception_terms')
    recall_list_names: list[str] = Field(default_factory=list)
    affected_employee_groups: list[str] = Field(default_factory=list)
    notice_method_terms: list[str] = Field(default_factory=list)
    exception_terms: list[str] = Field(default_factory=list)
    flags: JobSecurityRecallFlags | None = None


class TimeRestMealPeriodsFlags(BooleanFlagModel):
    has_rest_periods: bool | None = None
    has_meal_periods: bool | None = None
    has_paid_breaks: bool | None = None
    has_relief_breaks: bool | None = None
    has_missed_break_premium: bool | None = None


class TimeRestMealPeriodsExtraction(SchedulingExtraction):
    """Rest periods, meal periods, and relief breaks."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_TIME_REST_MEAL_PERIODS']] = 'C_TIME_REST_MEAL_PERIODS'
    category: ClassVar[Literal['Scheduling']] = 'Scheduling'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('break_type_names', 'shift_names', 'exception_terms')
    break_type_names: list[str] = Field(default_factory=list)
    shift_names: list[str] = Field(default_factory=list)
    exception_terms: list[str] = Field(default_factory=list)
    flags: TimeRestMealPeriodsFlags | None = None


class PremiumResponsibilitySpecialtyFlags(BooleanFlagModel):
    has_responsibility_premium: bool | None = None
    has_higher_classification_premium: bool | None = None
    has_specialty_premium: bool | None = None
    has_translation_premium: bool | None = None
    has_role_premium: bool | None = None


class PremiumResponsibilitySpecialtyExtraction(PremiumPayExtraction):
    """Responsibility, higher-classification, specialty, translation, flight, or role premiums."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_PREMIUM_RESPONSIBILITY_SPECIALTY']] = 'C_PREMIUM_RESPONSIBILITY_SPECIALTY'
    category: ClassVar[Literal['Compensation']] = 'Compensation'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('premium_role_names', 'classification_names', 'specialty_names')
    premium_role_names: list[str] = Field(default_factory=list)
    classification_names: list[str] = Field(default_factory=list)
    specialty_names: list[str] = Field(default_factory=list)
    flags: PremiumResponsibilitySpecialtyFlags | None = None


class RecognitionCoverageScopeFlags(BooleanFlagModel):
    has_bargaining_unit_scope: bool | None = None
    excludes_supervisors: bool | None = None
    excludes_confidential_employees: bool | None = None
    has_accretion_language: bool | None = None


class RecognitionCoverageScopeExtraction(RecognitionExtraction):
    """Bargaining unit scope."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_RECOGNITION_COVERAGE_SCOPE']] = 'C_RECOGNITION_COVERAGE_SCOPE'
    category: ClassVar[Literal['Recognition']] = 'Recognition'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('union_names', 'bargaining_unit_descriptions', 'included_employee_groups', 'excluded_employee_groups')
    union_names: list[str] = Field(default_factory=list)
    bargaining_unit_descriptions: list[str] = Field(default_factory=list)
    included_employee_groups: list[str] = Field(default_factory=list)
    excluded_employee_groups: list[str] = Field(default_factory=list)
    flags: RecognitionCoverageScopeFlags | None = None


class HealthDentalFlags(BooleanFlagModel):
    includes_dental: bool | None = None
    employer_paid: bool | None = None
    employee_paid: bool | None = None
    includes_dependent_coverage: bool | None = None
    has_waiting_period: bool | None = None


class HealthDentalExtraction(HealthBenefitExtraction):
    """Dental plan."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_HEALTH_DENTAL']] = 'C_HEALTH_DENTAL'
    category: ClassVar[Literal['Healthcare']] = 'Healthcare'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('plan_names', 'coverage_tiers', 'eligible_employee_groups', 'covered_service_names')
    plan_names: list[str] = Field(default_factory=list)
    coverage_tiers: list[str] = Field(default_factory=list)
    eligible_employee_groups: list[str] = Field(default_factory=list)
    covered_service_names: list[str] = Field(default_factory=list)
    flags: HealthDentalFlags | None = None


class LeaveParentalFamilyFlags(BooleanFlagModel):
    has_parental_leave: bool | None = None
    has_family_leave: bool | None = None
    paid: bool | None = None
    has_fmla_reference: bool | None = None
    has_job_protection: bool | None = None


class LeaveParentalFamilyExtraction(LeaveEntitlementExtraction):
    """Family leave."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_LEAVE_PARENTAL_FAMILY']] = 'C_LEAVE_PARENTAL_FAMILY'
    category: ClassVar[Literal['Leave']] = 'Leave'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('leave_type_names', 'relationship_terms', 'statute_names')
    leave_type_names: list[str] = Field(default_factory=list)
    relationship_terms: list[str] = Field(default_factory=list)
    statute_names: list[str] = Field(default_factory=list)
    flags: LeaveParentalFamilyFlags | None = None


class TrainingTuitionCertificationFlags(BooleanFlagModel):
    has_training_benefit: bool | None = None
    has_tuition_reimbursement: bool | None = None
    has_certification_support: bool | None = None
    employer_paid: bool | None = None
    has_professional_development: bool | None = None


class TrainingTuitionCertificationExtraction(AncillaryBenefitExtraction):
    """Training, tuition support, certification, and professional development."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_TRAINING_TUITION_CERTIFICATION']] = 'C_TRAINING_TUITION_CERTIFICATION'
    category: ClassVar[Literal['Ancillary']] = 'Ancillary'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('training_program_names', 'certification_names', 'eligible_employee_groups')
    training_program_names: list[str] = Field(default_factory=list)
    certification_names: list[str] = Field(default_factory=list)
    eligible_employee_groups: list[str] = Field(default_factory=list)
    flags: TrainingTuitionCertificationFlags | None = None


class JobSecuritySeveranceFlags(BooleanFlagModel):
    has_severance_pay: bool | None = None
    service_based: bool | None = None
    wage_based: bool | None = None
    has_layoff_trigger: bool | None = None
    has_maximum_duration: bool | None = None


class JobSecuritySeveranceExtraction(JobSecurityExtraction):
    """Income Protection Supplement."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_JOB_SECURITY_SEVERANCE']] = 'C_JOB_SECURITY_SEVERANCE'
    category: ClassVar[Literal['Security']] = 'Security'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('severance_plan_names', 'eligible_employee_groups', 'benefit_type_names')
    severance_plan_names: list[str] = Field(default_factory=list)
    eligible_employee_groups: list[str] = Field(default_factory=list)
    benefit_type_names: list[str] = Field(default_factory=list)
    flags: JobSecuritySeveranceFlags | None = None


class HealthMedicalActiveFlags(BooleanFlagModel):
    includes_medical: bool | None = None
    includes_dependent_coverage: bool | None = None
    employer_paid: bool | None = None
    employee_paid: bool | None = None
    has_external_plan: bool | None = None


class HealthMedicalActiveExtraction(HealthBenefitExtraction):
    """Active-worker medical umbrella record."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_HEALTH_MEDICAL_ACTIVE']] = 'C_HEALTH_MEDICAL_ACTIVE'
    category: ClassVar[Literal['Healthcare']] = 'Healthcare'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('plan_names', 'coverage_tiers', 'eligible_employee_groups', 'covered_service_names')
    plan_names: list[str] = Field(default_factory=list)
    coverage_tiers: list[str] = Field(default_factory=list)
    eligible_employee_groups: list[str] = Field(default_factory=list)
    covered_service_names: list[str] = Field(default_factory=list)
    flags: HealthMedicalActiveFlags | None = None


class HealthLifeAdDFlags(BooleanFlagModel):
    includes_life_insurance: bool | None = None
    includes_add: bool | None = None
    employer_paid: bool | None = None
    employee_paid: bool | None = None
    includes_dependent_coverage: bool | None = None


class HealthLifeAdDExtraction(HealthBenefitExtraction):
    """Group life and AD&D insurance."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_HEALTH_LIFE_AD_D']] = 'C_HEALTH_LIFE_AD_D'
    category: ClassVar[Literal['Healthcare']] = 'Healthcare'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('plan_names', 'coverage_tiers', 'eligible_employee_groups', 'covered_service_names')
    plan_names: list[str] = Field(default_factory=list)
    coverage_tiers: list[str] = Field(default_factory=list)
    eligible_employee_groups: list[str] = Field(default_factory=list)
    covered_service_names: list[str] = Field(default_factory=list)
    flags: HealthLifeAdDFlags | None = None


class DisciplineProgressiveFlags(BooleanFlagModel):
    has_progressive_discipline: bool | None = None
    has_warnings: bool | None = None
    has_notice_requirement: bool | None = None
    has_suspension_step: bool | None = None
    has_discharge_step: bool | None = None


class DisciplineProgressiveExtraction(ProcedureOrStandardExtraction):
    """Progressive discipline steps, warnings, and notice."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_DISCIPLINE_PROGRESSIVE']] = 'C_DISCIPLINE_PROGRESSIVE'
    category: ClassVar[Literal['Disputes']] = 'Disputes'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('discipline_step_names', 'offense_terms', 'notice_terms')
    discipline_step_names: list[str] = Field(default_factory=list)
    offense_terms: list[str] = Field(default_factory=list)
    notice_terms: list[str] = Field(default_factory=list)
    flags: DisciplineProgressiveFlags | None = None


class HealthMedicalActivePlanDesignFlags(BooleanFlagModel):
    includes_medical: bool | None = None
    has_deductible: bool | None = None
    has_copay: bool | None = None
    has_out_of_pocket_maximum: bool | None = None
    has_coverage_tiers: bool | None = None
    has_network_rules: bool | None = None


class HealthMedicalActivePlanDesignExtraction(HealthBenefitExtraction):
    """Active-worker medical plan design, covered services, deductibles, copays, OOP limits."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_HEALTH_MEDICAL_ACTIVE_PLAN_DESIGN']] = 'C_HEALTH_MEDICAL_ACTIVE_PLAN_DESIGN'
    category: ClassVar[Literal['Healthcare']] = 'Healthcare'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('plan_names', 'network_names', 'coverage_tiers', 'covered_service_names')
    plan_names: list[str] = Field(default_factory=list)
    network_names: list[str] = Field(default_factory=list)
    coverage_tiers: list[str] = Field(default_factory=list)
    covered_service_names: list[str] = Field(default_factory=list)
    flags: HealthMedicalActivePlanDesignFlags | None = None


class HiringHallDispatchFlags(BooleanFlagModel):
    has_hiring_hall: bool | None = None
    has_dispatch_rules: bool | None = None
    has_referral_priority: bool | None = None
    union_operated: bool | None = None
    has_registration_list: bool | None = None


class HiringHallDispatchExtraction(RecognitionExtraction):
    """Hiring hall, dispatch hall, and referral system."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_HIRING_HALL_DISPATCH']] = 'C_HIRING_HALL_DISPATCH'
    category: ClassVar[Literal['Recognition']] = 'Recognition'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('hiring_hall_names', 'referral_priority_terms', 'registration_list_names')
    hiring_hall_names: list[str] = Field(default_factory=list)
    referral_priority_terms: list[str] = Field(default_factory=list)
    registration_list_names: list[str] = Field(default_factory=list)
    flags: HiringHallDispatchFlags | None = None


class DisciplineInvestigationAppealFlags(BooleanFlagModel):
    has_appeal_right: bool | None = None
    has_investigation_procedure: bool | None = None
    has_record_removal: bool | None = None
    has_union_representation: bool | None = None
    has_deadline: bool | None = None


class DisciplineInvestigationAppealExtraction(ProcedureOrStandardExtraction):
    """Disciplinary record removal."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_DISCIPLINE_INVESTIGATION_APPEAL']] = 'C_DISCIPLINE_INVESTIGATION_APPEAL'
    category: ClassVar[Literal['Disputes']] = 'Disputes'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('appeal_step_names', 'record_removal_terms', 'representation_terms')
    appeal_step_names: list[str] = Field(default_factory=list)
    record_removal_terms: list[str] = Field(default_factory=list)
    representation_terms: list[str] = Field(default_factory=list)
    flags: DisciplineInvestigationAppealFlags | None = None


class HealthDisabilityIncomeFlags(BooleanFlagModel):
    includes_disability: bool | None = None
    has_short_term_disability: bool | None = None
    has_long_term_disability: bool | None = None
    employer_paid: bool | None = None
    wage_replacement_based: bool | None = None
    has_waiting_period: bool | None = None


class HealthDisabilityIncomeExtraction(HealthBenefitExtraction):
    """Income Protection and Extended Income Protection (disability income)."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_HEALTH_DISABILITY_INCOME']] = 'C_HEALTH_DISABILITY_INCOME'
    category: ClassVar[Literal['Healthcare']] = 'Healthcare'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('plan_names', 'disability_type_names', 'waiting_period_terms')
    plan_names: list[str] = Field(default_factory=list)
    disability_type_names: list[str] = Field(default_factory=list)
    waiting_period_terms: list[str] = Field(default_factory=list)
    flags: HealthDisabilityIncomeFlags | None = None


class JobSecurityBenefitContinuationFlags(BooleanFlagModel):
    has_benefit_continuation: bool | None = None
    includes_health_continuation: bool | None = None
    includes_life_insurance_continuation: bool | None = None
    applies_during_leave: bool | None = None
    employer_paid: bool | None = None


class JobSecurityBenefitContinuationExtraction(JobSecurityExtraction):
    """Benefits during leaves of absence."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_JOB_SECURITY_BENEFIT_CONTINUATION']] = 'C_JOB_SECURITY_BENEFIT_CONTINUATION'
    category: ClassVar[Literal['Security']] = 'Security'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('benefit_program_names', 'benefit_type_names', 'leave_type_names', 'eligible_employee_groups')
    benefit_program_names: list[str] = Field(default_factory=list)
    benefit_type_names: list[str] = Field(default_factory=list)
    leave_type_names: list[str] = Field(default_factory=list)
    eligible_employee_groups: list[str] = Field(default_factory=list)
    flags: JobSecurityBenefitContinuationFlags | None = None


class HealthRetireeFlags(BooleanFlagModel):
    includes_retiree_coverage: bool | None = None
    employer_paid: bool | None = None
    employee_paid: bool | None = None
    includes_dependent_coverage: bool | None = None
    has_eligibility_requirement: bool | None = None


class HealthRetireeExtraction(HealthBenefitExtraction):
    """Retiree health plan."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_HEALTH_RETIREE']] = 'C_HEALTH_RETIREE'
    category: ClassVar[Literal['Healthcare']] = 'Healthcare'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('plan_names', 'eligible_retiree_groups', 'eligibility_terms')
    plan_names: list[str] = Field(default_factory=list)
    eligible_retiree_groups: list[str] = Field(default_factory=list)
    eligibility_terms: list[str] = Field(default_factory=list)
    flags: HealthRetireeFlags | None = None


class SubcontractingWorkPreservationFlags(BooleanFlagModel):
    limits_subcontracting: bool | None = None
    has_work_preservation: bool | None = None
    requires_union_notice: bool | None = None
    allows_union_matching: bool | None = None
    protects_bargaining_unit_work: bool | None = None


class SubcontractingWorkPreservationExtraction(JobSecurityExtraction):
    """Subcontracting limits, non-unit work, and work preservation."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_SUBCONTRACTING_WORK_PRESERVATION']] = 'C_SUBCONTRACTING_WORK_PRESERVATION'
    category: ClassVar[Literal['Security']] = 'Security'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('protected_work_terms', 'subcontracting_terms', 'subcontracting_exception_terms', 'notice_recipient_names')
    protected_work_terms: list[str] = Field(default_factory=list)
    subcontracting_terms: list[str] = Field(default_factory=list)
    subcontracting_exception_terms: list[str] = Field(default_factory=list)
    notice_recipient_names: list[str] = Field(default_factory=list)
    flags: SubcontractingWorkPreservationFlags | None = None


class WorkloadClassSizeStaffingFlags(BooleanFlagModel):
    has_class_size_limit: bool | None = None
    has_staffing_ratio: bool | None = None
    has_preparation_period: bool | None = None
    has_duty_free_lunch: bool | None = None
    has_voluntary_extracurricular: bool | None = None


class WorkloadClassSizeStaffingExtraction(SchedulingExtraction):
    """School day defined."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_WORKLOAD_CLASS_SIZE_STAFFING']] = 'C_WORKLOAD_CLASS_SIZE_STAFFING'
    category: ClassVar[Literal['Scheduling']] = 'Scheduling'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('class_size_unit_names', 'staffing_ratio_terms', 'duty_terms')
    class_size_unit_names: list[str] = Field(default_factory=list)
    staffing_ratio_terms: list[str] = Field(default_factory=list)
    duty_terms: list[str] = Field(default_factory=list)
    flags: WorkloadClassSizeStaffingFlags | None = None


class SenioritySystemFlags(BooleanFlagModel):
    has_seniority_system: bool | None = None
    classification_based: bool | None = None
    plantwide_seniority: bool | None = None
    has_tie_breaker: bool | None = None
    affects_layoff: bool | None = None


class SenioritySystemExtraction(JobSecurityExtraction):
    """Seniority system."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_SENIORITY_SYSTEM']] = 'C_SENIORITY_SYSTEM'
    category: ClassVar[Literal['Security']] = 'Security'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('seniority_unit_names', 'seniority_type_names', 'seniority_group_names', 'classification_names', 'break_in_service_terms', 'tie_breaker_terms')
    seniority_unit_names: list[str] = Field(default_factory=list)
    seniority_type_names: list[str] = Field(default_factory=list)
    seniority_group_names: list[str] = Field(default_factory=list)
    classification_names: list[str] = Field(default_factory=list)
    break_in_service_terms: list[str] = Field(default_factory=list)
    tie_breaker_terms: list[str] = Field(default_factory=list)
    flags: SenioritySystemFlags | None = None


class PremiumZoneSubsistenceFlags(BooleanFlagModel):
    has_zone_pay: bool | None = None
    has_travel_subsistence: bool | None = None
    has_remote_site_allowance: bool | None = None
    distance_based: bool | None = None
    overnight_based: bool | None = None


class PremiumZoneSubsistenceExtraction(PremiumPayExtraction):
    """Zone pay, travel subsistence, and remote-site allowances."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_PREMIUM_ZONE_SUBSISTENCE']] = 'C_PREMIUM_ZONE_SUBSISTENCE'
    category: ClassVar[Literal['Compensation']] = 'Compensation'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('zone_names', 'geographic_areas', 'travel_terms')
    zone_names: list[str] = Field(default_factory=list)
    geographic_areas: list[str] = Field(default_factory=list)
    travel_terms: list[str] = Field(default_factory=list)
    flags: PremiumZoneSubsistenceFlags | None = None


class HealthVisionFlags(BooleanFlagModel):
    includes_vision: bool | None = None
    employer_paid: bool | None = None
    employee_paid: bool | None = None
    includes_dependent_coverage: bool | None = None
    has_waiting_period: bool | None = None


class HealthVisionExtraction(HealthBenefitExtraction):
    """Group vision care plan."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_HEALTH_VISION']] = 'C_HEALTH_VISION'
    category: ClassVar[Literal['Healthcare']] = 'Healthcare'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('plan_names', 'coverage_tiers', 'eligible_employee_groups', 'covered_service_names')
    plan_names: list[str] = Field(default_factory=list)
    coverage_tiers: list[str] = Field(default_factory=list)
    eligible_employee_groups: list[str] = Field(default_factory=list)
    covered_service_names: list[str] = Field(default_factory=list)
    flags: HealthVisionFlags | None = None


class JobPostingBiddingTransferFlags(BooleanFlagModel):
    has_job_posting: bool | None = None
    has_bidding_rights: bool | None = None
    has_transfer_rights: bool | None = None
    seniority_based: bool | None = None
    has_trial_period: bool | None = None


class JobPostingBiddingTransferExtraction(JobSecurityExtraction):
    """Job posting and promotion rights."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_JOB_POSTING_BIDDING_TRANSFER']] = 'C_JOB_POSTING_BIDDING_TRANSFER'
    category: ClassVar[Literal['Security']] = 'Security'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('job_posting_terms', 'bidding_unit_names', 'eligible_employee_groups', 'trial_period_terms')
    job_posting_terms: list[str] = Field(default_factory=list)
    bidding_unit_names: list[str] = Field(default_factory=list)
    eligible_employee_groups: list[str] = Field(default_factory=list)
    trial_period_terms: list[str] = Field(default_factory=list)
    flags: JobPostingBiddingTransferFlags | None = None


class SafetyAssaultViolenceFlags(BooleanFlagModel):
    has_assault_policy: bool | None = None
    has_violence_response: bool | None = None
    has_paid_release: bool | None = None
    has_response_team: bool | None = None
    has_reporting_requirement: bool | None = None


class SafetyAssaultViolenceExtraction(SafetyExtraction):
    """Physical violence and verbal abuse policy."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_SAFETY_ASSAULT_VIOLENCE']] = 'C_SAFETY_ASSAULT_VIOLENCE'
    category: ClassVar[Literal['Safety']] = 'Safety'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('violence_event_terms', 'response_team_names', 'reporting_terms')
    violence_event_terms: list[str] = Field(default_factory=list)
    response_team_names: list[str] = Field(default_factory=list)
    reporting_terms: list[str] = Field(default_factory=list)
    flags: SafetyAssaultViolenceFlags | None = None


class RetirementIncentiveFlags(BooleanFlagModel):
    has_retirement_bonus: bool | None = None
    service_based: bool | None = None
    date_based: bool | None = None
    has_age_requirement: bool | None = None
    has_notice_requirement: bool | None = None


class RetirementIncentiveExtraction(AncillaryBenefitExtraction):
    """Retirement bonus."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_RETIREMENT_INCENTIVE']] = 'C_RETIREMENT_INCENTIVE'
    category: ClassVar[Literal['Ancillary']] = 'Ancillary'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('incentive_names', 'eligible_employee_groups', 'effective_dates')
    incentive_names: list[str] = Field(default_factory=list)
    eligible_employee_groups: list[str] = Field(default_factory=list)
    effective_dates: list[str] = Field(default_factory=list)
    flags: RetirementIncentiveFlags | None = None


class JobSecurityLayoffRecallFlags(BooleanFlagModel):
    has_layoff_procedure: bool | None = None
    has_recall_rights: bool | None = None
    seniority_based: bool | None = None
    has_bumping_rights: bool | None = None
    has_notice_requirement: bool | None = None


class JobSecurityLayoffRecallExtraction(JobSecurityExtraction):
    """Force adjustments and recall."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_JOB_SECURITY_LAYOFF_RECALL']] = 'C_JOB_SECURITY_LAYOFF_RECALL'
    category: ClassVar[Literal['Security']] = 'Security'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('layoff_unit_names', 'recall_list_names', 'affected_employee_groups', 'notice_method_terms', 'exception_terms')
    layoff_unit_names: list[str] = Field(default_factory=list)
    recall_list_names: list[str] = Field(default_factory=list)
    affected_employee_groups: list[str] = Field(default_factory=list)
    notice_method_terms: list[str] = Field(default_factory=list)
    exception_terms: list[str] = Field(default_factory=list)
    flags: JobSecurityLayoffRecallFlags | None = None


class JobSecuritySubIncomeBridgeFlags(BooleanFlagModel):
    has_sub_income_benefit: bool | None = None
    wage_replacement_based: bool | None = None
    service_based: bool | None = None
    has_external_fund: bool | None = None
    has_duration_limit: bool | None = None


class JobSecuritySubIncomeBridgeExtraction(JobSecurityExtraction):
    """Supplemental Unemployment Benefit (SUB) fund."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_JOB_SECURITY_SUB_INCOME_BRIDGE']] = 'C_JOB_SECURITY_SUB_INCOME_BRIDGE'
    category: ClassVar[Literal['Security']] = 'Security'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('severance_plan_names', 'benefit_program_names', 'benefit_type_names', 'eligible_employee_groups')
    severance_plan_names: list[str] = Field(default_factory=list)
    benefit_program_names: list[str] = Field(default_factory=list)
    benefit_type_names: list[str] = Field(default_factory=list)
    eligible_employee_groups: list[str] = Field(default_factory=list)
    flags: JobSecuritySubIncomeBridgeFlags | None = None


class HealthActiveFlags(BooleanFlagModel):
    includes_medical: bool | None = None
    includes_dental: bool | None = None
    includes_vision: bool | None = None
    employer_paid: bool | None = None
    employee_paid: bool | None = None
    has_external_trust: bool | None = None


class HealthActiveExtraction(HealthBenefitExtraction):
    """Health benefits."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_HEALTH_ACTIVE']] = 'C_HEALTH_ACTIVE'
    category: ClassVar[Literal['Healthcare']] = 'Healthcare'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('plan_names', 'trust_names', 'coverage_tiers', 'eligible_employee_groups', 'covered_service_names')
    plan_names: list[str] = Field(default_factory=list)
    trust_names: list[str] = Field(default_factory=list)
    coverage_tiers: list[str] = Field(default_factory=list)
    eligible_employee_groups: list[str] = Field(default_factory=list)
    covered_service_names: list[str] = Field(default_factory=list)
    flags: HealthActiveFlags | None = None


class WageGeneralIncreaseFlags(BooleanFlagModel):
    has_general_increase: bool | None = None
    percentage_based: bool | None = None
    flat_amount_based: bool | None = None
    has_effective_dates: bool | None = None
    across_the_board: bool | None = None


class WageGeneralIncreaseExtraction(WageAdjustmentExtraction):
    """Scale increase."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_WAGE_GENERAL_INCREASE']] = 'C_WAGE_GENERAL_INCREASE'
    category: ClassVar[Literal['Compensation']] = 'Compensation'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('effective_dates', 'covered_employee_groups', 'adjustment_names')
    effective_dates: list[str] = Field(default_factory=list)
    covered_employee_groups: list[str] = Field(default_factory=list)
    adjustment_names: list[str] = Field(default_factory=list)
    flags: WageGeneralIncreaseFlags | None = None


class TimeNoCancellationSecurityFlags(BooleanFlagModel):
    has_no_cancellation_rule: bool | None = None
    has_involuntary_leave_limit: bool | None = None
    has_pay_protection: bool | None = None
    has_schedule_security: bool | None = None


class TimeNoCancellationSecurityExtraction(SchedulingExtraction):
    """Involuntary leave status caps."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_TIME_NO_CANCELLATION_SECURITY']] = 'C_TIME_NO_CANCELLATION_SECURITY'
    category: ClassVar[Literal['Scheduling']] = 'Scheduling'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('cancellation_terms', 'affected_employee_groups', 'pay_protection_terms')
    cancellation_terms: list[str] = Field(default_factory=list)
    affected_employee_groups: list[str] = Field(default_factory=list)
    pay_protection_terms: list[str] = Field(default_factory=list)
    flags: TimeNoCancellationSecurityFlags | None = None


class JobSecuritySeniorityFlags(BooleanFlagModel):
    has_seniority_groups: bool | None = None
    classification_based: bool | None = None
    affects_layoff: bool | None = None
    affects_recall: bool | None = None
    affects_bidding: bool | None = None


class JobSecuritySeniorityExtraction(JobSecurityExtraction):
    """Seniority."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_JOB_SECURITY_SENIORITY']] = 'C_JOB_SECURITY_SENIORITY'
    category: ClassVar[Literal['Security']] = 'Security'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('seniority_unit_names', 'seniority_type_names', 'seniority_group_names', 'classification_names', 'break_in_service_terms', 'tie_breaker_terms')
    seniority_unit_names: list[str] = Field(default_factory=list)
    seniority_type_names: list[str] = Field(default_factory=list)
    seniority_group_names: list[str] = Field(default_factory=list)
    classification_names: list[str] = Field(default_factory=list)
    break_in_service_terms: list[str] = Field(default_factory=list)
    tie_breaker_terms: list[str] = Field(default_factory=list)
    flags: JobSecuritySeniorityFlags | None = None


class WageApprenticeFlags(BooleanFlagModel):
    has_apprentice_scale: bool | None = None
    percentage_of_journeyman: bool | None = None
    has_periods: bool | None = None
    has_step_progression: bool | None = None
    hours_based: bool | None = None


class WageApprenticeExtraction(WageAdjustmentExtraction):
    """Apprentice wage schedule 40-82% of JW over 7 periods."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_WAGE_APPRENTICE']] = 'C_WAGE_APPRENTICE'
    category: ClassVar[Literal['Compensation']] = 'Compensation'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('apprenticeship_period_names', 'classification_names')
    apprenticeship_period_names: list[str] = Field(default_factory=list)
    classification_names: list[str] = Field(default_factory=list)
    flags: WageApprenticeFlags | None = None


class WageScheduledIncreaseFlags(BooleanFlagModel):
    has_scheduled_increases: bool | None = None
    service_based: bool | None = None
    longevity_based: bool | None = None
    has_effective_dates: bool | None = None
    flat_amount_based: bool | None = None


class WageScheduledIncreaseExtraction(WageAdjustmentExtraction):
    """Longevity pay."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_WAGE_SCHEDULED_INCREASE']] = 'C_WAGE_SCHEDULED_INCREASE'
    category: ClassVar[Literal['Compensation']] = 'Compensation'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('effective_dates', 'service_band_names', 'adjustment_names')
    effective_dates: list[str] = Field(default_factory=list)
    service_band_names: list[str] = Field(default_factory=list)
    adjustment_names: list[str] = Field(default_factory=list)
    flags: WageScheduledIncreaseFlags | None = None


class PremiumSundayHolidayFlags(BooleanFlagModel):
    has_sunday_premium: bool | None = None
    has_holiday_premium: bool | None = None
    has_double_time: bool | None = None
    has_sixth_day_premium: bool | None = None
    has_seventh_day_premium: bool | None = None


class PremiumSundayHolidayExtraction(PremiumPayExtraction):
    """6th and 7th day in workweek."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_PREMIUM_SUNDAY_HOLIDAY']] = 'C_PREMIUM_SUNDAY_HOLIDAY'
    category: ClassVar[Literal['Compensation']] = 'Compensation'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('day_names', 'holiday_names')
    day_names: list[str] = Field(default_factory=list)
    holiday_names: list[str] = Field(default_factory=list)
    flags: PremiumSundayHolidayFlags | None = None


class LightDutyAccommodationFlags(BooleanFlagModel):
    has_light_duty: bool | None = None
    has_accommodation_process: bool | None = None
    has_pay_protection: bool | None = None
    disability_related: bool | None = None
    has_medical_clearance: bool | None = None


class LightDutyAccommodationExtraction(JobSecurityExtraction):
    """Partially disabled employees."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_LIGHT_DUTY_ACCOMMODATION']] = 'C_LIGHT_DUTY_ACCOMMODATION'
    category: ClassVar[Literal['Security']] = 'Security'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('accommodation_terms', 'eligible_employee_groups', 'medical_clearance_terms')
    accommodation_terms: list[str] = Field(default_factory=list)
    eligible_employee_groups: list[str] = Field(default_factory=list)
    medical_clearance_terms: list[str] = Field(default_factory=list)
    flags: LightDutyAccommodationFlags | None = None


class JobSecurityRifLayoffFlags(BooleanFlagModel):
    has_rif_procedure: bool | None = None
    has_layoff_order: bool | None = None
    seniority_based: bool | None = None
    classification_based: bool | None = None
    has_recall_pool: bool | None = None


class JobSecurityRifLayoffExtraction(JobSecurityExtraction):
    """Layoff."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_JOB_SECURITY_RIF_LAYOFF']] = 'C_JOB_SECURITY_RIF_LAYOFF'
    category: ClassVar[Literal['Security']] = 'Security'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('layoff_unit_names', 'recall_list_names', 'affected_employee_groups', 'notice_method_terms', 'exception_terms')
    layoff_unit_names: list[str] = Field(default_factory=list)
    recall_list_names: list[str] = Field(default_factory=list)
    affected_employee_groups: list[str] = Field(default_factory=list)
    notice_method_terms: list[str] = Field(default_factory=list)
    exception_terms: list[str] = Field(default_factory=list)
    flags: JobSecurityRifLayoffFlags | None = None


class HealthExternalFundFlags(BooleanFlagModel):
    has_external_fund: bool | None = None
    employer_contribution: bool | None = None
    employee_contribution: bool | None = None
    trustee_administered: bool | None = None
    includes_health_welfare: bool | None = None


class HealthExternalFundExtraction(HealthBenefitExtraction):
    """Health/Welfare."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_HEALTH_EXTERNAL_FUND']] = 'C_HEALTH_EXTERNAL_FUND'
    category: ClassVar[Literal['Healthcare']] = 'Healthcare'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('fund_names', 'trustee_names', 'plan_names', 'contribution_terms')
    fund_names: list[str] = Field(default_factory=list)
    trustee_names: list[str] = Field(default_factory=list)
    plan_names: list[str] = Field(default_factory=list)
    contribution_terms: list[str] = Field(default_factory=list)
    flags: HealthExternalFundFlags | None = None


class HealthActivePlanDesignFlags(BooleanFlagModel):
    includes_medical: bool | None = None
    has_deductible: bool | None = None
    has_copay: bool | None = None
    has_out_of_pocket_maximum: bool | None = None
    has_network_rules: bool | None = None
    includes_dental: bool | None = None


class HealthActivePlanDesignExtraction(HealthBenefitExtraction):
    """Active health plan design."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_HEALTH_ACTIVE_PLAN_DESIGN']] = 'C_HEALTH_ACTIVE_PLAN_DESIGN'
    category: ClassVar[Literal['Healthcare']] = 'Healthcare'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('plan_names', 'network_names', 'coverage_tiers', 'covered_service_names')
    plan_names: list[str] = Field(default_factory=list)
    network_names: list[str] = Field(default_factory=list)
    coverage_tiers: list[str] = Field(default_factory=list)
    covered_service_names: list[str] = Field(default_factory=list)
    flags: HealthActivePlanDesignFlags | None = None


class WageIncreaseFlags(BooleanFlagModel):
    has_wage_increase: bool | None = None
    percentage_based: bool | None = None
    flat_amount_based: bool | None = None
    has_effective_dates: bool | None = None
    across_the_board: bool | None = None


class WageIncreaseExtraction(WageAdjustmentExtraction):
    """Annual wage increases."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_WAGE_INCREASE']] = 'C_WAGE_INCREASE'
    category: ClassVar[Literal['Compensation']] = 'Compensation'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('effective_dates', 'covered_employee_groups', 'adjustment_names')
    effective_dates: list[str] = Field(default_factory=list)
    covered_employee_groups: list[str] = Field(default_factory=list)
    adjustment_names: list[str] = Field(default_factory=list)
    flags: WageIncreaseFlags | None = None


class WageLongevityFlags(BooleanFlagModel):
    has_longevity_pay: bool | None = None
    service_based: bool | None = None
    has_steps: bool | None = None
    flat_amount_based: bool | None = None
    percentage_based: bool | None = None


class WageLongevityExtraction(WageAdjustmentExtraction):
    """Longevity pay."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_WAGE_LONGEVITY']] = 'C_WAGE_LONGEVITY'
    category: ClassVar[Literal['Compensation']] = 'Compensation'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('service_band_names', 'covered_employee_groups')
    service_band_names: list[str] = Field(default_factory=list)
    covered_employee_groups: list[str] = Field(default_factory=list)
    flags: WageLongevityFlags | None = None


class UnionDuesCheckoffFlags(BooleanFlagModel):
    has_dues_checkoff: bool | None = None
    has_remittance_deadline: bool | None = None
    has_authorization_requirement: bool | None = None
    percentage_based: bool | None = None
    flat_amount_based: bool | None = None


class UnionDuesCheckoffExtraction(RecognitionExtraction):
    """Monthly dues checkoff."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_UNION_DUES_CHECKOFF']] = 'C_UNION_DUES_CHECKOFF'
    category: ClassVar[Literal['Recognition']] = 'Recognition'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('union_names', 'authorization_terms', 'revocation_terms', 'fee_type_names')
    union_names: list[str] = Field(default_factory=list)
    authorization_terms: list[str] = Field(default_factory=list)
    revocation_terms: list[str] = Field(default_factory=list)
    fee_type_names: list[str] = Field(default_factory=list)
    flags: UnionDuesCheckoffFlags | None = None


class HealthPlanDesignFlags(BooleanFlagModel):
    includes_medical: bool | None = None
    has_plan_options: bool | None = None
    has_deductible: bool | None = None
    has_copay: bool | None = None
    has_out_of_pocket_maximum: bool | None = None
    has_premium_share: bool | None = None


class HealthPlanDesignExtraction(HealthBenefitExtraction):
    """Health plan design options."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_HEALTH_PLAN_DESIGN']] = 'C_HEALTH_PLAN_DESIGN'
    category: ClassVar[Literal['Healthcare']] = 'Healthcare'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('plan_names', 'network_names', 'coverage_tiers', 'covered_service_names')
    plan_names: list[str] = Field(default_factory=list)
    network_names: list[str] = Field(default_factory=list)
    coverage_tiers: list[str] = Field(default_factory=list)
    covered_service_names: list[str] = Field(default_factory=list)
    flags: HealthPlanDesignFlags | None = None


class WageMeritStepFlags(BooleanFlagModel):
    has_merit_step: bool | None = None
    performance_based: bool | None = None
    has_step_schedule: bool | None = None
    discretionary: bool | None = None
    has_review_process: bool | None = None


class WageMeritStepExtraction(WageAdjustmentExtraction):
    """Step advancement on salary schedule."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_WAGE_MERIT_STEP']] = 'C_WAGE_MERIT_STEP'
    category: ClassVar[Literal['Compensation']] = 'Compensation'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('step_names', 'eligibility_terms', 'review_terms')
    step_names: list[str] = Field(default_factory=list)
    eligibility_terms: list[str] = Field(default_factory=list)
    review_terms: list[str] = Field(default_factory=list)
    flags: WageMeritStepFlags | None = None


class DisciplineProbationFlags(BooleanFlagModel):
    has_probation_period: bool | None = None
    has_transfer_probation: bool | None = None
    has_shortened_discipline_rights: bool | None = None
    has_completion_rule: bool | None = None


class DisciplineProbationExtraction(ProcedureOrStandardExtraction):
    """Probation 90 working days."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_DISCIPLINE_PROBATION']] = 'C_DISCIPLINE_PROBATION'
    category: ClassVar[Literal['Disputes']] = 'Disputes'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('probationary_group_names', 'probation_completion_terms')
    probationary_group_names: list[str] = Field(default_factory=list)
    probation_completion_terms: list[str] = Field(default_factory=list)
    flags: DisciplineProbationFlags | None = None


class SafetyDrugTestingFlags(BooleanFlagModel):
    has_drug_testing: bool | None = None
    accident_triggered: bool | None = None
    reasonable_suspicion_based: bool | None = None
    random_testing: bool | None = None
    has_discipline_consequence: bool | None = None


class SafetyDrugTestingExtraction(SafetyExtraction):
    """Work accident investigation protocol."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_SAFETY_DRUG_TESTING']] = 'C_SAFETY_DRUG_TESTING'
    category: ClassVar[Literal['Safety']] = 'Safety'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('testing_trigger_terms', 'substance_test_names', 'consequence_terms')
    testing_trigger_terms: list[str] = Field(default_factory=list)
    substance_test_names: list[str] = Field(default_factory=list)
    consequence_terms: list[str] = Field(default_factory=list)
    flags: SafetyDrugTestingFlags | None = None


class PremiumGroupLeaderFlags(BooleanFlagModel):
    has_group_leader_premium: bool | None = None
    tiered_premium: bool | None = None
    flat_amount_based: bool | None = None
    has_role_premium: bool | None = None


class PremiumGroupLeaderExtraction(PremiumPayExtraction):
    """Group leader premium $1.20/$0.80/$0.40 per hour by tier."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_PREMIUM_GROUP_LEADER']] = 'C_PREMIUM_GROUP_LEADER'
    category: ClassVar[Literal['Compensation']] = 'Compensation'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('role_names', 'tier_names')
    role_names: list[str] = Field(default_factory=list)
    tier_names: list[str] = Field(default_factory=list)
    flags: PremiumGroupLeaderFlags | None = None


class WageIncentiveFlags(BooleanFlagModel):
    has_incentive_pay: bool | None = None
    performance_based: bool | None = None
    percentage_based: bool | None = None
    has_cap: bool | None = None
    has_bonus_components: bool | None = None


class WageIncentiveExtraction(WageAdjustmentExtraction):
    """Incentive pay."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_WAGE_INCENTIVE']] = 'C_WAGE_INCENTIVE'
    category: ClassVar[Literal['Compensation']] = 'Compensation'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('incentive_names', 'performance_metric_names')
    incentive_names: list[str] = Field(default_factory=list)
    performance_metric_names: list[str] = Field(default_factory=list)
    flags: WageIncentiveFlags | None = None


class HealthPrescriptionDrugFlags(BooleanFlagModel):
    includes_prescription_drug: bool | None = None
    has_copay: bool | None = None
    has_tiers: bool | None = None
    mail_order_included: bool | None = None
    generic_required: bool | None = None


class HealthPrescriptionDrugExtraction(HealthBenefitExtraction):
    """3-tier HMO prescription co-pay."""
    detail_fields: ClassVar[tuple[str, ...]] = ("values", "flags")
    concept_id: ClassVar[Literal['C_HEALTH_PRESCRIPTION_DRUG']] = 'C_HEALTH_PRESCRIPTION_DRUG'
    category: ClassVar[Literal['Healthcare']] = 'Healthcare'
    string_detail_fields: ClassVar[tuple[str, ...]] = ('plan_names', 'drug_tier_names', 'covered_service_names')
    plan_names: list[str] = Field(default_factory=list)
    drug_tier_names: list[str] = Field(default_factory=list)
    covered_service_names: list[str] = Field(default_factory=list)
    flags: HealthPrescriptionDrugFlags | None = None
