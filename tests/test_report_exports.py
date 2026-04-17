from __future__ import annotations

import json
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest.mock import patch

from docx import Document
from pypdf import PdfReader


REPO_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO_ROOT))

from profile_report_automation.report_exports import export_local_reports  # noqa: E402


class ReportExportsTests(unittest.TestCase):
    def test_export_local_reports_generates_docx_with_embedded_graphics_and_pdf(self) -> None:
        bundle = {
            "person": {
                "name": "Pessoa Teste",
                "application_date": "2024-10-18 00:00:00",
                "business_unit": "Operacoes",
                "demand": "Teste automatizado",
                "role": "Analista",
            },
            "neopi": {
                "domains": [
                    {"domain": "Neuroticismo", "category": "medio", "t_score": 50},
                    {"domain": "Extroversão", "category": "baixo", "t_score": 39},
                    {"domain": "Abertura", "category": "alto", "t_score": 61},
                    {"domain": "Amabilidade", "category": "medio", "t_score": 52},
                    {"domain": "Conscienciosidade", "category": "alto", "t_score": 64},
                ],
                "friendly_synthesis_by_domain": {
                    "Neuroticismo": "Mantém estabilidade emocional e boa moderação nas reações.",
                    "Extroversão": "Interage com maior discrição e reserva em parte dos contextos.",
                    "Abertura": "Demonstra curiosidade intelectual e abertura a novas ideias.",
                    "Amabilidade": "Equilibra cooperação e assertividade nas relações.",
                    "Conscienciosidade": "Apresenta organização, foco e senso de responsabilidade.",
                },
            },
            "profiler": {
                "scores": [
                    {"style": "Executor", "score": 0.21, "percentage": 21.0},
                    {"style": "Comunicador", "score": 0.19, "percentage": 19.0},
                    {"style": "Planejador", "score": 0.34, "percentage": 34.0},
                    {"style": "Analista", "score": 0.26, "percentage": 26.0},
                ],
                "dominant_style": "Planejador",
            },
            "career_anchors": {
                "scores": [
                    {"name": "Técnico Funcional", "average": 5.0, "description": "Valoriza especialização técnica."},
                    {"name": "Administrativo Geral", "average": 2.6, "description": "Integra esforços em direção a resultados."},
                    {"name": "Autonomia Independência", "average": 4.6, "description": "Busca liberdade para atuar."},
                    {"name": "Segurança Estabilidade", "average": 3.4, "description": "Prefere previsibilidade e estabilidade."},
                    {"name": "Criatividade Empreendedora", "average": 2.6, "description": "Valoriza criar algo novo."},
                    {"name": "Vontade de Servir", "average": 3.4, "description": "Atua em prol de uma causa maior."},
                    {"name": "Puro Desafio", "average": 4.4, "description": "Busca superar problemas complexos."},
                    {"name": "Estilo de Vida", "average": 4.0, "description": "Procura equilíbrio entre vida e carreira."},
                ],
                "top_anchors": [
                    {"name": "Técnico Funcional", "average": 5.0, "description": "Valoriza especialização técnica."},
                    {"name": "Autonomia Independência", "average": 4.6, "description": "Busca liberdade para atuar."},
                ],
            },
            "cultural_diagnosis": {
                "scores": [
                    {"culture": "Clã", "score": 37.5, "description": "Valoriza relações humanas e colaboração."},
                    {"culture": "Inovativa", "score": 20.0, "description": "Prefere abertura a novas ideias."},
                    {"culture": "Mercado", "score": 23.3, "description": "Foca em metas e resultados."},
                    {"culture": "Hierárquica", "score": 19.2, "description": "Valoriza estabilidade e processos claros."},
                ],
                "top_cultures": [
                    {"culture": "Clã", "score": 37.5, "description": "Valoriza relações humanas e colaboração."},
                    {"culture": "Mercado", "score": 23.3, "description": "Foca em metas e resultados."},
                ],
            },
        }
        draft = {
            "sections": [
                {
                    "key": "conclusion",
                    "bullets": [
                        "Consolidar os pontos fortes observados no perfil predominante.",
                        "Monitorar riscos de sobrecarga em cenários de maior pressão.",
                    ],
                }
            ]
        }

        with tempfile.TemporaryDirectory() as temp_dir:
            reports = export_local_reports(temp_dir, bundle, coverage={}, draft=draft)

            docx_path = Path(reports["docx"])
            pdf_path = Path(reports["pdf"])

            self.assertTrue(docx_path.exists())
            self.assertTrue(pdf_path.exists())
            self.assertGreater(docx_path.stat().st_size, 0)
            self.assertGreater(pdf_path.stat().st_size, 0)
            self.assertEqual(len(PdfReader(str(pdf_path)).pages), 3)

            document = Document(str(docx_path))
            self.assertGreaterEqual(len(document.inline_shapes), 3)
            self.assertIn("ANÁLISE DE PERFIL COMPORTAMENTAL", "\n".join(paragraph.text for paragraph in document.paragraphs))

            with zipfile.ZipFile(docx_path) as archive:
                media_files = [name for name in archive.namelist() if name.startswith("word/media/")]
            self.assertGreaterEqual(len(media_files), 4)

    def test_export_local_reports_cleans_partial_files_when_pdf_generation_fails(self) -> None:
        bundle = {
            "person": {
                "name": "Pessoa Teste",
            }
        }
        draft = {"sections": []}

        with tempfile.TemporaryDirectory() as temp_dir:
            docx_calls: list[Path] = []

            def fake_docx_builder(path: str | Path, bundle: dict[str, object], draft: dict[str, object]) -> None:
                target = Path(path)
                docx_calls.append(target)
                target.write_bytes(b"docx-temp")

            with (
                patch("profile_report_automation.report_exports.build_docx_report", side_effect=fake_docx_builder),
                patch(
                    "profile_report_automation.report_exports.build_pdf_report",
                    side_effect=RuntimeError("pdf generation failed"),
                ),
            ):
                with self.assertRaisesRegex(RuntimeError, "pdf generation failed"):
                    export_local_reports(temp_dir, bundle, coverage={}, draft=draft)

            self.assertEqual(len(docx_calls), 1)
            self.assertFalse(docx_calls[0].exists())
            self.assertEqual(list(Path(temp_dir).glob("*.docx")), [])
            self.assertEqual(list(Path(temp_dir).glob("*.pdf")), [])


if __name__ == "__main__":
    unittest.main()
