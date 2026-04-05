import { Button } from "../../atoms/button/Button";
import { Input } from "../../atoms/input/Input";
import { Select } from "../../atoms/select/Select";
import { Switch } from "../../atoms/switch/Switch";
import { FormField } from "../../molecules/form-field/FormField";
import type { DraftMode, StudioFormState } from "../../shared/types/api";

interface ControlPanelProps {
  form: StudioFormState;
  busyAction: string | null;
  onChange: <K extends keyof StudioFormState>(field: K, value: StudioFormState[K]) => void;
  onHealthCheck: () => void;
  onOAuthStatus: () => void;
  onOAuthStart: () => void;
  onRunPipeline: () => void;
  onPublishWorkspace: () => void;
}

export function ControlPanel({
  form,
  busyAction,
  onChange,
  onHealthCheck,
  onOAuthStatus,
  onOAuthStart,
  onRunPipeline,
  onPublishWorkspace,
}: ControlPanelProps) {
  return (
    <section className="surface surface--panel">
      <div className="panel-heading">
        <div>
          <p className="panel-heading__eyebrow">Operação</p>
          <h2 className="panel-heading__title">Controle do pipeline</h2>
        </div>
        <p className="panel-heading__description">Campos mínimos para usar os endpoints já expostos pelo backend.</p>
      </div>

      <div className="form-grid">
        <FormField label="Base URL da API" hint="Opcional quando o proxy do Vite estiver ativo.">
          <Input
            placeholder="http://127.0.0.1:8000"
            value={form.apiBaseUrl}
            onChange={(event) => onChange("apiBaseUrl", event.target.value)}
          />
        </FormField>

        <FormField label="Analyst ID" hint="Identificador usado para o vínculo do OAuth e da publicação.">
          <Input value={form.analystId} onChange={(event) => onChange("analystId", event.target.value)} />
        </FormField>

        <FormField label="Bundle input" hint="Pode ser um JSON normalizado ou uma pasta de intake.">
          <Input value={form.bundleInput} onChange={(event) => onChange("bundleInput", event.target.value)} />
        </FormField>

        <FormField label="Output dir" hint="Diretório onde o backend vai escrever os artefatos.">
          <Input value={form.outputDir} onChange={(event) => onChange("outputDir", event.target.value)} />
        </FormField>

        <FormField label="Modo do draft" hint="Preview gera artefatos locais; live usa Vertex AI.">
          <Select
            value={form.draftMode}
            onChange={(event) => onChange("draftMode", event.target.value as DraftMode)}
          >
            <option value="preview">Preview</option>
            <option value="live">Live</option>
          </Select>
        </FormField>
      </div>

      <div className="toggle-row">
        <Switch
          label="Publicar Google Doc"
          checked={form.publishDocument}
          onChange={(event) => onChange("publishDocument", event.target.checked)}
        />
        <Switch
          label="Publicar Google Sheet"
          checked={form.publishSpreadsheet}
          onChange={(event) => onChange("publishSpreadsheet", event.target.checked)}
        />
      </div>

      <div className="action-grid">
        <Button variant="secondary" busy={busyAction === "health"} onClick={onHealthCheck}>
          Validar backend
        </Button>
        <Button variant="secondary" busy={busyAction === "oauth-status"} onClick={onOAuthStatus}>
          Ver status do OAuth
        </Button>
        <Button variant="ghost" busy={busyAction === "oauth-start"} onClick={onOAuthStart}>
          Conectar Google
        </Button>
        <Button busy={busyAction === "pipeline"} onClick={onRunPipeline}>
          Rodar pipeline
        </Button>
        <Button variant="primary" busy={busyAction === "publish"} onClick={onPublishWorkspace} stretch>
          Publicar no Workspace
        </Button>
      </div>
    </section>
  );
}
