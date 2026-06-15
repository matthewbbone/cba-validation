# Provision Structures for Deterministic CBA Extraction

This project compares LLM and human extractions from collective bargaining agreements by converting provision text into deterministic attributes. Every provision extraction includes `exists` and `summarize`; comparison should otherwise rely on booleans, numeric values, durations, money amounts, percentages, multipliers, and the small set of retained string-list attributes that affect generosity or comparability.

## Core Provision Strategy

The full dictionary contains 99 provision concepts, but validation should start with a smaller core set. The core provisions are the terms most likely to appear across CBAs and most likely to determine the economic and procedural value of an agreement: base wages, overtime, grievance and arbitration machinery, recognition scope, layoff and recall, health contributions, retirement, vacation, seniority, discipline, holidays, safety, sick leave, and conditional union-security or dues-checkoff rules.

Prioritizing these provisions keeps the human annotation workload tractable and avoids spreading validation effort too thin across rare or highly idiosyncratic clauses. A focused core set makes it easier to build a reliable human benchmark, compare annotators against one another, compare LLM extractions against human extractions, and diagnose where a model is failing. It also ensures that disagreement is measured on provisions that matter for downstream generosity scoring rather than on marginal concepts that may appear infrequently or require specialized interpretation.

The purpose of structuring the core provisions is not just to identify whether a clause exists. Each core provision should be represented through deterministic attributes that can be compared mechanically: booleans for rights and rule features, numeric values for amounts and thresholds, durations for time limits, and tightly scoped string lists only where the literal value affects comparability. This allows validation to ask concrete questions such as whether two extractors found the same overtime multiplier, the same grievance deadline, the same covered employee group, or the same employer health contribution.

Non-core provisions remain in the schema so the project can expand coverage over time. They should be treated as standard or advanced targets until the core provision benchmark is stable enough to support broader extraction and generosity validation.

## Attribute Policy

Provision attributes should be directly verifiable from the CBA. Numeric and boolean attributes are preferred. String-list attributes are retained only when the literal surface form changes how generosity should be compared, such as covered groups, excluded groups, bargaining-unit scope, classifications, effective dates, concrete thresholds, deadlines, waiting periods, exceptions, or similar rule boundaries.

Do not add string attributes merely to capture labels. Plan names, fund names, certification names, step names, program names, union names, forum names, committee names, and broad eligibility prose are intentionally excluded unless a future schema normalizes them into categorical or numeric comparison fields.

## Provision Concepts by Dictionary Category

### Compensation

