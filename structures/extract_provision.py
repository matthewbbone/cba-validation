from __future__ import annotations

import argparse
import base64
import difflib
import json
import os
import sys
from pathlib import Path
from typing import Any

from pydantic import ValidationError


if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from structures import (  # noqa: E402
    PROVISION_EXTRACTION_REGISTRY,
    PROVISION_FORMAT_REGISTRY,
)


MODEL = "gpt-5.4-mini"
REPO_ROOT = Path(__file__).resolve().parents[1]
CBAS_DIR = REPO_ROOT / "data" / "cbas"
RESULTS_DIR = REPO_ROOT / "structures" / "test_results"


def load_dotenv(path: Path) -> None:
    if not path.exists():
        return

    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key and key not in os.environ:
            os.environ[key] = value


def safe_filename_part(value: str) -> str:
    return "".join(char if char.isalnum() or char in ("-", "_") else "_" for char in value)


def normalize_provision_name(provision_name: str) -> str:
    candidates = {provision_name, provision_name.upper().replace("-", "_")}
    normalized = provision_name.upper().replace("-", "_")
    if not normalized.startswith("C_"):
        candidates.add(f"C_{normalized}")
    candidates.add(normalized.removesuffix("EXTRACTION"))

    class_name_matches = {
        cls.__name__.upper(): concept_id
        for concept_id, cls in PROVISION_EXTRACTION_REGISTRY.items()
    }

    for candidate in candidates:
        if candidate in PROVISION_EXTRACTION_REGISTRY:
            return candidate
        class_match = class_name_matches.get(candidate)
        if class_match is not None:
            return class_match

    possible = sorted(PROVISION_EXTRACTION_REGISTRY)
    suggestions = difflib.get_close_matches(f"C_{normalized}", possible, n=5)
    message = f"Unknown provision name {provision_name!r}."
    if suggestions:
        message += f" Did you mean one of: {', '.join(suggestions)}?"
    raise SystemExit(message)


def resolve_pdf_path(source: str, document_id: str) -> Path:
    cbas_root = CBAS_DIR.resolve()
    source_dir = (CBAS_DIR / source).resolve()
    if not source_dir.is_relative_to(cbas_root):
        raise SystemExit(f"Invalid CBA source {source!r}.")
    if not source_dir.is_dir():
        available = sorted(path.name for path in cbas_root.iterdir() if path.is_dir())
        raise SystemExit(
            f"Unknown CBA source {source!r}. Available sources: {', '.join(available)}"
        )

    if Path(document_id).name != document_id:
        raise SystemExit("document_id must be a PDF stem, not a path.")
    if document_id.lower().endswith(".pdf"):
        raise SystemExit("document_id must be the PDF stem without the .pdf suffix.")

    stem_matches = [path for path in source_dir.glob("*.pdf") if path.stem == document_id]
    if len(stem_matches) == 1:
        return stem_matches[0]

    raise SystemExit(
        f"Could not find PDF with stem {document_id!r} in source {source!r}."
    )


def build_prompt(source: str, document_id: str, provision_id: str) -> str:
    extraction_format = PROVISION_FORMAT_REGISTRY[provision_id]
    model_cls = PROVISION_EXTRACTION_REGISTRY[provision_id]
    schema = model_cls.model_json_schema()
    properties = schema.get("properties", {})
    field_names = ", ".join(properties)
    category = getattr(model_cls, "category", "")
    description = (model_cls.__doc__ or "").strip()

    return (
        "You are extracting one provision from a U.S. collective bargaining "
        "agreement PDF. Return only the structured object requested by the "
        "provided schema.\n\n"
        f"CBA source: {source}\n"
        f"CBA document id: {document_id}\n"
        f"Provision concept_id: {provision_id}\n"
        f"Provision category: {category}\n"
        f"Provision description: {description}\n"
        f"Provision format: {extraction_format}\n"
        f"Schema fields: {field_names}\n\n"
        "Rules:\n"
        "- Always set summarize to a concise natural-language description of what "
        "the PDF says about this provision. This is the only free-text output field.\n"
        "- Always set exists to true if the provision exists in the PDF and false otherwise.\n"
        "- Do not invent values. Use null, empty lists, or exists=false when "
        "the PDF does not support a value.\n"
        "- Do not add quoted evidence, article names, worker group names, labels, "
        "or other string-valued extracted fields.\n"
        "- All fields other than summarize must be numeric values, boolean values, "
        "lists of numeric/boolean values, or null.\n"
        "- For binary provisions, the comparison target is exists.\n"
        "- For quantitative provisions, put the single normalized amount in value; "
        "if absent, set exists=false and value=null.\n"
        "- For complex provisions, put quantitative amounts in values and boolean "
        "inclusions, rights, or requirements in flags."
    )


def call_openai(
    api_key: str,
    pdf_path: Path,
    prompt: str,
    schema: dict[str, Any],
) -> str:
    try:
        from openai import OpenAI
    except ImportError as exc:
        raise RuntimeError(
            "The OpenAI Python SDK is required. Install it with `python3 -m pip "
            "install openai` or run this script in an environment where `openai` "
            "is installed."
        ) from exc

    client = OpenAI(api_key=api_key)
    encoded_pdf = base64.b64encode(pdf_path.read_bytes()).decode("utf-8")

    response = client.responses.create(
        model=MODEL,
        input=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "input_file",
                        "filename": pdf_path.name,
                        "file_data": f"data:application/pdf;base64,{encoded_pdf}",
                    },
                    {
                        "type": "input_text",
                        "text": prompt,
                    },
                ],
            }
        ],
        text={
            "format": {
                "type": "json_schema",
                "name": "provision_extraction",
                "schema": schema,
                "strict": False,
            }
        },
    )

    if not response.output_text:
        raise RuntimeError("OpenAI response did not contain output_text.")
    return response.output_text


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Extract one CBA provision from a local PDF using OpenAI."
    )
    parser.add_argument("source", help="CBA source directory under data/cbas")
    parser.add_argument("document_id", help="PDF filename stem, without the .pdf suffix")
    parser.add_argument(
        "provision_name",
        help="Provision concept id/name, e.g. C_WAGE_BASE_RATE or wage_base_rate",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    load_dotenv(REPO_ROOT / ".env")

    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise SystemExit("OPENAI_API_KEY is not set in the environment or .env file.")

    provision_id = normalize_provision_name(args.provision_name)
    model_cls = PROVISION_EXTRACTION_REGISTRY[provision_id]
    pdf_path = resolve_pdf_path(args.source, args.document_id)

    prompt = build_prompt(args.source, args.document_id, provision_id)
    raw_text = call_openai(
        api_key=api_key,
        pdf_path=pdf_path,
        prompt=prompt,
        schema=model_cls.model_json_schema(),
    )

    try:
        raw_extraction = json.loads(raw_text)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"OpenAI response was not valid JSON: {raw_text}") from exc

    try:
        extraction = model_cls.model_validate(raw_extraction)
    except ValidationError as exc:
        raise RuntimeError(f"OpenAI response did not validate: {exc}") from exc

    RESULTS_DIR.mkdir(parents=True, exist_ok=True)
    output_path = (
        RESULTS_DIR
        / f"{safe_filename_part(args.document_id)}_{safe_filename_part(args.provision_name)}.json"
    )
    output_path.write_text(
        json.dumps(extraction.model_dump(mode="json"), indent=2) + "\n",
        encoding="utf-8",
    )
    print(output_path)


if __name__ == "__main__":
    main()
