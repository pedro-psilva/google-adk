import { useState } from "react";
import type { ChangeEvent } from "react";

import { Badge } from "../../atoms/badge/Badge";
import { Button } from "../../atoms/button/Button";
import { Select } from "../../atoms/select/Select";
import { FormField } from "../../molecules/form-field/FormField";
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
  CoverageResponse,
  DraftMode,
  DraftResponse,
  PipelineResponse,
  StudioFormState,
  UploadedAssessmentFile,
  UploadedSourceResponse,
} from "../../shared/types/api";

const initialForm: StudioFormState = {
  apiBaseUrl: import.meta.env.DEV ? "" : (import.meta.env.VITE_API_BASE_URL ?? ""),
  bundleInput: "",
  outputDir: "",
  draftMode: "preview",
};

const initialSelectedFiles: AssessmentUploadFiles = {
  neopi: null,
  profiler: null,
  anchors: null,
};

const sectionLabels: Record<string, string> = {
  neopi: "NEO PI-R",
  profiler: "Perfil comportamental",
  career_anchors: "Ancoras de carreira",
  cultural_diagnosis: "Diagnostico cultural",
  conclusion: "Conclusao",
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
    label: "Ancoras e diagnostico",
    category: "anchors_workbook",
    accept: ".xlsx",
    hint: "Selecione a planilha de ancoras e diagnostico.",
  },
] as const satisfies ReadonlyArray<{
  id: AssessmentUploadSlotId;
  label: string;
  category: string;
  accept: string;
  hint: string;
}>;

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