| Concept ID | Priority/Rank | Format | Attributes | Description |
|---|---:|---|---|---|
| `C_WAGE_BASE_RATE` | core / 1 | `complex` | `values[]`, `flags.has_base_rate`, `flags.has_rate_table`, `flags.has_classification_rates`, `flags.has_step_rates`, `flags.has_salary_rates`, `flags.has_hourly_rates`, `occupation_names`, `classification_names`, `geographic_areas`, `effective_dates` | Base wage or salary rates for covered jobs, classifications, or employees. |
| `C_PREMIUM_OVERTIME` | core / 2 | `complex` | `values[]`, `flags.has_overtime_threshold`, `flags.has_daily_overtime`, `flags.has_weekly_overtime`, `flags.has_premium_multiplier`, `flags.has_double_time`, `trigger_terms`, `covered_employee_groups`, `excluded_employee_groups` | Overtime eligibility, thresholds, multipliers, and related premium-pay rules. |
| `C_WAGE_INCREASES_COLA` | standard | `complex` | `values[]`, `flags.has_scheduled_increases`, `flags.has_cola`, `flags.has_lump_sum_adjustment`, `flags.has_across_the_board_increase`, `effective_dates`, `covered_employee_groups` | Scheduled wage increases, cost-of-living adjustments, and across-the-board raises. |
| `C_PREMIUM_CALL_IN_REPORTING` | standard | `complex` | `values[]`, `flags.has_call_in_pay`, `flags.has_call_back_pay`, `flags.has_reporting_pay`, `flags.has_minimum_pay_guarantee`, `trigger_terms`, `covered_employee_groups` | Pay guarantees for reporting, call-in, call-back, or unscheduled work appearances. |
| `C_PREMIUM_SHIFT` | advanced | `quantitative` | `value`, `covered_employee_groups` | Premium pay for work on specified shifts, nights, weekends, or undesirable schedules. |
| `C_WAGE_PROGRESSION` | standard | `complex` | `values[]`, `flags.has_step_progression`, `flags.has_classification_movement`, `flags.has_seniority_progression`, `flags.has_training_progression`, `flags.has_automatic_progression`, `classification_names`, `occupation_names`, `effective_dates` | Movement through wage steps, classifications, training levels, or progression schedules. |
| `C_PREMIUM_RESPONSIBILITY_SPECIALTY` | standard | `complex` | `values[]`, `flags.has_responsibility_premium`, `flags.has_higher_classification_premium`, `flags.has_specialty_premium`, `flags.has_translation_premium`, `flags.has_role_premium`, `classification_names`, `specialty_names` | Premium pay for added responsibility, specialty duties, or temporary higher assignments. |
| `C_PREMIUM_STANDBY_ON_CALL` | advanced | `quantitative` | `value`, `covered_employee_groups` | Compensation for being on standby, on call, or otherwise available for work. |
| `C_UNIFORM_CLOTHING_ALLOWANCE` | standard | `quantitative` | `value`, `covered_employee_groups` | Employer-provided uniforms, clothing, tools, footwear, or related reimbursements. |
| `C_PREMIUM_ZONE_SUBSISTENCE` | standard | `complex` | `values[]`, `flags.has_zone_pay`, `flags.has_travel_subsistence`, `flags.has_remote_site_allowance`, `flags.distance_based`, `flags.overnight_based`, `geographic_areas` | Zone pay, travel allowances, remote-site allowances, or subsistence benefits. |
| `C_WAGE_GENERAL_INCREASE` | standard | `complex` | `values[]`, `flags.has_general_increase`, `flags.percentage_based`, `flags.flat_amount_based`, `flags.has_effective_dates`, `flags.across_the_board`, `effective_dates`, `covered_employee_groups` | General wage increases applying broadly across covered employees or wage schedules. |
| `C_WAGE_APPRENTICE` | standard | `complex` | `values[]`, `flags.has_apprentice_scale`, `flags.percentage_of_journeyman`, `flags.has_periods`, `flags.has_step_progression`, `flags.hours_based`, `classification_names` | Apprentice or trainee wage scales, progression, and relation to journey-level rates. |
| `C_WAGE_SCHEDULED_INCREASE` | standard | `complex` | `values[]`, `flags.has_scheduled_increases`, `flags.service_based`, `flags.longevity_based`, `flags.has_effective_dates`, `flags.flat_amount_based`, `effective_dates`, `service_band_names` | Scheduled wage increases tied to dates, service bands, longevity, or other triggers. |
| `C_PREMIUM_SUNDAY_HOLIDAY` | standard | `complex` | `values[]`, `flags.has_sunday_premium`, `flags.has_holiday_premium`, `flags.has_double_time`, `flags.has_sixth_day_premium`, `flags.has_seventh_day_premium` | Premium pay for Sunday, holiday, sixth-day, seventh-day, or similar special-day work. |
| `C_PREMIUM_FOREMAN` | standard | `quantitative` | `value`, `classification_names` | Premium pay for foremen, general foremen, supervisors, or comparable lead roles. |
| `C_PREMIUM_HAZARD` | standard | `quantitative` | `value`, `covered_employee_groups` | Premium pay for hazardous, difficult, dirty, or unusually risky work. |
| `C_WAGE_INCREASE` | standard | `complex` | `values[]`, `flags.has_wage_increase`, `flags.percentage_based`, `flags.flat_amount_based`, `flags.has_effective_dates`, `flags.across_the_board`, `effective_dates`, `covered_employee_groups` | Wage increases, raise schedules, or adjustments for covered employees. |
| `C_WAGE_LONGEVITY` | standard | `complex` | `values[]`, `flags.has_longevity_pay`, `flags.service_based`, `flags.has_steps`, `flags.flat_amount_based`, `flags.percentage_based`, `service_band_names`, `covered_employee_groups` | Additional pay based on length of service or longevity milestones. |
| `C_WAGE_MERIT_STEP` | standard | `complex` | `values[]`, `flags.has_merit_step`, `flags.performance_based`, `flags.has_step_schedule`, `flags.discretionary`, `flags.has_review_process` | Merit, performance, review, or discretionary step-advancement pay systems. |
| `C_WAGE_SAVINGS` | standard | `quantitative` | `value` | Employer contributions to savings, deferred compensation, or similar wage-related accounts. |
| `C_WAGE_VACATION_SUPP` | standard | `quantitative` | `value` | Vacation, supplemental dues, or comparable wage-related contribution benefits. |
| `C_WAGE_ACCRUAL_VACATION` | standard | `quantitative` | `value`, `covered_employee_groups` | Vacation or holiday pay accruals calculated from hours, wages, or service. |
| `C_PREMIUM_LEADMAN` | standard | `quantitative` | `value`, `classification_names` | Premium pay for lead workers, leadmen, or similar work-direction roles. |
| `C_PREMIUM_GROUP_LEADER` | standard | `complex` | `values[]`, `flags.has_group_leader_premium`, `flags.tiered_premium`, `flags.flat_amount_based`, `flags.has_role_premium` | Premium pay for group leaders, crew leaders, or similar tiered responsibility roles. |
| `C_WAGE_INCENTIVE` | standard | `complex` | `values[]`, `flags.has_incentive_pay`, `flags.performance_based`, `flags.percentage_based`, `flags.has_cap`, `flags.has_bonus_components` | Incentive, bonus, performance, gainsharing, or productivity-based pay. |
| `C_PREMIUM_STANDBY` | standard | `binary` | None beyond `exists` and `summarize` | Standby availability requirements and related rights or compensation. |

