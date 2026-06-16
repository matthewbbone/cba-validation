"use client";

import type { ProvisionAnnotation, ProvisionSchema, AnnotationValue, AnnotationDuration } from "@/lib/types";

// ── Helpers ───────────────────────────────────────────────────────────────────

function emptyValue(): AnnotationValue {
  return {
    money: null, percent: null, duration: null, number: null,
    multiplier: null, included: null, employer_paid: null, employee_paid: null,
  };
}

function emptyStringFields(schema: ProvisionSchema): Record<string, string[]> {
  const fields: Record<string, string[]> = {};
  for (const f of schema.string_fields ?? []) fields[f] = [];
  return fields;
}

function emptyAnnotation(conceptId: string, category: string, schema: ProvisionSchema): ProvisionAnnotation {
  const base = {
    concept_id: conceptId,
    category,
    format: schema.format,
    exists: null,
    summarize: "",
    string_fields: emptyStringFields(schema),
  };
  if (schema.format === "quantitative") return { ...base, value: emptyValue() };
  if (schema.format === "complex") {
    const flags: Record<string, boolean | null> = {};
    for (const f of schema.flags) flags[f] = null;
    return { ...base, values: [], flags };
  }
  return base;
}

function flagLabel(name: string): string {
  return name.replace(/_/g, " ").replace(/^\w/, (c) => c.toUpperCase());
}

// Plain-language label + helper text for the typed "key term" fields. Field
// names are shared across provisions, so one shared map keeps them consistent.
const FIELD_INFO: Record<string, { label: string; help: string }> = {
  eligible_employee_groups: { label: "Eligible employee groups", help: "Which workers qualify for this benefit (e.g. \"full-time staff\", \"employees with 1+ year of service\")." },
  covered_employee_groups: { label: "Covered employee groups", help: "Which workers this provision applies to." },
  excluded_employee_groups: { label: "Excluded employee groups", help: "Which workers are specifically left out." },
  included_employee_groups: { label: "Included employee groups", help: "Job groups the contract specifically includes." },
  affected_employee_groups: { label: "Affected employee groups", help: "Which workers are affected (e.g. by a layoff)." },
  vesting_terms: { label: "Vesting terms", help: "How long someone must work before the benefit is locked in and theirs to keep (e.g. \"5 years of service\")." },
  occupation_names: { label: "Job / occupation names", help: "Specific job titles named in the contract (e.g. \"Electrician\", \"Registered Nurse\")." },
  classification_names: { label: "Classification names", help: "Pay grades or job classifications named (e.g. \"Grade 3\", \"Journeyman\")." },
  geographic_areas: { label: "Geographic areas", help: "Regions, cities, or zones named (e.g. \"King County\")." },
  effective_dates: { label: "Effective dates", help: "Dates the terms take effect (e.g. \"July 1, 2024\")." },
  eligible_filers: { label: "Who can file a grievance", help: "Who is allowed to start the grievance process (e.g. \"any employee\", \"the union\")." },
  excluded_claim_types: { label: "Excluded claim types", help: "Types of disputes that cannot use this process (e.g. \"probationary discharge\")." },
  deadline_terms: { label: "Deadlines", help: "Time limits named in the contract (e.g. \"within 10 working days\")." },
  arbitrator_selection_terms: { label: "How the arbitrator is chosen", help: "The method for picking the arbitrator (e.g. \"from a list provided by the American Arbitration Association\")." },
  remedy_limit_terms: { label: "Limits on the arbitrator", help: "Limits on what the arbitrator may order (e.g. \"no punitive damages\")." },
  trigger_terms: { label: "What triggers the pay", help: "The condition that earns the pay (e.g. \"over 8 hours in a day\", \"over 40 hours in a week\")." },
  coverage_tiers: { label: "Coverage tiers", help: "Coverage levels named (e.g. \"employee only\", \"employee + family\")." },
  service_band_names: { label: "Service tiers", help: "Length-of-service brackets that change the benefit (e.g. \"after 5 years\", \"10-15 years\")." },
  exception_terms: { label: "Exceptions", help: "Situations where the rule does not apply." },
  bargaining_unit_descriptions: { label: "Bargaining unit description", help: "How the contract describes the overall group of covered jobs." },
  seniority_type_names: { label: "Seniority types", help: "Kinds of seniority named (e.g. \"plant-wide\", \"classification\")." },
  seniority_group_names: { label: "Seniority groups", help: "The groups within which seniority is tracked." },
  break_in_service_terms: { label: "Break-in-service rules", help: "What interrupts or resets seniority (e.g. \"a layoff over 12 months\")." },
  tie_breaker_terms: { label: "Tie-breakers", help: "How ties in seniority are settled (e.g. \"by lottery\", \"by birth date\")." },
};

