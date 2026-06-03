import { Search, Volume2 } from "lucide-react";
import type { RagAnswerResponse } from "../types";
import { formatScore } from "../utils/format";

type AnswerPanelProps = {
  answer: RagAnswerResponse | null;
};

export function AnswerPanel({ answer }: AnswerPanelProps) {
  if (!answer) {
    return (
      <div className="answer-empty-state">
        <Search aria-hidden="true" />
        <span>Ask a question to see the grounded answer.</span>
      </div>
    );
  }

  return (
    <div className="answer-stack">
      {answer.transcription && (
        <div className="transcription-box">
          <strong>Transcription</strong>
          <p>{answer.transcription.text}</p>
        </div>
      )}

      <div className={`safety-card ${answer.safety.risk_level}`}>
        <strong>{answer.safety.risk_level} risk</strong>
        <span>{answer.safety.disclaimer}</span>
        {answer.safety.escalation_message && <span>{answer.safety.escalation_message}</span>}
      </div>

      <div className="answer-bubble">
        <p>{answer.answer}</p>
      </div>

      {answer.tts && (
        <div className="tts-row">
          <Volume2 aria-hidden="true" />
          <span>
            TTS: {answer.tts.provider} / {answer.tts.model}
          </span>
        </div>
      )}

      <div className="citation-list">
        <h3>Citations</h3>
        {answer.citations.length === 0 ? (
          <p className="muted-text">No citations returned.</p>
        ) : (
          answer.citations.map((citation) => (
            <article className="citation-card" key={citation.chunk_id}>
              <div className="citation-header">
                <strong>{citation.title}</strong>
                <span>{formatScore(citation.score)}</span>
              </div>
              <p>{citation.snippet}</p>
              <small>{citation.chunk_id}</small>
            </article>
          ))
        )}
      </div>
    </div>
  );
}
