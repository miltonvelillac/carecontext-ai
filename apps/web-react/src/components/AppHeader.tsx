import type { ApiStatus } from "../types";
import { apiBaseUrl } from "../api/client";

type AppHeaderProps = {
  apiStatus: ApiStatus;
};

export function AppHeader({ apiStatus }: AppHeaderProps) {
  return (
    <header className="app-header">
      <div>
        <p className="eyebrow">CareContext AI</p>
        <h1>Ask grounded questions from your health and psychology sources</h1>
      </div>
      <div className={`api-pill ${apiStatus}`}>
        <span className="status-dot" />
        <span>{apiStatus === "checking" ? "Checking API" : `API ${apiStatus}`}</span>
        <small>{apiBaseUrl}</small>
      </div>
    </header>
  );
}
