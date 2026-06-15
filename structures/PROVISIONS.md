# Provision Structures for Deterministic CBA Extraction

This project compares LLM and human extractions from collective bargaining agreements by converting provisions into deterministic attributes. The primary comparison targets remain booleans, numeric values, durations, money amounts, percentages, and multipliers. String-list attributes are retained only where the literal surface forms affect generosity or comparability.

## String Attribute Policy

String attributes should be short, directly verifiable values from the CBA. They should identify who is covered, who is excluded, what unit or classification is being compared, when a wage or benefit applies, or what concrete threshold, deadline, exception, or waiting period controls the value of the provision.

Do not add string attributes merely to capture labels. Plan names, fund names, certification names, step names, program names, union names, forum names, committee names, and broad eligibility prose are intentionally excluded unless a future schema normalizes them into categorical or numeric comparison fields.

## Provision Concepts by Dictionary Category

### Compensation

| Concept ID | Priority | Format | Retained string attributes | Why retained |
|---|---:|---|---|---|
| `C_WAGE_BASE_RATE` | core / 1 | `complex` | `occupation_names`, `classification_names`, `geographic_areas`, `effective_dates` | Retained because it affects comparison scope, timing. |
| `C_PREMIUM_OVERTIME` | core / 2 | `complex` | `trigger_terms`, `covered_employee_groups`, `excluded_employee_groups` | Retained because it affects coverage population, rule boundary. |
| `C_WAGE_INCREASES_COLA` | standard | `complex` | `effective_dates`, `covered_employee_groups` | Retained because it affects coverage population, timing. |
| `C_PREMIUM_CALL_IN_REPORTING` | standard | `complex` | `trigger_terms`, `covered_employee_groups` | Retained because it affects coverage population, rule boundary. |
| `C_PREMIUM_SHIFT` | advanced | `quantitative` | `covered_employee_groups` | Retained because it affects coverage population. |
| `C_WAGE_PROGRESSION` | standard | `complex` | `classification_names`, `occupation_names`, `effective_dates` | Retained because it affects comparison scope, timing. |
| `C_PREMIUM_RESPONSIBILITY_SPECIALTY` | standard | `complex` | `classification_names`, `specialty_names` | Retained because it affects comparison scope. |
| `C_PREMIUM_STANDBY_ON_CALL` | advanced | `quantitative` | `covered_employee_groups` | Retained because it affects coverage population. |
| `C_UNIFORM_CLOTHING_ALLOWANCE` | standard | `quantitative` | `covered_employee_groups` | Retained because it affects coverage population. |
| `C_PREMIUM_ZONE_SUBSISTENCE` | standard | `complex` | `geographic_areas` | Retained because it affects comparison scope. |
| `C_WAGE_GENERAL_INCREASE` | standard | `complex` | `effective_dates`, `covered_employee_groups` | Retained because it affects coverage population, timing. |
| `C_WAGE_APPRENTICE` | standard | `complex` | `classification_names` | Retained because it affects comparison scope. |
| `C_WAGE_SCHEDULED_INCREASE` | standard | `complex` | `effective_dates`, `service_band_names` | Retained because it affects timing, threshold rule. |
| `C_PREMIUM_SUNDAY_HOLIDAY` | standard | `complex` | None | No retained string attributes; compare with booleans, numeric values, and summary only. |
| `C_PREMIUM_FOREMAN` | standard | `quantitative` | `classification_names` | Retained because it affects comparison scope. |
| `C_PREMIUM_HAZARD` | standard | `quantitative` | `covered_employee_groups` | Retained because it affects coverage population. |
| `C_WAGE_INCREASE` | standard | `complex` | `effective_dates`, `covered_employee_groups` | Retained because it affects coverage population, timing. |
| `C_WAGE_LONGEVITY` | standard | `complex` | `service_band_names`, `covered_employee_groups` | Retained because it affects coverage population, threshold rule. |
| `C_WAGE_MERIT_STEP` | standard | `complex` | None | No retained string attributes; compare with booleans, numeric values, and summary only. |
| `C_WAGE_SAVINGS` | standard | `quantitative` | None | No retained string attributes; compare with booleans, numeric values, and summary only. |
| `C_WAGE_VACATION_SUPP` | standard | `quantitative` | None | No retained string attributes; compare with booleans, numeric values, and summary only. |
| `C_WAGE_ACCRUAL_VACATION` | standard | `quantitative` | `covered_employee_groups` | Retained because it affects coverage population. |
| `C_PREMIUM_LEADMAN` | standard | `quantitative` | `classification_names` | Retained because it affects comparison scope. |
| `C_PREMIUM_GROUP_LEADER` | standard | `complex` | None | No retained string attributes; compare with booleans, numeric values, and summary only. |
| `C_WAGE_INCENTIVE` | standard | `complex` | None | No retained string attributes; compare with booleans, numeric values, and summary only. |
| `C_PREMIUM_STANDBY` | standard | `binary` | None | No retained string attributes; compare with booleans, numeric values, and summary only. |