function fieldInfo(name: string): { label: string; help: string } {
  return FIELD_INFO[name] ?? { label: flagLabel(name), help: "" };
}

// ── Tri-state flag radio ──────────────────────────────────────────────────────

function FlagRow({ name, groupName, value, onChange }: {
  name: string;       // display label (the flag's field name)
  groupName: string;  // deterministic, unique native radio-group name
  value: boolean | null;
  onChange: (v: boolean | null) => void;
}) {
  return (
    <div className="flag-row">
      <span className="flag-label">{flagLabel(name)}</span>
      <div className="flag-radios">
        {([true, false, null] as (boolean | null)[]).map((opt) => {
          const id = `${groupName}-${opt === null ? "null" : String(opt)}`;
          const label = opt === true ? "Yes" : opt === false ? "No" : "?";
          return (
            <label key={id} className={`flag-option${value === opt ? " flag-selected" : ""}`}>
              <input type="radio" name={groupName} checked={value === opt} onChange={() => onChange(opt)} />
              {label}
            </label>
          );
        })}
      </div>
    </div>
  );
}

// ── Typed string-list attribute (named source terms) ─────────────────────────

function StringListInput({ name, values, onChange }: {
  name: string;
  values: string[];
  onChange: (v: string[]) => void;
}) {
  function addFromInput(el: HTMLInputElement) {
    const term = el.value.trim();
    if (!term) return;
    onChange([...values, term]);
    el.value = "";
  }

  const info = fieldInfo(name);

  return (
    <div className="string-list">
      <label className="string-list-label">{info.label}</label>
      {info.help && <p className="string-list-help">{info.help}</p>}
      <div className="string-list-chips">
        {values.map((v, i) => (
          <span key={i} className="string-chip">
            {v}
            <button
              type="button"
              className="string-chip-remove"
              title="Remove"
              onClick={() => onChange(values.filter((_, j) => j !== i))}
            >
              ×
            </button>
          </span>
        ))}
        <input
          type="text"
          className="string-list-input"
          placeholder="Add term, press Enter…"
          onKeyDown={(e) => {
            if (e.key === "Enter") {
              e.preventDefault();
              addFromInput(e.currentTarget);
            }
          }}
          onBlur={(e) => addFromInput(e.currentTarget)}
        />
      </div>
    </div>
  );
}

// ── QuantitativeValue editor ─────────────────────────────────────────────────

function parseNum(s: string): number | null {
  const n = parseFloat(s);
  return isNaN(n) ? null : n;
}

