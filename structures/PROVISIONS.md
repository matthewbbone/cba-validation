# Provision Structures for Deterministic CBA Extraction

This project compares LLM and human extractions from collective bargaining agreements by converting provision text into deterministic attributes. Every provision extraction includes `exists` and `summarize`; comparison should otherwise rely on booleans, numeric values, durations, money amounts, percentages, multipliers, and the small set of retained string-list attributes that affect generosity or comparability.

## Attribute Policy

Provision attributes should be directly verifiable from the CBA. Numeric and boolean attributes are preferred. String-list attributes are retained only when the literal surface form changes how generosity should be compared, such as covered groups, excluded groups, bargaining-unit scope, classifications, effective dates, concrete thresholds, deadlines, waiting periods, exceptions, or similar rule boundaries.

Do not add string attributes merely to capture labels. Plan names, fund names, certification names, step names, program names, union names, forum names, committee names, and broad eligibility prose are intentionally excluded unless a future schema normalizes them into categorical or numeric comparison fields.

## Provision Concepts by Dictionary Category

### Compensation

| Concept ID | Priority/Rank | Format | Attributes | Description |
|---|---:|---|---|---|
| `C_WAGE_BASE_RATE` | core / 1 | `complex` | `values[]`, `flags.has_base_rate`, `flags.has_rate_table`, `flags.has_classification_rates`, `flags.has_step_rates`, `flags.has_salary_rates`, `flags.has_hourly_rates`, `occupation_names`, `classification_names`, `geographic_areas`, `effective_dates` | Base wage or salary rate |
| `C_PREMIUM_OVERTIME` | core / 2 | `complex` | `values[]`, `flags.has_overtime_threshold`, `flags.has_daily_overtime`, `flags.has_weekly_overtime`, `flags.has_premium_multiplier`, `flags.has_double_time`, `trigger_terms`, `covered_employee_groups`, `excluded_employee_groups` | Overtime eligibility thresholds and multipliers |
| `C_WAGE_INCREASES_COLA` | standard | `complex` | `values[]`, `flags.has_scheduled_increases`, `flags.has_cola`, `flags.has_lump_sum_adjustment`, `flags.has_across_the_board_increase`, `effective_dates`, `covered_employee_groups` | Annual wage increases: $0.25/hr for time workers (12/17/01, 12/16/02, 12/15/03); $0.25/hr equivalent for piece workers |
| `C_PREMIUM_CALL_IN_REPORTING` | standard | `complex` | `values[]`, `flags.has_call_in_pay`, `flags.has_call_back_pay`, `flags.has_reporting_pay`, `flags.has_minimum_pay_guarantee`, `trigger_terms`, `covered_employee_groups` | Call-in, call-back, reporting, and minimum-pay guarantees |
| `C_PREMIUM_SHIFT` | advanced | `quantitative` | `value`, `covered_employee_groups` | Shift differentials and night/weekend premiums |
| `C_WAGE_PROGRESSION` | standard | `complex` | `values[]`, `flags.has_step_progression`, `flags.has_classification_movement`, `flags.has_seniority_progression`, `flags.has_training_progression`, `flags.has_automatic_progression`, `classification_names`, `occupation_names`, `effective_dates` | Wage progression, steps, and classification movement |
| `C_PREMIUM_RESPONSIBILITY_SPECIALTY` | standard | `complex` | `values[]`, `flags.has_responsibility_premium`, `flags.has_higher_classification_premium`, `flags.has_specialty_premium`, `flags.has_translation_premium`, `flags.has_role_premium`, `classification_names`, `specialty_names` | Responsibility, higher-classification, specialty, translation, flight, or role premiums |
| `C_PREMIUM_STANDBY_ON_CALL` | advanced | `quantitative` | `value`, `covered_employee_groups` | Standby pay |
| `C_UNIFORM_CLOTHING_ALLOWANCE` | standard | `quantitative` | `value`, `covered_employee_groups` | Safety shoe program: 100% cost for Wood Processing/Pulp Mill employees; up to $110 reimbursement for others |
| `C_PREMIUM_ZONE_SUBSISTENCE` | standard | `complex` | `values[]`, `flags.has_zone_pay`, `flags.has_travel_subsistence`, `flags.has_remote_site_allowance`, `flags.distance_based`, `flags.overnight_based`, `geographic_areas` | Zone pay, travel subsistence, and remote-site allowances |
| `C_WAGE_GENERAL_INCREASE` | standard | `complex` | `values[]`, `flags.has_general_increase`, `flags.percentage_based`, `flags.flat_amount_based`, `flags.has_effective_dates`, `flags.across_the_board`, `effective_dates`, `covered_employee_groups` | Scale increase: 2.5% in year 2 (2/16/2003), 3.5% in year 3 (2/15/2004) |
| `C_WAGE_APPRENTICE` | standard | `complex` | `values[]`, `flags.has_apprentice_scale`, `flags.percentage_of_journeyman`, `flags.has_periods`, `flags.has_step_progression`, `flags.hours_based`, `classification_names` | Apprentice wage schedule 40-82% of JW over 7 periods |
| `C_WAGE_SCHEDULED_INCREASE` | standard | `complex` | `values[]`, `flags.has_scheduled_increases`, `flags.service_based`, `flags.longevity_based`, `flags.has_effective_dates`, `flags.flat_amount_based`, `effective_dates`, `service_band_names` | Longevity pay — $0.10/hr at 10yr through $0.25/hr at 25yr |
| `C_PREMIUM_SUNDAY_HOLIDAY` | standard | `complex` | `values[]`, `flags.has_sunday_premium`, `flags.has_holiday_premium`, `flags.has_double_time`, `flags.has_sixth_day_premium`, `flags.has_seventh_day_premium` | 6th and 7th day in workweek — 1.5x (150%); 6 legal holidays — 2.0x |
| `C_PREMIUM_FOREMAN` | standard | `quantitative` | `value`, `classification_names` | Foreman and General Foreman premium |
| `C_PREMIUM_HAZARD` | standard | `quantitative` | `value`, `covered_employee_groups` | Hazardous work differential — 15% above classification rate |
| `C_WAGE_INCREASE` | standard | `complex` | `values[]`, `flags.has_wage_increase`, `flags.percentage_based`, `flags.flat_amount_based`, `flags.has_effective_dates`, `flags.across_the_board`, `effective_dates`, `covered_employee_groups` | Annual wage increases: $0.50 3/1/2001, $0.50 9/2/2002, $1.00 3/1/2004 |
| `C_WAGE_LONGEVITY` | standard | `complex` | `values[]`, `flags.has_longevity_pay`, `flags.service_based`, `flags.has_steps`, `flags.flat_amount_based`, `flags.percentage_based`, `service_band_names`, `covered_employee_groups` | Longevity pay |
| `C_WAGE_MERIT_STEP` | standard | `complex` | `values[]`, `flags.has_merit_step`, `flags.performance_based`, `flags.has_step_schedule`, `flags.discretionary`, `flags.has_review_process` | Step advancement on salary schedule |
| `C_WAGE_SAVINGS` | standard | `quantitative` | `value` | Savings/deferred compensation contribution |
| `C_WAGE_VACATION_SUPP` | standard | `quantitative` | `value` | Vacation/Supplemental dues contribution $2.95/hr |
| `C_WAGE_ACCRUAL_VACATION` | standard | `quantitative` | `value`, `covered_employee_groups` | Vacation/holiday pay accrual ($0.50/hr) |
| `C_PREMIUM_LEADMAN` | standard | `quantitative` | `value`, `classification_names` | Leadman premium — $2.00/hr |
| `C_PREMIUM_GROUP_LEADER` | standard | `complex` | `values[]`, `flags.has_group_leader_premium`, `flags.tiered_premium`, `flags.flat_amount_based`, `flags.has_role_premium` | Group leader premium $1.20/$0.80/$0.40 per hour by tier |
| `C_WAGE_INCENTIVE` | standard | `complex` | `values[]`, `flags.has_incentive_pay`, `flags.performance_based`, `flags.percentage_based`, `flags.has_cap`, `flags.has_bonus_components` | Incentive pay: up to 5% company performance + 5% cell bonus + 5% stretch targets = max 15% of annual base salary |
| `C_PREMIUM_STANDBY` | standard | `binary` | None beyond `exists` and `summarize` | Standby provision — reachable by signal device; 1-hour response time |

