# Core CBA Provision Extraction Targets

## Purpose

This document defines the provision taxonomy for validating human and LLM extraction from U.S. collective bargaining agreements (CBAs). The project goal is to compare extractions deterministically while still preserving short, verifiable surface strings that help explain what the model or human found.

Every provision model keeps `summarize` as a concise audit field. The comparison target is structured data: `exists`, boolean flags, numeric values, and typed string-list attributes such as occupation names, plan names, effective-date strings, bargaining-unit descriptions, holiday names, and other contract terms that can be checked directly against the source CBA.

## Extraction Model

The current structures use three provision formats:

- `binary`: compare `exists`, plus any typed string-list details that identify the relevant clause terms.
- `quantitative`: compare `exists`, a single normalized `value` when available, and typed string-list details when the CBA identifies named plans, groups, dates, or terms.
- `complex`: compare `exists`, zero or more normalized `values`, provision-specific boolean `flags`, and typed string-list details.

String details are short source terms, not long evidence spans. Date-like attributes are literal strings for now, for example `effective_dates: ["July 1, 2026"]`; no ISO parsing or normalization is enforced in this layer.

A provision with `exists=true` may validate with flags, numeric values, or non-empty string detail. A provision with `exists=false` must not contain flags, numeric values, or non-empty string detail.

## Category Tables

The concepts below are grouped and ordered exactly as they appear by category in `data/cba_meta/cba_provision_dictionary.csv`.

### Compensation