### Disputes

| Concept ID | Priority | Format | Retained string attributes | Why retained |
|---|---:|---|---|---|
| `C_GRIEVANCE_PROCEDURE` | core / 3 | `complex` | `eligible_filers`, `excluded_claim_types`, `deadline_terms` | Retained because it affects rule boundary. |
| `C_ARBITRATION` | core / 3 | `complex` | `arbitrator_selection_terms`, `excluded_claim_types`, `remedy_limit_terms` | Retained because it affects rule boundary. |
| `C_DISCIPLINE_JUST_CAUSE` | core / 10 | `complex` | `covered_employee_groups`, `excluded_employee_groups` | Retained because it affects coverage population. |
| `C_DISCIPLINE_PROGRESSIVE` | standard | `complex` | None | No retained string attributes; compare with booleans, numeric values, and summary only. |
| `C_DISCIPLINE_INVESTIGATION_APPEAL` | standard | `complex` | None | No retained string attributes; compare with booleans, numeric values, and summary only. |
| `C_DISCIPLINE_PROBATION` | advanced | `complex` | `probationary_group_names` | Retained because it affects coverage population. |

### Leave

| Concept ID | Priority | Format | Retained string attributes | Why retained |
|---|---:|---|---|---|
| `C_LEAVE_HOLIDAYS` | core / 11 | `complex` | None | No retained string attributes; compare with booleans, numeric values, and summary only. |
| `C_LEAVE_VACATION` | core / 8 | `complex` | `service_band_names`, `eligible_employee_groups` | Retained because it affects coverage population, threshold rule. |
| `C_LEAVE_SICK` | core / 14 | `complex` | `eligible_employee_groups` | Retained because it affects coverage population. |
| `C_LEAVE_PERSONAL_MISC` | standard | `quantitative` | None | No retained string attributes; compare with booleans, numeric values, and summary only. |
| `C_LEAVE_PARENTAL_FAMILY` | standard | `complex` | None | No retained string attributes; compare with booleans, numeric values, and summary only. |
| `C_LEAVE_BEREAVEMENT` | standard | `quantitative` | None | No retained string attributes; compare with booleans, numeric values, and summary only. |
| `C_LEAVE_PERSONAL` | standard | `quantitative` | None | No retained string attributes; compare with booleans, numeric values, and summary only. |
| `C_LEAVE_SUBSISTENCE` | standard | `quantitative` | `geographic_areas` | Retained because it affects comparison scope. |
| `C_LEAVE_JURY_DUTY` | standard | `quantitative` | None | No retained string attributes; compare with booleans, numeric values, and summary only. |

### Recognition

| Concept ID | Priority | Format | Retained string attributes | Why retained |
|---|---:|---|---|---|
| `C_UNION_ACCESS_BUSINESS` | advanced | `complex` | None | No retained string attributes; compare with booleans, numeric values, and summary only. |
| `C_UNION_SECURITY_DUES_CHECKOFF` | conditional_core / 15 | `complex` | None | No retained string attributes; compare with booleans, numeric values, and summary only. |
| `C_RECOGNITION_COVERAGE_SCOPE` | core / 4 | `complex` | `bargaining_unit_descriptions`, `included_employee_groups`, `excluded_employee_groups` | Retained because it affects coverage population, comparison scope. |
| `C_HIRING_HALL_DISPATCH` | standard | `complex` | None | No retained string attributes; compare with booleans, numeric values, and summary only. |
| `C_UNION_SECURITY` | standard | `binary` | `excluded_employee_groups` | Retained because it affects coverage population. |
| `C_UNION_DUES_CHECKOFF` | standard | `complex` | None | No retained string attributes; compare with booleans, numeric values, and summary only. |

### Healthcare