### Disputes

| Concept ID | Priority/Rank | Format | Attributes | Description |
|---|---:|---|---|---|
| `C_GRIEVANCE_PROCEDURE` | core / 3 | `complex` | `values[]`, `flags.has_grievance_steps`, `flags.has_deadlines`, `flags.has_union_representation`, `flags.has_written_grievance`, `flags.has_management_response`, `eligible_filers`, `excluded_claim_types`, `deadline_terms` | Grievance steps, timelines, representation, and scope |
| `C_ARBITRATION` | core / 3 | `complex` | `values[]`, `flags.has_arbitration`, `flags.final_and_binding`, `flags.has_neutral_arbitrator`, `flags.has_shared_costs`, `flags.limits_arbitrator_authority`, `arbitrator_selection_terms`, `excluded_claim_types`, `remedy_limit_terms` | Arbitration access, selection, authority, costs, and finality |
| `C_DISCIPLINE_JUST_CAUSE` | core / 10 | `complex` | `values[]`, `flags.has_just_cause_standard`, `flags.covers_discipline`, `flags.covers_discharge`, `flags.has_hearing_right`, `flags.has_investigatory_right`, `flags.has_probation_exception`, `flags.has_progressive_discipline`, `covered_employee_groups`, `excluded_employee_groups` | Just cause and substantive discipline/discharge standard |
| `C_DISCIPLINE_PROGRESSIVE` | standard | `complex` | `values[]`, `flags.has_progressive_discipline`, `flags.has_warnings`, `flags.has_notice_requirement`, `flags.has_suspension_step`, `flags.has_discharge_step` | Progressive discipline steps, warnings, and notice |
| `C_DISCIPLINE_INVESTIGATION_APPEAL` | standard | `complex` | `values[]`, `flags.has_appeal_right`, `flags.has_investigation_procedure`, `flags.has_record_removal`, `flags.has_union_representation`, `flags.has_deadline` | Disciplinary record removal — 1 year no recurrence |
| `C_DISCIPLINE_PROBATION` | advanced | `complex` | `values[]`, `flags.has_probation_period`, `flags.has_transfer_probation`, `flags.has_shortened_discipline_rights`, `flags.has_completion_rule`, `probationary_group_names` | Probation 90 working days; 60 days for classification transfer |

