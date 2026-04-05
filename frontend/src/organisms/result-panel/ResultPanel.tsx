import { Badge } from "../../atoms/badge/Badge";

interface ResultPanelProps {
  error: string | null;
  result: unknown;
}

function extractLinks(payload: unknown) {
  if (!payload || typeof payload !== "object") {
    return [];
  }

  const candidate = payload as Record<string, unknown>;
  const links: Array<{ label: string; url: string }> = [];

  if (typeof candidate.document_url === "string") {
    links.push({ label: "Abrir Google Doc", url: candidate.document_url });
  }
  if (typeof candidate.spreadsheet_url === "string") {
    links.push({ label: "Abrir Google Sheet", url: candidate.spreadsheet_url });
  }

  return links;
}

export function ResultPanel({ error, result }: ResultPanelProps) {
  const links = extractLinks(result);

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

      {links.length ? (
        <div className="result-panel__links">
          {links.map((link) => (
            <a
              key={link.url}
              className="result-panel__link"
              href={link.url}
              target="_blank"
              rel="noreferrer"
            >
              {link.label}
            </a>
          ))}
        </div>
      ) : null}

      <pre className="result-panel__code">{JSON.stringify(result, null, 2)}</pre>
    </section>
  );
}
