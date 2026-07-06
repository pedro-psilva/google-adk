import { useState } from "react";
import type { ChangeEvent } from "react";

import { Badge } from "../../atoms/badge/Badge";
import { Button } from "../../atoms/button/Button";
import { MetricCard } from "../../molecules/metric-card/MetricCard";
import {
  buildDownloadUrl,
  loadJsonArtifact,
  runPipeline,
  uploadAssessmentFiles,
} from "../../shared/api/client";
import type {
  AssessmentUploadFiles,
  AssessmentUploadSlotId,
  BundleResponse,
  CoverageResponse,
  DraftResponse,
  PipelineResponse,
  UploadedAssessmentFile,
  UploadedSourceResponse,
} from "../../shared/types/api";

const initialSelectedFiles: AssessmentUploadFiles = {
  neopi: null,
  profiler: null,
  anchors: null,
};

const sectionLabels: Record<string, string> = {
  neopi: "NEO PI-R",
  profiler: "Perfil comportamental",
  career_anchors: "Âncoras de carreira",
  cultural_diagnosis: "Diagnóstico cultural",
  conclusion: "Conclusão",
};

const intakeSlots = [
  {
    id: "neopi",
    label: "NEO PI-R",
    category: "neopi_pdf",
    accept: ".pdf",
    hint: "Selecione o PDF do NEO PI-R.",
  },
  {
    id: "profiler",
    label: "Perfil comportamental",
    category: "profiler_pdf",
    accept: ".pdf",
    hint: "Selecione o PDF do perfil comportamental.",
  },
  {
    id: "anchors",
    label: "Âncoras e diagnóstico",
    category: "anchors_workbook",
    accept: ".xlsx",
    hint: "Selecione a planilha de âncoras e diagnóstico.",
  },
] as const satisfies ReadonlyArray<{
  id: AssessmentUploadSlotId;
  label: string;
  category: string;
  accept: string;
  hint: string;
}>;

type NeopiAttentionItem = {
  id: string;
  name: string;
  category: string;
  detail: string;
};

const negativeNeopiDomainRules: Record<string, { categories: string[]; detail: string }> = {
  Neuroticismo: {
    categories: ["muito alto"],
    detail: "Pede atenção especial a pressão, frustração e autorregulação em contextos mais exigentes.",
  },
  Amabilidade: {
    categories: ["muito baixo"],
    detail: "Pede atenção ao equilíbrio entre assertividade, escuta e abertura ao outro.",
  },
  Conscienciosidade: {
    categories: ["muito baixo"],
    detail: "Pede atenção a preparo, planejamento e avaliação antes da ação.",
  },
};

const negativeNeopiFacetRules: Record<string, { categories: string[]; detail: string }> = {
  Raiva: {
    categories: ["muito alto"],
    detail: "Merece atenção à forma de expressar desconforto e irritação em situações de tensão.",
  },
  Depressão: {
    categories: ["muito alto"],
    detail: "Merece atenção a sinais de desânimo e queda de energia diante de frustrações.",
  },
  Impulsividade: {
    categories: ["muito alto"],
    detail: "Merece atenção ao ritmo de resposta e à ponderação antes de agir.",
  },
  Vulnerabilidade: {
    categories: ["muito alto"],
    detail: "Merece atenção à resposta emocional sob pressão ou sobrecarga.",
  },
  Complacência: {
    categories: ["muito baixo"],
    detail: "Pede atenção à flexibilidade em conflitos e ao tom das interações.",
  },
  Modéstia: {
    categories: ["muito baixo"],
    detail: "Pede atenção ao equilíbrio entre autoconfiança, escuta e percepção do outro.",
  },
  Competência: {
    categories: ["muito baixo"],
    detail: "Pede atenção à percepção de preparo e segurança para decidir.",
  },
  "Senso de dever": {
    categories: ["muito baixo"],
    detail: "Pede atenção à constância com responsabilidades e combinados.",
  },
  Ponderação: {
    categories: ["muito baixo"],
    detail: "Pede atenção à análise de cenários e riscos antes da ação.",
  },
};

