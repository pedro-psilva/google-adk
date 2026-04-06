import type { ReactNode } from "react";

interface StudioTemplateProps {
  hero: ReactNode;
  status: ReactNode;
  controls: ReactNode;
  results: ReactNode;
}

export function StudioTemplate({ hero, status, controls, results }: StudioTemplateProps) {
  return (
    <div className="studio-template">
      <aside className="studio-template__aside">{hero}</aside>
      <main className="studio-template__main">
        {status}
        {controls}
        {results}
      </main>
    </div>
  );
}
