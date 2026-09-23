from __future__ import annotations

import json
from pathlib import Path

from PIL import Image

from tools.gallery_common import full_dir, manifest_path, thumb_dir
from tools.verify_site import main, verify


def _consistent_site(site: Path) -> dict:
    for folder in (thumb_dir(site), full_dir(site)):
        folder.mkdir(parents=True, exist_ok=True)
        Image.new("RGB", (40, 30)).save(folder / "a.webp", "WEBP")
    manifest = {
        "version": 1,
        "photos": [
            {
                "id": "a",
                "thumb": "images/thumb/a.webp",
                "full": "images/full/a.webp",
                "width": 4000,
                "height": 3000,
                "orientation": "landscape",
                "date": "2026-09-14",
                "title": "",
            }
        ],
    }
    manifest_path(site).write_text(json.dumps(manifest))
    return manifest


def _rewrite(site: Path, manifest: dict) -> None:
    manifest_path(site).write_text(json.dumps(manifest))


def test_consistent_site_passes(site_dir):
    _consistent_site(site_dir)

    assert verify(site_dir) == []
    assert main(["--site", str(site_dir)]) == 0


def test_missing_manifest_is_reported(site_dir):
    problems = verify(site_dir)

    assert len(problems) == 1
    assert "manifest not found" in problems[0]


def test_missing_image_file_is_reported(site_dir):
    _consistent_site(site_dir)
    (full_dir(site_dir) / "a.webp").unlink()

    problems = verify(site_dir)

    assert problems == ["a: full file not found: images/full/a.webp"]
    assert main(["--site", str(site_dir)]) == 1


def test_orphan_image_is_reported(site_dir):
    _consistent_site(site_dir)
    Image.new("RGB", (40, 30)).save(full_dir(site_dir) / "orphan.webp", "WEBP")

    problems = verify(site_dir)

    assert problems == ["images/full/orphan.webp: not in manifest (run build_manifest)"]


def test_orientation_size_and_date_are_validated(site_dir):
    manifest = _consistent_site(site_dir)
    manifest["photos"][0].update({"orientation": "portrait", "date": "2026/09/14"})
    _rewrite(site_dir, manifest)

    problems = verify(site_dir)

    assert problems == [
        "a: orientation 'portrait' does not match 4000x3000",
        "a: date must be YYYY-MM-DD, got '2026/09/14'",
    ]


def test_duplicate_ids_and_missing_keys_are_reported(site_dir):
    manifest = _consistent_site(site_dir)
    manifest["photos"].append({"id": "a"})
    _rewrite(site_dir, manifest)

    problems = verify(site_dir)

    assert problems[0] == "duplicate ids: ['a']"
    assert any("missing keys" in problem for problem in problems)