export function WorkflowPage() {
  const [form, setForm] = useState<StudioFormState>(initialForm);
  const [coverage, setCoverage] = useState<CoverageResponse | null>(null);
  const [draft, setDraft] = useState<DraftResponse | null>(null);
  const [pipelineResult, setPipelineResult] = useState<PipelineResponse | null>(null);
  const [uploadedSource, setUploadedSource] = useState<UploadedSourceResponse | null>(null);
  const [selectedFiles, setSelectedFiles] = useState<AssessmentUploadFiles>(initialSelectedFiles);
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [lastAction, setLastAction] = useState("Aguardando arquivos");
  const [error, setError] = useState<string | null>(null);

  function updateField<K extends keyof StudioFormState>(field: K, value: StudioFormState[K]) {
    setForm((current) => ({ ...current, [field]: value }));
  }

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
    setPipelineResult(null);
    setError(null);
    setLastAction("Arquivos atualizados");
  }

  async function handleUploadFiles() {
    const missingSlots = intakeSlots.filter((slot) => !selectedFiles[slot.id]).map((slot) => slot.label);
    if (missingSlots.length) {
      setError(`Selecione os 3 arquivos antes de enviar. Faltando: ${missingSlots.join(", ")}.`);
      setLastAction("Upload com falha");
      return;
    }

    const payload = await runAction("Arquivos enviados", () => uploadAssessmentFiles(form.apiBaseUrl, selectedFiles));
    if (!payload) {
      return;
    }

    setUploadedSource(payload);
    setForm((current) => ({
      ...current,
      bundleInput: payload.bundle_input,
      outputDir: payload.output_dir,
    }));
    setCoverage(null);
    setDraft(null);
    setPipelineResult(null);
  }

  async function handleRunAutomation() {
    if (!form.bundleInput) {
      setError("Envie os arquivos da avaliacao antes de gerar a analise.");
      setLastAction("Analise bloqueada");
      return;
    }

    const hasPendingUpload = intakeSlots.some((slot) => {
      const selectedFile = selectedFiles[slot.id];
      const uploadedFile = findUploadedSlotFile(uploadedSource?.files ?? [], slot.category);
      return !isCurrentSelectionUploaded(selectedFile, uploadedFile);
    });

    if (hasPendingUpload) {
      setError("Os arquivos foram alterados. Clique em Enviar arquivos para atualizar a base antes de gerar a analise.");
      setLastAction("Analise bloqueada");
      return;
    }

    const payload = await runAction("Analise gerada", async () => {
      const pipeline = await runPipeline(form.apiBaseUrl, form);
      const [coveragePayload, draftPayload] = await Promise.all([
        loadJsonArtifact<CoverageResponse>(form.apiBaseUrl, pipeline.artifacts.coverage_report),
        loadJsonArtifact<DraftResponse>(form.apiBaseUrl, pipeline.artifacts.draft_output),
      ]);

      return {
        pipeline,
        coveragePayload,
        draftPayload,
      };
    });
    if (!payload) {
      return;
    }

    setPipelineResult(payload.pipeline);
    setCoverage(payload.coveragePayload);
    setDraft(payload.draftPayload);
  }

  const missingOverall =
    coverage?.required_signals.filter((item) => item.importance === "required" && !item.coverage.all_sections.covered) ?? [];
  const missingConclusion =
    coverage?.required_signals.filter((item) => item.importance === "required" && !item.coverage.conclusion.covered) ?? [];
  const mediumMentions = coverage?.possible_medium_mentions ?? [];
  const localXlsxPath = pipelineResult?.artifacts.local_report_xlsx ?? null;
  const selectedCount = intakeSlots.filter((slot) => selectedFiles[slot.id]).length;
  const pendingSlotLabels = intakeSlots.filter((slot) => !selectedFiles[slot.id]).map((slot) => slot.label);
  const hasPendingUpload = intakeSlots.some((slot) => {
    const selectedFile = selectedFiles[slot.id];
    const uploadedFile = findUploadedSlotFile(uploadedSource?.files ?? [], slot.category);
    return !isCurrentSelectionUploaded(selectedFile, uploadedFile);
  });
  const canUpload = pendingSlotLabels.length === 0;
  const canRunAutomation = Boolean(form.bundleInput) && !hasPendingUpload;

  return (
    <div className="page-stack">
      <section className="surface surface--hero workflow-hero workflow-hero--compact">
        <div className="workflow-hero__content">
          <p className="workflow-hero__eyebrow">Analise de perfil</p>
          <h1 className="workflow-hero__title">Selecione os 3 arquivos e devolva a planilha final.</h1>
          <p className="workflow-hero__description">
            Escolha um arquivo em cada card, envie a base e gere o `.xlsx` preenchido para revisao final.
          </p>

          <div className="workflow-hero__badges">
            <Badge tone="neutral">Fluxo por arquivos</Badge>
            <Badge tone={uploadedSource && !hasPendingUpload ? "success" : canUpload ? "neutral" : "warning"}>
              {uploadedSource && !hasPendingUpload
                ? "Base pronta"
                : canUpload
                  ? "Pronto para envio"
                  : `${selectedCount}/3 selecionados`}
            </Badge>
            <Badge tone={localXlsxPath ? "success" : "neutral"}>{localXlsxPath ? "Excel pronto" : "Aguardando geracao"}</Badge>
          </div>
        </div>

        <div className="workflow-shortcuts">
          <MetricCard
            label="Arquivos"
            value={String(selectedCount)}
            detail="Cada card recebe um documento especifico da avaliacao."
            tone={canUpload ? "success" : "warning"}
          />
          <MetricCard
            label="Pendencias"
            value={coverage ? String(coverage.summary.required_overall.missing) : "--"}
            detail="Itens obrigatorios ainda ausentes no texto."
            tone={coverage?.summary.required_overall.missing === 0 ? "success" : "warning"}
          />
          <MetricCard
            label="Ultima acao"
            value={lastAction}
            detail={localXlsxPath ? "A planilha final ja pode ser baixada." : "Depois da analise, a planilha final aparece aqui."}
            tone={localXlsxPath ? "success" : "neutral"}
          />
        </div>
      </section>

      <section className="surface surface--panel workflow-panel">
        <div className="panel-heading panel-heading--compact">
          <div>
            <p className="panel-heading__eyebrow">Entrada</p>
            <h2 className="panel-heading__title">Arquivos da avaliacao</h2>
          </div>
        </div>

        <div className="workflow-intake-grid workflow-intake-grid--slots">
          {intakeSlots.map((slot) => {
            const selectedFile = selectedFiles[slot.id];
            const uploadedFile = findUploadedSlotFile(uploadedSource?.files ?? [], slot.category);
            const isUploaded = isCurrentSelectionUploaded(selectedFile, uploadedFile);
            const badgeTone = isUploaded || (!selectedFile && uploadedFile) ? "success" : selectedFile ? "neutral" : "warning";
            const badgeLabel = isUploaded ? "pronto" : selectedFile ? "selecionado" : uploadedFile ? "enviado" : "pendente";
            const headline = selectedFile?.name ?? uploadedFile?.name ?? slot.hint;
            const meta = selectedFile
              ? formatFileSize(selectedFile.size)
              : uploadedFile
                ? formatFileSize(uploadedFile.size_bytes)
                : slot.accept.toUpperCase().replace(".", "");
            const actionCopy = isUploaded
              ? "Clique para trocar o arquivo."
              : selectedFile
                ? "Clique para confirmar no envio."
                : "Clique para selecionar o arquivo.";

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

        <div className="workflow-form-grid">
          <FormField label="Modo" hint="Rascunho rapido ou geracao completa com IA.">
            <Select value={form.draftMode} onChange={(event) => updateField("draftMode", event.target.value as DraftMode)}>
              <option value="preview">Rascunho rapido</option>
              <option value="live">IA completa</option>
            </Select>
          </FormField>
        </div>

        <div className="workflow-actions">
          <Button
            variant="secondary"
            busy={busyAction === "Arquivos enviados"}
            disabled={!canUpload}
            onClick={() => void handleUploadFiles()}
          >
            Enviar arquivos
          </Button>
          <Button busy={busyAction === "Analise gerada"} disabled={!canRunAutomation} onClick={() => void handleRunAutomation()}>
            Gerar analise
          </Button>
        </div>

        {!canUpload ? (
          <p className="empty-state">Selecione os 3 arquivos obrigatorios para habilitar o envio.</p>
        ) : null}

        {uploadedSource && hasPendingUpload ? (
          <p className="empty-state">Voce alterou um ou mais arquivos. Clique em Enviar arquivos para atualizar a base ativa.</p>
        ) : null}

        {uploadedSource ? (
          <div className="workflow-file-group">
            <p className="workflow-file-group__label">Base atual pronta para analise</p>
            <div className="workflow-file-list">
              {uploadedSource.files.map((file) => (
                <span key={`${file.name}-${file.size_bytes}`} className="workflow-file-chip workflow-file-chip--uploaded">
                  <strong>{file.label || file.name}</strong>
                  <span>{file.name}</span>
                </span>
              ))}
            </div>
          </div>
        ) : null}

        {error ? <p className="result-panel__error">{error}</p> : null}
      </section>

      <div className="workflow-results-grid">
        <section className="surface surface--panel workflow-panel">
          <div className="panel-heading panel-heading--compact">
            <div>
              <p className="panel-heading__eyebrow">Revisao</p>
              <h2 className="panel-heading__title">Sinais para ajustar</h2>
            </div>
            <Badge tone={coverage?.summary.status === "pass" ? "success" : "warning"}>
              {coverage ? coverage.summary.status : "aguardando"}
            </Badge>
          </div>

          {coverage ? (
            <div className="workflow-review-stack">
              <article className="workflow-review-card">
                <h3>Faltando no relatorio</h3>
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
                  <p className="empty-state">Nenhuma pendencia no corpo principal.</p>
                )}
              </article>

              <article className="workflow-review-card">
                <h3>Faltando na conclusao</h3>
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
                  <p className="empty-state">A conclusao ja cobre os sinais obrigatorios.</p>
                )}
              </article>

              <article className="workflow-review-card">
                <h3>Mencoes medias</h3>
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
                  <p className="empty-state">Nenhum indicador medio destacado para revisao.</p>
                )}
              </article>
            </div>
          ) : (
            <p className="empty-state">Depois da geracao, esta area mostra o que precisa entrar no texto final.</p>
          )}
        </section>

        <section className="surface surface--panel workflow-panel">
          <div className="panel-heading panel-heading--compact">
            <div>
              <p className="panel-heading__eyebrow">Texto sugerido</p>
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
            <p className="empty-state">O rascunho aparece aqui depois da geracao.</p>
          )}
        </section>
      </div>

      <section className="surface surface--panel workflow-panel">
        <div className="panel-heading panel-heading--compact">
          <div>
            <p className="panel-heading__eyebrow">Saida</p>
            <h2 className="panel-heading__title">Planilha final</h2>
          </div>
          <Badge tone={localXlsxPath ? "success" : "neutral"}>{localXlsxPath ? "pronto" : "aguardando"}</Badge>
        </div>

        <div className="workflow-delivery-grid">
          <article className="workflow-review-card">
            <h3>Baixar Excel</h3>
            {localXlsxPath ? (
              <div className="workflow-link-row">
                <a
                  className="workflow-link-chip"
                  href={buildDownloadUrl(form.apiBaseUrl, localXlsxPath)}
                  target="_blank"
                  rel="noreferrer"
                >
                  Baixar Excel
                </a>
              </div>
            ) : (
              <p className="empty-state">Depois da analise, a planilha preenchida aparece aqui para download.</p>
            )}
          </article>

          <article className="workflow-review-card">
            <h3>Resultado esperado</h3>
            {localXlsxPath ? (
              <p className="empty-state">A planilha modelo foi preenchida com os dados da avaliacao e esta pronta para revisao final.</p>
            ) : (
              <p className="empty-state">O foco desta tela agora e somente gerar e devolver o arquivo `.xlsx` final.</p>
            )}
          </article>
        </div>
      </section>
    </div>
  );
}
