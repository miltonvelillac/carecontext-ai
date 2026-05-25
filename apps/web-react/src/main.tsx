import React from "react";
import ReactDOM from "react-dom/client";
import { Upload, Mic, Volume2, BookOpen } from "lucide-react";
import "./styles.css";

const apiBaseUrl = import.meta.env.VITE_API_BASE_URL ?? "http://localhost:8000";

function App() {
  return (
    <main className="app-shell">
      <section className="workspace">
        <header className="app-header">
          <div>
            <p className="eyebrow">CareContext AI</p>
            <h1>Health and psychology RAG assistant</h1>
          </div>
          <span className="api-pill">API: {apiBaseUrl}</span>
        </header>

        <div className="grid">
          <section className="panel">
            <Upload aria-hidden="true" />
            <h2>Upload</h2>
            <p>PDF ingestion, tags, and indexing status will live here.</p>
          </section>

          <section className="panel">
            <BookOpen aria-hidden="true" />
            <h2>Corpus</h2>
            <p>Curated and uploaded documents will be listed here.</p>
          </section>

          <section className="panel">
            <Mic aria-hidden="true" />
            <h2>Ask</h2>
            <p>Text and audio questions will share the same grounded RAG flow.</p>
          </section>

          <section className="panel">
            <Volume2 aria-hidden="true" />
            <h2>Answer</h2>
            <p>Citations, snippets, safety notes, and TTS playback will appear here.</p>
          </section>
        </div>
      </section>
    </main>
  );
}

ReactDOM.createRoot(document.getElementById("root")!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
);

