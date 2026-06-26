from __future__ import annotations

import json
import os
from typing import Any, Literal

from google.genai import Client, types
from pydantic import BaseModel, Field

from .bundle import normalize_text, section_text

DEFAULT_VERTEX_MODEL = "gemini-2.5-flash"


class NeopiFactorSummary(BaseModel):
    domain: Literal["Neuroticismo", "Extroversão", "Abertura", "Amabilidade", "Conscienciosidade"]
    summary: str


class DraftSection(BaseModel):
    key: Literal[
        "executive_summary",
        "neopi",
        "profiler",
        "career_anchors",
        "cultural_diagnosis",
        "conclusion",
    ]
    title: str
    paragraphs: list[str] = Field(default_factory=list)
    bullets: list[str] = Field(default_factory=list)
    mandatory_signal_ids: list[str] = Field(default_factory=list)


class DraftedReport(BaseModel):
    report_title: str
    language: str = "pt-BR"
    tone: str = "corporate_respectful"
    sections: list[DraftSection]
    neopi_factor_summaries: list[NeopiFactorSummary] = Field(default_factory=list)
    qa_notes: list[str] = Field(default_factory=list)


def build_generation_payload(bundle: dict[str, Any], coverage: dict[str, Any]) -> dict[str, Any]:
    required_signals = [
        {
            "signal_id": item["signal_id"],
            "signal_type": item["signal_type"],
            "name": item["name"],
            "importance": item["importance"],
            "source_section": item["source_section"],
            "metadata": item["metadata"],
        }
        for item in coverage.get("required_signals", [])
        if item["importance"] == "required"
    ]
    recommended_signals = [
        {
            "signal_id": item["signal_id"],
            "signal_type": item["signal_type"],
            "name": item["name"],
            "importance": item["importance"],
            "source_section": item["source_section"],
            "metadata": item["metadata"],
        }
        for item in coverage.get("required_signals", [])
        if item["importance"] == "recommended"
    ]

    source_snapshot = {
        "person": bundle.get("person", {}),
        "profiler": {
            "dominant_style": bundle.get("profiler", {}).get("dominant_style"),
            "scores": bundle.get("profiler", {}).get("scores", []),
        },
        "career_anchors": bundle.get("career_anchors", {}),
        "cultural_diagnosis": bundle.get("cultural_diagnosis", {}),
        "neopi": {
            "domains": bundle.get("neopi", {}).get("domains", []),
            "facets": bundle.get("neopi", {}).get("facets", []),
            "synthesis_by_domain": bundle.get("neopi", {}).get("synthesis_by_domain", {}),
            "friendly_synthesis_by_domain": bundle.get("neopi", {}).get("friendly_synthesis_by_domain", {}),
        },
        "existing_sections": bundle.get("report_template", {}).get("sections", {}),
    }

    system_instruction = (
        "Voce escreve relatorios organizacionais em portugues do Brasil. "
        "Use linguagem corporativa, respeitosa, nao clinica e baseada apenas "
        "nos sinais fornecidos. Preserve todos os sinais obrigatorios. "
        "Nao invente fatos, nao use diagnosticos clinicos e nao force a citacao "
        "de indicadores medios. Ao reescrever trechos do NEO PI-R, preserve o significado "
        "tecnico do texto original, mas traduza para uma linguagem mais acolhedora, "
        "organizacional e orientada a desenvolvimento. Evite rotulos duros ou expressoes "
        "como medo, apatia, despreparo, rigidez ou hostilidade quando houver formulacoes "
        "mais profissionais e precisas disponiveis. Prefira termos como tendencia, cautela, "
        "seriedade, constancia, momento atual e pontos de atencao. Nos fatores Neuroticismo, "
        "Amabilidade e Conscienciosidade, redobre o cuidado para evitar julgamentos de valor "
        "ou formulacoes que possam soar invasivas, estigmatizantes ou excessivamente negativas. "
        "Responda somente em JSON valido conforme o schema."
    )

    user_prompt = (
        "Gere um rascunho estruturado para um relatorio de analise de perfil.\n\n"
        "Regras:\n"
        "- todos os sinais obrigatorios devem aparecer nas secoes apropriadas\n"
        "- sinais recomendados podem aparecer se ajudarem a explicar o perfil\n"
        "- o tom deve ser respeitoso e organizacional\n"
        "- a secao de conclusao deve ser objetiva\n"
        "- se houver texto existente aproveitavel, pode reutilizar e reescrever\n"
        "- quando o estilo dominante do Profiler for composto (ex: 'Comunicador Planejador' ou 'Planejador Comunicador Analista'), mencione TODOS os estilos listados explicitamente na secao de Profiler; nao omita nenhum\n"
        "- se as linhas de conclusao fornecidas como 'bullets' ja estiverem numeradas (padrao '1-', '2-' etc.), use-as como base principal da conclusao, reescrevendo em tom profissional mas preservando o conteudo\n\n"
        "Orientacoes especificas para o NEO PI-R:\n"
        "- use o texto original como fonte principal e nao perca o sentido tecnico\n"
        "- transforme a linguagem para um tom profissional, claro e mais amigavel\n"
        "- nao use palavras que soem estigmatizantes ou excessivamente duras\n"
        "- quando houver uma formulacao sensivel, prefira uma leitura de tendencia ou contexto\n"
        "- preserve pontos fortes, riscos e cuidados, mas com boa comunicacao\n\n"
        "Saida esperada:\n"
        "- preencha `sections` normalmente\n"
        "- preencha `neopi_factor_summaries` com 1 resumo por fator do NEO PI-R\n"
        "- cada resumo do NEO deve ter 1 ou 2 frases, ser fiel ao texto fonte e caber bem em uma planilha\n"
        "- em Neuroticismo, fale em sensibilidade a pressao, frustracao e necessidade de pausas ou regulacao, sem termos como descontrole, medo ou impulsividade como rotulo\n"
        "- em Amabilidade, descreva assertividade, valorizacao de si e cuidado com a forma da interacao, sem termos como superioridade, presuncao ou arrogancia\n"
        "- em Conscienciosidade, descreva necessidade de estrutura, preparo, planejamento e avaliacao, sem termos como despreparo, irresponsabilidade ou precipitacao como rotulo\n\n"
        f"Sinais obrigatorios:\n{json.dumps(required_signals, ensure_ascii=False, indent=2)}\n\n"
        f"Sinais recomendados:\n{json.dumps(recommended_signals, ensure_ascii=False, indent=2)}\n\n"
        f"Fonte estruturada:\n{json.dumps(source_snapshot, ensure_ascii=False, indent=2)}"
    )

    return {
        "model": os.getenv("VERTEX_MODEL", DEFAULT_VERTEX_MODEL),
        "system_instruction": system_instruction,
        "user_prompt": user_prompt,
        "response_schema": DraftedReport.model_json_schema(),
    }


