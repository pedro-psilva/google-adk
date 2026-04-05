import type { PropsWithChildren } from "react";

type BadgeTone = "neutral" | "success" | "warning";

interface BadgeProps extends PropsWithChildren {
  tone?: BadgeTone;
}

export function Badge({ children, tone = "neutral" }: BadgeProps) {
  return <span className={`badge badge--${tone}`}>{children}</span>;
}
