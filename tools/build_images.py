"""Convert original photos into thumbnail and full-size WebP files for the site.

Usage: python -m tools.build_images --source originals --site site [options]

For every supported file in the source folder this writes
`site/images/thumb/<id>.webp` (grid) and `site/images/full/<id>.webp` (viewer), applies the
EXIF orientation, strips all metadata (including GPS) and records the capture date in
`site/images/sources.json` so the manifest builder can sort photos without EXIF.
"""

from __future__ import annotations

import argparse
import json
import logging
import sys
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path

from PIL import Image, ImageOps

from tools.gallery_common import (
    FULL_DIR_NAME,
    THUMB_DIR_NAME,
    GalleryError,
    images_dir,
    sources_path,
)

SUPPORTED_SUFFIXES = frozenset({".jpg", ".jpeg", ".png", ".webp"})
EXIF_IFD_TAG = 0x8769
DATETIME_ORIGINAL_TAG = 36867
DATETIME_TAG = 306
EXIF_DATETIME_FORMAT = "%Y:%m:%d %H:%M:%S"

logger = logging.getLogger(__name__)


class DuplicatePhotoIdError(GalleryError):
    """Two source files would produce the same output name."""


@dataclass(frozen=True, slots=True)
class ConversionSettings:
    thumb_max: int
    full_max: int
    quality: int


@dataclass(slots=True)
class ConversionResult:
    converted: list[str] = field(default_factory=list)
    skipped: list[str] = field(default_factory=list)
    ignored: list[str] = field(default_factory=list)


def photo_id(source: Path) -> str:
    return source.stem


def output_paths(source: Path, site_dir: Path) -> tuple[Path, Path]:
    """Return (thumb, full) output paths for a source photo."""
    name = f"{photo_id(source)}.webp"
    return (
        images_dir(site_dir) / THUMB_DIR_NAME / name,
        images_dir(site_dir) / FULL_DIR_NAME / name,
    )


def read_capture_date(image: Image.Image, source: Path) -> str:
    """Return the capture date as YYYY-MM-DD from EXIF, else the file's modification date."""
    exif = image.getexif()
    raw = exif.get_ifd(EXIF_IFD_TAG).get(DATETIME_ORIGINAL_TAG) or exif.get(DATETIME_TAG)
    if isinstance(raw, str):
        try:
            return datetime.strptime(raw.strip(), EXIF_DATETIME_FORMAT).date().isoformat()
        except ValueError:
            logger.warning("%s: unreadable EXIF date %r, using file time", source.name, raw)
    return datetime.fromtimestamp(source.stat().st_mtime).date().isoformat()


def is_up_to_date(source: Path, outputs: tuple[Path, Path]) -> bool:
    source_mtime = source.stat().st_mtime
    return all(path.exists() and path.stat().st_mtime >= source_mtime for path in outputs)


def _flatten_for_web(image: Image.Image) -> Image.Image:
    has_alpha = image.mode in ("RGBA", "LA") or "transparency" in image.info
    return image.convert("RGBA" if has_alpha else "RGB")


def _save_resized(image: Image.Image, target: Path, max_side: int, quality: int) -> None:
    resized = image.copy()
    # thumbnail() keeps the aspect ratio and never upscales.
    resized.thumbnail((max_side, max_side), Image.Resampling.LANCZOS)
    target.parent.mkdir(parents=True, exist_ok=True)
    # No exif= argument: every tag, GPS included, is dropped on purpose.
    resized.save(target, "WEBP", quality=quality, method=6)


def convert_photo(source: Path, site_dir: Path, settings: ConversionSettings) -> str:
    """Write both WebP variants for one photo and return its capture date."""
    thumb, full = output_paths(source, site_dir)
    with Image.open(source) as opened:
        capture_date = read_capture_date(opened, source)
        upright = ImageOps.exif_transpose(opened)
        upright.load()
    web_image = _flatten_for_web(upright)
    _save_resized(web_image, thumb, settings.thumb_max, settings.quality)
    _save_resized(web_image, full, settings.full_max, settings.quality)
    return capture_date


def load_sources(site_dir: Path) -> dict[str, dict[str, str]]:
    path = sources_path(site_dir)
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


def save_sources(site_dir: Path, sources: dict[str, dict[str, str]]) -> None:
    path = sources_path(site_dir)
    path.parent.mkdir(parents=True, exist_ok=True)
    ordered = dict(sorted(sources.items()))
    path.write_text(json.dumps(ordered, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _ensure_unique_ids(sources: list[Path]) -> None:
    seen: dict[str, Path] = {}
    for source in sources:
        identifier = photo_id(source)
        if identifier in seen:
            raise DuplicatePhotoIdError(
                f"{source.name} and {seen[identifier].name} both map to {identifier}.webp"
            )
        seen[identifier] = source


def convert_all(
    source_dir: Path, site_dir: Path, settings: ConversionSettings
) -> ConversionResult:
    """Convert every supported photo in `source_dir` that is newer than its outputs."""
    result = ConversionResult()
    candidates = sorted(path for path in source_dir.iterdir() if path.is_file())
    supported = [path for path in candidates if path.suffix.lower() in SUPPORTED_SUFFIXES]
    result.ignored = [
        path.name for path in candidates if path not in supported and path.name[0] != "."
    ]
    _ensure_unique_ids(supported)

    sources = load_sources(site_dir)
    for source in supported:
        if is_up_to_date(source, output_paths(source, site_dir)):
            result.skipped.append(source.name)
            continue
        capture_date = convert_photo(source, site_dir, settings)
        sources[photo_id(source)] = {"source": source.name, "date": capture_date}
        result.converted.append(source.name)
        logger.info("converted %s (%s)", source.name, capture_date)

    if result.converted or not sources_path(site_dir).exists():
        save_sources(site_dir, sources)
    return result


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--source", type=Path, default=Path("originals"))
    parser.add_argument("--site", type=Path, default=Path("site"))
    parser.add_argument("--thumb-max", type=int, default=1200, help="longest side of grid images")
    parser.add_argument("--full-max", type=int, default=2400, help="longest side of viewer images")
    parser.add_argument("--quality", type=int, default=80, help="WebP quality 0-100")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = parse_args(argv)
    if not args.source.is_dir():
        logger.error("source folder not found: %s", args.source)
        return 1
    settings = ConversionSettings(args.thumb_max, args.full_max, args.quality)
    try:
        result = convert_all(args.source, args.site, settings)
    except (GalleryError, OSError) as error:
        logger.error("%s", error)
        return 1
    for name in result.ignored:
        logger.warning("ignored (unsupported type): %s", name)
    logger.info(
        "images: %d converted, %d up to date, %d ignored",
        len(result.converted),
        len(result.skipped),
        len(result.ignored),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