| Concept | Tier / rank | Format | String attributes | Why these strings are useful |
| --- | --- | --- | --- | --- |
| `C_WAGE_BASE_RATE` | core / 1 | `complex` | `occupation_names`, `classification_names`, `step_names`, `wage_schedule_names`, `geographic_areas`, `effective_dates` | Verifies named terms in base wage or salary rate. |
| `C_PREMIUM_OVERTIME` | core / 2 | `complex` | `trigger_terms`, `covered_employee_groups`, `excluded_employee_groups`, `premium_names` | Verifies named terms in overtime eligibility thresholds and multipliers. |
| `C_WAGE_INCREASES_COLA` | standard | `complex` | `effective_dates`, `covered_employee_groups`, `adjustment_names`, `cola_index_names` | Verifies named terms in annual wage increases: $0.25/hr for time workers (12/17/01, 12/16/02, 12/15/03); $0.25/hr equivalent for piece workers. |
| `C_PREMIUM_CALL_IN_REPORTING` | standard | `complex` | `trigger_terms`, `covered_employee_groups`, `guarantee_names` | Verifies named terms in call-in, call-back, reporting, and minimum-pay guarantees. |
| `C_PREMIUM_SHIFT` | advanced | `quantitative` | `shift_names`, `covered_employee_groups` | Verifies named terms in shift differentials and night/weekend premiums. |
| `C_WAGE_PROGRESSION` | standard | `complex` | `progression_step_names`, `classification_names`, `occupation_names`, `effective_dates` | Verifies named terms in wage progression, steps, and classification movement. |
| `C_PREMIUM_RESPONSIBILITY_SPECIALTY` | standard | `complex` | `premium_role_names`, `classification_names`, `specialty_names` | Verifies named terms in responsibility, higher-classification, specialty, translation, flight, or role premiums. |
| `C_PREMIUM_STANDBY_ON_CALL` | advanced | `quantitative` | `standby_terms`, `covered_employee_groups` | Verifies named terms in standby pay. |
| `C_UNIFORM_CLOTHING_ALLOWANCE` | standard | `quantitative` | `covered_item_names`, `covered_employee_groups` | Verifies named terms in safety shoe program: 100% cost for wood processing/pulp mill employees; up to $110 reimbursement for others. |
| `C_PREMIUM_ZONE_SUBSISTENCE` | standard | `complex` | `zone_names`, `geographic_areas`, `travel_terms` | Verifies named terms in zone pay, travel subsistence, and remote-site allowances. |
| `C_WAGE_GENERAL_INCREASE` | standard | `complex` | `effective_dates`, `covered_employee_groups`, `adjustment_names` | Verifies named terms in scale increase: 2.5% in year 2 (2/16/2003), 3.5% in year 3 (2/15/2004). |
| `C_WAGE_APPRENTICE` | standard | `complex` | `apprenticeship_period_names`, `classification_names` | Verifies named terms in apprentice wage schedule 40-82% of jw over 7 periods. |
| `C_WAGE_SCHEDULED_INCREASE` | standard | `complex` | `effective_dates`, `service_band_names`, `adjustment_names` | Verifies named terms in longevity pay — $0.10/hr at 10yr through $0.25/hr at 25yr. |
| `C_PREMIUM_SUNDAY_HOLIDAY` | standard | `complex` | `day_names`, `holiday_names` | Verifies named terms in 6th and 7th day in workweek — 1.5x (150%); 6 legal holidays — 2.0x. |
| `C_PREMIUM_FOREMAN` | standard | `quantitative` | `role_names`, `classification_names` | Verifies named terms in foreman and general foreman premium. |
| `C_PREMIUM_HAZARD` | standard | `quantitative` | `hazard_names`, `covered_employee_groups` | Verifies named terms in hazardous work differential — 15% above classification rate. |
| `C_WAGE_INCREASE` | standard | `complex` | `effective_dates`, `covered_employee_groups`, `adjustment_names` | Verifies named terms in annual wage increases: $0.50 3/1/2001, $0.50 9/2/2002, $1.00 3/1/2004. |
| `C_WAGE_LONGEVITY` | standard | `complex` | `service_band_names`, `covered_employee_groups` | Verifies named terms in longevity pay. |
| `C_WAGE_MERIT_STEP` | standard | `complex` | `step_names`, `eligibility_terms`, `review_terms` | Verifies named terms in step advancement on salary schedule. |
| `C_WAGE_SAVINGS` | standard | `quantitative` | `plan_names`, `fund_names` | Verifies named terms in savings/deferred compensation contribution. |
| `C_WAGE_VACATION_SUPP` | standard | `quantitative` | `fund_names`, `contribution_names` | Verifies named terms in vacation/supplemental dues contribution $2.95/hr. |
| `C_WAGE_ACCRUAL_VACATION` | standard | `quantitative` | `accrual_names`, `covered_employee_groups` | Verifies named terms in vacation/holiday pay accrual ($0.50/hr). |
| `C_PREMIUM_LEADMAN` | standard | `quantitative` | `role_names`, `classification_names` | Verifies named terms in leadman premium — $2.00/hr. |
| `C_PREMIUM_GROUP_LEADER` | standard | `complex` | `role_names`, `tier_names` | Verifies named terms in group leader premium $1.20/$0.80/$0.40 per hour by tier. |
| `C_WAGE_INCENTIVE` | standard | `complex` | `incentive_names`, `performance_metric_names` | Verifies named terms in incentive pay: up to 5% company performance + 5% cell bonus + 5% stretch targets = max 15% of annual base salary. |
| `C_PREMIUM_STANDBY` | standard | `binary` | `standby_terms`, `response_terms` | Verifies named terms in standby provision — reachable by signal device; 1-hour response time. |

### Disputes

| Concept | Tier / rank | Format | String attributes | Why these strings are useful |
| --- | --- | --- | --- | --- |
| `C_GRIEVANCE_PROCEDURE` | core / 3 | `complex` | `grievance_step_names`, `eligible_filers`, `excluded_claim_types`, `deadline_terms` | Verifies named terms in grievance steps, timelines, representation, and scope. |
| `C_ARBITRATION` | core / 3 | `complex` | `arbitrator_selection_terms`, `excluded_claim_types`, `forum_names`, `remedy_limit_terms` | Verifies named terms in arbitration access, selection, authority, costs, and finality. |
| `C_DISCIPLINE_JUST_CAUSE` | core / 10 | `complex` | `discipline_terms`, `covered_employee_groups`, `excluded_employee_groups`, `offense_terms` | Verifies named terms in just cause and substantive discipline/discharge standard. |
| `C_DISCIPLINE_PROGRESSIVE` | standard | `complex` | `discipline_step_names`, `offense_terms`, `notice_terms` | Verifies named terms in progressive discipline steps, warnings, and notice. |
| `C_DISCIPLINE_INVESTIGATION_APPEAL` | standard | `complex` | `appeal_step_names`, `record_removal_terms`, `representation_terms` | Verifies named terms in disciplinary record removal — 1 year no recurrence. |
| `C_DISCIPLINE_PROBATION` | advanced | `complex` | `probationary_group_names`, `probation_completion_terms` | Verifies named terms in probation 90 working days; 60 days for classification transfer. |

