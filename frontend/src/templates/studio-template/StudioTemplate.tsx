import type { ReactNode } from "react";

interface StudioTemplateProps {
  hero: ReactNode;
  status: ReactNode;
  controls: ReactNode;
  results: ReactNode;
}

export function StudioTemplate({ hero, status, controls, results }: StudioTemplateProps) {
  return (
    <div className="studio-shell">
      <div className="studio-shell__glow studio-shell__glow--left" aria-hidden="true" />
      <div className="studio-shell__glow studio-shell__glow--right" aria-hidden="true" />

      <div className="studio-template">
        <aside className="studio-template__aside">{hero}</aside>
        <main className="studio-template__main">
          {status}
          {controls}
          {results}
        </main>
      </div>
    </div>
  );
}
