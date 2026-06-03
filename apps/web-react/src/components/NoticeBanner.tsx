import { AlertTriangle, CheckCircle2 } from "lucide-react";

type NoticeBannerProps = {
  error: string | null;
  notice: string | null;
};

export function NoticeBanner({ error, notice }: NoticeBannerProps) {
  if (!error && !notice) {
    return null;
  }

  return (
    <div className={`banner ${error ? "error" : "success"}`}>
      {error ? <AlertTriangle aria-hidden="true" /> : <CheckCircle2 aria-hidden="true" />}
      <span>{error ?? notice}</span>
    </div>
  );
}