### Leave

| Concept | Tier / rank | Format | String attributes | Why these strings are useful |
| --- | --- | --- | --- | --- |
| `C_LEAVE_HOLIDAYS` | core / 11 | `complex` | `holiday_names`, `observed_rule_terms`, `eligibility_terms` | Verifies named terms in holidays and holiday pay. |
| `C_LEAVE_VACATION` | core / 8 | `complex` | `service_band_names`, `vacation_schedule_terms`, `eligible_employee_groups` | Verifies named terms in vacation and annual leave. |
| `C_LEAVE_SICK` | core / 14 | `complex` | `sick_leave_bank_names`, `eligible_employee_groups`, `permitted_use_terms` | Verifies named terms in sick/personal days: 3 days for 1–4 yr service; 5 days for 5+ yrs; unused days paid out at end of each period. |
| `C_LEAVE_PERSONAL_MISC` | standard | `quantitative` | `leave_type_names`, `relationship_terms`, `eligibility_terms` | Verifies named terms in bereavement/compassionate leave. |
| `C_LEAVE_PARENTAL_FAMILY` | standard | `complex` | `leave_type_names`, `relationship_terms`, `statute_names` | Verifies named terms in family leave — cfra and fmla compliance. |
| `C_LEAVE_BEREAVEMENT` | standard | `quantitative` | `relationship_terms`, `leave_type_names` | Verifies named terms in bereavement leave — 5 days. |
| `C_LEAVE_PERSONAL` | standard | `quantitative` | `leave_type_names`, `eligibility_terms` | Verifies named terms in perfect attendance days (paid personal time). |
| `C_LEAVE_SUBSISTENCE` | standard | `quantitative` | `geographic_areas`, `subsistence_terms` | Verifies named terms in subsistence: $75/night (torrent) or $50-$70/day by distance (agc main). |
| `C_LEAVE_JURY_DUTY` | standard | `quantitative` | `civic_duty_terms`, `eligibility_terms` | Verifies named terms in jury duty — 8x regular rate per day. |

### Recognition

| Concept | Tier / rank | Format | String attributes | Why these strings are useful |
| --- | --- | --- | --- | --- |
| `C_UNION_ACCESS_BUSINESS` | advanced | `complex` | `union_role_names`, `access_location_names`, `communication_channel_names` | Verifies named terms in steward access, union business time, bulletin boards, and meeting rights. |
| `C_UNION_SECURITY_DUES_CHECKOFF` | conditional_core / 15 | `complex` | `union_names`, `authorization_terms`, `revocation_terms`, `fee_type_names` | Verifies named terms in dues checkoff, agency shop, union security, and payroll remittance. |
| `C_RECOGNITION_COVERAGE_SCOPE` | core / 4 | `complex` | `union_names`, `bargaining_unit_descriptions`, `included_employee_groups`, `excluded_employee_groups` | Verifies named terms in bargaining unit scope. |
| `C_HIRING_HALL_DISPATCH` | standard | `complex` | `hiring_hall_names`, `referral_priority_terms`, `registration_list_names` | Verifies named terms in hiring hall, dispatch hall, and referral system. |
| `C_UNION_SECURITY` | standard | `binary` | `union_names`, `membership_terms`, `excluded_employee_groups` | Verifies named terms in union membership required as condition of employment. |
| `C_UNION_DUES_CHECKOFF` | standard | `complex` | `union_names`, `authorization_terms`, `revocation_terms`, `fee_type_names` | Verifies named terms in monthly dues checkoff; remit by 15th of following month. |

### Healthcare