function formatSectionLabel(sectionName: string) {
  return sectionLabels[sectionName] ?? sectionName;
}

function formatFileSize(sizeBytes: number) {
  if (sizeBytes >= 1024 * 1024) {
    return `${(sizeBytes / (1024 * 1024)).toFixed(1)} MB`;
  }
  if (sizeBytes >= 1024) {
    return `${Math.round(sizeBytes / 1024)} KB`;
  }
  return `${sizeBytes} B`;
}

function findUploadedSlotFile(files: UploadedAssessmentFile[], category: string) {
  return files.find((file) => file.category === category) ?? null;
}

function isCurrentSelectionUploaded(file: File | null, uploadedFile: UploadedAssessmentFile | null) {
  if (!file || !uploadedFile) {
    return false;
  }
  return uploadedFile.name === file.name && uploadedFile.size_bytes === file.size;
}

function normalizeCategory(category: string | undefined) {
  return (category ?? "").trim().toLowerCase();
}

function buildNeopiAttentionItems(bundle: BundleResponse | null): NeopiAttentionItem[] {
  if (!bundle?.neopi) {
    return [];
  }

  const items: NeopiAttentionItem[] = [];

  for (const domain of bundle.neopi.domains ?? []) {
    const name = domain.domain?.trim();
    const category = domain.category?.trim();
    if (!name || !category) {
      continue;
    }

    const rule = negativeNeopiDomainRules[name];
    if (!rule || !rule.categories.includes(normalizeCategory(category))) {
      continue;
    }

    items.push({
      id: `domain-${name}`,
      name,
      category,
      detail: rule.detail,
    });
  }

  for (const facet of bundle.neopi.facets ?? []) {
    const name = facet.facet?.trim();
    const category = facet.category?.trim();
    if (!name || !category) {
      continue;
    }

    const rule = negativeNeopiFacetRules[name];
    if (!rule || !rule.categories.includes(normalizeCategory(category))) {
      continue;
    }

    items.push({
      id: `facet-${name}`,
      name,
      category,
      detail: rule.detail,
    });
  }

  return items;
}