function ValueEditor({ value, onChange, onRemove, idPrefix }: {
  value: AnnotationValue;
  onChange: (v: AnnotationValue) => void;
  onRemove?: () => void;
  idPrefix: string; // deterministic prefix scoping this value's radio groups
}) {
  function set(patch: Partial<AnnotationValue>) {
    onChange({ ...value, ...patch });
  }

  const dur = value.duration ?? { hours: null, days: null, weeks: null, months: null, years: null };

  return (
    <div className="value-editor">
      {onRemove && (
        <button className="value-remove" onClick={onRemove} title="Remove this value">×</button>
      )}

      <div className="value-grid">
        {/* Money */}
        <div className="value-field">
          <label className="value-field-label">$ Amount</label>
          <input
            type="number"
            step="0.01"
            className="value-input"
            placeholder="e.g. 2.00"
            value={value.money?.amount ?? ""}
            onChange={(e) => set({ money: e.target.value ? { amount: parseFloat(e.target.value) } : null })}
          />
        </div>

        {/* Percent */}
        <div className="value-field">
          <label className="value-field-label">% (enter as %)</label>
          <input
            type="number"
            step="0.01"
            className="value-input"
            placeholder="e.g. 5 for 5%"
            value={value.percent !== null ? (value.percent.value * 100).toFixed(4).replace(/\.?0+$/, "") : ""}
            onChange={(e) => set({ percent: e.target.value ? { value: parseFloat(e.target.value) / 100 } : null })}
          />
        </div>

        {/* Count */}
        <div className="value-field">
          <label className="value-field-label">Count</label>
          <input
            type="number"
            step="0.5"
            className="value-input"
            placeholder="e.g. 8"
            value={value.number ?? ""}
            onChange={(e) => set({ number: parseNum(e.target.value) })}
          />
        </div>

        {/* Multiplier */}
        <div className="value-field">
          <label className="value-field-label">Multiplier (×)</label>
          <input
            type="number"
            step="0.25"
            className="value-input"
            placeholder="e.g. 1.5"
            value={value.multiplier ?? ""}
            onChange={(e) => set({ multiplier: parseNum(e.target.value) })}
          />
        </div>
      </div>

      {/* Duration */}
      <div className="duration-row">
        <span className="value-field-label">Duration</span>
        {(["hours", "days", "weeks", "months", "years"] as (keyof AnnotationDuration)[]).map((unit) => (
          <label key={unit} className="duration-cell">
            <span>{unit.slice(0, 2)}</span>
            <input
              type="number"
              step="0.5"
              className="value-input duration-input"
              placeholder="—"
              value={dur[unit] ?? ""}
              onChange={(e) => {
                const updated = { ...dur, [unit]: parseNum(e.target.value) };
                const anySet = Object.values(updated).some((v) => v !== null);
                set({ duration: anySet ? updated : null });
              }}
            />
          </label>
        ))}
      </div>

      {/* Boolean attributes */}
      <div className="bool-attrs">
        {(["included", "employer_paid", "employee_paid"] as (keyof Pick<AnnotationValue, "included" | "employer_paid" | "employee_paid">)[]).map((attr) => (
          <div key={attr} className="bool-attr-row">
            <span className="value-field-label">{flagLabel(attr)}</span>
            <div className="flag-radios">
              {([null, true, false] as (boolean | null)[]).map((opt) => (
                <label key={String(opt)} className={`flag-option${value[attr] === opt ? " flag-selected" : ""}`}>
                  <input
                    type="radio"
                    name={`${idPrefix}-${attr}`}
                    checked={value[attr] === opt}
                    onChange={() => set({ [attr]: opt })}
                  />
                  {opt === null ? "?" : opt ? "Yes" : "No"}
                </label>
              ))}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

// ── Main ProvisionForm ────────────────────────────────────────────────────────

export interface ProvisionFormProps {
  index: number;
  conceptId: string;
  category: string;
  label: string;
  schema: ProvisionSchema;
  annotation: ProvisionAnnotation;
  onChange: (a: ProvisionAnnotation) => void;
}

export function ProvisionForm({ index, conceptId, label, schema, annotation, onChange }: ProvisionFormProps) {
  function set(patch: Partial<ProvisionAnnotation>) {
    onChange({ ...annotation, ...patch });
  }

  function handleExistsChange(exists: boolean) {
    if (!exists) {
      // Clear all detail fields when marking absent — absent provisions must
      // carry no normalized detail (mirrors validate_presence_consistency).
      const cleared: ProvisionAnnotation = { ...annotation, exists: false, summarize: annotation.summarize };
      cleared.string_fields = emptyStringFields(schema);
      if (schema.format === "quantitative") cleared.value = null;
      if (schema.format === "complex") {
        cleared.values = [];
        const flags: Record<string, boolean | null> = {};
        for (const f of schema.flags) flags[f] = null;
        cleared.flags = flags;
      }
      onChange(cleared);
    } else {
      set({ exists: true });
    }
  }

  const title = schema.title ?? label;
  const description = schema.description ?? "";

  return (
    <div className="provision-card">
      {/* Header */}
      <div className="provision-header">
        <span className="provision-num">{index + 1}.</span>
        <h3 className="provision-title">{title}</h3>
      </div>
      {description && <p className="provision-label">{description}</p>}

      {/* Exists toggle */}
      <div className="exists-row">
        <span className="exists-label">Present in this CBA?</span>
        <div className="flag-radios">
          {[true, false].map((opt) => (
            <label key={String(opt)} className={`flag-option${annotation.exists === opt ? " flag-selected" : ""}`}>
              <input
                type="radio"
                name={`${conceptId}-exists`}
                checked={annotation.exists === opt}
                onChange={() => handleExistsChange(opt)}
              />
              {opt ? "Yes" : "No"}
            </label>
          ))}
        </div>
      </div>

      {/* Detail fields — only when present */}
      {annotation.exists && schema.format === "quantitative" && (
        <div className="detail-section">
          <p className="detail-heading">Value</p>
          <ValueEditor
            value={annotation.value ?? emptyValue()}
            onChange={(v) => set({ value: v })}
            idPrefix={`${conceptId}-value`}
          />
        </div>
      )}

      {annotation.exists && schema.format === "complex" && (
        <div className="detail-section">
          {/* Values list */}
          <div className="detail-heading-row">
            <p className="detail-heading">Values</p>
            <button
              className="btn btn-add"
              onClick={() => set({ values: [...(annotation.values ?? []), emptyValue()] })}
            >
              + Add value
            </button>
          </div>
          {(annotation.values ?? []).length === 0 && (
            <p className="empty-hint">No values added yet.</p>
          )}
          {(annotation.values ?? []).map((v, i) => (
            <ValueEditor
              key={i}
              value={v}
              idPrefix={`${conceptId}-${i}`}
              onChange={(updated) => {
                const next = [...(annotation.values ?? [])];
                next[i] = updated;
                set({ values: next });
              }}
              onRemove={() => {
                const next = [...(annotation.values ?? [])];
                next.splice(i, 1);
                set({ values: next });
              }}
            />
          ))}

          {/* Flags */}
          {schema.flags.length > 0 && (
            <>
              <p className="detail-heading" style={{ marginTop: "0.75rem" }}>Flags</p>
              <div className="flags-grid">
                {schema.flags.map((flagName) => (
                  <FlagRow
                    key={flagName}
                    name={flagName}
                    groupName={`${conceptId}-flag-${flagName}`}
                    value={(annotation.flags ?? {})[flagName] ?? null}
                    onChange={(v) =>
                      set({ flags: { ...(annotation.flags ?? {}), [flagName]: v } })
                    }
                  />
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {/* Typed string-list attributes — key terms copied from the contract */}
      {annotation.exists && (schema.string_fields?.length ?? 0) > 0 && (
        <div className="detail-section">
          <p className="detail-heading">Key terms from the contract</p>
          <p className="detail-hint">
            Optional. If the contract states any of these, type the short phrase and
            press Enter to add it. Skip any that don&apos;t apply or aren&apos;t mentioned.
          </p>
          {schema.string_fields!.map((fieldName) => (
            <StringListInput
              key={fieldName}
              name={fieldName}
              values={(annotation.string_fields ?? {})[fieldName] ?? []}
              onChange={(v) =>
                set({ string_fields: { ...(annotation.string_fields ?? {}), [fieldName]: v } })
              }
            />
          ))}
        </div>
      )}

      {/* Summary — placed last so it follows the detailed fields above */}
      <div className="summary-row">
        <label className="value-field-label">Summary</label>
        <p className="detail-hint">
          In one or two sentences, state the key facts the contract gives for this
          topic — the amounts, rates, durations, or conditions. Describe only what the
          document actually says; don&apos;t add outside knowledge.
        </p>
        <textarea
          className="provision-textarea"
          placeholder="e.g. Overtime is paid at 1.5× the base rate for hours over 40 in a week, and 2× on Sundays."
          value={annotation.summarize}
          onChange={(e) => set({ summarize: e.target.value })}
        />
      </div>
    </div>
  );
}

export { emptyAnnotation };
