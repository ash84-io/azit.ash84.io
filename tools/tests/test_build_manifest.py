from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

import pytest
from PIL import Image

from tools.build_manifest import (
    MissingThumbnailError,
    Photo,
    build_manifest,
    main,
    sort_newest_first,
)
from tools.gallery_common import full_dir, manifest_path, sources_path, thumb_dir

REQUIRED_KEYS = {"id", "thumb", "full", "width", "height", "orientation", "date", "title"}


def _add_webp(
    site: Path, identifier: str, size: tuple[int, int], *, with_thumb: bool = True
) -> None:
    for folder, enabled in ((full_dir(site), True), (thumb_dir(site), with_thumb)):
        if not enabled:
            continue
        folder.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", size, color=(10, 20, 30)).save(folder / f"{identifier}.webp", "WEBP")


def _write_sources(site: Path, dates: dict[str, str]) -> None:
    sources_path(site).parent.mkdir(parents=True, exist_ok=True)
    payload = {
        identifier: {"source": f"{identifier}.jpg", "date": date}
        for identifier, date in dates.items()
    }
    sources_path(site).write_text(json.dumps(payload))


def _photo(identifier: str, date: str) -> Photo:
    return Photo(identifier, "t", "f", 10, 5, "landscape", date, "")


@pytest.mark.parametrize(
    ("size", "expected"),
    [((3000, 2000), "landscape"), ((2000, 3000), "portrait"), ((2000, 2000), "portrait")],
)
def test_orientation_follows_pixel_size(site_dir, size, expected):
    _add_webp(site_dir, "a", size)
    _write_sources(site_dir, {"a": "2026-09-01"})

    photos = build_manifest(site_dir)

    assert photos[0].orientation == expected
    assert (photos[0].width, photos[0].height) == size


def test_sorted_newest_first_then_id_ascending():
    photos = [
        _photo("b", "2026-09-01"),
        _photo("a", "2026-09-01"),
        _photo("z", "2026-09-20"),
        _photo("m", "2025-12-31"),
    ]

    ordered = sort_newest_first(photos)

    assert [photo.id for photo in ordered] == ["z", "a", "b", "m"]
    assert [photo.id for photo in photos] == ["b", "a", "z", "m"], "input must not be mutated"


def test_titles_survive_rebuild_and_removed_photos_disappear(site_dir):
    _add_webp(site_dir, "keep", (300, 200))
    _add_webp(site_dir, "gone", (300, 200))
    _write_sources(site_dir, {"keep": "2026-09-01", "gone": "2026-09-02"})
    build_manifest(site_dir)
    manifest = json.loads(manifest_path(site_dir).read_text())
    for photo in manifest["photos"]:
        photo["title"] = f"title of {photo['id']}"
    manifest_path(site_dir).write_text(json.dumps(manifest))
    (full_dir(site_dir) / "gone.webp").unlink()
    (thumb_dir(site_dir) / "gone.webp").unlink()

    photos = build_manifest(site_dir)

    assert [(photo.id, photo.title) for photo in photos] == [("keep", "title of keep")]


def test_missing_thumbnail_is_an_error(site_dir):
    _add_webp(site_dir, "lonely", (300, 200), with_thumb=False)

    with pytest.raises(MissingThumbnailError):
        build_manifest(site_dir)
    assert main(["--site", str(site_dir)]) == 1


def test_manifest_file_matches_schema(site_dir):
    _add_webp(site_dir, "IMG_1", (400, 300))
    _write_sources(site_dir, {"IMG_1": "2026-09-14"})

    assert main(["--site", str(site_dir)]) == 0

    manifest = json.loads(manifest_path(site_dir).read_text())
    assert manifest["version"] == 1
    assert len(manifest["photos"]) == 1
    photo = manifest["photos"][0]
    assert set(photo) == REQUIRED_KEYS
    assert photo["thumb"] == "images/thumb/IMG_1.webp"
    assert photo["full"] == "images/full/IMG_1.webp"
    assert photo["date"] == "2026-09-14"
    assert photo["title"] == ""


def test_date_falls_back_to_file_mtime_without_sources(site_dir):
    _add_webp(site_dir, "old", (400, 300))
    stamp = datetime(2024, 5, 6, 12, 0).timestamp()
    os.utime(full_dir(site_dir) / "old.webp", (stamp, stamp))

    photos = build_manifest(site_dir)

    assert photos[0].date == "2024-05-06"