### Leave

| Concept ID | Priority/Rank | Format | Attributes | Description |
|---|---:|---|---|---|
| `C_LEAVE_HOLIDAYS` | core / 11 | `complex` | `values[]`, `flags.has_paid_holidays`, `flags.has_holiday_premium_pay`, `flags.has_floating_holidays`, `flags.has_observed_holidays` | Holidays and holiday pay |
| `C_LEAVE_VACATION` | core / 8 | `complex` | `values[]`, `flags.has_paid_vacation`, `flags.accrues_with_service`, `flags.has_cashout`, `flags.has_scheduling_rules`, `flags.has_vacation_fund`, `service_band_names`, `eligible_employee_groups` | Vacation and annual leave |
| `C_LEAVE_SICK` | core / 14 | `complex` | `values[]`, `flags.has_paid_sick_leave`, `flags.accrues_with_service`, `flags.has_carryover`, `flags.has_cashout`, `flags.has_medical_certification_requirement`, `eligible_employee_groups` | Sick/personal days: 3 days for 1–4 yr service; 5 days for 5+ yrs; unused days paid out at end of each period |
| `C_LEAVE_PERSONAL_MISC` | standard | `quantitative` | `value` | Bereavement/compassionate leave |
| `C_LEAVE_PARENTAL_FAMILY` | standard | `complex` | `values[]`, `flags.has_parental_leave`, `flags.has_family_leave`, `flags.paid`, `flags.has_fmla_reference`, `flags.has_job_protection` | Family leave — CFRA and FMLA compliance |
| `C_LEAVE_BEREAVEMENT` | standard | `quantitative` | `value` | Bereavement leave — 5 days |
| `C_LEAVE_PERSONAL` | standard | `quantitative` | `value` | Perfect Attendance Days (paid personal time) |
| `C_LEAVE_SUBSISTENCE` | standard | `quantitative` | `value`, `geographic_areas` | Subsistence: $75/night (Torrent) or $50-$70/day by distance (AGC main) |
| `C_LEAVE_JURY_DUTY` | standard | `quantitative` | `value` | Jury duty — 8x regular rate per day |