| Concept ID | Priority | Format | Retained string attributes | Why retained |
|---|---:|---|---|---|
| `C_HEALTH_MEDICAL_ACTIVE_CONTRIBUTION` | core / 6 | `quantitative` | `coverage_tiers`, `eligible_employee_groups` | Retained because it affects coverage population, benefit tier. |
| `C_HEALTH_DENTAL` | standard | `complex` | `coverage_tiers`, `eligible_employee_groups` | Retained because it affects coverage population, benefit tier. |
| `C_HEALTH_MEDICAL_ACTIVE` | standard | `complex` | `coverage_tiers`, `eligible_employee_groups` | Retained because it affects coverage population, benefit tier. |
| `C_HEALTH_LIFE_AD_D` | standard | `complex` | `coverage_tiers`, `eligible_employee_groups` | Retained because it affects coverage population, benefit tier. |
| `C_HEALTH_MEDICAL_ACTIVE_PLAN_DESIGN` | advanced | `complex` | `coverage_tiers` | Retained because it affects benefit tier. |
| `C_HEALTH_DISABILITY_INCOME` | standard | `complex` | `waiting_period_terms` | Retained because it affects threshold rule. |
| `C_HEALTH_RETIREE` | standard | `complex` | `eligible_retiree_groups` | Retained because it affects coverage population. |
| `C_HEALTH_VISION` | standard | `complex` | `coverage_tiers`, `eligible_employee_groups` | Retained because it affects coverage population, benefit tier. |
| `C_HEALTH_EMPLOYER_CONTRIBUTION` | standard | `quantitative` | `coverage_tiers`, `eligible_employee_groups` | Retained because it affects coverage population, benefit tier. |
| `C_HEALTH_ACTIVE` | standard | `complex` | `coverage_tiers`, `eligible_employee_groups` | Retained because it affects coverage population, benefit tier. |
| `C_HEALTH_LIFE_INSURANCE` | standard | `binary` | `coverage_tiers`, `eligible_employee_groups` | Retained because it affects coverage population, benefit tier. |
| `C_HEALTH_ACTIVE_CONTRIBUTION` | standard | `quantitative` | `coverage_tiers`, `eligible_employee_groups` | Retained because it affects coverage population, benefit tier. |
| `C_HEALTH_EXTERNAL_FUND` | standard | `complex` | None | No retained string attributes; compare with booleans, numeric values, and summary only. |
| `C_HEALTH_ACTIVE_PLAN_DESIGN` | standard | `complex` | `coverage_tiers` | Retained because it affects benefit tier. |
| `C_HEALTH_PLAN_DESIGN` | standard | `complex` | `coverage_tiers` | Retained because it affects benefit tier. |
| `C_HEALTH_INSURANCE_BUYOUT` | standard | `quantitative` | `eligible_employee_groups` | Retained because it affects coverage population. |
| `C_HEALTH_WELFARE_FUND` | standard | `quantitative` | None | No retained string attributes; compare with booleans, numeric values, and summary only. |
| `C_HEALTH_DISABILITY` | standard | `quantitative` | `waiting_period_terms` | Retained because it affects threshold rule. |
| `C_HEALTH_PRESCRIPTION_DRUG` | standard | `complex` | None | No retained string attributes; compare with booleans, numeric values, and summary only. |
| `C_HEALTH_BENEFITS` | standard | `binary` | `coverage_tiers`, `eligible_employee_groups` | Retained because it affects coverage population, benefit tier. |

### Safety

| Concept ID | Priority | Format | Retained string attributes | Why retained |
|---|---:|---|---|---|
| `C_SAFETY_PPE_UNSAFE_WORK` | core / 12 | `complex` | None | No retained string attributes; compare with booleans, numeric values, and summary only. |
| `C_LABOR_MANAGEMENT_COMMITTEE` | advanced | `binary` | None | No retained string attributes; compare with booleans, numeric values, and summary only. |
| `C_SAFETY_ASSAULT_VIOLENCE` | standard | `complex` | None | No retained string attributes; compare with booleans, numeric values, and summary only. |
| `C_SAFETY_DRUG_TESTING` | standard | `complex` | `consequence_terms` | Retained because it affects rule boundary. |

### Ancillary

| Concept ID | Priority | Format | Retained string attributes | Why retained |
|---|---:|---|---|---|
| `C_RETIREMENT_PENSION` | core / 7 | `complex` | `eligible_employee_groups`, `vesting_terms` | Retained because it affects coverage population, threshold rule. |
| `C_RETIREMENT_SAVINGS_ANNUITY` | standard | `quantitative` | `eligible_employee_groups`, `vesting_terms` | Retained because it affects coverage population, threshold rule. |
| `C_TRAINING_TUITION_CERTIFICATION` | standard | `complex` | `eligible_employee_groups` | Retained because it affects coverage population. |
| `C_LEGAL_SERVICES_FUND` | standard | `quantitative` | None | No retained string attributes; compare with booleans, numeric values, and summary only. |
| `C_RETIREMENT_INCENTIVE` | standard | `complex` | `eligible_employee_groups`, `effective_dates` | Retained because it affects coverage population, timing. |
| `C_CHILD_DEPENDENT_CARE` | standard | `quantitative` | `eligible_dependent_terms` | Retained because it affects coverage population. |
| `C_TRANSIT_COMMUTER_BENEFIT` | standard | `quantitative` | None | No retained string attributes; compare with booleans, numeric values, and summary only. |

