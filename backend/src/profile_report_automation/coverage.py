from __future__ import annotations

from typing import Any

from .bundle import ExpectedSignal, build_corpora, normalize_text, short_style_stem, text_contains_any

KNOWN_PROFILER_STYLES = {"Executor", "Comunicador", "Planejador", "Analista"}

DOMAIN_PATTERNS = {
    "Neuroticismo": ["preocup", "apreens", "tens", "estresse", "frustr", "agitad", "rispid"],
    "Extroversão": ["animad", "agitad", "ocup", "movimento", "comunic", "entusiasm"],
    "Abertura": ["pragmat", "concret", "curios", "abstrat", "novas ideias", "resistent"],
    "Amabilidade": ["comedid", "ponto de vista", "racional", "fatos", "cordial", "simpat"],
    "Conscienciosidade": ["determin", "responsab", "ambic", "realiz", "disciplina", "obrigac", "metas"],
}

FACET_PATTERNS = {
    "Ansiedade": ["preocup", "apreens", "futuro"],
    "Raiva": ["raiva", "irrit", "rispid", "hostil", "frustr"],
    "Depressão": ["triste", "desesper", "desanima", "desencoraj"],
    "Embaraço": ["constrang", "desconfort", "angust"],
    "Impulsividade": ["impuls", "frustr", "resistir"],
    "Vulnerabilidade": ["pressao", "insegur", "estresse", "decisoes"],
    "Acolhimento caloroso": ["vinculos", "simpat", "formal", "reservad"],
    "Gregarismo": ["companhia", "grupos", "interagir", "sozinh"],
    "Assertividade": ["afirmativ", "comandos", "orientac", "posicion"],
    "Atividade": ["dinam", "entusiasm", "vagar"],
    "Busca de sensações": ["animad", "agitad", "sereno", "sensacoes"],
    "Emoções positivas": ["otim", "alegre", "lado positivo", "bem humor"],
    "Fantasia": ["imagin", "criativ"],
    "Estética": ["arte", "estetic"],
    "Sentimentos": ["sentimentos", "emoc"],
    "Ações variadas": ["rotina", "mudanc", "novas atividades"],
    "Ideias": ["ideias abstratas", "curiosidade intelectual", "interesses intelectuais"],
    "Valores": ["valores", "tradicional", "conservador", "reavaliar"],
    "Confiança": ["confi", "desconfi", "cetic"],
    "Franqueza": ["franqueza", "opiniao", "ponto de vista", "adular"],
    "Altruísmo": ["ajudar", "atenciosa", "cordial", "autocentr"],
    "Complacência": ["ressent", "sarcasmo", "ironia", "compreens"],
    "Modéstia": ["vaidos", "humild", "arrog", "presunc"],
    "Sensibilidade": ["necessidades alheias", "compaix", "realista"],
    "Competência": ["eficien", "desprepar", "informacao", "decisoes"],
    "Ordem": ["organiz", "metod", "planeja"],
    "Senso de dever": ["obrigac", "responsab", "etic", "principios"],
    "Esforço por realizações": ["metas", "ambic", "trabalho", "realiz"],
    "Autodisciplina": ["disciplina", "procrast", "finalizar", "desistir"],
    "Ponderação": ["analisar", "cautel", "prevent", "riscos", "ponder"],
}


def _named_patterns(name: str) -> list[str]:
    normalized = normalize_text(name)
    patterns = [name, normalized]
    if " " in normalized:
        patterns.append(normalized.replace(" ", ""))
    return patterns


def build_expected_signals(bundle: dict[str, Any]) -> list[ExpectedSignal]:
    signals: list[ExpectedSignal] = []

    profiler = bundle.get("profiler", {})
    dominant_style = profiler.get("dominant_style")
    if dominant_style:
        # dominant_style may be a multi-style label (e.g. "Comunicador Planejador").
        # Create one ExpectedSignal per individual style so coverage verification
        # checks that EACH named style appears in the generated text.
        # Only include tokens that are canonical Profiler style names; if none match
        # (e.g. an unusual PDF produced a non-canonical label), fall back to a single
        # signal for the full label string to avoid spurious required-signal failures.
        individual_styles = [s.strip() for s in dominant_style.split() if s.strip() in KNOWN_PROFILER_STYLES]
        if not individual_styles:
            individual_styles = [dominant_style]
        for style_name in individual_styles:
            signals.append(
                ExpectedSignal(
                    signal_id=f"profiler:{normalize_text(style_name)}",
                    signal_type="profiler",
                    importance="required",
                    name=style_name,
                    source_section="profiler",
                    patterns=[style_name, short_style_stem(style_name)],
                    metadata={
                        "scores": profiler.get("scores", []),
                        "dominant_style": dominant_style,
                    },
                )
            )

    for anchor in bundle.get("career_anchors", {}).get("top_anchors", []):
        name = anchor["name"]
        signals.append(
            ExpectedSignal(
                signal_id=f"career_anchor:{normalize_text(name)}",
                signal_type="career_anchor",
                importance="required",
                name=name,
                source_section="career_anchors",
                patterns=_named_patterns(name),
                metadata=anchor,
            )
        )

    for culture in bundle.get("cultural_diagnosis", {}).get("top_cultures", []):
        name = culture["culture"]
        signals.append(
            ExpectedSignal(
                signal_id=f"culture:{normalize_text(name)}",
                signal_type="culture",
                importance="required",
                name=name,
                source_section="cultural_diagnosis",
                patterns=_named_patterns(name),
                metadata=culture,
            )
        )

    for domain in bundle.get("neopi", {}).get("domains", []):
        if not domain.get("citation_candidate"):
            continue
        name = domain["domain"]
        patterns = DOMAIN_PATTERNS.get(name, []) + _named_patterns(name)
        signals.append(
            ExpectedSignal(
                signal_id=f"neopi_domain:{normalize_text(name)}",
                signal_type="neopi_domain",
                importance="required",
                name=name,
                source_section="neopi",
                patterns=patterns,
                metadata=domain,
            )
        )

    for facet in bundle.get("neopi", {}).get("facets", []):
        if not facet.get("citation_candidate"):
            continue
        name = facet["facet"]
        patterns = FACET_PATTERNS.get(name, []) + _named_patterns(name)
        signals.append(
            ExpectedSignal(
                signal_id=f"neopi_facet:{normalize_text(name)}",
                signal_type="neopi_facet",
                importance="recommended",
                name=name,
                source_section="neopi",
                patterns=patterns,
                metadata=facet,
            )
        )

    return signals