### Recognition

| Concept ID | Priority/Rank | Format | Attributes | Description |
|---|---:|---|---|---|
| `C_UNION_ACCESS_BUSINESS` | advanced | `complex` | `values[]`, `flags.has_steward_access`, `flags.has_union_business_time`, `flags.has_bulletin_board_rights`, `flags.has_meeting_rights`, `flags.has_paid_union_time` | Steward access, union business time, bulletin boards, and meeting rights |
| `C_UNION_SECURITY_DUES_CHECKOFF` | conditional_core / 15 | `complex` | `values[]`, `flags.has_dues_checkoff`, `flags.has_union_security`, `flags.has_agency_shop`, `flags.has_remittance_deadline`, `flags.has_authorization_requirement` | Dues checkoff, agency shop, union security, and payroll remittance |
| `C_RECOGNITION_COVERAGE_SCOPE` | core / 4 | `complex` | `values[]`, `flags.has_bargaining_unit_scope`, `flags.excludes_supervisors`, `flags.excludes_confidential_employees`, `flags.has_accretion_language`, `bargaining_unit_descriptions`, `included_employee_groups`, `excluded_employee_groups` | Bargaining unit scope |
| `C_HIRING_HALL_DISPATCH` | standard | `complex` | `values[]`, `flags.has_hiring_hall`, `flags.has_dispatch_rules`, `flags.has_referral_priority`, `flags.union_operated`, `flags.has_registration_list` | Hiring hall, dispatch hall, and referral system |
| `C_UNION_SECURITY` | standard | `binary` | `excluded_employee_groups` | Union membership required as condition of employment |
| `C_UNION_DUES_CHECKOFF` | standard | `complex` | `values[]`, `flags.has_dues_checkoff`, `flags.has_remittance_deadline`, `flags.has_authorization_requirement`, `flags.percentage_based`, `flags.flat_amount_based` | Monthly dues checkoff; remit by 15th of following month |

### Healthcare