### Disputes

| Concept ID | Priority/Rank | Format | Attributes | Description |
|---|---:|---|---|---|
| `C_GRIEVANCE_PROCEDURE` | core / 3 | `complex` | `values[]`, `flags.has_grievance_steps`, `flags.has_deadlines`, `flags.has_union_representation`, `flags.has_written_grievance`, `flags.has_management_response`, `eligible_filers`, `excluded_claim_types`, `deadline_terms` | Procedures for filing, processing, and resolving contractual grievances. |
| `C_ARBITRATION` | core / 3 | `complex` | `values[]`, `flags.has_arbitration`, `flags.final_and_binding`, `flags.has_neutral_arbitrator`, `flags.has_shared_costs`, `flags.limits_arbitrator_authority`, `arbitrator_selection_terms`, `excluded_claim_types`, `remedy_limit_terms` | Rules for referring unresolved disputes to arbitration and defining arbitral authority. |
| `C_DISCIPLINE_JUST_CAUSE` | core / 10 | `complex` | `values[]`, `flags.has_just_cause_standard`, `flags.covers_discipline`, `flags.covers_discharge`, `flags.has_hearing_right`, `flags.has_investigatory_right`, `flags.has_probation_exception`, `flags.has_progressive_discipline`, `covered_employee_groups`, `excluded_employee_groups` | Just-cause standards and substantive protections against discipline or discharge. |
| `C_DISCIPLINE_PROGRESSIVE` | standard | `complex` | `values[]`, `flags.has_progressive_discipline`, `flags.has_warnings`, `flags.has_notice_requirement`, `flags.has_suspension_step`, `flags.has_discharge_step` | Progressive discipline steps, warnings, notice, suspension, and discharge sequencing. |
| `C_DISCIPLINE_INVESTIGATION_APPEAL` | standard | `complex` | `values[]`, `flags.has_appeal_right`, `flags.has_investigation_procedure`, `flags.has_record_removal`, `flags.has_union_representation`, `flags.has_deadline` | Investigation, appeal, representation, deadline, and record-removal rights in discipline matters. |
| `C_DISCIPLINE_PROBATION` | advanced | `complex` | `values[]`, `flags.has_probation_period`, `flags.has_transfer_probation`, `flags.has_shortened_discipline_rights`, `flags.has_completion_rule`, `probationary_group_names` | Probationary period rules and exceptions to ordinary discipline or grievance protections. |

### Leave

| Concept ID | Priority/Rank | Format | Attributes | Description |
|---|---:|---|---|---|
| `C_LEAVE_HOLIDAYS` | core / 11 | `complex` | `values[]`, `flags.has_paid_holidays`, `flags.has_holiday_premium_pay`, `flags.has_floating_holidays`, `flags.has_observed_holidays` | Paid holidays, holiday observance rules, and holiday premium pay. |
| `C_LEAVE_VACATION` | core / 8 | `complex` | `values[]`, `flags.has_paid_vacation`, `flags.accrues_with_service`, `flags.has_cashout`, `flags.has_scheduling_rules`, `flags.has_vacation_fund`, `service_band_names`, `eligible_employee_groups` | Vacation entitlement, accrual, scheduling, carryover, and payout rules. |
| `C_LEAVE_SICK` | core / 14 | `complex` | `values[]`, `flags.has_paid_sick_leave`, `flags.accrues_with_service`, `flags.has_carryover`, `flags.has_cashout`, `flags.has_medical_certification_requirement`, `eligible_employee_groups` | Paid sick leave entitlement, accrual, carryover, use, certification, and payout rules. |
| `C_LEAVE_PERSONAL_MISC` | standard | `quantitative` | `value` | Miscellaneous personal or compassionate leave entitlements not captured elsewhere. |
| `C_LEAVE_PARENTAL_FAMILY` | standard | `complex` | `values[]`, `flags.has_parental_leave`, `flags.has_family_leave`, `flags.paid`, `flags.has_fmla_reference`, `flags.has_job_protection` | Parental, family, caregiving, or statutory family-leave rights and protections. |
| `C_LEAVE_BEREAVEMENT` | standard | `quantitative` | `value` | Bereavement leave entitlement, pay status, duration, and covered family relationships. |
| `C_LEAVE_PERSONAL` | standard | `quantitative` | `value` | Personal leave, attendance days, floating leave, or comparable discretionary paid time off. |
| `C_LEAVE_SUBSISTENCE` | standard | `quantitative` | `value`, `geographic_areas` | Subsistence, travel, meal, lodging, or expense allowances associated with work location. |
| `C_LEAVE_JURY_DUTY` | standard | `quantitative` | `value` | Jury duty or civic duty leave entitlement and pay treatment. |