| Concept | Tier / rank | Format | String attributes | Why these strings are useful |
| --- | --- | --- | --- | --- |
| `C_HEALTH_MEDICAL_ACTIVE_CONTRIBUTION` | core / 6 | `quantitative` | `plan_names`, `fund_names`, `coverage_tiers`, `eligible_employee_groups`, `contribution_terms` | Verifies named terms in h&w fund contribution: 17.625% of payroll (12/17/01); declining to 13% (7/1/02); rising to 15.5% (7/1/03); allocated to eastern states h&w f. |
| `C_HEALTH_DENTAL` | standard | `complex` | `plan_names`, `coverage_tiers`, `eligible_employee_groups`, `covered_service_names` | Verifies named terms in dental plan — employer-paid after 6 months. |
| `C_HEALTH_MEDICAL_ACTIVE` | standard | `complex` | `plan_names`, `coverage_tiers`, `eligible_employee_groups`, `covered_service_names` | Verifies named terms in active-worker medical umbrella record. |
| `C_HEALTH_LIFE_AD_D` | standard | `complex` | `plan_names`, `coverage_tiers`, `eligible_employee_groups`, `covered_service_names` | Verifies named terms in group life and ad&d insurance — employer-paid. |
| `C_HEALTH_MEDICAL_ACTIVE_PLAN_DESIGN` | advanced | `complex` | `plan_names`, `network_names`, `coverage_tiers`, `covered_service_names` | Verifies named terms in active-worker medical plan design, covered services, deductibles, copays, oop limits. |
| `C_HEALTH_DISABILITY_INCOME` | standard | `complex` | `plan_names`, `disability_type_names`, `waiting_period_terms` | Verifies named terms in income protection and extended income protection (disability income). |
| `C_HEALTH_RETIREE` | standard | `complex` | `plan_names`, `eligible_retiree_groups`, `eligibility_terms` | Verifies named terms in retiree health plan — kaiser foundation employer-paid. |
| `C_HEALTH_VISION` | standard | `complex` | `plan_names`, `coverage_tiers`, `eligible_employee_groups`, `covered_service_names` | Verifies named terms in group vision care plan. |
| `C_HEALTH_EMPLOYER_CONTRIBUTION` | standard | `quantitative` | `plan_names`, `fund_names`, `coverage_tiers`, `eligible_employee_groups`, `contribution_terms` | Verifies named terms in iaff veba health benefit fund. |
| `C_HEALTH_ACTIVE` | standard | `complex` | `plan_names`, `trust_names`, `coverage_tiers`, `eligible_employee_groups`, `covered_service_names` | Verifies named terms in health benefits — veba trust; state-funded monthly allocation per fte; plan design in trust. |
| `C_HEALTH_LIFE_INSURANCE` | standard | `binary` | `plan_names`, `coverage_tiers`, `eligible_employee_groups`, `covered_service_names` | Verifies named terms in life insurance board-provided. |
| `C_HEALTH_ACTIVE_CONTRIBUTION` | standard | `quantitative` | `plan_names`, `fund_names`, `coverage_tiers`, `eligible_employee_groups`, `contribution_terms` | Verifies named terms in active health — plan terms not recovered in cba text. |
| `C_HEALTH_EXTERNAL_FUND` | standard | `complex` | `fund_names`, `trustee_names`, `plan_names`, `contribution_terms` | Verifies named terms in health/welfare — gldc-ila health and welfare fund (external trust). |
| `C_HEALTH_ACTIVE_PLAN_DESIGN` | standard | `complex` | `plan_names`, `network_names`, `coverage_tiers`, `covered_service_names` | Verifies named terms in active health plan design — pos in-network 100%, out-of-network 70% after $295/$885 deductible; oop $1,750/$5,250; dental 100% premium compa. |
| `C_HEALTH_PLAN_DESIGN` | standard | `complex` | `plan_names`, `network_names`, `coverage_tiers`, `covered_service_names` | Verifies named terms in health plan design options. |
| `C_HEALTH_INSURANCE_BUYOUT` | standard | `quantitative` | `plan_names`, `eligible_employee_groups`, `contribution_terms` | Verifies named terms in health insurance opt-out payment $1,200/year. |
| `C_HEALTH_WELFARE_FUND` | standard | `quantitative` | `fund_names`, `trustee_names`, `plan_names`, `contribution_terms` | Verifies named terms in welfare fund employer contributions. |
| `C_HEALTH_DISABILITY` | standard | `quantitative` | `plan_names`, `disability_type_names`, `waiting_period_terms` | Verifies named terms in short-term disability $400/week max 26 weeks. |
| `C_HEALTH_PRESCRIPTION_DRUG` | standard | `complex` | `plan_names`, `drug_tier_names`, `covered_service_names` | Verifies named terms in 3-tier hmo prescription co-pay. |
| `C_HEALTH_BENEFITS` | standard | `binary` | `plan_names`, `fund_names`, `coverage_tiers`, `eligible_employee_groups`, `covered_service_names` | Verifies named terms in health and welfare benefits. |

