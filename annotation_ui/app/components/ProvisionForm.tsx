"use client";

import type { ProvisionAnnotation, ProvisionSchema, AnnotationValue, AnnotationDuration } from "@/lib/types";

// ── Helpers ───────────────────────────────────────────────────────────────────

function emptyValue(): AnnotationValue {
  return {
    money: null, percent: null, duration: null, number: null,
    multiplier: null, included: null, employer_paid: null, employee_paid: null,
  };
}

function normalizeValue(value: Partial<AnnotationValue> | null | undefined): AnnotationValue {
  return {
    money: value?.money ?? null,
    percent: value?.percent ?? null,
    duration: value?.duration
      ? {
          hours: value.duration.hours ?? null,
          days: value.duration.days ?? null,
          weeks: value.duration.weeks ?? null,
          months: value.duration.months ?? null,
          years: value.duration.years ?? null,
        }
      : null,
    number: value?.number ?? null,
    multiplier: value?.multiplier ?? null,
    included: value?.included ?? null,
    employer_paid: value?.employer_paid ?? null,
    employee_paid: value?.employee_paid ?? null,
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
    for (const f of schema.flags ?? []) flags[f] = null;
    return { ...base, values: [], flags };
  }
  return base;
}

function normalizeStringFields(
  value: ProvisionAnnotation["string_fields"],
  schema: ProvisionSchema
): Record<string, string[]> {
  const fields = emptyStringFields(schema);
  for (const fieldName of schema.string_fields ?? []) {
    const fieldValue = value?.[fieldName];
    fields[fieldName] = Array.isArray(fieldValue)
      ? fieldValue.filter((v): v is string => typeof v === "string")
      : [];
  }
  return fields;
}

function normalizeAnnotation(
  annotation: ProvisionAnnotation | undefined,
  conceptId: string,
  category: string,
  schema: ProvisionSchema
): ProvisionAnnotation {
  const base = emptyAnnotation(conceptId, category, schema);
  if (!annotation) return base;

  const normalized: ProvisionAnnotation = {
    ...base,
    exists:
      annotation.exists === true ? true : annotation.exists === false ? false : null,
    summarize: typeof annotation.summarize === "string" ? annotation.summarize : "",
    string_fields: normalizeStringFields(annotation.string_fields, schema),
  };

  if (schema.format === "quantitative") {
    normalized.value = normalizeValue(annotation.value);
  }

  if (schema.format === "complex") {
    normalized.values = Array.isArray(annotation.values)
      ? annotation.values.map((v) => normalizeValue(v))
      : [];
    normalized.flags = {};
    for (const flagName of schema.flags ?? []) {
      const flagValue = annotation.flags?.[flagName];
      normalized.flags[flagName] =
        flagValue === true ? true : flagValue === false ? false : null;
    }
  }

  return normalized;
}

