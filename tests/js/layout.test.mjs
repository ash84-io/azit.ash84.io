import assert from "node:assert/strict";
import { describe, it } from "node:test";

import {
  formatMonth,
  metaText,
  orientationOf,
  shuffle,
  sortNewestFirst,
  wrapIndex,
} from "../../site/js/layout.js";

describe("orientationOf", () => {
  it("is landscape only when wider than tall", () => {
    assert.equal(orientationOf(3000, 2000), "landscape");
    assert.equal(orientationOf(2000, 3000), "portrait");
    assert.equal(orientationOf(2000, 2000), "portrait");
  });
});

describe("shuffle", () => {
  it("keeps every element, is deterministic with an injected rng and leaves the input alone", () => {
    const input = [1, 2, 3, 4, 5];
    const sequence = [0.1, 0.9, 0.5, 0.3];
    const rng = () => sequence.shift();

    const result = shuffle(input, rng);

    assert.deepEqual([...result].sort(), [1, 2, 3, 4, 5]);
    assert.deepEqual(result, [3, 5, 2, 4, 1]);
    assert.deepEqual(input, [1, 2, 3, 4, 5]);
  });

  it("handles empty and single-element lists", () => {
    assert.deepEqual(shuffle([]), []);
    assert.deepEqual(shuffle(["only"]), ["only"]);
  });
});

describe("wrapIndex", () => {
  it("wraps both directions and tolerates an empty collection", () => {
    assert.equal(wrapIndex(-1, 5), 4);
    assert.equal(wrapIndex(5, 5), 0);
    assert.equal(wrapIndex(2, 5), 2);
    assert.equal(wrapIndex(3, 0), 0);
  });
});

describe("formatMonth", () => {
  it("returns YYYY.MM or an empty string", () => {
    assert.equal(formatMonth("2026-09-14"), "2026.09");
    assert.equal(formatMonth(""), "");
    assert.equal(formatMonth(undefined), "");
    assert.equal(formatMonth("14.09.2026"), "");
  });
});

describe("metaText", () => {
  it("joins title and month with a middle dot, dropping missing parts", () => {
    assert.equal(metaText({ title: "창가 책상", date: "2026-09-14" }), "창가 책상 · 2026.09");
    assert.equal(metaText({ title: "", date: "2026-09-14" }), "2026.09");
    assert.equal(metaText({ title: "제목만", date: "" }), "제목만");
    assert.equal(metaText({ title: "", date: "" }), "");
  });
});

describe("sortNewestFirst", () => {
  it("orders by date descending then id ascending without mutating the input", () => {
    const photos = [
      { id: "b", date: "2026-09-01" },
      { id: "a", date: "2026-09-01" },
      { id: "z", date: "2026-09-20" },
      { id: "m", date: "2025-12-31" },
    ];

    const ordered = sortNewestFirst(photos);

    assert.deepEqual(
      ordered.map((photo) => photo.id),
      ["z", "a", "b", "m"],
    );
    assert.deepEqual(
      photos.map((photo) => photo.id),
      ["b", "a", "z", "m"],
    );
  });
});
