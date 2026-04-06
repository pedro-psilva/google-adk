import { Badge } from "../../atoms/badge/Badge";

interface ResultPanelProps {
  error: string | null;
  result: unknown;
}

export function ResultPanel({ error, result }: ResultPanelProps) {

  return (
    <section className="surface surface--panel">
      <div className="panel-heading">
        <div>
          <p className="panel-heading__eyebrow">Retorno</p>
          <h2 className="panel-heading__title">Resposta da última chamada</h2>
        </div>
        <Badge tone={error ? "warning" : "success"}>{error ? "com atenção" : "ok"}</Badge>
      </div>

      {error ? <p className="result-panel__error">{error}</p> : null}

      <pre className="result-panel__code">{JSON.stringify(result, null, 2)}</pre>
    </section>
  );
}