### Safety

| Concept | Tier / rank | Format | String attributes | Why these strings are useful |
| --- | --- | --- | --- | --- |
| `C_SAFETY_PPE_UNSAFE_WORK` | core / 12 | `complex` | `ppe_item_names`, `hazard_names`, `safety_standard_names`, `committee_names` | Verifies named terms in ppe, unsafe-work rights, safety standards, and hazard response. |
| `C_LABOR_MANAGEMENT_COMMITTEE` | advanced | `binary` | `committee_names`, `committee_purpose_terms`, `participant_group_names` | Verifies named terms in labor-management cooperation committee (lmcc). |
| `C_SAFETY_ASSAULT_VIOLENCE` | standard | `complex` | `violence_event_terms`, `response_team_names`, `reporting_terms` | Verifies named terms in physical violence and verbal abuse policy; response team; paid release on shift of assault. |
| `C_SAFETY_DRUG_TESTING` | standard | `complex` | `testing_trigger_terms`, `substance_test_names`, `consequence_terms` | Verifies named terms in work accident investigation protocol. |

### Ancillary

| Concept | Tier / rank | Format | String attributes | Why these strings are useful |
| --- | --- | --- | --- | --- |
| `C_RETIREMENT_PENSION` | core / 7 | `complex` | `plan_names`, `fund_names`, `eligible_employee_groups`, `vesting_terms` | Verifies named terms in pension and retirement plan eligibility/contributions. |
| `C_RETIREMENT_SAVINGS_ANNUITY` | standard | `quantitative` | `plan_names`, `fund_names`, `eligible_employee_groups`, `vesting_terms` | Verifies named terms in annuity fund (ct carpenters) contributions. |
| `C_TRAINING_TUITION_CERTIFICATION` | standard | `complex` | `training_program_names`, `certification_names`, `eligible_employee_groups` | Verifies named terms in training, tuition support, certification, and professional development. |
| `C_LEGAL_SERVICES_FUND` | standard | `quantitative` | `fund_names`, `covered_service_names` | Verifies named terms in group legal services fund. |
| `C_RETIREMENT_INCENTIVE` | standard | `complex` | `incentive_names`, `eligible_employee_groups`, `effective_dates` | Verifies named terms in retirement bonus — $10,000 at june 30 2005, $7,500 at june 30 2006, $5,000 at june 30 2007 — for teachers with 30+ years acs service. |
| `C_CHILD_DEPENDENT_CARE` | standard | `quantitative` | `program_names`, `eligible_dependent_terms` | Verifies named terms in fellowships for day care. |
| `C_TRANSIT_COMMUTER_BENEFIT` | standard | `quantitative` | `benefit_program_names`, `transit_mode_names` | Verifies named terms in transit subsidy per smc 4.20.370. |

### Security

