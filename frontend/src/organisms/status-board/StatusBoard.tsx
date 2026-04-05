import { MetricCard } from "../../molecules/metric-card/MetricCard";
import type { HealthResponse, OAuthStatusResponse } from "../../shared/types/api";

interface StatusBoardProps {
  health: HealthResponse | null;
  oauthStatus: OAuthStatusResponse | null;
  lastAction: string;
}

export function StatusBoard({ health, oauthStatus, lastAction }: StatusBoardProps) {
  return (
    <section className="status-board">
      <MetricCard
        label="Backend"
        value={health?.status === "ok" ? "online" : "pendente"}
        detail={health ? `Serviço: ${health.service}` : "Faça a checagem de saúde para validar a API."}
        tone={health?.status === "ok" ? "success" : "warning"}
      />
      <MetricCard
        label="Google OAuth"
        value={oauthStatus?.connected ? "conectado" : "desconectado"}
        detail={
          oauthStatus?.connected
            ? oauthStatus.email || "Conta autenticada sem e-mail exposto."
            : "Conecte a conta do analista antes de publicar."
        }
        tone={oauthStatus?.connected ? "success" : "warning"}
      />
      <MetricCard
        label="Última ação"
        value={lastAction}
        detail="O painel abaixo sempre mostra o payload retornado pela chamada mais recente."
        tone="neutral"
      />
    </section>
  );
}
