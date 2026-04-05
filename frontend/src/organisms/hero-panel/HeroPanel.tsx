import { Badge } from "../../atoms/badge/Badge";

interface HeroPanelProps {
  apiBaseUrl: string;
}

export function HeroPanel({ apiBaseUrl }: HeroPanelProps) {
  const endpointLabel = apiBaseUrl.trim() ? apiBaseUrl : "mesma origem / proxy local";

  return (
    <section className="surface surface--hero">
      <div className="hero-panel__eyebrow">Profile Report Studio</div>
      <h1 className="hero-panel__title">Frontend mínimo, responsivo e pronto para operar o pipeline.</h1>
      <p className="hero-panel__description">
        Esta interface já separa frontend e backend, organiza a UI em Atomic Design e concentra o fluxo operacional
        em quatro passos: validar backend, conferir OAuth, gerar artefatos e publicar no Google Workspace.
      </p>

      <div className="hero-panel__badges">
        <Badge tone="success">Atomic Design</Badge>
        <Badge tone="neutral">Frontend separado</Badge>
        <Badge tone="warning">OAuth em popup</Badge>
      </div>

      <div className="hero-panel__steps">
        <div className="hero-step">
          <span className="hero-step__index">01</span>
          <p>Conecte o backend via proxy local ou mesma origem.</p>
        </div>
        <div className="hero-step">
          <span className="hero-step__index">02</span>
          <p>Valide o analista e o bundle que será processado.</p>
        </div>
        <div className="hero-step">
          <span className="hero-step__index">03</span>
          <p>Rode o pipeline em preview ou live.</p>
        </div>
        <div className="hero-step">
          <span className="hero-step__index">04</span>
          <p>Publique Docs e Sheets com a conta do analista.</p>
        </div>
      </div>

      <div className="hero-panel__endpoint">
        <span className="hero-panel__endpoint-label">Conexão atual</span>
        <strong>{endpointLabel}</strong>
      </div>
    </section>
  );
}
