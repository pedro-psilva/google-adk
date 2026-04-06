import { useEffect, useState } from "react";

import { StudioPage } from "../pages/studio/StudioPage";
import { WorkflowPage } from "../pages/workflow/WorkflowPage";

type AppRoute = "workflow" | "status";
type ThemeMode = "light" | "dark";

const themeStorageKey = "cognit-theme";

function resolveRoute(pathname: string): AppRoute {
  return pathname.startsWith("/status") ? "status" : "workflow";
}

function resolveInitialTheme(): ThemeMode {
  const storedTheme = window.localStorage.getItem(themeStorageKey);
  return storedTheme === "light" ? "light" : "dark";
}

export function App() {
  const [route, setRoute] = useState<AppRoute>(() => resolveRoute(window.location.pathname));
  const [theme, setTheme] = useState<ThemeMode>(resolveInitialTheme);

  useEffect(() => {
    const handlePopState = () => {
      setRoute(resolveRoute(window.location.pathname));
    };

    window.addEventListener("popstate", handlePopState);
    return () => window.removeEventListener("popstate", handlePopState);
  }, []);

  useEffect(() => {
    document.documentElement.dataset.theme = theme;
    window.localStorage.setItem(themeStorageKey, theme);
  }, [theme]);

  function navigate(nextRoute: AppRoute) {
    const nextPath = nextRoute === "status" ? "/status" : "/";
    if (window.location.pathname === nextPath) {
      return;
    }

    window.history.pushState({}, "", nextPath);
    setRoute(nextRoute);
  }

  function toggleTheme() {
    setTheme((current) => (current === "dark" ? "light" : "dark"));
  }

  return (
    <div className="app-shell">
      <div className="app-shell__orb app-shell__orb--one" aria-hidden="true" />
      <div className="app-shell__orb app-shell__orb--two" aria-hidden="true" />

      <header className="app-topbar">
        <button className="brand-button" onClick={() => navigate("workflow")}>
          <span className="brand-button__mark">PA</span>
          <span className="brand-button__copy">
            <strong>Analise de Perfil</strong>
            <span>Arquivos, revisao automatica e planilha final</span>
          </span>
        </button>

        <nav className="app-nav" aria-label="Navegacao principal">
          <button
            className={`app-nav__link ${route === "workflow" ? "app-nav__link--active" : ""}`.trim()}
            onClick={() => navigate("workflow")}
          >
            Operacao
          </button>
          <button
            className={`app-nav__link ${route === "status" ? "app-nav__link--active" : ""}`.trim()}
            onClick={() => navigate("status")}
          >
            Status tecnico
          </button>
        </nav>

        <button className="theme-toggle" onClick={toggleTheme}>
          {theme === "dark" ? "Tema claro" : "Tema escuro"}
        </button>
      </header>

      <main className="app-content">{route === "status" ? <StudioPage /> : <WorkflowPage />}</main>
    </div>
  );
}