| Concept ID | Priority/Rank | Format | Attributes | Description |
|---|---:|---|---|---|
| `C_HEALTH_MEDICAL_ACTIVE_CONTRIBUTION` | core / 6 | `quantitative` | `value`, `coverage_tiers`, `eligible_employee_groups` | H&W Fund contribution: 17.625% of payroll (12/17/01); declining to 13% (7/1/02); rising to 15.5% (7/1/03); allocated to Eastern States H&W F |
| `C_HEALTH_DENTAL` | standard | `complex` | `values[]`, `flags.includes_dental`, `flags.employer_paid`, `flags.employee_paid`, `flags.includes_dependent_coverage`, `flags.has_waiting_period`, `coverage_tiers`, `eligible_employee_groups` | Dental plan — employer-paid after 6 months |
| `C_HEALTH_MEDICAL_ACTIVE` | standard | `complex` | `values[]`, `flags.includes_medical`, `flags.includes_dependent_coverage`, `flags.employer_paid`, `flags.employee_paid`, `flags.has_external_plan`, `coverage_tiers`, `eligible_employee_groups` | Active-worker medical umbrella record |
| `C_HEALTH_LIFE_AD_D` | standard | `complex` | `values[]`, `flags.includes_life_insurance`, `flags.includes_add`, `flags.employer_paid`, `flags.employee_paid`, `flags.includes_dependent_coverage`, `coverage_tiers`, `eligible_employee_groups` | Group life and AD&D insurance — employer-paid |
| `C_HEALTH_MEDICAL_ACTIVE_PLAN_DESIGN` | advanced | `complex` | `values[]`, `flags.includes_medical`, `flags.has_deductible`, `flags.has_copay`, `flags.has_out_of_pocket_maximum`, `flags.has_coverage_tiers`, `flags.has_network_rules`, `coverage_tiers` | Active-worker medical plan design, covered services, deductibles, copays, OOP limits |
| `C_HEALTH_DISABILITY_INCOME` | standard | `complex` | `values[]`, `flags.includes_disability`, `flags.has_short_term_disability`, `flags.has_long_term_disability`, `flags.employer_paid`, `flags.wage_replacement_based`, `flags.has_waiting_period`, `waiting_period_terms` | Income Protection and Extended Income Protection (disability income) |
| `C_HEALTH_RETIREE` | standard | `complex` | `values[]`, `flags.includes_retiree_coverage`, `flags.employer_paid`, `flags.employee_paid`, `flags.includes_dependent_coverage`, `flags.has_eligibility_requirement`, `eligible_retiree_groups` | Retiree health plan — Kaiser Foundation employer-paid |
| `C_HEALTH_VISION` | standard | `complex` | `values[]`, `flags.includes_vision`, `flags.employer_paid`, `flags.employee_paid`, `flags.includes_dependent_coverage`, `flags.has_waiting_period`, `coverage_tiers`, `eligible_employee_groups` | Group vision care plan |
| `C_HEALTH_EMPLOYER_CONTRIBUTION` | standard | `quantitative` | `value`, `coverage_tiers`, `eligible_employee_groups` | IAFF VEBA health benefit fund |
| `C_HEALTH_ACTIVE` | standard | `complex` | `values[]`, `flags.includes_medical`, `flags.includes_dental`, `flags.includes_vision`, `flags.employer_paid`, `flags.employee_paid`, `flags.has_external_trust`, `coverage_tiers`, `eligible_employee_groups` | Health benefits — VEBA Trust; state-funded monthly allocation per FTE; plan design in Trust |
| `C_HEALTH_LIFE_INSURANCE` | standard | `binary` | `coverage_tiers`, `eligible_employee_groups` | Life insurance Board-provided |
| `C_HEALTH_ACTIVE_CONTRIBUTION` | standard | `quantitative` | `value`, `coverage_tiers`, `eligible_employee_groups` | Active health — plan terms not recovered in CBA text |
| `C_HEALTH_EXTERNAL_FUND` | standard | `complex` | `values[]`, `flags.has_external_fund`, `flags.employer_contribution`, `flags.employee_contribution`, `flags.trustee_administered`, `flags.includes_health_welfare` | Health/Welfare — GLDC-ILA Health and Welfare Fund (external trust) |
| `C_HEALTH_ACTIVE_PLAN_DESIGN` | standard | `complex` | `values[]`, `flags.includes_medical`, `flags.has_deductible`, `flags.has_copay`, `flags.has_out_of_pocket_maximum`, `flags.has_network_rules`, `flags.includes_dental`, `coverage_tiers` | Active health plan design — POS in-network 100%, out-of-network 70% after $295/$885 deductible; OOP $1,750/$5,250; dental 100% premium compa |
| `C_HEALTH_PLAN_DESIGN` | standard | `complex` | `values[]`, `flags.includes_medical`, `flags.has_plan_options`, `flags.has_deductible`, `flags.has_copay`, `flags.has_out_of_pocket_maximum`, `flags.has_premium_share`, `coverage_tiers` | Health plan design options |
| `C_HEALTH_INSURANCE_BUYOUT` | standard | `quantitative` | `value`, `eligible_employee_groups` | Health insurance opt-out payment $1,200/year |
| `C_HEALTH_WELFARE_FUND` | standard | `quantitative` | `value` | Welfare fund employer contributions |
| `C_HEALTH_DISABILITY` | standard | `quantitative` | `value`, `waiting_period_terms` | Short-term disability $400/week max 26 weeks |
| `C_HEALTH_PRESCRIPTION_DRUG` | standard | `complex` | `values[]`, `flags.includes_prescription_drug`, `flags.has_copay`, `flags.has_tiers`, `flags.mail_order_included`, `flags.generic_required` | 3-tier HMO prescription co-pay |
| `C_HEALTH_BENEFITS` | standard | `binary` | `coverage_tiers`, `eligible_employee_groups` | Health and welfare benefits |

