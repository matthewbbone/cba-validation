"use client";

import type { ProvisionAnnotation, ProvisionSchema, AnnotationValue, AnnotationDuration } from "@/lib/types";

// ── Helpers ───────────────────────────────────────────────────────────────────

function emptyValue(): AnnotationValue {
  return {
    money: null, percent: null, duration: null, number: null,
    multiplier: null, included: null, employer_paid: null, employee_paid: null,
  };
}

function emptyAnnotation(conceptId: string, category: string, schema: ProvisionSchema): ProvisionAnnotation {
  const base = { concept_id: conceptId, category, format: schema.format, exists: null, summarize: "" };
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

export function ProvisionForm({ index, conceptId, category, label, schema, annotation, onChange }: ProvisionFormProps) {
  function set(patch: Partial<ProvisionAnnotation>) {
    onChange({ ...annotation, ...patch });
  }

  function handleExistsChange(exists: boolean) {
    if (!exists) {
      // Clear detail fields when marking absent
      const cleared: ProvisionAnnotation = { ...annotation, exists: false, summarize: annotation.summarize };
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

  const categoryClass = `category-badge category-${category}`;

  return (
    <div className="provision-card">
      {/* Header */}
      <div className="provision-header">
        <span className="provision-num">{index + 1}.</span>
        <span className="provision-id">{conceptId}</span>
        <span className={categoryClass}>{category}</span>
        <span className="format-badge">{schema.format}</span>
      </div>
      <p className="provision-label">{label}</p>

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

      {/* Summary */}
      <div className="summary-row">
        <label className="value-field-label">Summary</label>
        <textarea
          className="provision-textarea"
          placeholder="Describe what the CBA says about this provision…"
          value={annotation.summarize}
          onChange={(e) => set({ summarize: e.target.value })}
        />
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
    </div>
  );
}

export { emptyAnnotation };