| Concept | Tier / rank | Format | String attributes | Why these strings are useful |
| --- | --- | --- | --- | --- |
| `C_JOB_SECURITY_LAYOFF_ORDER` | core / 5 | `complex` | `layoff_unit_names`, `affected_employee_groups`, `notice_method_terms`, `exception_terms` | Verifies named terms in layoff notification and procedure. |
| `C_JOB_SECURITY_RECALL` | core / 5 | `complex` | `recall_list_names`, `affected_employee_groups`, `notice_method_terms`, `exception_terms` | Verifies named terms in recall rights — equal to continuous service or 2 years maximum. |
| `C_JOB_SECURITY_SEVERANCE` | advanced | `complex` | `severance_plan_names`, `eligible_employee_groups`, `benefit_type_names` | Verifies named terms in income protection supplement: 100% of base wage + cola for 13-52 weeks by service tier after layoff pay exhausted. |
| `C_JOB_SECURITY_BENEFIT_CONTINUATION` | standard | `complex` | `benefit_program_names`, `benefit_type_names`, `leave_type_names`, `eligible_employee_groups` | Verifies named terms in benefits during leaves of absence — health, dental, life insurance continuation. |
| `C_SUBCONTRACTING_WORK_PRESERVATION` | standard | `complex` | `protected_work_terms`, `subcontracting_terms`, `subcontracting_exception_terms`, `notice_recipient_names` | Verifies named terms in subcontracting limits, non-unit work, and work preservation. |
| `C_SENIORITY_SYSTEM` | core / 9 | `complex` | `seniority_unit_names`, `seniority_type_names`, `seniority_group_names`, `classification_names`, `break_in_service_terms`, `tie_breaker_terms` | Verifies named terms in seniority system — length of service at premises by classification. |
| `C_JOB_POSTING_BIDDING_TRANSFER` | standard | `complex` | `job_posting_terms`, `bidding_unit_names`, `eligible_employee_groups`, `trial_period_terms` | Verifies named terms in job posting and promotion rights. |
| `C_JOB_SECURITY_LAYOFF_RECALL` | standard | `complex` | `layoff_unit_names`, `recall_list_names`, `affected_employee_groups`, `notice_method_terms`, `exception_terms` | Verifies named terms in force adjustments and recall — art. 10. |
| `C_JOB_SECURITY_SUB_INCOME_BRIDGE` | standard | `complex` | `severance_plan_names`, `benefit_program_names`, `benefit_type_names`, `eligible_employee_groups` | Verifies named terms in supplemental unemployment benefit (sub) fund. |
| `C_JOB_SECURITY_LAYOFF` | standard | `quantitative` | `layoff_unit_names`, `affected_employee_groups`, `notice_method_terms`, `exception_terms` | Verifies named terms in dismissal pay — 2 weeks if musician not re-engaged within 90 days. |
| `C_JOB_SECURITY_SENIORITY` | standard | `complex` | `seniority_unit_names`, `seniority_type_names`, `seniority_group_names`, `classification_names`, `break_in_service_terms`, `tie_breaker_terms` | Verifies named terms in seniority — 3 groups: meatcutters, wrappers, service counter. |
| `C_LIGHT_DUTY_ACCOMMODATION` | standard | `complex` | `accommodation_terms`, `eligible_employee_groups`, `medical_clearance_terms` | Verifies named terms in partially disabled employees — modified duty with pay protection. |
| `C_JOB_SECURITY_SUBCONTRACTING` | standard | `binary` | `protected_work_terms`, `subcontracting_terms`, `subcontracting_exception_terms`, `notice_recipient_names` | Verifies named terms in subcontracting at company discretion; union matching opportunity discussion. |
| `C_JOB_SECURITY_RIF_LAYOFF` | standard | `complex` | `layoff_unit_names`, `recall_list_names`, `affected_employee_groups`, `notice_method_terms`, `exception_terms` | Verifies named terms in layoff — inverse seniority within classification; recall from employment pool for 1 year. |
| `C_JOB_SECURITY_BUMPING` | advanced / 5 | `binary` | `layoff_unit_names`, `affected_employee_groups`, `exception_terms` | Verifies named terms in bumping rights to former classification. |
| `C_JOB_SECURITY_NO_CONTRACTING_OUT` | standard | `binary` | `protected_work_terms`, `subcontracting_terms`, `subcontracting_exception_terms`, `notice_recipient_names` | Verifies named terms in subcontracting limitation. |

### Scheduling

| Concept | Tier / rank | Format | String attributes | Why these strings are useful |
| --- | --- | --- | --- | --- |
| `C_TIME_REGULAR_SCHEDULE` | standard | `complex` | `shift_names`, `workweek_definition_terms`, `covered_employee_groups` | Verifies named terms in regular hours and schedule structure. |
| `C_TIME_REST_MEAL_PERIODS` | standard | `complex` | `break_type_names`, `shift_names`, `exception_terms` | Verifies named terms in rest periods, meal periods, and relief breaks. |
| `C_WORKLOAD_CLASS_SIZE_STAFFING` | standard | `complex` | `class_size_unit_names`, `staffing_ratio_terms`, `duty_terms` | Verifies named terms in school day defined; preparation periods required where practicable (45-minute duty-free lunch); extracurricular on voluntary basis. |
| `C_TIME_SCHEDULE_NOTICE_CHANGE` | standard | `quantitative` | `notice_trigger_terms`, `affected_employee_groups` | Verifies named terms in schedule changes — thursday advance notice rule. |
| `C_TIME_NO_CANCELLATION_SECURITY` | standard | `complex` | `cancellation_terms`, `affected_employee_groups`, `pay_protection_terms` | Verifies named terms in involuntary leave status caps. |

