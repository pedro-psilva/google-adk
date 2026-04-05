import { Badge } from "../../atoms/badge/Badge";

interface MetricCardProps {
  label: string;
  value: string;
  detail: string;
  tone?: "neutral" | "success" | "warning";
}

export function MetricCard({ label, value, detail, tone = "neutral" }: MetricCardProps) {
  return (
    <article className="metric-card">
      <div className="metric-card__top">
        <span className="metric-card__label">{label}</span>
        <Badge tone={tone}>{value}</Badge>
      </div>
      <p className="metric-card__detail">{detail}</p>
    </article>
  );
}
