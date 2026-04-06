import { useState } from "react";

import { ControlPanel } from "../../organisms/control-panel/ControlPanel";
import { HeroPanel } from "../../organisms/hero-panel/HeroPanel";
import { ResultPanel } from "../../organisms/result-panel/ResultPanel";
import { StatusBoard } from "../../organisms/status-board/StatusBoard";
import { getHealth, runPipeline } from "../../shared/api/client";
import type { HealthResponse, StudioFormState } from "../../shared/types/api";
import { StudioTemplate } from "../../templates/studio-template/StudioTemplate";

const initialForm: StudioFormState = {
  apiBaseUrl: import.meta.env.DEV ? "" : (import.meta.env.VITE_API_BASE_URL ?? ""),
  bundleInput: "artifacts/maria-abrahao-bundle.json",
  outputDir: "artifacts/frontend-run",
  draftMode: "preview",
};

export function StudioPage() {
  const [form, setForm] = useState<StudioFormState>(initialForm);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [lastAction, setLastAction] = useState("aguardando");
  const [result, setResult] = useState<unknown>({
    message: "O painel vai mostrar aqui o payload da última chamada ao backend.",
  });
  const [error, setError] = useState<string | null>(null);

  function updateField<K extends keyof StudioFormState>(field: K, value: StudioFormState[K]) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function runAction<T>(actionKey: string, callback: () => Promise<T>): Promise<T | null> {
    setBusyAction(actionKey);
    setError(null);

    try {
      const payload = await callback();
      setResult(payload);
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

  async function handleHealthCheck() {
    const payload = await runAction("health", () => getHealth(form.apiBaseUrl));
    if (payload) {
      setHealth(payload as HealthResponse);
    }
  }

  async function handleRunPipeline() {
    await runAction("pipeline", () => runPipeline(form.apiBaseUrl, form));
  }

  return (
    <StudioTemplate
      hero={<HeroPanel apiBaseUrl={form.apiBaseUrl} />}
      status={<StatusBoard health={health} lastAction={lastAction} />}
      controls={
        <ControlPanel
          form={form}
          busyAction={busyAction}
          onChange={updateField}
          onHealthCheck={() => void handleHealthCheck()}
          onRunPipeline={() => void handleRunPipeline()}
        />
      }
      results={<ResultPanel error={error} result={result} />}
    />
  );
}