### Recognition

| Concept ID | Priority/Rank | Format | Attributes | Description |
|---|---:|---|---|---|
| `C_UNION_ACCESS_BUSINESS` | advanced | `complex` | `values[]`, `flags.has_steward_access`, `flags.has_union_business_time`, `flags.has_bulletin_board_rights`, `flags.has_meeting_rights`, `flags.has_paid_union_time` | Union representative access, union business time, communications, and meeting rights. |
| `C_UNION_SECURITY_DUES_CHECKOFF` | conditional_core / 15 | `complex` | `values[]`, `flags.has_dues_checkoff`, `flags.has_union_security`, `flags.has_agency_shop`, `flags.has_remittance_deadline`, `flags.has_authorization_requirement` | Union-security and dues-checkoff rules, including payroll deduction requirements. |
| `C_RECOGNITION_COVERAGE_SCOPE` | core / 4 | `complex` | `values[]`, `flags.has_bargaining_unit_scope`, `flags.excludes_supervisors`, `flags.excludes_confidential_employees`, `flags.has_accretion_language`, `bargaining_unit_descriptions`, `included_employee_groups`, `excluded_employee_groups` | Recognition clause defining the bargaining unit, covered employees, and exclusions. |
| `C_HIRING_HALL_DISPATCH` | standard | `complex` | `values[]`, `flags.has_hiring_hall`, `flags.has_dispatch_rules`, `flags.has_referral_priority`, `flags.union_operated`, `flags.has_registration_list` | Hiring hall, dispatch, referral, registration, and priority-of-referral rules. |
| `C_UNION_SECURITY` | standard | `binary` | `excluded_employee_groups` | Union membership, agency-shop, maintenance-of-membership, or related union-security obligations. |
| `C_UNION_DUES_CHECKOFF` | standard | `complex` | `values[]`, `flags.has_dues_checkoff`, `flags.has_remittance_deadline`, `flags.has_authorization_requirement`, `flags.percentage_based`, `flags.flat_amount_based` | Payroll deduction, remittance, authorization, or administration of union dues and fees. |

### Healthcare

