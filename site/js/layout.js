// Pure helpers for the gallery: no DOM, no fetch, so they run in the browser and in `node --test`.

/** A photo wider than tall spans half the row; anything else (squares included) a quarter. */
export function orientationOf(width, height) {
  return width > height ? "landscape" : "portrait";
}

/** Fisher–Yates shuffle into a new array. `random` is injectable for deterministic tests. */
export function shuffle(items, random = Math.random) {
  const copy = [...items];
  for (let i = copy.length - 1; i > 0; i -= 1) {
    const j = Math.floor(random() * (i + 1));
    [copy[i], copy[j]] = [copy[j], copy[i]];
  }
  return copy;
}

/** Wrap an index into [0, length) so prev/next loop around the collection. */
export function wrapIndex(index, length) {
  if (length <= 0) {
    return 0;
  }
  return ((index % length) + length) % length;
}

/** "2026-09-14" → "2026.09"; anything unparsable → "". */
export function formatMonth(date) {
  const match = /^(\d{4})-(\d{2})/.exec(date ?? "");
  return match ? `${match[1]}.${match[2]}` : "";
}

/** Hover caption: "title · 2026.09", or whichever part exists. */
export function metaText({ title, date }) {
  return [title, formatMonth(date)].filter(Boolean).join(" · ");
}

/** Newest date first; same-day photos in ascending id order. Does not mutate the input. */
export function sortNewestFirst(photos) {
  return [...photos].sort((a, b) => {
    if (a.date !== b.date) {
      return a.date < b.date ? 1 : -1;
    }
    if (a.id === b.id) {
      return 0;
    }
    return a.id < b.id ? -1 : 1;
  });
}
