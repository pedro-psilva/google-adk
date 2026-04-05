import { useEffect, useState } from "react";

import { ControlPanel } from "../../organisms/control-panel/ControlPanel";
import { HeroPanel } from "../../organisms/hero-panel/HeroPanel";
import { ResultPanel } from "../../organisms/result-panel/ResultPanel";
import { StatusBoard } from "../../organisms/status-board/StatusBoard";
import { getHealth, getOAuthStatus, publishWorkspace, runPipeline, startOAuth } from "../../shared/api/client";
import type { HealthResponse, OAuthStatusResponse, StudioFormState } from "../../shared/types/api";
import { StudioTemplate } from "../../templates/studio-template/StudioTemplate";

const initialForm: StudioFormState = {
  apiBaseUrl: import.meta.env.VITE_API_BASE_URL ?? "",
  analystId: "maria-abrahao",
  bundleInput: "artifacts/maria-abrahao-bundle.json",
  outputDir: "artifacts/frontend-run",
  draftMode: "preview",
  publishDocument: true,
  publishSpreadsheet: true,
};

export function StudioPage() {
  const [form, setForm] = useState<StudioFormState>(initialForm);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [oauthStatus, setOauthStatus] = useState<OAuthStatusResponse | null>(null);
  const [busyAction, setBusyAction] = useState<string | null>(null);
  const [lastAction, setLastAction] = useState("aguardando");
  const [result, setResult] = useState<unknown>({
    message: "O painel vai mostrar aqui o payload da última chamada ao backend.",
  });
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    void handleHealthCheck();
    void handleOAuthStatus();
  }, []);

  function updateField<K extends keyof StudioFormState>(field: K, value: StudioFormState[K]) {
    setForm((current) => ({ ...current, [field]: value }));
  }

  async function runAction<T>(actionKey: string, callback: () => Promise<T>) {
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
      throw caughtError;
    } finally {
      setBusyAction(null);
    }
  }

  async function handleHealthCheck() {
    const payload = await runAction("health", () => getHealth(form.apiBaseUrl));
    setHealth(payload as HealthResponse);
  }

  async function handleOAuthStatus() {
    if (!form.analystId.trim()) {
      setError("Informe um analyst_id antes de consultar o status do OAuth.");
      setLastAction("oauth-status com falha");
      return;
    }

    const payload = await runAction("oauth-status", () => getOAuthStatus(form.apiBaseUrl, form.analystId));
    setOauthStatus(payload as OAuthStatusResponse);
  }

  async function handleOAuthStart() {
    if (!form.analystId.trim()) {
      setError("Informe um analyst_id antes de iniciar o OAuth.");
      setLastAction("oauth-start com falha");
      return;
    }

    const payload = await runAction("oauth-start", () => startOAuth(form.apiBaseUrl, form.analystId));
    const authorization = payload as { authorization_url: string };
    const popup = window.open(
      authorization.authorization_url,
      "google-oauth",
      "popup=yes,width=560,height=720,noopener,noreferrer",
    );

    if (!popup) {
      window.location.href = authorization.authorization_url;
    }
  }

  async function handleRunPipeline() {
    await runAction("pipeline", () => runPipeline(form.apiBaseUrl, form));
  }

  async function handlePublishWorkspace() {
    const payload = await runAction("publish", () => publishWorkspace(form.apiBaseUrl, form));
    await handleOAuthStatus();
    setResult(payload);
    setLastAction("publish");
  }

  return (
    <StudioTemplate
      hero={<HeroPanel apiBaseUrl={form.apiBaseUrl} />}
      status={<StatusBoard health={health} oauthStatus={oauthStatus} lastAction={lastAction} />}
      controls={
        <ControlPanel
          form={form}
          busyAction={busyAction}
          onChange={updateField}
          onHealthCheck={() => void handleHealthCheck()}
          onOAuthStatus={() => void handleOAuthStatus()}
          onOAuthStart={() => void handleOAuthStart()}
          onRunPipeline={() => void handleRunPipeline()}
          onPublishWorkspace={() => void handlePublishWorkspace()}
        />
      }
      results={<ResultPanel error={error} result={result} />}
    />
  );
}
