import { useEffect, useState } from "react";

import { WorkflowPage } from "../pages/workflow/WorkflowPage";

type ThemeMode = "light" | "dark";

const themeStorageKey = "cognit-theme";

function resolveInitialTheme(): ThemeMode {
  const storedTheme = window.localStorage.getItem(themeStorageKey);
  return storedTheme === "light" ? "light" : "dark";
}

export function App() {
  const [theme, setTheme] = useState<ThemeMode>(resolveInitialTheme);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem(themeStorageKey, theme);
  }, [theme]);

  function toggleTheme() {
    setTheme((current) => (current === "dark" ? "light" : "dark"));
  }

  return (
    <div className="app-shell">
      <div className="app-shell__orb app-shell__orb--one" aria-hidden="true" />
      <div className="app-shell__orb app-shell__orb--two" aria-hidden="true" />

      <header className="app-topbar">
        <div className="brand-button">
          <span className="brand-button__mark">PA</span>
          <span className="brand-button__copy">
            <strong>Análise de Perfil</strong>
            <span>Arquivos, revisão automática e planilha final</span>
          </span>
        </div>

        <button className="theme-toggle" onClick={toggleTheme}>
          {theme === "dark" ? "Tema claro" : "Tema escuro"}
        </button>
      </header>

      <main className="app-content">
        <WorkflowPage />
      </main>
    </div>
  );
}