| Concept ID | Priority/Rank | Format | Attributes | Description |
|---|---:|---|---|---|
| `C_HEALTH_MEDICAL_ACTIVE_CONTRIBUTION` | core / 6 | `quantitative` | `value`, `coverage_tiers`, `eligible_employee_groups` | Employer or employee contributions toward active employee medical coverage. |
| `C_HEALTH_DENTAL` | standard | `complex` | `values[]`, `flags.includes_dental`, `flags.employer_paid`, `flags.employee_paid`, `flags.includes_dependent_coverage`, `flags.has_waiting_period`, `coverage_tiers`, `eligible_employee_groups` | Dental insurance coverage, eligibility, contribution, and dependent-coverage terms. |
| `C_HEALTH_MEDICAL_ACTIVE` | standard | `complex` | `values[]`, `flags.includes_medical`, `flags.includes_dependent_coverage`, `flags.employer_paid`, `flags.employee_paid`, `flags.has_external_plan`, `coverage_tiers`, `eligible_employee_groups` | Active employee medical coverage, eligibility, premium sharing, and plan participation. |
| `C_HEALTH_LIFE_AD_D` | standard | `complex` | `values[]`, `flags.includes_life_insurance`, `flags.includes_add`, `flags.employer_paid`, `flags.employee_paid`, `flags.includes_dependent_coverage`, `coverage_tiers`, `eligible_employee_groups` | Life insurance and accidental death or dismemberment benefits for covered employees. |
| `C_HEALTH_MEDICAL_ACTIVE_PLAN_DESIGN` | advanced | `complex` | `values[]`, `flags.includes_medical`, `flags.has_deductible`, `flags.has_copay`, `flags.has_out_of_pocket_maximum`, `flags.has_coverage_tiers`, `flags.has_network_rules`, `coverage_tiers` | Active medical plan design features such as deductibles, copays, networks, and coverage tiers. |
| `C_HEALTH_DISABILITY_INCOME` | standard | `complex` | `values[]`, `flags.includes_disability`, `flags.has_short_term_disability`, `flags.has_long_term_disability`, `flags.employer_paid`, `flags.wage_replacement_based`, `flags.has_waiting_period`, `waiting_period_terms` | Disability income or wage-replacement benefits for short- or long-term disability. |
| `C_HEALTH_RETIREE` | standard | `complex` | `values[]`, `flags.includes_retiree_coverage`, `flags.employer_paid`, `flags.employee_paid`, `flags.includes_dependent_coverage`, `flags.has_eligibility_requirement`, `eligible_retiree_groups` | Retiree health coverage, retiree eligibility, dependent coverage, and contribution rules. |
| `C_HEALTH_VISION` | standard | `complex` | `values[]`, `flags.includes_vision`, `flags.employer_paid`, `flags.employee_paid`, `flags.includes_dependent_coverage`, `flags.has_waiting_period`, `coverage_tiers`, `eligible_employee_groups` | Vision insurance coverage, eligibility, contribution, and dependent-coverage terms. |
| `C_HEALTH_EMPLOYER_CONTRIBUTION` | standard | `quantitative` | `value`, `coverage_tiers`, `eligible_employee_groups` | Employer contributions toward health coverage or health benefit funds. |
| `C_HEALTH_ACTIVE` | standard | `complex` | `values[]`, `flags.includes_medical`, `flags.includes_dental`, `flags.includes_vision`, `flags.employer_paid`, `flags.employee_paid`, `flags.has_external_trust`, `coverage_tiers`, `eligible_employee_groups` | Active employee health benefits across medical, dental, vision, or welfare coverage. |
| `C_HEALTH_LIFE_INSURANCE` | standard | `binary` | `coverage_tiers`, `eligible_employee_groups` | Life insurance benefits and eligibility for covered employees or dependents. |
| `C_HEALTH_ACTIVE_CONTRIBUTION` | standard | `quantitative` | `value`, `coverage_tiers`, `eligible_employee_groups` | Contribution amounts or formulas for active employee health benefits. |
| `C_HEALTH_EXTERNAL_FUND` | standard | `complex` | `values[]`, `flags.has_external_fund`, `flags.employer_contribution`, `flags.employee_contribution`, `flags.trustee_administered`, `flags.includes_health_welfare` | External health, welfare, or benefit funds and related contribution or administration rules. |
| `C_HEALTH_ACTIVE_PLAN_DESIGN` | standard | `complex` | `values[]`, `flags.includes_medical`, `flags.has_deductible`, `flags.has_copay`, `flags.has_out_of_pocket_maximum`, `flags.has_network_rules`, `flags.includes_dental`, `coverage_tiers` | Active health plan design terms, including cost sharing, networks, and coverage tiers. |
| `C_HEALTH_PLAN_DESIGN` | standard | `complex` | `values[]`, `flags.includes_medical`, `flags.has_plan_options`, `flags.has_deductible`, `flags.has_copay`, `flags.has_out_of_pocket_maximum`, `flags.has_premium_share`, `coverage_tiers` | Health plan design features such as options, cost sharing, coverage tiers, and premiums. |
| `C_HEALTH_INSURANCE_BUYOUT` | standard | `quantitative` | `value`, `eligible_employee_groups` | Cash or benefit incentives for waiving employer health insurance coverage. |
| `C_HEALTH_WELFARE_FUND` | standard | `quantitative` | `value` | Health and welfare fund contributions or benefit-fund participation. |
| `C_HEALTH_DISABILITY` | standard | `quantitative` | `value`, `waiting_period_terms` | Disability benefits, wage replacement, waiting periods, and maximum benefit duration. |
| `C_HEALTH_PRESCRIPTION_DRUG` | standard | `complex` | `values[]`, `flags.includes_prescription_drug`, `flags.has_copay`, `flags.has_tiers`, `flags.mail_order_included`, `flags.generic_required` | Prescription drug coverage, formularies, copays, tiers, or mail-order benefits. |
| `C_HEALTH_BENEFITS` | standard | `binary` | `coverage_tiers`, `eligible_employee_groups` | General health and welfare benefits not limited to a single benefit type. |

### Safety

| Concept ID | Priority/Rank | Format | Attributes | Description |
|---|---:|---|---|---|
| `C_SAFETY_PPE_UNSAFE_WORK` | core / 12 | `complex` | `values[]`, `flags.has_ppe_requirement`, `flags.has_unsafe_work_right`, `flags.has_safety_standards`, `flags.has_hazard_response`, `flags.has_safety_committee` | Safety protections, PPE obligations, hazard response, and unsafe-work rights. |
| `C_LABOR_MANAGEMENT_COMMITTEE` | advanced | `binary` | None beyond `exists` and `summarize` | Joint labor-management committees for cooperation, safety, operations, or dispute prevention. |
| `C_SAFETY_ASSAULT_VIOLENCE` | standard | `complex` | `values[]`, `flags.has_assault_policy`, `flags.has_violence_response`, `flags.has_paid_release`, `flags.has_response_team`, `flags.has_reporting_requirement` | Workplace violence, assault, abuse, reporting, response, and paid-release protections. |
| `C_SAFETY_DRUG_TESTING` | standard | `complex` | `values[]`, `flags.has_drug_testing`, `flags.accident_triggered`, `flags.reasonable_suspicion_based`, `flags.random_testing`, `flags.has_discipline_consequence`, `consequence_terms` | Drug or alcohol testing rules, triggers, procedures, and consequences. |

### Ancillary

