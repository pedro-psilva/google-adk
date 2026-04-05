from __future__ import annotations

from typing import Any


def build_google_doc_package(bundle: dict[str, Any], coverage: dict[str, Any], draft: dict[str, Any]) -> dict[str, Any]:
    title = draft.get("report_title") or f"Analise de Perfil - {bundle.get('person', {}).get('name', 'Sem Nome')}"
    requests = []
    cursor = 1

    def insert_block(text: str, named_style: str | None = None) -> None:
        nonlocal cursor
        start = cursor
        requests.append({"insertText": {"location": {"index": cursor}, "text": text}})
        cursor += len(text)
        if named_style:
            requests.append(
                {
                    "updateParagraphStyle": {
                        "range": {"startIndex": start, "endIndex": cursor},
                        "paragraphStyle": {"namedStyleType": named_style},
                        "fields": "namedStyleType",
                    }
                }
            )

    insert_block(f"{title}\n", "HEADING_1")

    for section in draft.get("sections", []):
        insert_block(f"\n{section['title']}\n", "HEADING_2")
        for paragraph in section.get("paragraphs", []):
            insert_block(f"{paragraph}\n")
        for bullet in section.get("bullets", []):
            insert_block(f"- {bullet}\n")

    preview_lines = [f"# {title}", ""]
    for section in draft.get("sections", []):
        preview_lines.append(f"## {section['title']}")
        preview_lines.extend(section.get("paragraphs", []))
        preview_lines.extend([f"- {bullet}" for bullet in section.get("bullets", [])])
        preview_lines.append("")

    return {
        "document_title": title,
        "markdown_preview": "\n".join(preview_lines).strip(),
        "google_docs_requests": requests,
        "source_bundle_person": bundle.get("person", {}),
        "coverage_summary": coverage.get("summary", {}),
    }


def build_google_sheets_package(bundle: dict[str, Any], coverage: dict[str, Any], draft: dict[str, Any]) -> dict[str, Any]:
    overview_rows = [
        ["Campo", "Valor"],
        ["Nome", bundle.get("person", {}).get("name", "")],
        ["Data da aplicacao", bundle.get("person", {}).get("application_date", "")],
        ["Unidade", bundle.get("person", {}).get("business_unit", "")],
        ["Demanda", bundle.get("person", {}).get("demand", "")],
        ["Cargo", bundle.get("person", {}).get("role", "")],
        ["Profiler dominante", bundle.get("profiler", {}).get("dominant_style", "")],
    ]

    signal_rows = [["Signal ID", "Tipo", "Importancia", "Nome", "Coberto no relatorio", "Coberto na conclusao"]]
    for item in coverage.get("required_signals", []):
        signal_rows.append(
            [
                item["signal_id"],
                item["signal_type"],
                item["importance"],
                item["name"],
                item["coverage"]["all_sections"]["covered"],
                item["coverage"]["conclusion"]["covered"],
            ]
        )

    draft_rows = [["Secao", "Titulo", "Conteudo"]]
    for section in draft.get("sections", []):
        body_parts = []
        body_parts.extend(section.get("paragraphs", []))
        body_parts.extend([f"- {bullet}" for bullet in section.get("bullets", [])])
        draft_rows.append([section["key"], section["title"], "\n".join(body_parts)])

    coverage_rows = [
        ["Metrica", "Valor"],
        ["Required overall total", coverage.get("summary", {}).get("required_overall", {}).get("total", 0)],
        ["Required overall covered", coverage.get("summary", {}).get("required_overall", {}).get("covered", 0)],
        ["Required overall missing", coverage.get("summary", {}).get("required_overall", {}).get("missing", 0)],
        ["Required conclusion total", coverage.get("summary", {}).get("required_conclusion", {}).get("total", 0)],
        ["Required conclusion covered", coverage.get("summary", {}).get("required_conclusion", {}).get("covered", 0)],
        ["Required conclusion missing", coverage.get("summary", {}).get("required_conclusion", {}).get("missing", 0)],
    ]

    return {
        "spreadsheet_title": title_from_draft(draft),
        "sheets": [
            {"title": "Overview", "rows": overview_rows},
            {"title": "Signals", "rows": signal_rows},
            {"title": "Draft", "rows": draft_rows},
            {"title": "Coverage", "rows": coverage_rows},
        ],
    }


def title_from_draft(draft: dict[str, Any]) -> str:
    return draft.get("report_title") or "Analise de Perfil"
