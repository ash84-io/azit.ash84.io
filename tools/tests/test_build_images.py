from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path

import pytest
from PIL import Image

from tools.build_images import (
    ConversionSettings,
    DuplicatePhotoIdError,
    convert_all,
    main,
    output_paths,
)
from tools.gallery_common import sources_path

SETTINGS = ConversionSettings(thumb_max=120, full_max=240, quality=80)


def _size(path: Path) -> tuple[int, int]:
    with Image.open(path) as image:
        return image.size


def test_writes_thumb_and_full_webp_keeping_aspect_ratio(make_photo, site_dir):
    source = make_photo("IMG_0001.jpg", size=(4000, 3000))

    result = convert_all(source.parent, site_dir, SETTINGS)

    thumb, full = output_paths(source, site_dir)
    assert result.converted == ["IMG_0001.jpg"]
    assert _size(thumb) == (120, 90)
    assert _size(full) == (240, 180)
    with Image.open(full) as image:
        assert image.format == "WEBP"


def test_does_not_upscale_small_originals(make_photo, site_dir):
    source = make_photo("small.png", size=(100, 80))

    convert_all(source.parent, site_dir, SETTINGS)

    thumb, full = output_paths(source, site_dir)
    assert _size(thumb) == (100, 80)
    assert _size(full) == (100, 80)


def test_applies_exif_orientation(make_photo, site_dir):
    # Orientation 6 = rotate 90° clockwise to display: a 400×300 file is really a portrait.
    source = make_photo("rotated.jpg", size=(400, 300), exif_orientation=6)

    convert_all(source.parent, site_dir, SETTINGS)

    _thumb, full = output_paths(source, site_dir)
    assert _size(full) == (180, 240)


def test_capture_date_from_exif_else_file_mtime(make_photo, site_dir):
    make_photo("with_exif.jpg", exif_date="2026:09:14 10:30:00")
    make_photo("no_exif.jpg", mtime=datetime(2026, 8, 2, 9, 0))

    convert_all(site_dir.parent / "originals", site_dir, SETTINGS)

    sources = json.loads(sources_path(site_dir).read_text())
    assert sources["with_exif"] == {"source": "with_exif.jpg", "date": "2026-09-14"}
    assert sources["no_exif"] == {"source": "no_exif.jpg", "date": "2026-08-02"}


def test_second_run_skips_up_to_date_outputs(make_photo, site_dir):
    source = make_photo("IMG_0002.jpg")

    first = convert_all(source.parent, site_dir, SETTINGS)
    second = convert_all(source.parent, site_dir, SETTINGS)

    assert first.converted == ["IMG_0002.jpg"]
    assert second.converted == []
    assert second.skipped == ["IMG_0002.jpg"]


def test_ignores_unsupported_files_and_hidden_files(make_photo, site_dir):
    source = make_photo("ok.jpg")
    (source.parent / "phone.heic").write_bytes(b"not really an image")
    (source.parent / "notes.txt").write_text("x")
    (source.parent / ".DS_Store").write_bytes(b"")

    result = convert_all(source.parent, site_dir, SETTINGS)

    assert result.converted == ["ok.jpg"]
    assert result.ignored == ["notes.txt", "phone.heic"]


def test_output_has_no_exif_metadata(make_photo, site_dir):
    source = make_photo("gps.jpg", exif_date="2026:09:14 10:30:00", exif_orientation=1)

    convert_all(source.parent, site_dir, SETTINGS)

    _thumb, full = output_paths(source, site_dir)
    with Image.open(full) as image:
        assert len(image.getexif()) == 0


def test_alpha_is_preserved_for_png(make_photo, site_dir):
    source = make_photo("logo.png", mode="RGBA")

    convert_all(source.parent, site_dir, SETTINGS)

    _thumb, full = output_paths(source, site_dir)
    with Image.open(full) as image:
        assert image.mode == "RGBA"


def test_duplicate_ids_are_rejected(make_photo, site_dir):
    make_photo("same.jpg")
    make_photo("same.png")

    with pytest.raises(DuplicatePhotoIdError):
        convert_all(site_dir.parent / "originals", site_dir, SETTINGS)


def test_main_returns_1_when_source_missing(tmp_path):
    assert main(["--source", str(tmp_path / "nope"), "--site", str(tmp_path / "site")]) == 1


def test_main_converts_with_cli_options(make_photo, site_dir):
    source = make_photo("cli.jpg", size=(1000, 500))

    code = main(
        [
            "--source",
            str(source.parent),
            "--site",
            str(site_dir),
            "--thumb-max",
            "100",
            "--full-max",
            "200",
        ]
    )

    thumb, full = output_paths(source, site_dir)
    assert code == 0
    assert _size(thumb) == (100, 50)
    assert _size(full) == (200, 100)