export function WorkflowPage() {
  const [coverage, setCoverage] = useState<CoverageResponse | null>(null);
  const [draft, setDraft] = useState<DraftResponse | null>(null);
  const [bundle, setBundle] = useState<BundleResponse | null>(null);
  const [pipelineResult, setPipelineResult] = useState<PipelineResponse | null>(null);
  const [uploadedSource, setUploadedSource] = useState<UploadedSourceResponse | null>(null);
  const [selectedFiles, setSelectedFiles] = useState<AssessmentUploadFiles>(initialSelectedFiles);
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [lastAction, setLastAction] = useState("Aguardando arquivos");
  const [error, setError] = useState<string | null>(null);
  const [useAiDrafting, setUseAiDrafting] = useState(true);
  const apiBaseUrl = import.meta.env.DEV ? "" : (import.meta.env.VITE_API_BASE_URL ?? "");

  async function runAction<T>(actionKey: string, callback: () => Promise<T>): Promise<T | null> {
    setBusyAction(actionKey);
    setError(null);

    try {
      const payload = await callback();
      setLastAction(actionKey);
      return payload;
    } catch (caughtError) {
      const message = caughtError instanceof Error ? caughtError.message : "O backend retornou um erro inesperado.";
      setError(message);
      setLastAction(`${actionKey} com falha`);
      return null;
    } finally {
      setBusyAction(null);
    }
  }

  function handleSlotFileSelection(slotId: AssessmentUploadSlotId, event: ChangeEvent<HTMLInputElement>) {
    const nextFile = event.target.files?.[0] ?? null;
    event.target.value = "";

    if (!nextFile) {
      return;
    }

    setSelectedFiles((current) => ({
      ...current,
      [slotId]: nextFile,
    }));
    setCoverage(null);
    setDraft(null);
    setBundle(null);
    setPipelineResult(null);
    setError(null);
    setLastAction("Arquivos atualizados");
  }

  function handleClearSelectedFile(slotId: AssessmentUploadSlotId) {
    setSelectedFiles((current) => ({
      ...current,
      [slotId]: null,
    }));
    setCoverage(null);
    setDraft(null);
    setBundle(null);
    setPipelineResult(null);
    setError(null);
    setLastAction("Arquivos atualizados");
  }

  async function handleRunAutomation() {
    const missingSlots = intakeSlots.filter((slot) => !selectedFiles[slot.id]).map((slot) => slot.label);
    if (missingSlots.length) {
      setError(`Selecione os 3 arquivos obrigatórios antes de gerar a análise. Faltando: ${missingSlots.join(", ")}.`);
      setLastAction("Análise bloqueada");
      return;
    }

    const payload = await runAction("Análise gerada", async () => {
      const uploaded = await uploadAssessmentFiles(apiBaseUrl, selectedFiles);
      const pipeline = await runPipeline(apiBaseUrl, {
        bundleInput: uploaded.bundle_input,
        outputDir: uploaded.output_dir,
        draftMode: useAiDrafting ? "live" : "preview",
      });
      const [bundlePayload, coveragePayload, draftPayload] = await Promise.all([
        loadJsonArtifact<BundleResponse>(apiBaseUrl, pipeline.bundle_path),
        loadJsonArtifact<CoverageResponse>(apiBaseUrl, pipeline.artifacts.coverage_report),
        loadJsonArtifact<DraftResponse>(apiBaseUrl, pipeline.artifacts.draft_output),
      ]);

      return {
        uploaded,
        bundlePayload,
        pipeline,
        coveragePayload,
        draftPayload,
      };
    });
    if (!payload) {
      return;
    }

    setUploadedSource(payload.uploaded);
    setBundle(payload.bundlePayload);
    setPipelineResult(payload.pipeline);
    setCoverage(payload.coveragePayload);
    setDraft(payload.draftPayload);
  }

  const missingOverall =
    coverage?.required_signals.filter((item) => item.importance === "required" && !item.coverage.all_sections.covered) ?? [];
  const missingConclusion =
    coverage?.required_signals.filter((item) => item.importance === "required" && !item.coverage.conclusion.covered) ?? [];
  const mediumMentions = coverage?.possible_medium_mentions ?? [];
  const localDocxPath = pipelineResult?.artifacts.local_report_docx ?? null;
  const localPdfPath = pipelineResult?.artifacts.local_report_pdf ?? null;
  const hasFinalReports = Boolean(localDocxPath || localPdfPath);
  const attentionItems = buildNeopiAttentionItems(bundle);
  const selectedCount = intakeSlots.filter((slot) => selectedFiles[slot.id]).length;
  const canRunAutomation = selectedCount === intakeSlots.length;

  return (
    <div className="page-stack">
      <section className="surface surface--hero workflow-hero workflow-hero--compact">
        <div className="workflow-hero__content">
          <p className="workflow-hero__eyebrow">Análise de perfil</p>
          <h1 className="workflow-hero__title">Gere o relatório final a partir dos 3 arquivos.</h1>
          <p className="workflow-hero__description">
            Selecione um documento em cada card e a geração cuida do resto.
          </p>
        </div>

        <div className="workflow-shortcuts">
          <MetricCard
            label="Arquivos"
            value={`${selectedCount}/3`}
            detail="Documentos selecionados."
            tone={canRunAutomation ? "success" : "warning"}
          />
          <MetricCard
            label="Pendências"
            value={coverage ? String(coverage.summary.required_overall.missing) : "—"}
            detail="Itens obrigatórios ausentes."
            tone={coverage?.summary.required_overall.missing === 0 ? "success" : "warning"}
          />
          <MetricCard
            label="Relatório"
            value={localDocxPath ? "Pronto" : "—"}
            detail="Word final para download."
            tone={localDocxPath ? "success" : "neutral"}
          />
        </div>
      </section>

      <section className="surface surface--panel workflow-panel">
        <div className="panel-heading panel-heading--compact">
          <h2 className="panel-heading__title">Arquivos da avaliação</h2>
        </div>

        <div className="workflow-intake-grid workflow-intake-grid--slots">
          {intakeSlots.map((slot) => {
            const selectedFile = selectedFiles[slot.id];
            const uploadedFile = findUploadedSlotFile(uploadedSource?.files ?? [], slot.category);
            const isUploaded = isCurrentSelectionUploaded(selectedFile, uploadedFile);
            const badgeTone = isUploaded || (!selectedFile && uploadedFile) ? "success" : selectedFile ? "neutral" : "warning";
            const badgeLabel = isUploaded ? "confirmado" : selectedFile ? "selecionado" : uploadedFile ? "recebido" : "pendente";
            const headline = selectedFile?.name ?? uploadedFile?.name ?? slot.hint;
            const meta = selectedFile
              ? formatFileSize(selectedFile.size)
              : uploadedFile
                ? formatFileSize(uploadedFile.size_bytes)
                : slot.accept.toUpperCase().replace(".", "");
            const actionCopy = isUploaded ? "Clique para trocar o arquivo." : "Clique para selecionar o arquivo.";

            return (
              <div key={slot.id} className="workflow-intake-slot">
                <label
                  className={`workflow-intake-card workflow-intake-card--selectable ${isUploaded ? "workflow-intake-card--ready" : ""}`.trim()}
                  htmlFor={`workflow-upload-${slot.id}`}
                >
                  <input
                    id={`workflow-upload-${slot.id}`}
                    className="workflow-intake-card__input"
                    type="file"
                    accept={slot.accept}
                    onChange={(event) => handleSlotFileSelection(slot.id, event)}
                  />
                  <div className="workflow-intake-card__top">
                    <strong>{slot.label}</strong>
                    <Badge tone={badgeTone}>{badgeLabel}</Badge>
                  </div>
                  <p className="workflow-intake-card__filename">{headline}</p>
                  <div className="workflow-intake-card__footer">
                    <span className="workflow-intake-card__action">{actionCopy}</span>
                    <span className="workflow-intake-card__meta">{meta}</span>
                  </div>
                </label>

                {selectedFile ? (
                  <button
                    className="workflow-intake-card__clear"
                    type="button"
                    onClick={() => handleClearSelectedFile(slot.id)}
                  >
                    Limpar
                  </button>
                ) : null}
              </div>
            );
          })}
        </div>

        <div className="workflow-actions">
          <Button busy={busyAction === "Análise gerada"} disabled={!canRunAutomation} onClick={() => void handleRunAutomation()}>
            Gerar análise
          </Button>
          <label className="workflow-actions__toggle">
            <input
              type="checkbox"
              checked={useAiDrafting}
              onChange={(event) => setUseAiDrafting(event.target.checked)}
            />
            <span>Gerar textos com IA (Vertex AI)</span>
          </label>
        </div>

        {!canRunAutomation ? (
          <p className="empty-state">Selecione os 3 arquivos obrigatórios para habilitar a geração.</p>
        ) : null}

        {error ? <p className="result-panel__error">{error}</p> : null}
      </section>

      <div className="workflow-results-grid">
        <section className="surface surface--panel workflow-panel">
          <div className="panel-heading panel-heading--compact">
            <div>
              <h2 className="panel-heading__title">Sinais para ajustar</h2>
            </div>
            <Badge tone={coverage?.summary.status === "pass" ? "success" : "warning"}>
              {coverage ? coverage.summary.status : "aguardando"}
            </Badge>
          </div>

          {coverage ? (
            <div className="workflow-review-stack">
              <article className="workflow-review-card">
                <h3>Faltando no relatório</h3>
                {missingOverall.length ? (
                  <ul className="workflow-review-list">
                    {missingOverall.map((item) => (
                      <li key={item.signal_id}>
                        <strong>{item.name}</strong>
                        <span>{formatSectionLabel(item.source_section)}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="empty-state">Nenhuma pendência no corpo principal.</p>
                )}
              </article>

              <article className="workflow-review-card">
                <h3>Faltando na conclusão</h3>
                {missingConclusion.length ? (
                  <ul className="workflow-review-list">
                    {missingConclusion.map((item) => (
                      <li key={item.signal_id}>
                        <strong>{item.name}</strong>
                        <span>{formatSectionLabel(item.source_section)}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="empty-state">A conclusão já cobre os sinais obrigatórios.</p>
                )}
              </article>

              <article className="workflow-review-card">
                <h3>Menções médias</h3>
                {mediumMentions.length ? (
                  <ul className="workflow-review-list">
                    {mediumMentions.map((item) => (
                      <li key={item.signal_id}>
                        <strong>{item.name}</strong>
                        <span>{formatSectionLabel(item.source_section)}</span>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="empty-state">Nenhum indicador médio destacado para revisão.</p>
                )}
              </article>

              <article className="workflow-review-card">
                <h3>Pontos de atenção</h3>
                {attentionItems.length ? (
                  <ul className="workflow-review-list workflow-review-list--attention">
                    {attentionItems.map((item) => (
                      <li key={item.id}>
                        <strong>{item.name}</strong>
                        <span>{item.category}</span>
                        <p>{item.detail}</p>
                      </li>
                    ))}
                  </ul>
                ) : (
                  <p className="empty-state">Nenhum ponto extremo negativo sinalizado no NEO PI-R.</p>
                )}
              </article>
            </div>
          ) : (
            <p className="empty-state">Depois da geração, esta área mostra o que precisa entrar no texto final.</p>
          )}
        </section>

        <section className="surface surface--panel workflow-panel">
          <div className="panel-heading panel-heading--compact">
            <div>
              <h2 className="panel-heading__title">Rascunho</h2>
            </div>
            <Badge tone={draft ? "success" : "neutral"}>{draft ? "pronto" : "aguardando"}</Badge>
          </div>

          {draft ? (
            <div className="report-preview">
              {draft.sections.map((section) => (
                <article key={section.key} className="report-section">
                  <h3>{section.title}</h3>
                  {(section.paragraphs ?? []).map((paragraph) => (
                    <p key={paragraph}>{paragraph}</p>
                  ))}
                  {(section.bullets ?? []).length ? (
                    <ul>
                      {(section.bullets ?? []).map((bullet) => (
                        <li key={bullet}>{bullet}</li>
                      ))}
                    </ul>
                  ) : null}
                </article>
              ))}
            </div>
          ) : (
            <p className="empty-state">O rascunho aparece aqui depois da geração.</p>
          )}
        </section>
      </div>

      <section className="surface surface--panel workflow-panel">
        <div className="panel-heading panel-heading--compact">
          <h2 className="panel-heading__title">Arquivos finais</h2>
          <Badge tone={hasFinalReports ? "success" : "neutral"}>
            {hasFinalReports ? "pronto" : "aguardando"}
          </Badge>
        </div>

        {hasFinalReports ? (
          <div className="workflow-link-row">
            {localDocxPath ? (
              <a
                className="workflow-link-chip"
                href={buildDownloadUrl(apiBaseUrl, localDocxPath)}
                target="_blank"
                rel="noreferrer"
              >
                Baixar Word
              </a>
            ) : null}
            {localPdfPath ? (
              <a
                className="workflow-link-chip"
                href={buildDownloadUrl(apiBaseUrl, localPdfPath)}
                target="_blank"
                rel="noreferrer"
              >
                Baixar PDF
              </a>
            ) : null}
          </div>
        ) : (
          <p className="empty-state">Os arquivos finais em Word e PDF aparecem aqui após a geração.</p>
        )}
      </section>
    </div>
  );
}