def build_possible_medium_signals(bundle: dict[str, Any]) -> list[ExpectedSignal]:
    signals: list[ExpectedSignal] = []
    for domain in bundle.get("neopi", {}).get("domains", []):
        if domain.get("category") != "medio":
            continue
        name = domain["domain"]
        signals.append(
            ExpectedSignal(
                signal_id=f"medium_domain:{normalize_text(name)}",
                signal_type="neopi_domain_medium",
                importance="optional",
                name=name,
                source_section="neopi",
                patterns=DOMAIN_PATTERNS.get(name, []) + _named_patterns(name),
                metadata=domain,
            )
        )

    for facet in bundle.get("neopi", {}).get("facets", []):
        if facet.get("category") != "medio":
            continue
        name = facet["facet"]
        signals.append(
            ExpectedSignal(
                signal_id=f"medium_facet:{normalize_text(name)}",
                signal_type="neopi_facet_medium",
                importance="optional",
                name=name,
                source_section="neopi",
                patterns=FACET_PATTERNS.get(name, []) + _named_patterns(name),
                metadata=facet,
            )
        )
    return signals


def _evaluate_signal(signal: ExpectedSignal, corpora: dict[str, str]) -> dict[str, Any]:
    result = signal.to_dict()
    coverage = {}
    for corpus_name, text in corpora.items():
        matched, matched_patterns = text_contains_any(text, signal.patterns)
        coverage[corpus_name] = {
            "covered": matched,
            "matched_patterns": matched_patterns,
        }
    result["coverage"] = coverage
    return result


def _summarize(results: list[dict[str, Any]], corpus_name: str, importance: str) -> dict[str, Any]:
    scoped = [item for item in results if item["importance"] == importance]
    covered = [item for item in scoped if item["coverage"][corpus_name]["covered"]]
    missing = [item for item in scoped if not item["coverage"][corpus_name]["covered"]]
    return {
        "total": len(scoped),
        "covered": len(covered),
        "missing": len(missing),
        "missing_ids": [item["signal_id"] for item in missing],
    }


def analyze_coverage(bundle: dict[str, Any]) -> dict[str, Any]:
    corpora = build_corpora(bundle)
    expected_signals = build_expected_signals(bundle)
    medium_signals = build_possible_medium_signals(bundle)

    evaluated = [_evaluate_signal(signal, corpora) for signal in expected_signals]
    medium_mentions = [_evaluate_signal(signal, corpora) for signal in medium_signals]

    required_overall = _summarize(evaluated, "all_sections", "required")
    required_conclusion = _summarize(evaluated, "conclusion", "required")
    recommended_overall = _summarize(evaluated, "all_sections", "recommended")
    recommended_conclusion = _summarize(evaluated, "conclusion", "recommended")

    possible_medium_mentions = [
        item
        for item in medium_mentions
        if item["coverage"]["conclusion"]["covered"] or item["coverage"]["all_sections"]["covered"]
    ]

    named_section_mismatches = {
        "career_anchors": _check_named_section(
            corpora.get("career_anchors", ""),
            [item["name"] for item in bundle.get("career_anchors", {}).get("top_anchors", [])],
        ),
        "cultural_diagnosis": _check_named_section(
            corpora.get("cultural_diagnosis", ""),
            [item["culture"] for item in bundle.get("cultural_diagnosis", {}).get("top_cultures", [])],
        ),
    }

    return {
        "person": bundle.get("person", {}),
        "summary": {
            "required_overall": required_overall,
            "required_conclusion": required_conclusion,
            "recommended_overall": recommended_overall,
            "recommended_conclusion": recommended_conclusion,
            "status": "pass" if required_overall["missing"] == 0 else "warn",
        },
        "required_signals": evaluated,
        "possible_medium_mentions": possible_medium_mentions,
        "named_section_checks": named_section_mismatches,
        "notes": bundle.get("notes", []),
    }


def _check_named_section(section_text: str, expected_names: list[str]) -> dict[str, Any]:
    normalized_text = normalize_text(section_text)
    mentioned = [name for name in expected_names if normalize_text(name) in normalized_text]
    missing = [name for name in expected_names if name not in mentioned]
    return {
        "expected": expected_names,
        "mentioned": mentioned,
        "missing": missing,
    }