## Ranked Priority Families

The deep research report recommends ranking the most important extraction families as follows. Some ranked families map to more than one existing concept.

| Rank | Concept | Category | Tier | Score | Family |
| ---: | --- | --- | --- | ---: | --- |
| 1 | `C_WAGE_BASE_RATE` | Compensation | core | 98 | base_wage_schedule |
| 2 | `C_PREMIUM_OVERTIME` | Compensation | core | 96 | overtime_and_premium_pay |
| 3 | `C_ARBITRATION` | Disputes | core | 95 | grievance_arbitration |
| 3 | `C_GRIEVANCE_PROCEDURE` | Disputes | core | 95 | grievance_arbitration |
| 4 | `C_RECOGNITION_COVERAGE_SCOPE` | Recognition | core | 94 | recognition_bargaining_unit |
| 5 | `C_JOB_SECURITY_BUMPING` | Security | advanced | 92 | layoff_recall_bumping |
| 5 | `C_JOB_SECURITY_LAYOFF_ORDER` | Security | core | 92 | layoff_recall_bumping |
| 5 | `C_JOB_SECURITY_RECALL` | Security | core | 92 | layoff_recall_bumping |
| 6 | `C_HEALTH_MEDICAL_ACTIVE_CONTRIBUTION` | Healthcare | core | 91 | health_insurance_employer_contribution |
| 7 | `C_RETIREMENT_PENSION` | Ancillary | core | 89 | pension_retirement_contribution |
| 8 | `C_LEAVE_VACATION` | Leave | core | 88 | paid_vacation |
| 9 | `C_SENIORITY_SYSTEM` | Security | core | 87 | seniority |
| 10 | `C_DISCIPLINE_JUST_CAUSE` | Disputes | core | 86 | just_cause_discipline_discharge |
| 11 | `C_LEAVE_HOLIDAYS` | Leave | core | 84 | paid_holidays |
| 12 | `C_SAFETY_PPE_UNSAFE_WORK` | Safety | core | 83 | safety_ppe_training |
| 14 | `C_LEAVE_SICK` | Leave | core | 80 | sick_leave_paid_leave_bank |
| 15 | `C_UNION_SECURITY_DUES_CHECKOFF` | Recognition | conditional_core | 75 | dues_checkoff_union_security |
|  | `C_DISCIPLINE_PROBATION` | Disputes | advanced |  | probationary_period |
|  | `C_HEALTH_MEDICAL_ACTIVE_PLAN_DESIGN` | Healthcare | advanced |  | active_medical_plan_design |
|  | `C_JOB_SECURITY_SEVERANCE` | Security | advanced |  | severance |
|  | `C_LABOR_MANAGEMENT_COMMITTEE` | Safety | advanced |  | labor_management_committee |
|  | `C_PREMIUM_SHIFT` | Compensation | advanced |  | shift_differential |
|  | `C_PREMIUM_STANDBY_ON_CALL` | Compensation | advanced |  | standby_on_call_pay |
|  | `C_UNION_ACCESS_BUSINESS` | Recognition | advanced |  | union_business_access |

Rank 13 from the report, agreement duration/effective dates/renewal/reopeners, remains a future document-level metadata target rather than a provision concept. The provision schemas now include literal date strings when a date is part of a specific clause, but agreement-wide term extraction should be modeled separately later.

## Evaluation Guidance

Evaluation should prioritize exact agreement on `exists`, exact agreement on boolean flags, numeric agreement within provision-specific tolerances, and direct string matching or adjudicated near-matching for typed string-list attributes. `summarize` should be reviewed only to diagnose structured disagreements.