function flagLabel(name: string): string {
  return name.replace(/_/g, " ").replace(/^\w/, (c) => c.toUpperCase());
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

  return (
    <div className="string-list">
      <label className="string-list-label">{flagLabel(name)}</label>
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
  const normalizedValue = normalizeValue(value);

  function set(patch: Partial<AnnotationValue>) {
    onChange(normalizeValue({ ...normalizedValue, ...patch }));
  }

  const dur = normalizedValue.duration ?? { hours: null, days: null, weeks: null, months: null, years: null };

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
            value={normalizedValue.money?.amount ?? ""}
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
            value={normalizedValue.percent !== null ? (normalizedValue.percent.value * 100).toFixed(4).replace(/\.?0+$/, "") : ""}
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
            value={normalizedValue.number ?? ""}
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
            value={normalizedValue.multiplier ?? ""}
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
                <label key={String(opt)} className={`flag-option${normalizedValue[attr] === opt ? " flag-selected" : ""}`}>
                  <input
                    type="radio"
                    name={`${idPrefix}-${attr}`}
                    checked={normalizedValue[attr] === opt}
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

export function ProvisionForm({ index, conceptId, category, label, schema, annotation, onChange }: ProvisionFormProps) {
  const current = normalizeAnnotation(annotation, conceptId, category, schema);

  function set(patch: Partial<ProvisionAnnotation>) {
    onChange({ ...current, ...patch });
  }

  function handleExistsChange(exists: boolean) {
    if (!exists) {
      // Clear all detail fields when marking absent — absent provisions must
      // carry no normalized detail (mirrors validate_presence_consistency).
      const cleared: ProvisionAnnotation = { ...current, exists: false, summarize: current.summarize };
      cleared.string_fields = emptyStringFields(schema);
      if (schema.format === "quantitative") cleared.value = null;
      if (schema.format === "complex") {
        cleared.values = [];
        const flags: Record<string, boolean | null> = {};
        for (const f of schema.flags ?? []) flags[f] = null;
        cleared.flags = flags;
      }
      onChange(cleared);
    } else {
      set({ exists: true });
    }
  }

  const categoryClass = `category-badge category-${category}`;

  return (
    <div className="provision-card">
      {/* Header */}
      <div className="provision-header">
        <span className="provision-num">{index + 1}.</span>
        <span className="provision-id">{conceptId}</span>
        <span className={categoryClass}>{category}</span>
        <span className="format-badge">{schema.format}</span>
        {schema.meta?.priority_tier && (
          <span className="tier-badge" data-tier={schema.meta.priority_tier}>
            {schema.meta.priority_tier.replace(/_/g, " ")}
            {schema.meta.rank != null ? ` · #${schema.meta.rank}` : ""}
          </span>
        )}
      </div>
      <p className="provision-label">{label}</p>

      {/* Exists toggle */}
      <div className="exists-row">
        <span className="exists-label">Present in this CBA?</span>
        <div className="flag-radios">
          {[true, false].map((opt) => (
            <label key={String(opt)} className={`flag-option${current.exists === opt ? " flag-selected" : ""}`}>
              <input
                type="radio"
                name={`${conceptId}-exists`}
                checked={current.exists === opt}
                onChange={() => handleExistsChange(opt)}
              />
              {opt ? "Yes" : "No"}
            </label>
          ))}
        </div>
      </div>

      {/* Summary */}
      <div className="summary-row">
        <label className="value-field-label">Summary</label>
        <textarea
          className="provision-textarea"
          placeholder="Describe what the CBA says about this provision…"
          value={current.summarize}
          onChange={(e) => set({ summarize: e.target.value })}
        />
      </div>

      {/* Detail fields — only when present */}
      {current.exists && schema.format === "quantitative" && (
        <div className="detail-section">
          <p className="detail-heading">Value</p>
          <ValueEditor
            value={current.value ?? emptyValue()}
            onChange={(v) => set({ value: v })}
            idPrefix={`${conceptId}-value`}
          />
        </div>
      )}

      {current.exists && schema.format === "complex" && (
        <div className="detail-section">
          {/* Values list */}
          <div className="detail-heading-row">
            <p className="detail-heading">Values</p>
            <button
              className="btn btn-add"
              onClick={() => set({ values: [...(current.values ?? []), emptyValue()] })}
            >
              + Add value
            </button>
          </div>
          {(current.values ?? []).length === 0 && (
            <p className="empty-hint">No values added yet.</p>
          )}
          {(current.values ?? []).map((v, i) => (
            <ValueEditor
              key={i}
              value={v}
              idPrefix={`${conceptId}-${i}`}
              onChange={(updated) => {
                const next = [...(current.values ?? [])];
                next[i] = updated;
                set({ values: next });
              }}
              onRemove={() => {
                const next = [...(current.values ?? [])];
                next.splice(i, 1);
                set({ values: next });
              }}
            />
          ))}

          {/* Flags */}
          {(schema.flags ?? []).length > 0 && (
            <>
              <p className="detail-heading" style={{ marginTop: "0.75rem" }}>Flags</p>
              <div className="flags-grid">
                {(schema.flags ?? []).map((flagName) => (
                  <FlagRow
                    key={flagName}
                    name={flagName}
                    groupName={`${conceptId}-flag-${flagName}`}
                    value={(current.flags ?? {})[flagName] ?? null}
                    onChange={(v) =>
                      set({ flags: { ...(current.flags ?? {}), [flagName]: v } })
                    }
                  />
                ))}
              </div>
            </>
          )}
        </div>
      )}

      {/* Typed string-list attributes — named source terms, all formats */}
      {current.exists && (schema.string_fields?.length ?? 0) > 0 && (
        <div className="detail-section">
          <p className="detail-heading">Named terms</p>
          <p className="detail-hint">
            Short terms copied from the CBA (occupations, plan names, dates, etc.). Optional.
          </p>
          {schema.string_fields!.map((fieldName) => (
            <StringListInput
              key={fieldName}
              name={fieldName}
              values={(current.string_fields ?? {})[fieldName] ?? []}
              onChange={(v) =>
                set({ string_fields: { ...(current.string_fields ?? {}), [fieldName]: v } })
              }
            />
          ))}
        </div>
      )}
    </div>
  );
}

export { emptyAnnotation, normalizeAnnotation };
