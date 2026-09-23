"""Generate `site/images/manifest.json` from the converted WebP files.

Usage: python -m tools.build_manifest --site site

Every `full/<id>.webp` becomes one entry with its pixel size, orientation, capture date
(from `sources.json`, else the file's modification date) and the `title` carried over from the
previous manifest so hand-written titles survive a rebuild. Photos are sorted newest first.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import asdict, dataclass
from datetime import datetime
from operator import attrgetter
from pathlib import Path

from PIL import Image

from tools.gallery_common import (
    FULL_DIR_NAME,
    IMAGES_DIR_NAME,
    MANIFEST_VERSION,
    THUMB_DIR_NAME,
    GalleryError,
    Orientation,
    full_dir,
    manifest_path,
    orientation_of,
    sources_path,
    thumb_dir,
)

logger = logging.getLogger(__name__)


class MissingThumbnailError(GalleryError):
    """A full-size image has no matching thumbnail."""


@dataclass(frozen=True, slots=True)
class Photo:
    id: str
    thumb: str
    full: str
    width: int
    height: int
    orientation: Orientation
    date: str
    title: str

    def to_dict(self) -> dict[str, str | int]:
        return asdict(self)


def read_size(path: Path) -> tuple[int, int]:
    with Image.open(path) as image:
        return image.size


def load_titles(path: Path) -> dict[str, str]:
    """Titles from an existing manifest, keyed by photo id."""
    if not path.exists():
        return {}
    manifest = json.loads(path.read_text(encoding="utf-8"))
    return {photo["id"]: photo.get("title", "") for photo in manifest.get("photos", [])}


def load_dates(path: Path) -> dict[str, str]:
    if not path.exists():
        return {}
    sources = json.loads(path.read_text(encoding="utf-8"))
    return {identifier: entry["date"] for identifier, entry in sources.items() if "date" in entry}


def file_date(path: Path) -> str:
    return datetime.fromtimestamp(path.stat().st_mtime).date().isoformat()


def build_photos(site_dir: Path, titles: dict[str, str], dates: dict[str, str]) -> list[Photo]:
    photos: list[Photo] = []
    for full_path in sorted(full_dir(site_dir).glob("*.webp")):
        identifier = full_path.stem
        thumb_path = thumb_dir(site_dir) / full_path.name
        if not thumb_path.exists():
            raise MissingThumbnailError(
                f"no thumbnail for {full_path.name}; run build_images first"
            )
        width, height = read_size(full_path)
        photos.append(
            Photo(
                id=identifier,
                thumb=f"{IMAGES_DIR_NAME}/{THUMB_DIR_NAME}/{full_path.name}",
                full=f"{IMAGES_DIR_NAME}/{FULL_DIR_NAME}/{full_path.name}",
                width=width,
                height=height,
                orientation=orientation_of(width, height),
                date=dates.get(identifier) or file_date(full_path),
                title=titles.get(identifier, ""),
            )
        )
    return photos


def sort_newest_first(photos: list[Photo]) -> list[Photo]:
    """Newest date first; same-day photos keep ascending id order."""
    by_id = sorted(photos, key=attrgetter("id"))
    return sorted(by_id, key=attrgetter("date"), reverse=True)


def write_manifest(path: Path, photos: list[Photo]) -> None:
    manifest = {"version": MANIFEST_VERSION, "photos": [photo.to_dict() for photo in photos]}
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(manifest, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def build_manifest(site_dir: Path) -> list[Photo]:
    target = manifest_path(site_dir)
    photos = sort_newest_first(
        build_photos(site_dir, load_titles(target), load_dates(sources_path(site_dir)))
    )
    write_manifest(target, photos)
    return photos


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--site", type=Path, default=Path("site"))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = parse_args(argv)
    try:
        photos = build_manifest(args.site)
    except (GalleryError, OSError) as error:
        logger.error("%s", error)
        return 1
    logger.info("manifest: %d photos → %s", len(photos), manifest_path(args.site))
    return 0


if __name__ == "__main__":
    sys.exit(main())
