from __future__ import annotations

from pathlib import Path
from typing import Any
import json
import yaml
from jsonschema import Draft202012Validator


def _project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def load_design_card(path: str | Path) -> dict[str, Any]:
    path = Path(path)
    with path.open("r", encoding="utf-8") as f:
        if path.suffix.lower() in {".yaml", ".yml"}:
            data = yaml.safe_load(f) or {}
        elif path.suffix.lower() == ".json":
            data = json.load(f)
        else:
            raise ValueError(f"Unsupported design-card format: {path.suffix}")
    if not isinstance(data, dict):
        raise ValueError("Design card must be a mapping/object.")
    return data


def load_schema(schema_path: str | Path | None = None) -> dict[str, Any]:
    if schema_path is None:
        schema_path = _project_root() / "schemas" / "design_card.schema.json"
    with Path(schema_path).open("r", encoding="utf-8") as f:
        return json.load(f)


def validate_design_card(card: dict[str, Any], schema_path: str | Path | None = None) -> list[str]:
    """Return validation errors. Empty list means the card passed schema validation."""
    schema = load_schema(schema_path)
    validator = Draft202012Validator(schema)
    errors = sorted(validator.iter_errors(card), key=lambda e: list(e.path))
    messages: list[str] = []
    for err in errors:
        loc = "/".join(str(x) for x in err.path) or "<root>"
        messages.append(f"{loc}: {err.message}")
    return messages


def summarize_card(card: dict[str, Any]) -> str:
    # Supports both the compact schema used by this project and older nested cards.
    study = card.get("study", {})
    policy_nested = card.get("policy", {})
    data_nested = card.get("data", {})
    design_nested = card.get("design", {})

    question = card.get("question") or study.get("question", "未填写")
    title = card.get("title") or study.get("title") or card.get("policy_event", {}).get("name", "未命名")
    treatment = card.get("treatment", {}).get("definition") or policy_nested.get("treatment", "未填写")
    unit = card.get("unit_of_analysis") or data_nested.get("unit", "未填写")
    structure = card.get("data_requirements", {}).get("structure") or data_nested.get("structure", "未填写")
    primary = card.get("identification_strategy", {}).get("primary_method") or design_nested.get("primary_method", "未填写")
    secondary = card.get("identification_strategy", {}).get("secondary_methods") or design_nested.get("secondary_methods", []) or []
    lines = [
        f"研究：{title}",
        f"问题：{question}",
        f"政策/处理：{treatment}",
        f"数据结构：{structure}；观察单位：{unit}",
        f"优先设计：{primary}；备选：{', '.join(secondary)}",
    ]
    return "\n".join(lines)


def card_to_router_metadata(card: dict[str, Any]) -> dict[str, Any]:
    data = card.get("data", {})
    policy = card.get("policy", {})
    design = card.get("design", {})
    data_req = card.get("data_requirements", {})
    treatment = card.get("treatment", {})
    ident = card.get("identification_strategy", {})
    return {
        "data_structure": data_req.get("structure") or data.get("structure", ""),
        "treatment_timing": treatment.get("timing") or policy.get("timing", ""),
        "assignment_mechanism": treatment.get("assignment_mechanism") or policy.get("assignment_mechanism", ""),
        "unit_of_observation": card.get("unit_of_analysis") or data.get("unit", ""),
        "number_of_treated_units": treatment.get("number_of_treated_units") or policy.get("number_of_treated_units", ""),
        "primary_method": ident.get("primary_method") or design.get("primary_method", ""),
    }
