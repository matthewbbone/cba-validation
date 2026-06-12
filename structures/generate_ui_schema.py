#!/usr/bin/env python3
"""
Generate provision UI schema for the annotation tool.
Outputs JSON to stdout mapping concept_id -> { format, flags[] }.

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
    entry: dict = {"format": fmt, "flags": []}
    if fmt == "complex":
        cls = PROVISION_EXTRACTION_REGISTRY[concept_id]
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