def build_template_fallback(bundle: dict[str, Any], coverage: dict[str, Any]) -> dict[str, Any]:
    person = bundle.get("person", {})
    name = person.get("name") or "Pessoa avaliada"
    profiler_style = bundle.get("profiler", {}).get("dominant_style") or "perfil misto"
    top_anchors = [item["name"] for item in bundle.get("career_anchors", {}).get("top_anchors", [])]
    top_cultures = [item["culture"] for item in bundle.get("cultural_diagnosis", {}).get("top_cultures", [])]

    executive_summary = (
        f"{name} apresenta predominio comportamental {profiler_style.lower()}, "
        f"com maior aderencia as ancoras {', '.join(top_anchors) if top_anchors else 'mais relevantes do questionario'} "
        f"e preferencia por contextos culturais {', '.join(top_cultures) if top_cultures else 'mais aderentes ao resultado'}."
    )

    signal_map = {}
    for item in coverage.get("required_signals", []):
        signal_map.setdefault(item["source_section"], []).append(item["signal_id"])

    conclusion_lines = bundle.get("report_template", {}).get("sections", {}).get("conclusion", [])
    conclusion_bullets = [line for line in conclusion_lines if normalize_text(line).startswith(tuple(str(i) for i in range(1, 10)))]
    if not conclusion_bullets:
        conclusion_bullets = [
            "Consolidar os pontos fortes observados no perfil predominante.",
            "Monitorar riscos de sobrecarga e dispersao quando houver excesso de demandas simultaneas.",
        ]

    draft = DraftedReport(
        report_title=f"Analise de Perfil - {name}",
        sections=[
            DraftSection(
                key="executive_summary",
                title="Resumo Executivo",
                paragraphs=[executive_summary],
                mandatory_signal_ids=[item["signal_id"] for item in coverage.get("required_signals", []) if item["importance"] == "required"],
            ),
            DraftSection(
                key="neopi",
                title="NEO PI-R",
                paragraphs=_existing_or_fallback(bundle, "neopi", ["Resultados do NEO PI-R organizados para revisao."]),
                mandatory_signal_ids=signal_map.get("neopi", []),
            ),
            DraftSection(
                key="profiler",
                title="Profiler",
                paragraphs=_existing_or_fallback(bundle, "profiler", [f"Predomina o estilo {profiler_style}."]),
                mandatory_signal_ids=signal_map.get("profiler", []),
            ),
            DraftSection(
                key="career_anchors",
                title="Ancoras de Carreira",
                paragraphs=_existing_or_fallback(
                    bundle,
                    "career_anchors",
                    [f"As ancoras mais fortes foram {', '.join(top_anchors)}." if top_anchors else "Anchors disponiveis para revisao."],
                ),
                mandatory_signal_ids=signal_map.get("career_anchors", []),
            ),
            DraftSection(
                key="cultural_diagnosis",
                title="Diagnostico Cultural",
                paragraphs=_existing_or_fallback(
                    bundle,
                    "cultural_diagnosis",
                    [f"As preferencias culturais mais fortes foram {', '.join(top_cultures)}." if top_cultures else "Preferencias culturais disponiveis para revisao."],
                ),
                mandatory_signal_ids=signal_map.get("cultural_diagnosis", []),
            ),
            DraftSection(
                key="conclusion",
                title="Conclusao",
                bullets=conclusion_bullets,
                mandatory_signal_ids=[item["signal_id"] for item in coverage.get("required_signals", []) if item["importance"] == "required"],
            ),
        ],
        neopi_factor_summaries=_fallback_neopi_factor_summaries(bundle),
        qa_notes=[
            "Fallback local gerado sem chamada ao Vertex AI.",
            "Use o preview salvo para enviar a mesma estrutura ao modelo quando as credenciais estiverem disponiveis.",
        ],
    )
    return draft.model_dump()