### Safety

| Concept ID | Priority/Rank | Format | Attributes | Description |
|---|---:|---|---|---|
| `C_SAFETY_PPE_UNSAFE_WORK` | core / 12 | `complex` | `values[]`, `flags.has_ppe_requirement`, `flags.has_unsafe_work_right`, `flags.has_safety_standards`, `flags.has_hazard_response`, `flags.has_safety_committee` | PPE, unsafe-work rights, safety standards, and hazard response |
| `C_LABOR_MANAGEMENT_COMMITTEE` | advanced | `binary` | None beyond `exists` and `summarize` | Labor-Management Cooperation Committee (LMCC) |
| `C_SAFETY_ASSAULT_VIOLENCE` | standard | `complex` | `values[]`, `flags.has_assault_policy`, `flags.has_violence_response`, `flags.has_paid_release`, `flags.has_response_team`, `flags.has_reporting_requirement` | Physical violence and verbal abuse policy; response team; paid release on shift of assault |
| `C_SAFETY_DRUG_TESTING` | standard | `complex` | `values[]`, `flags.has_drug_testing`, `flags.accident_triggered`, `flags.reasonable_suspicion_based`, `flags.random_testing`, `flags.has_discipline_consequence`, `consequence_terms` | Work accident investigation protocol |

### Ancillary

| Concept ID | Priority/Rank | Format | Attributes | Description |
|---|---:|---|---|---|
| `C_RETIREMENT_PENSION` | core / 7 | `complex` | `values[]`, `flags.has_defined_benefit_pension`, `flags.has_employer_contribution`, `flags.has_employee_contribution`, `flags.has_vesting_requirement`, `flags.has_external_fund`, `eligible_employee_groups`, `vesting_terms` | Pension and retirement plan eligibility/contributions |
| `C_RETIREMENT_SAVINGS_ANNUITY` | standard | `quantitative` | `value`, `eligible_employee_groups`, `vesting_terms` | Annuity Fund (CT Carpenters) contributions |
| `C_TRAINING_TUITION_CERTIFICATION` | standard | `complex` | `values[]`, `flags.has_training_benefit`, `flags.has_tuition_reimbursement`, `flags.has_certification_support`, `flags.employer_paid`, `flags.has_professional_development`, `eligible_employee_groups` | Training, tuition support, certification, and professional development |
| `C_LEGAL_SERVICES_FUND` | standard | `quantitative` | `value` | Group legal services fund |
| `C_RETIREMENT_INCENTIVE` | standard | `complex` | `values[]`, `flags.has_retirement_bonus`, `flags.service_based`, `flags.date_based`, `flags.has_age_requirement`, `flags.has_notice_requirement`, `eligible_employee_groups`, `effective_dates` | Retirement bonus — $10,000 at June 30 2005, $7,500 at June 30 2006, $5,000 at June 30 2007 — for teachers with 30+ years ACS service |
| `C_CHILD_DEPENDENT_CARE` | standard | `quantitative` | `value`, `eligible_dependent_terms` | Fellowships for Day Care |
| `C_TRANSIT_COMMUTER_BENEFIT` | standard | `quantitative` | `value` | Transit subsidy per SMC 4.20.370 |

