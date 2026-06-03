import { FormEvent, useState } from "react";
import { Mic, Send, SlidersHorizontal } from "lucide-react";
import type { LanguageCode, RagAnswerResponse, SourceType, TextQueryPayload } from "../types";
import { splitTags } from "../utils/format";
import { AnswerPanel } from "./AnswerPanel";
import { Button } from "./ui/Button";

type QuestionSectionProps = {
  answer: RagAnswerResponse | null;
  isSubmittingAudio: boolean;
  isSubmittingText: boolean;
  onSubmitAudio: (formData: FormData) => Promise<void>;
  onSubmitText: (payload: TextQueryPayload) => Promise<void>;
};

export function QuestionSection({
  answer,
  isSubmittingAudio,
  isSubmittingText,
  onSubmitAudio,
  onSubmitText,
}: QuestionSectionProps) {
  const [query, setQuery] = useState("");
  const [language, setLanguage] = useState<LanguageCode>("auto");
  const [sourceType, setSourceType] = useState<"all" | SourceType>("all");
  const [filterTags, setFilterTags] = useState("");
  const [topK, setTopK] = useState(5);
  const [includeTts, setIncludeTts] = useState(false);
  const [audioFile, setAudioFile] = useState<File | null>(null);

  async function handleTextSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!query.trim()) {
      return;
    }

    const sourceTypes = sourceType === "all" ? [] : [sourceType];
    const topicTags = splitTags(filterTags);
    await onSubmitText({
      query: query.trim(),
      language,
      top_k: topK,
      filters:
        sourceTypes.length || topicTags.length || language !== "auto"
          ? {
              source_types: sourceTypes,
              topic_tags: topicTags,
              language,
            }
          : null,
      include_tts: includeTts,
    });
  }

  async function handleAudioSubmit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (!audioFile) {
      return;
    }

    const formData = new FormData();
    formData.append("file", audioFile);
    formData.append("language", language);
    formData.append("top_k", String(topK));
    formData.append("include_tts", String(includeTts));
    await onSubmitAudio(formData);
    setAudioFile(null);
  }

  return (
    <section className="workspace-card question-card">
      <div className="card-intro">
        <div className="icon-plate">
          <Send aria-hidden="true" />
        </div>
        <div>
          <p className="section-label">Ask</p>
          <h2>Chat with loaded context</h2>
        </div>
      </div>

      <form className="chat-box" onSubmit={handleTextSubmit}>
        <label className="field chat-field">
          <span>Written question</span>
          <textarea
            placeholder="What does this source say about sleep routines and stress?"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </label>

        <div className="control-bar">
          <label className="field">
            <span>Language</span>
            <select
              value={language}
              onChange={(event) => setLanguage(event.target.value as LanguageCode)}
            >
              <option value="auto">Auto</option>
              <option value="en">English</option>
              <option value="es">Spanish</option>
            </select>
          </label>
          <label className="field">
            <span>Source</span>
            <select
              value={sourceType}
              onChange={(event) => setSourceType(event.target.value as "all" | SourceType)}
            >
              <option value="all">All</option>
              <option value="curated">Curated</option>
              <option value="uploaded">Uploaded</option>
            </select>
          </label>
          <label className="field">
            <span>Top K</span>
            <input
              max={20}
              min={1}
              type="number"
              value={topK}
              onChange={(event) => setTopK(Number(event.target.value))}
            />
          </label>
        </div>

        <div className="control-bar wider">
          <label className="field">
            <span>Filter tags</span>
            <input
              placeholder="sleep, anxiety"
              type="text"
              value={filterTags}
              onChange={(event) => setFilterTags(event.target.value)}
            />
          </label>
          <label className="toggle-field">
            <input
              checked={includeTts}
              type="checkbox"
              onChange={(event) => setIncludeTts(event.target.checked)}
            />
            <span>Include TTS metadata</span>
          </label>
        </div>

        <Button
          disabled={!query.trim() || isSubmittingText}
          icon={<Send aria-hidden="true" />}
          isLoading={isSubmittingText}
          type="submit"
        >
          Ask in chat
        </Button>
      </form>

      <form className="audio-question" onSubmit={handleAudioSubmit}>
        <div className="mini-panel-title">
          <Mic aria-hidden="true" />
          <strong>Audio question</strong>
        </div>
        <label className="field">
          <span>Audio file</span>
          <input
            accept="audio/*"
            type="file"
            onChange={(event) => setAudioFile(event.target.files?.[0] ?? null)}
          />
        </label>
        <Button
          disabled={!audioFile || isSubmittingAudio}
          icon={<Mic aria-hidden="true" />}
          isLoading={isSubmittingAudio}
          type="submit"
          variant="secondary"
        >
          Ask with audio
        </Button>
      </form>

      <div className="answer-shell">
        <div className="mini-panel-title">
          <SlidersHorizontal aria-hidden="true" />
          <strong>Grounded answer</strong>
        </div>
        <AnswerPanel answer={answer} />
      </div>
    </section>
  );
}
