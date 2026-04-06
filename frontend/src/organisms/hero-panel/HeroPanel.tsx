import { Badge } from "../../atoms/badge/Badge";

interface HeroPanelProps {
  apiBaseUrl: string;
}

export function HeroPanel({ apiBaseUrl }: HeroPanelProps) {
  const endpointLabel = apiBaseUrl.trim() ? apiBaseUrl : "mesma origem / proxy local";

  return (
    <section className="surface surface--hero">
      <div className="hero-panel__eyebrow">Painel tecnico</div>
      <h1 className="hero-panel__title">Status, payloads e testes detalhados da geracao local.</h1>
      <p className="hero-panel__description">
        Esta rota fica reservada para validar infraestrutura, bundle e retorno bruto do backend. O foco do produto agora
        e gerar e devolver a planilha `.xlsx`.
      </p>

      <div className="hero-panel__badges">
        <Badge tone="success">Health check</Badge>
        <Badge tone="neutral">Retorno bruto</Badge>
        <Badge tone="neutral">Artefatos locais</Badge>
      </div>

      <div className="hero-panel__steps">
        <div className="hero-step">
          <span className="hero-step__index">01</span>
          <p>Valide o backend e a base de URL antes de qualquer teste.</p>
        </div>
        <div className="hero-step">
          <span className="hero-step__index">02</span>
          <p>Informe o bundle ou a pasta de intake que vai ser processada.</p>
        </div>
        <div className="hero-step">
          <span className="hero-step__index">03</span>
          <p>Rode o pipeline em preview ou live para inspecionar os artefatos.</p>
        </div>
        <div className="hero-step">
          <span className="hero-step__index">04</span>
          <p>Confira o caminho do `.xlsx` final no payload retornado.</p>
        </div>
      </div>

      <div className="hero-panel__endpoint">
        <span className="hero-panel__endpoint-label">Conexao atual</span>
        <strong>{endpointLabel}</strong>
      </div>
    </section>
  );
}
