"""Shared fixtures: tiny generated photos with controllable size, EXIF and timestamps."""

from __future__ import annotations

import os
from collections.abc import Callable
from datetime import datetime
from pathlib import Path

import pytest
from PIL import ExifTags, Image

type PhotoFactory = Callable[..., Path]


@pytest.fixture
def make_photo(tmp_path: Path) -> PhotoFactory:
    """Create a solid-colour JPEG/PNG at `originals/<name>` with optional EXIF fields."""
    originals = tmp_path / "originals"
    originals.mkdir(exist_ok=True)

    def _make(
        name: str,
        *,
        size: tuple[int, int] = (400, 300),
        exif_date: str | None = None,
        exif_orientation: int | None = None,
        mtime: datetime | None = None,
        mode: str = "RGB",
    ) -> Path:
        path = originals / name
        image = Image.new(
            mode, size, color=(200, 120, 60) if mode == "RGB" else (200, 120, 60, 128)
        )
        save_options: dict[str, object] = {}
        if exif_date or exif_orientation:
            exif = Image.Exif()
            if exif_orientation:
                exif[ExifTags.Base.Orientation] = exif_orientation
            if exif_date:
                exif.get_ifd(ExifTags.IFD.Exif)[ExifTags.Base.DateTimeOriginal] = exif_date
            save_options["exif"] = exif.tobytes()
        image.save(path, **save_options)
        if mtime:
            stamp = mtime.timestamp()
            os.utime(path, (stamp, stamp))
        return path

    return _make


@pytest.fixture
def site_dir(tmp_path: Path) -> Path:
    path = tmp_path / "site"
    path.mkdir()
    return path
