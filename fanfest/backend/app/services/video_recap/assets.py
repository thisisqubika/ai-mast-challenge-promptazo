"""Resolve and probe image assets for the renderer."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, UnidentifiedImageError

from .errors import AssetError
from .models import TimelineScene


def _resolve(image_ref: str, base_dir: Path) -> Path:
    ref = Path(image_ref)
    candidate = ref if ref.is_absolute() else (base_dir / ref)
    return candidate.resolve()


def prepare_assets(scenes: list[TimelineScene], base_dir: str | Path) -> list[TimelineScene]:
    base_dir = Path(base_dir).resolve()

    for scene in scenes:
        path = _resolve(scene.image_ref, base_dir)
        if not path.exists():
            raise AssetError(
                f"Image for scene {scene.scene_index} not found: {scene.image_ref} "
                f"(resolved to {path})"
            )
        try:
            with Image.open(path) as im:
                im.verify()
            with Image.open(path) as im:
                width, height = im.size
        except (UnidentifiedImageError, OSError) as exc:
            raise AssetError(f"Image for scene {scene.scene_index} is unreadable: {path} ({exc})") from exc

        scene.image_path = str(path)
        scene.width = width
        scene.height = height

    return scenes
