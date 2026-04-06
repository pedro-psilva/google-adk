import { MetricCard } from "../../molecules/metric-card/MetricCard";
import type { HealthResponse } from "../../shared/types/api";

interface StatusBoardProps {
  health: HealthResponse | null;
  lastAction: string;
}

export function StatusBoard({ health, lastAction }: StatusBoardProps) {
  return (
    <section className="status-board">
      <MetricCard
        label="Backend"
        value={health?.status === "ok" ? "online" : "pendente"}
        detail={health ? `Servico: ${health.service}` : "Faca a checagem de saude para validar a API."}
        tone={health?.status === "ok" ? "success" : "warning"}
      />
      <MetricCard
        label="Fluxo"
        value="xlsx local"
        detail="A rota tecnica agora valida apenas a geracao local dos artefatos."
        tone="neutral"
      />
      <MetricCard
        label="Ultima acao"
        value={lastAction}
        detail="O painel abaixo sempre mostra o payload retornado pela chamada mais recente."
        tone="neutral"
      />
    </section>
  );
}
