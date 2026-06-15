#!/usr/bin/env python3
"""
Generate provision UI schema for the annotation tool.

Outputs JSON to stdout mapping each concept_id to:
    {
        "format": "binary" | "quantitative" | "complex",
        "description": str,           # generic provision description (class docstring)
        "flags": [str, ...],          # boolean flag field names (complex only)
        "string_fields": [str, ...],  # typed string-list attribute names (all formats)
        "meta": {                     # ProvisionMeta, identifies tier/rank
            "priority_tier": "core" | "conditional_core" | "advanced" | "standard",
            "rank": int | null,
            "priority_score": int | null,
            "difficulty": "low" | "medium" | "high" | null,
            "core_family": str | null,
            "notes": [str, ...]
        }
    }

Usage:
    python structures/generate_ui_schema.py > annotation_ui/lib/provision-schemas.json
"""
import json
import sys
import os
import typing

# Allow running from repo root or from structures/
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from structures import PROVISION_FORMAT_REGISTRY, PROVISION_EXTRACTION_REGISTRY

schema = {}
for concept_id, fmt in PROVISION_FORMAT_REGISTRY.items():
    cls = PROVISION_EXTRACTION_REGISTRY[concept_id]
    entry: dict = {
        "format": fmt,
        # Generic provision description (class docstring), used as the card
        # subtext in the annotation UI — not a document-specific example.
        "description": (cls.__doc__ or "").strip(),
        "flags": [],
        "string_fields": list(cls.string_detail_fields),
        "meta": cls.meta.model_dump(mode="json"),
    }
    if fmt == "complex":
        hints = typing.get_type_hints(cls)
        if "flags" in hints:
            flags_type = hints["flags"]
            args = typing.get_args(flags_type)
            flags_cls = next(
                (a for a in args if isinstance(a, type) and a.__name__ != "NoneType"),
                None,
            )
            if flags_cls:
                entry["flags"] = list(flags_cls.model_fields.keys())
    schema[concept_id] = entry

print(json.dumps(schema, indent=2))