| Concept ID | Priority/Rank | Format | Attributes | Description |
|---|---:|---|---|---|
| `C_RETIREMENT_PENSION` | core / 7 | `complex` | `values[]`, `flags.has_defined_benefit_pension`, `flags.has_employer_contribution`, `flags.has_employee_contribution`, `flags.has_vesting_requirement`, `flags.has_external_fund`, `eligible_employee_groups`, `vesting_terms` | Pension or retirement plan eligibility, participation, contributions, and vesting. |
| `C_RETIREMENT_SAVINGS_ANNUITY` | standard | `quantitative` | `value`, `eligible_employee_groups`, `vesting_terms` | Savings, annuity, or defined-contribution retirement benefits and contributions. |
| `C_TRAINING_TUITION_CERTIFICATION` | standard | `complex` | `values[]`, `flags.has_training_benefit`, `flags.has_tuition_reimbursement`, `flags.has_certification_support`, `flags.employer_paid`, `flags.has_professional_development`, `eligible_employee_groups` | Training, tuition assistance, certification support, or professional development benefits. |
| `C_LEGAL_SERVICES_FUND` | standard | `quantitative` | `value` | Legal-services benefit funds or legal assistance benefits for covered employees. |
| `C_RETIREMENT_INCENTIVE` | standard | `complex` | `values[]`, `flags.has_retirement_bonus`, `flags.service_based`, `flags.date_based`, `flags.has_age_requirement`, `flags.has_notice_requirement`, `eligible_employee_groups`, `effective_dates` | Retirement incentives, bonuses, or enhanced benefits tied to retirement timing or eligibility. |
| `C_CHILD_DEPENDENT_CARE` | standard | `quantitative` | `value`, `eligible_dependent_terms` | Child care, dependent care, or related assistance benefits. |
| `C_TRANSIT_COMMUTER_BENEFIT` | standard | `quantitative` | `value` | Transit, commuting, parking, or transportation subsidy benefits. |

### Security