### Security

| Concept ID | Priority/Rank | Format | Attributes | Description |
|---|---:|---|---|---|
| `C_JOB_SECURITY_LAYOFF_ORDER` | core / 5 | `complex` | `values[]`, `flags.has_layoff_notice`, `flags.seniority_based`, `flags.has_bumping_rights`, `flags.has_inverse_seniority_order`, `flags.has_union_notice`, `affected_employee_groups`, `exception_terms` | Layoff notification and procedure |
| `C_JOB_SECURITY_RECALL` | core / 5 | `complex` | `values[]`, `flags.has_recall_rights`, `flags.seniority_based`, `flags.has_recall_period_limit`, `flags.has_recall_notice`, `flags.has_preference_over_new_hires`, `affected_employee_groups`, `exception_terms` | Recall rights — equal to continuous service or 2 years maximum |
| `C_JOB_SECURITY_SEVERANCE` | advanced | `complex` | `values[]`, `flags.has_severance_pay`, `flags.service_based`, `flags.wage_based`, `flags.has_layoff_trigger`, `flags.has_maximum_duration`, `eligible_employee_groups` | Income Protection Supplement: 100% of base wage + COLA for 13-52 weeks by service tier after layoff pay exhausted |
| `C_JOB_SECURITY_BENEFIT_CONTINUATION` | standard | `complex` | `values[]`, `flags.has_benefit_continuation`, `flags.includes_health_continuation`, `flags.includes_life_insurance_continuation`, `flags.applies_during_leave`, `flags.employer_paid`, `eligible_employee_groups` | Benefits during leaves of absence — health, dental, life insurance continuation |
| `C_SUBCONTRACTING_WORK_PRESERVATION` | standard | `complex` | `values[]`, `flags.limits_subcontracting`, `flags.has_work_preservation`, `flags.requires_union_notice`, `flags.allows_union_matching`, `flags.protects_bargaining_unit_work`, `protected_work_terms`, `subcontracting_exception_terms`, `notice_recipient_names` | Subcontracting limits, non-unit work, and work preservation |
| `C_SENIORITY_SYSTEM` | core / 9 | `complex` | `values[]`, `flags.has_seniority_system`, `flags.classification_based`, `flags.plantwide_seniority`, `flags.has_tie_breaker`, `flags.affects_layoff`, `seniority_type_names`, `seniority_group_names`, `classification_names`, `break_in_service_terms`, `tie_breaker_terms` | Seniority system — length of service at premises by classification |
| `C_JOB_POSTING_BIDDING_TRANSFER` | standard | `complex` | `values[]`, `flags.has_job_posting`, `flags.has_bidding_rights`, `flags.has_transfer_rights`, `flags.seniority_based`, `flags.has_trial_period`, `bidding_unit_names`, `eligible_employee_groups`, `trial_period_terms` | Job posting and promotion rights |
| `C_JOB_SECURITY_LAYOFF_RECALL` | standard | `complex` | `values[]`, `flags.has_layoff_procedure`, `flags.has_recall_rights`, `flags.seniority_based`, `flags.has_bumping_rights`, `flags.has_notice_requirement`, `affected_employee_groups`, `exception_terms` | Force adjustments and recall — Art. 10 |
| `C_JOB_SECURITY_SUB_INCOME_BRIDGE` | standard | `complex` | `values[]`, `flags.has_sub_income_benefit`, `flags.wage_replacement_based`, `flags.service_based`, `flags.has_external_fund`, `flags.has_duration_limit`, `eligible_employee_groups` | Supplemental Unemployment Benefit (SUB) fund |
| `C_JOB_SECURITY_LAYOFF` | standard | `quantitative` | `value`, `affected_employee_groups`, `exception_terms` | Dismissal pay — 2 weeks if musician not re-engaged within 90 days |
| `C_JOB_SECURITY_SENIORITY` | standard | `complex` | `values[]`, `flags.has_seniority_groups`, `flags.classification_based`, `flags.affects_layoff`, `flags.affects_recall`, `flags.affects_bidding`, `seniority_type_names`, `seniority_group_names`, `classification_names`, `break_in_service_terms`, `tie_breaker_terms` | Seniority — 3 groups: Meatcutters, Wrappers, Service Counter |
| `C_LIGHT_DUTY_ACCOMMODATION` | standard | `complex` | `values[]`, `flags.has_light_duty`, `flags.has_accommodation_process`, `flags.has_pay_protection`, `flags.disability_related`, `flags.has_medical_clearance`, `eligible_employee_groups` | Partially disabled employees — modified duty with pay protection |
| `C_JOB_SECURITY_SUBCONTRACTING` | standard | `binary` | `protected_work_terms`, `subcontracting_exception_terms`, `notice_recipient_names` | Subcontracting at company discretion; union matching opportunity discussion |
| `C_JOB_SECURITY_RIF_LAYOFF` | standard | `complex` | `values[]`, `flags.has_rif_procedure`, `flags.has_layoff_order`, `flags.seniority_based`, `flags.classification_based`, `flags.has_recall_pool`, `affected_employee_groups`, `exception_terms` | Layoff — inverse seniority within classification; recall from employment pool for 1 year |
| `C_JOB_SECURITY_BUMPING` | advanced / 5 | `binary` | `affected_employee_groups`, `exception_terms` | Bumping rights to former classification |
| `C_JOB_SECURITY_NO_CONTRACTING_OUT` | standard | `binary` | `protected_work_terms`, `subcontracting_exception_terms`, `notice_recipient_names` | Subcontracting limitation |