### Security

| Concept ID | Priority | Format | Retained string attributes | Why retained |
|---|---:|---|---|---|
| `C_JOB_SECURITY_LAYOFF_ORDER` | core / 5 | `complex` | `affected_employee_groups`, `exception_terms` | Retained because it affects coverage population, rule boundary. |
| `C_JOB_SECURITY_RECALL` | core / 5 | `complex` | `affected_employee_groups`, `exception_terms` | Retained because it affects coverage population, rule boundary. |
| `C_JOB_SECURITY_SEVERANCE` | advanced | `complex` | `eligible_employee_groups` | Retained because it affects coverage population. |
| `C_JOB_SECURITY_BENEFIT_CONTINUATION` | standard | `complex` | `eligible_employee_groups` | Retained because it affects coverage population. |
| `C_SUBCONTRACTING_WORK_PRESERVATION` | standard | `complex` | `protected_work_terms`, `subcontracting_exception_terms`, `notice_recipient_names` | Retained because it affects rule boundary. |
| `C_SENIORITY_SYSTEM` | core / 9 | `complex` | `seniority_type_names`, `seniority_group_names`, `classification_names`, `break_in_service_terms`, `tie_breaker_terms` | Retained because it affects comparison scope, threshold rule. |
| `C_JOB_POSTING_BIDDING_TRANSFER` | standard | `complex` | `bidding_unit_names`, `eligible_employee_groups`, `trial_period_terms` | Retained because it affects coverage population, comparison scope, threshold rule. |
| `C_JOB_SECURITY_LAYOFF_RECALL` | standard | `complex` | `affected_employee_groups`, `exception_terms` | Retained because it affects coverage population, rule boundary. |
| `C_JOB_SECURITY_SUB_INCOME_BRIDGE` | standard | `complex` | `eligible_employee_groups` | Retained because it affects coverage population. |
| `C_JOB_SECURITY_LAYOFF` | standard | `quantitative` | `affected_employee_groups`, `exception_terms` | Retained because it affects coverage population, rule boundary. |
| `C_JOB_SECURITY_SENIORITY` | standard | `complex` | `seniority_type_names`, `seniority_group_names`, `classification_names`, `break_in_service_terms`, `tie_breaker_terms` | Retained because it affects comparison scope, threshold rule. |
| `C_LIGHT_DUTY_ACCOMMODATION` | standard | `complex` | `eligible_employee_groups` | Retained because it affects coverage population. |
| `C_JOB_SECURITY_SUBCONTRACTING` | standard | `binary` | `protected_work_terms`, `subcontracting_exception_terms`, `notice_recipient_names` | Retained because it affects rule boundary. |
| `C_JOB_SECURITY_RIF_LAYOFF` | standard | `complex` | `affected_employee_groups`, `exception_terms` | Retained because it affects coverage population, rule boundary. |
| `C_JOB_SECURITY_BUMPING` | advanced / 5 | `binary` | `affected_employee_groups`, `exception_terms` | Retained because it affects coverage population, rule boundary. |
| `C_JOB_SECURITY_NO_CONTRACTING_OUT` | standard | `binary` | `protected_work_terms`, `subcontracting_exception_terms`, `notice_recipient_names` | Retained because it affects rule boundary. |

### Scheduling

| Concept ID | Priority | Format | Retained string attributes | Why retained |
|---|---:|---|---|---|
| `C_TIME_REGULAR_SCHEDULE` | standard | `complex` | `covered_employee_groups` | Retained because it affects coverage population. |
| `C_TIME_REST_MEAL_PERIODS` | standard | `complex` | `exception_terms` | Retained because it affects rule boundary. |
| `C_WORKLOAD_CLASS_SIZE_STAFFING` | standard | `complex` | `staffing_ratio_terms`, `duty_terms` | Retained because it affects rule boundary. |
| `C_TIME_SCHEDULE_NOTICE_CHANGE` | standard | `quantitative` | `notice_trigger_terms`, `affected_employee_groups` | Retained because it affects coverage population, rule boundary. |
| `C_TIME_NO_CANCELLATION_SECURITY` | standard | `complex` | `affected_employee_groups` | Retained because it affects coverage population. |

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