def _fallback_neopi_factor_summaries(bundle: dict[str, Any]) -> list[NeopiFactorSummary]:
    synthesis_map = bundle.get("neopi", {}).get("friendly_synthesis_by_domain") or bundle.get("neopi", {}).get("synthesis_by_domain", {})
    summaries: list[NeopiFactorSummary] = []
    for domain_name in ["Neuroticismo", "Extroversão", "Abertura", "Amabilidade", "Conscienciosidade"]:
        raw_text = str(synthesis_map.get(domain_name) or "").strip()
        if not raw_text:
            continue
        summaries.append(NeopiFactorSummary(domain=domain_name, summary=raw_text))
    return summaries


def _existing_or_fallback(bundle: dict[str, Any], section_name: str, fallback: list[str]) -> list[str]:
    raw = bundle.get("report_template", {}).get("sections", {}).get(section_name, [])
    if not raw:
        return fallback
    cleaned = []
    for line in raw:
        normalized = normalize_text(str(line))
        if normalized.startswith("3.") or normalized.startswith("iv.") or normalized == "a partir dos indicadores de seu perfil, apresenta:":
            continue
        cleaned.append(str(line))
    return cleaned or fallback


def prepare_vertex_request_preview(bundle: dict[str, Any], coverage: dict[str, Any]) -> dict[str, Any]:
    return {
        "mode": "preview",
        **build_generation_payload(bundle, coverage),
    }


def generate_draft_with_vertex(
    bundle: dict[str, Any],
    coverage: dict[str, Any],
    *,
    project: str | None = None,
    location: str | None = None,
    model: str | None = None,
) -> dict[str, Any]:
    payload = build_generation_payload(bundle, coverage)
    project_id = project or os.getenv("GOOGLE_CLOUD_PROJECT")
    region = location or os.getenv("GOOGLE_CLOUD_LOCATION")
    model_name = model or payload["model"]

    if not project_id or not region:
        raise ValueError("GOOGLE_CLOUD_PROJECT and GOOGLE_CLOUD_LOCATION are required for live Vertex calls.")

    client = Client(vertexai=True, project=project_id, location=region)
    response = client.models.generate_content(
        model=model_name,
        contents=payload["user_prompt"],
        config=types.GenerateContentConfig(
            system_instruction=payload["system_instruction"],
            response_mime_type="application/json",
            response_schema=payload["response_schema"],
            temperature=0.2,
        ),
    )
    return json.loads(response.text)
