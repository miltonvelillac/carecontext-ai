export function splitTags(value: string): string[] {
  return value
    .split(",")
    .map((tag) => tag.trim())
    .filter(Boolean);
}

export function formatScore(score: number | null): string {
  if (score === null || Number.isNaN(score)) {
    return "n/a";
  }
  return score.toFixed(2);
}