| Concept ID | Priority/Rank | Format | Attributes | Description |
|---|---:|---|---|---|
| `C_JOB_SECURITY_LAYOFF_ORDER` | core / 5 | `complex` | `values[]`, `flags.has_layoff_notice`, `flags.seniority_based`, `flags.has_bumping_rights`, `flags.has_inverse_seniority_order`, `flags.has_union_notice`, `affected_employee_groups`, `exception_terms` | Rules determining layoff order, notice, seniority application, and displacement rights. |
| `C_JOB_SECURITY_RECALL` | core / 5 | `complex` | `values[]`, `flags.has_recall_rights`, `flags.seniority_based`, `flags.has_recall_period_limit`, `flags.has_recall_notice`, `flags.has_preference_over_new_hires`, `affected_employee_groups`, `exception_terms` | Recall rights, recall order, notice, duration, and preference after layoff. |
| `C_JOB_SECURITY_SEVERANCE` | advanced | `complex` | `values[]`, `flags.has_severance_pay`, `flags.service_based`, `flags.wage_based`, `flags.has_layoff_trigger`, `flags.has_maximum_duration`, `eligible_employee_groups` | Severance pay or income protection triggered by layoff, displacement, or separation. |
| `C_JOB_SECURITY_BENEFIT_CONTINUATION` | standard | `complex` | `values[]`, `flags.has_benefit_continuation`, `flags.includes_health_continuation`, `flags.includes_life_insurance_continuation`, `flags.applies_during_leave`, `flags.employer_paid`, `eligible_employee_groups` | Continuation of benefits during layoff, leave, disability, or other employment interruptions. |
| `C_SUBCONTRACTING_WORK_PRESERVATION` | standard | `complex` | `values[]`, `flags.limits_subcontracting`, `flags.has_work_preservation`, `flags.requires_union_notice`, `flags.allows_union_matching`, `flags.protects_bargaining_unit_work`, `protected_work_terms`, `subcontracting_exception_terms`, `notice_recipient_names` | Restrictions on subcontracting, non-unit work, and preservation of bargaining-unit work. |
| `C_SENIORITY_SYSTEM` | core / 9 | `complex` | `values[]`, `flags.has_seniority_system`, `flags.classification_based`, `flags.plantwide_seniority`, `flags.has_tie_breaker`, `flags.affects_layoff`, `seniority_type_names`, `seniority_group_names`, `classification_names`, `break_in_service_terms`, `tie_breaker_terms` | Seniority definitions and rules affecting rights such as layoff, recall, bidding, and scheduling. |
| `C_JOB_POSTING_BIDDING_TRANSFER` | standard | `complex` | `values[]`, `flags.has_job_posting`, `flags.has_bidding_rights`, `flags.has_transfer_rights`, `flags.seniority_based`, `flags.has_trial_period`, `bidding_unit_names`, `eligible_employee_groups`, `trial_period_terms` | Job posting, bidding, promotion, transfer, trial-period, and selection rights. |
| `C_JOB_SECURITY_LAYOFF_RECALL` | standard | `complex` | `values[]`, `flags.has_layoff_procedure`, `flags.has_recall_rights`, `flags.seniority_based`, `flags.has_bumping_rights`, `flags.has_notice_requirement`, `affected_employee_groups`, `exception_terms` | Combined layoff and recall procedures, including seniority, notice, bumping, and recall rights. |
| `C_JOB_SECURITY_SUB_INCOME_BRIDGE` | standard | `complex` | `values[]`, `flags.has_sub_income_benefit`, `flags.wage_replacement_based`, `flags.service_based`, `flags.has_external_fund`, `flags.has_duration_limit`, `eligible_employee_groups` | Supplemental unemployment, bridge income, or wage-replacement benefits after job loss. |
| `C_JOB_SECURITY_LAYOFF` | standard | `quantitative` | `value`, `affected_employee_groups`, `exception_terms` | Layoff-related pay, dismissal pay, or benefits triggered by non-reengagement or separation. |
| `C_JOB_SECURITY_SENIORITY` | standard | `complex` | `values[]`, `flags.has_seniority_groups`, `flags.classification_based`, `flags.affects_layoff`, `flags.affects_recall`, `flags.affects_bidding`, `seniority_type_names`, `seniority_group_names`, `classification_names`, `break_in_service_terms`, `tie_breaker_terms` | Seniority rules specifically governing job-security outcomes such as layoff, recall, or bidding. |
| `C_LIGHT_DUTY_ACCOMMODATION` | standard | `complex` | `values[]`, `flags.has_light_duty`, `flags.has_accommodation_process`, `flags.has_pay_protection`, `flags.disability_related`, `flags.has_medical_clearance`, `eligible_employee_groups` | Light-duty, modified-duty, accommodation, medical-clearance, or pay-protection rules. |
| `C_JOB_SECURITY_SUBCONTRACTING` | standard | `binary` | `protected_work_terms`, `subcontracting_exception_terms`, `notice_recipient_names` | Employer subcontracting rights or limits and any related notice or bargaining protections. |
| `C_JOB_SECURITY_RIF_LAYOFF` | standard | `complex` | `values[]`, `flags.has_rif_procedure`, `flags.has_layoff_order`, `flags.seniority_based`, `flags.classification_based`, `flags.has_recall_pool`, `affected_employee_groups`, `exception_terms` | Reduction-in-force or layoff procedures, including order, seniority, and recall pools. |
| `C_JOB_SECURITY_BUMPING` | advanced / 5 | `binary` | `affected_employee_groups`, `exception_terms` | Bumping or displacement rights allowing employees to claim other positions during layoffs. |
| `C_JOB_SECURITY_NO_CONTRACTING_OUT` | standard | `binary` | `protected_work_terms`, `subcontracting_exception_terms`, `notice_recipient_names` | Limits on contracting out work normally performed by bargaining-unit employees. |

### Scheduling

| Concept ID | Priority/Rank | Format | Attributes | Description |
|---|---:|---|---|---|
| `C_TIME_REGULAR_SCHEDULE` | standard | `complex` | `values[]`, `flags.has_regular_hours`, `flags.has_workweek_definition`, `flags.has_shift_schedule`, `flags.has_flexible_schedule`, `flags.has_guaranteed_hours`, `covered_employee_groups` | Regular workday, workweek, shift, and guaranteed-hour scheduling rules. |
| `C_TIME_REST_MEAL_PERIODS` | standard | `complex` | `values[]`, `flags.has_rest_periods`, `flags.has_meal_periods`, `flags.has_paid_breaks`, `flags.has_relief_breaks`, `flags.has_missed_break_premium`, `exception_terms` | Rest breaks, meal periods, relief breaks, paid-break rules, and missed-break remedies. |
| `C_WORKLOAD_CLASS_SIZE_STAFFING` | standard | `complex` | `values[]`, `flags.has_class_size_limit`, `flags.has_staffing_ratio`, `flags.has_preparation_period`, `flags.has_duty_free_lunch`, `flags.has_voluntary_extracurricular`, `staffing_ratio_terms`, `duty_terms` | Workload, class-size, staffing-ratio, preparation-time, or duty-assignment protections. |
| `C_TIME_SCHEDULE_NOTICE_CHANGE` | standard | `quantitative` | `value`, `notice_trigger_terms`, `affected_employee_groups` | Advance notice requirements and remedies for schedule changes or cancellations. |
| `C_TIME_NO_CANCELLATION_SECURITY` | standard | `complex` | `values[]`, `flags.has_no_cancellation_rule`, `flags.has_involuntary_leave_limit`, `flags.has_pay_protection`, `flags.has_schedule_security`, `affected_employee_groups` | Schedule-security protections limiting cancellations, involuntary leave, or lost pay. |

