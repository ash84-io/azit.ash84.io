"""Names and helpers shared by the build scripts."""

from __future__ import annotations

from pathlib import Path
from typing import Literal

MANIFEST_VERSION = 1
IMAGES_DIR_NAME = "images"
THUMB_DIR_NAME = "thumb"
FULL_DIR_NAME = "full"
MANIFEST_FILE_NAME = "manifest.json"
SOURCES_FILE_NAME = "sources.json"

type Orientation = Literal["landscape", "portrait"]


class GalleryError(Exception):
    """Base class for build-time failures that should stop the run."""


def orientation_of(width: int, height: int) -> Orientation:
    """Classify a photo by its pixel size; squares count as portrait (quarter-width cells)."""
    return "landscape" if width > height else "portrait"


def images_dir(site_dir: Path) -> Path:
    return site_dir / IMAGES_DIR_NAME


def thumb_dir(site_dir: Path) -> Path:
    return images_dir(site_dir) / THUMB_DIR_NAME


def full_dir(site_dir: Path) -> Path:
    return images_dir(site_dir) / FULL_DIR_NAME


def manifest_path(site_dir: Path) -> Path:
    return images_dir(site_dir) / MANIFEST_FILE_NAME


def sources_path(site_dir: Path) -> Path:
    return images_dir(site_dir) / SOURCES_FILE_NAME
