// Loads images/manifest.json, renders the photo flow and drives the full-screen viewer.
// Everything that can be tested without a DOM lives in layout.js.

import { formatMonth, metaText, shuffle, sortNewestFirst, wrapIndex } from "./layout.js";

const MANIFEST_URL = "images/manifest.json";
const EAGER_IMAGE_COUNT = 4;
const SWIPE_THRESHOLD_PX = 50;
// Same placeholder as in index.html: keeps the viewer <img> valid while nothing is open.
const EMPTY_IMAGE = "data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg'/%3E";

const photosSection = document.getElementById("photos");
const statusLine = document.getElementById("status");
const shuffleButton = document.getElementById("shuffle-button");
const viewer = document.getElementById("viewer");
const viewerImage = document.getElementById("viewer-image");
const viewerTitle = document.getElementById("viewer-title");
const viewerDate = document.getElementById("viewer-date");

/** Photos in display order; the viewer walks this same list. */
let photos = [];
let currentIndex = -1;
let touchStartX = 0;

function showStatus(message) {
  statusLine.textContent = message;
  statusLine.hidden = false;
}

function hideStatus() {
  statusLine.hidden = true;
}

async function loadManifest() {
  const response = await fetch(MANIFEST_URL);
  if (!response.ok) {
    throw new Error(`manifest request failed: ${response.status}`);
  }
  const manifest = await response.json();
  if (!Array.isArray(manifest.photos)) {
    throw new Error("manifest.photos is not a list");
  }
  return manifest.photos;
}

function createMeta(photo, className) {
  const meta = document.createElement("span");
  meta.className = className;
  meta.setAttribute("aria-hidden", "true");
  const title = document.createElement("span");
  title.textContent = photo.title ?? "";
  const date = document.createElement("span");
  date.textContent = formatMonth(photo.date);
  meta.append(title, date);
  return meta;
}

function createPhotoElement(photo, index) {
  const button = document.createElement("button");
  button.type = "button";
  button.className = photo.orientation === "landscape" ? "photo landscape" : "photo";
  button.dataset.index = String(index);
  const caption = metaText(photo);
  button.setAttribute("aria-label", caption ? `${caption} 크게 보기` : "사진 크게 보기");

  const image = document.createElement("img");
  image.src = photo.thumb;
  image.width = photo.width;
  image.height = photo.height;
  image.alt = photo.title ?? "";
  image.loading = index < EAGER_IMAGE_COUNT ? "eager" : "lazy";
  image.decoding = "async";

  button.append(image, createMeta(photo, "meta"));
  return button;
}

function render(list) {
  const elements = list.map((photo, index) => createPhotoElement(photo, index));
  photosSection.replaceChildren(statusLine, ...elements);
}

function openViewer(index) {
  currentIndex = wrapIndex(index, photos.length);
  const photo = photos[currentIndex];
  viewerImage.src = photo.full;
  viewerImage.alt = photo.title ?? "";
  viewerTitle.textContent = photo.title ?? "";
  viewerDate.textContent = formatMonth(photo.date);
  if (!viewer.open) {
    viewer.showModal();
  }
}

function stepViewer(delta) {
  if (photos.length > 0) {
    openViewer(currentIndex + delta);
  }
}

function onViewerClosed() {
  // Drop the large image and hand focus back to the thumbnail that was open.
  viewerImage.src = EMPTY_IMAGE;
  const opened = photosSection.querySelector(`.photo[data-index="${currentIndex}"]`);
  opened?.focus({ preventScroll: false });
}

function bindEvents() {
  photosSection.addEventListener("click", (event) => {
    const photoButton = event.target.closest(".photo");
    if (photoButton) {
      openViewer(Number(photoButton.dataset.index));
    }
  });

  shuffleButton.addEventListener("click", () => {
    photos = shuffle(photos);
    render(photos);
  });

  document.getElementById("viewer-close").addEventListener("click", () => viewer.close());
  document.getElementById("viewer-prev").addEventListener("click", () => stepViewer(-1));
  document.getElementById("viewer-next").addEventListener("click", () => stepViewer(1));

  // Clicking the photo itself (or the empty background) closes, as on the reference site.
  viewer.addEventListener("click", (event) => {
    if (event.target === viewer || event.target === viewerImage) {
      viewer.close();
    }
  });
  viewer.addEventListener("close", onViewerClosed);

  document.addEventListener("keydown", (event) => {
    if (!viewer.open) {
      return;
    }
    if (event.key === "ArrowLeft") {
      stepViewer(-1);
    } else if (event.key === "ArrowRight") {
      stepViewer(1);
    }
  });

  viewer.addEventListener("touchstart", (event) => {
    touchStartX = event.changedTouches[0].screenX;
  });
  viewer.addEventListener("touchend", (event) => {
    const distance = event.changedTouches[0].screenX - touchStartX;
    if (Math.abs(distance) > SWIPE_THRESHOLD_PX) {
      stepViewer(distance < 0 ? 1 : -1);
    }
  });
}

async function init() {
  bindEvents();
  try {
    photos = sortNewestFirst(await loadManifest());
  } catch (error) {
    console.error(error);
    showStatus("사진 목록을 불러오지 못했습니다.");
    return;
  }
  if (photos.length === 0) {
    showStatus("아직 사진이 없습니다.");
    return;
  }
  hideStatus();
  render(photos);
}

init();
