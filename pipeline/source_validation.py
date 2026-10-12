from __future__ import annotations

import json
from collections import Counter
from pathlib import Path
from typing import Any

from .common import ROOT, PipelineError

UTET_ROOT = ROOT / "data" / "utet" / "bank-v2"
SCHEMA_DIR = UTET_ROOT / "schemas"


class SchemaValidationFailure(PipelineError):
    pass


def _load_schemas(schema_dir: Path) -> tuple[dict[str, dict[str, Any]], Any]:
    try:
        from jsonschema import Draft202012Validator, validators
        from referencing import Registry, Resource
    except ImportError as exc:  # pragma: no cover - covered by CLI dependency smoke test
        raise PipelineError("Install pinned pipeline dependencies with `python -m pip install -r requirements.txt`.") from exc

    schemas: dict[str, dict[str, Any]] = {}
    for path in sorted(schema_dir.glob("*.schema.json")):
        try:
            schemas[path.name] = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise PipelineError(f"Cannot load UTET schema {path.relative_to(ROOT)}: {exc}") from exc
    if len(schemas) != 12:
        raise PipelineError(f"Expected 12 pinned UTET schemas; found {len(schemas)} in {schema_dir}")

    registry = Registry()
    for name, schema in schemas.items():
        Draft202012Validator.check_schema(schema)
        resource = Resource.from_contents(schema)
        registry = registry.with_resource(schema["$id"], resource)
        registry = registry.with_resource(f"https://tet.local/schemas/{name}", resource)
    return schemas, registry


def validate_utet_sources(root: Path = UTET_ROOT) -> dict[str, Any]:
    """Validate pinned UTET core NDJSON against the vendored Draft 2020-12 schemas."""
    try:
        from jsonschema import validators
    except ImportError as exc:  # pragma: no cover
        raise PipelineError("Install pinned pipeline dependencies with `python -m pip install -r requirements.txt`.") from exc

    schema_dir = root / "schemas"
    schemas, registry = _load_schemas(schema_dir)
    checks = (
        ("exams/utet/paper-1", "questions.ndjson", "question.schema.json"),
        ("paper-forms/utet/paper-1", "appearances.ndjson", "appearance.schema.json"),
        ("paper-forms/utet/paper-1", "forms.ndjson", "paper-form.schema.json"),
        ("exams/utet/paper-1", "stimuli.ndjson", "stimulus.schema.json"),
    )
    counts: Counter[str] = Counter()
    errors: list[str] = []
    for base_rel, basename, schema_name in checks:
        validator_type = validators.validator_for(schemas[schema_name])
        validator = validator_type(schemas[schema_name], registry=registry)
        for path in sorted((root / base_rel).rglob(basename)):
            try:
                text = path.read_text(encoding="utf-8")
            except OSError as exc:
                raise PipelineError(f"Cannot read UTET source {path}: {exc}") from exc
            for line_number, line in enumerate(text.splitlines(), 1):
                if not line.strip():
                    continue
                counts[basename] += 1
                try:
                    value = json.loads(line)
                except json.JSONDecodeError as exc:
                    errors.append(f"{path.relative_to(ROOT)}:{line_number}: invalid JSON: {exc.msg}")
                    continue
                for error in validator.iter_errors(value):
                    json_path = ".".join(str(piece) for piece in error.absolute_path) or "<root>"
                    errors.append(f"{path.relative_to(ROOT)}:{line_number}:{json_path}: {error.message}")
                    if len(errors) >= 50:
                        break
                if len(errors) >= 50:
                    break
            if len(errors) >= 50:
                break
        if len(errors) >= 50:
            break

    expected = {
        "questions.ndjson": 900,
        "appearances.ndjson": 900,
        "forms.ndjson": 6,
        "stimuli.ndjson": 24,
    }
    if not errors:
        for filename, expected_count in expected.items():
            actual = counts[filename]
            if actual != expected_count:
                errors.append(f"{filename}: expected {expected_count} records, found {actual}")

    if errors:
        raise SchemaValidationFailure(
            "UTET schema/data validation failed:\n  - " + "\n  - ".join(errors[:50])
        )
    return {
        "schema_files_checked": len(schemas),
        "schema_draft": "2020-12",
        "validated_records": dict(sorted(counts.items())),
        "errors": 0,
    }
