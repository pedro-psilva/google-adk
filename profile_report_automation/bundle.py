from __future__ import annotations

import json
import re
import unicodedata
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

SECTION_ORDER = [
    "executive_summary",
    "neopi",
    "profiler",
    "career_anchors",
    "cultural_diagnosis",
    "conclusion",
]


@dataclass
class ExpectedSignal:
    signal_id: str
    signal_type: str
    importance: str
    name: str
    source_section: str
    patterns: list[str]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_text(value: str) -> str:
    normalized = unicodedata.normalize("NFKD", value)
    without_marks = "".join(ch for ch in normalized if not unicodedata.combining(ch))
    return re.sub(r"\s+", " ", without_marks).strip().lower()


def load_bundle(path: str | Path) -> dict[str, Any]:
    bundle_path = Path(path)
    return json.loads(bundle_path.read_text(encoding="utf-8"))


def save_json(path: str | Path, payload: Any) -> Path:
    output_path = Path(path)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    return output_path


def section_text(bundle: dict[str, Any], section_name: str) -> str:
    raw_section = bundle.get("report_template", {}).get("sections", {}).get(section_name, [])
    if isinstance(raw_section, str):
        return raw_section
    if isinstance(raw_section, list):
        return "\n".join(str(item) for item in raw_section if item)
    return ""


def build_corpora(bundle: dict[str, Any]) -> dict[str, str]:
    sections = {
        "neopi": section_text(bundle, "neopi"),
        "profiler": section_text(bundle, "profiler"),
        "career_anchors": section_text(bundle, "career_anchors"),
        "cultural_diagnosis": section_text(bundle, "cultural_diagnosis"),
        "conclusion": section_text(bundle, "conclusion"),
    }
    sections["all_sections"] = "\n\n".join(
        sections[name]
        for name in ["neopi", "profiler", "career_anchors", "cultural_diagnosis", "conclusion"]
        if sections[name]
    )
    return sections


def text_contains_any(text: str, patterns: list[str]) -> tuple[bool, list[str]]:
    normalized_text = normalize_text(text)
    matches: list[str] = []
    for pattern in patterns:
        normalized_pattern = normalize_text(pattern)
        if normalized_pattern and normalized_pattern in normalized_text:
            matches.append(pattern)
    return bool(matches), matches


def short_style_stem(style_name: str) -> str:
    normalized = normalize_text(style_name)
    if normalized.endswith("or") or normalized.endswith("ora"):
        return normalized[:-1] if normalized.endswith("ora") else normalized
    return normalized


def ensure_list(value: Any) -> list[Any]:
    if value is None:
        return []
    if isinstance(value, list):
        return value
    return [value]