### Scheduling

| Concept ID | Priority/Rank | Format | Attributes | Description |
|---|---:|---|---|---|
| `C_TIME_REGULAR_SCHEDULE` | standard | `complex` | `values[]`, `flags.has_regular_hours`, `flags.has_workweek_definition`, `flags.has_shift_schedule`, `flags.has_flexible_schedule`, `flags.has_guaranteed_hours`, `covered_employee_groups` | Regular hours and schedule structure |
| `C_TIME_REST_MEAL_PERIODS` | standard | `complex` | `values[]`, `flags.has_rest_periods`, `flags.has_meal_periods`, `flags.has_paid_breaks`, `flags.has_relief_breaks`, `flags.has_missed_break_premium`, `exception_terms` | Rest periods, meal periods, and relief breaks |
| `C_WORKLOAD_CLASS_SIZE_STAFFING` | standard | `complex` | `values[]`, `flags.has_class_size_limit`, `flags.has_staffing_ratio`, `flags.has_preparation_period`, `flags.has_duty_free_lunch`, `flags.has_voluntary_extracurricular`, `staffing_ratio_terms`, `duty_terms` | School day defined; preparation periods required where practicable (45-minute duty-free lunch); extracurricular on voluntary basis |
| `C_TIME_SCHEDULE_NOTICE_CHANGE` | standard | `quantitative` | `value`, `notice_trigger_terms`, `affected_employee_groups` | Schedule changes — Thursday advance notice rule |
| `C_TIME_NO_CANCELLATION_SECURITY` | standard | `complex` | `values[]`, `flags.has_no_cancellation_rule`, `flags.has_involuntary_leave_limit`, `flags.has_pay_protection`, `flags.has_schedule_security`, `affected_employee_groups` | Involuntary leave status caps |

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
