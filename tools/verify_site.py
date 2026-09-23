"""Check that `manifest.json` and the image files agree before a deploy.

Usage: python -m tools.verify_site --site site

Exit code 1 lists every problem found: missing files, orphan images, bad sizes or dates,
duplicate ids, wrong orientation.
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
from pathlib import Path

from tools.gallery_common import (
    MANIFEST_VERSION,
    full_dir,
    manifest_path,
    orientation_of,
    thumb_dir,
)

REQUIRED_KEYS = frozenset(
    {"id", "thumb", "full", "width", "height", "orientation", "date", "title"}
)
DATE_PATTERN = re.compile(r"^\d{4}-\d{2}-\d{2}$")

logger = logging.getLogger(__name__)


def _check_photo(photo: dict, site_dir: Path) -> list[str]:
    label = photo.get("id", "<no id>")
    problems: list[str] = []
    missing = REQUIRED_KEYS - photo.keys()
    if missing:
        problems.append(f"{label}: missing keys {sorted(missing)}")
        return problems
    for key in ("thumb", "full"):
        if not (site_dir / photo[key]).is_file():
            problems.append(f"{label}: {key} file not found: {photo[key]}")
    width, height = photo["width"], photo["height"]
    if not (isinstance(width, int) and isinstance(height, int) and width > 0 and height > 0):
        problems.append(f"{label}: width/height must be positive integers")
    elif photo["orientation"] != orientation_of(width, height):
        problems.append(
            f"{label}: orientation {photo['orientation']!r} does not match {width}x{height}"
        )
    if not DATE_PATTERN.match(str(photo["date"])):
        problems.append(f"{label}: date must be YYYY-MM-DD, got {photo['date']!r}")
    return problems


def _check_orphans(photos: list[dict], site_dir: Path) -> list[str]:
    listed = {photo.get("id") for photo in photos}
    problems: list[str] = []
    for folder in (thumb_dir(site_dir), full_dir(site_dir)):
        if not folder.is_dir():
            continue
        for path in sorted(folder.glob("*.webp")):
            if path.stem not in listed:
                problems.append(
                    f"{path.relative_to(site_dir)}: not in manifest (run build_manifest)"
                )
    return problems


def verify(site_dir: Path) -> list[str]:
    """Return a list of problems; an empty list means the site is consistent."""
    target = manifest_path(site_dir)
    if not target.is_file():
        return [f"manifest not found: {target}"]
    try:
        manifest = json.loads(target.read_text(encoding="utf-8"))
    except json.JSONDecodeError as error:
        return [f"manifest is not valid JSON: {error}"]

    problems: list[str] = []
    if manifest.get("version") != MANIFEST_VERSION:
        problems.append(f"manifest version must be {MANIFEST_VERSION}")
    photos = manifest.get("photos")
    if not isinstance(photos, list):
        return [*problems, "manifest.photos must be a list"]

    ids = [photo.get("id") for photo in photos]
    duplicates = sorted({identifier for identifier in ids if ids.count(identifier) > 1})
    if duplicates:
        problems.append(f"duplicate ids: {duplicates}")
    for photo in photos:
        problems.extend(_check_photo(photo, site_dir))
    problems.extend(_check_orphans(photos, site_dir))
    return problems


def parse_args(argv: list[str] | None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    parser.add_argument("--site", type=Path, default=Path("site"))
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    logging.basicConfig(level=logging.INFO, format="%(message)s")
    args = parse_args(argv)
    problems = verify(args.site)
    for problem in problems:
        logger.error("✗ %s", problem)
    if problems:
        logger.error("verify: %d problem(s)", len(problems))
        return 1
    logger.info("verify: ok")
    return 0


if __name__ == "__main__":
    sys.exit(main())