## Ranked Core Families

The deep research workflow ranked target families by importance for common CBA comparison. These priorities determine the `meta.priority_tier`, `meta.rank`, and related metadata on each provision class.

- `C_WAGE_BASE_RATE`: core, rank 1, score 98, difficulty medium. Family: `base_wage_schedule`. Core pay tables, classifications, steps, and rates.
- `C_PREMIUM_OVERTIME`: core, rank 2, score 96, difficulty medium. Family: `overtime_and_premium_pay`. Overtime triggers, thresholds, multipliers, and stacking rules.
- `C_ARBITRATION`: core, rank 3, score 95, difficulty high. Family: `grievance_arbitration`. Procedural backbone for contract enforcement.
- `C_GRIEVANCE_PROCEDURE`: core, rank 3, score 95, difficulty high. Family: `grievance_arbitration`. Procedural backbone for contract enforcement.
- `C_RECOGNITION_COVERAGE_SCOPE`: core, rank 4, score 94, difficulty low. Family: `recognition_bargaining_unit`. Defines covered employees and exclusions for downstream provisions.
- `C_JOB_SECURITY_BUMPING`: advanced, rank 5, score 92, difficulty high. Family: `layoff_recall_bumping`. Advanced subcomponent of the layoff/recall family.
- `C_JOB_SECURITY_LAYOFF_ORDER`: core, rank 5, score 92, difficulty high. Family: `layoff_recall_bumping`. Workforce reduction order, notice, and displacement rules.
- `C_JOB_SECURITY_RECALL`: core, rank 5, score 92, difficulty high. Family: `layoff_recall_bumping`. Recall rights for laid-off workers.
- `C_HEALTH_MEDICAL_ACTIVE_CONTRIBUTION`: core, rank 6, score 91, difficulty medium. Family: `health_insurance_employer_contribution`. Employer/employee medical premium shares and contributions.
- `C_RETIREMENT_PENSION`: core, rank 7, score 89, difficulty medium. Family: `pension_retirement_contribution`. Retirement plan eligibility and contribution terms.
- `C_LEAVE_VACATION`: core, rank 8, score 88, difficulty medium. Family: `paid_vacation`. Vacation entitlement, accrual, service tiers, and scheduling.
- `C_SENIORITY_SYSTEM`: core, rank 9, score 87, difficulty high. Family: `seniority`. Connective rule for layoff, recall, bidding, vacation, and overtime.
- `C_DISCIPLINE_JUST_CAUSE`: core, rank 10, score 86, difficulty high. Family: `just_cause_discipline_discharge`. Discipline/discharge standard central to grievance and arbitration.
- `C_LEAVE_HOLIDAYS`: core, rank 11, score 84, difficulty low. Family: `paid_holidays`. Holiday list, observed rules, eligibility, and premium pay.
- `C_SAFETY_PPE_UNSAFE_WORK`: core, rank 12, score 83, difficulty medium. Family: `safety_ppe_training`. Safety duties, PPE, unsafe-work rights, and hazard response.
- `C_LEAVE_SICK`: core, rank 14, score 80, difficulty medium. Family: `sick_leave_paid_leave_bank`. Sick leave accrual, caps, usage rules, and payout.
- `C_UNION_SECURITY_DUES_CHECKOFF`: conditional_core, rank 15, score 75, difficulty low. Family: `dues_checkoff_union_security`. Jurisdiction-conditional dues deduction and union-security terms.
- `C_DISCIPLINE_PROBATION`: advanced, unranked, difficulty medium. Family: `probationary_period`. Valuable next-module discipline provision.
- `C_HEALTH_MEDICAL_ACTIVE_PLAN_DESIGN`: advanced, unranked, difficulty medium. Family: `active_medical_plan_design`. Demoted because detailed plan terms may live outside the CBA.
- `C_JOB_SECURITY_SEVERANCE`: advanced, unranked, difficulty medium. Family: `severance`. Valuable next-module job-security provision.
- `C_LABOR_MANAGEMENT_COMMITTEE`: advanced, unranked, difficulty low. Family: `labor_management_committee`. Optional governance provision, not a substitute for grievance machinery.
- `C_PREMIUM_SHIFT`: advanced, unranked, difficulty medium. Family: `shift_differential`. Valuable next-module premium-pay provision.
- `C_PREMIUM_STANDBY_ON_CALL`: advanced, unranked, difficulty medium. Family: `standby_on_call_pay`. Valuable next-module premium-pay provision.
- `C_UNION_ACCESS_BUSINESS`: advanced, unranked, difficulty medium. Family: `union_business_access`. Useful next-module provision for union capacity and access.

## Document-Level Metadata Still Needed

The agreement term, effective dates, expiration date, reopeners, and amendment dates should be modeled as document-level metadata rather than repeated provision fields. Those values are central for time comparisons, but they should be extracted once per agreement and then joined to provision-level attributes.
