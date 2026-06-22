"""Validate a generated storyboard against the contract."""

from __future__ import annotations

from ..errors import StoryboardValidationError
from ..models import Storyboard, TimelineScene


def validate_storyboard(storyboard: Storyboard, scenes: list[TimelineScene]) -> None:
    if not storyboard.scenes:
        raise StoryboardValidationError("Storyboard has no scenes.")

    known_refs = {s.image_ref for s in scenes}
    positions = [sc.chronological_position for sc in storyboard.scenes]

    if positions != sorted(positions) or positions != list(range(1, len(positions) + 1)):
        raise StoryboardValidationError(
            f"Storyboard scenes are not in strict chronological order: positions={positions}"
        )

    for sc in storyboard.scenes:
        where = f"scene '{sc.scene_id}' (position {sc.chronological_position})"

        if sc.source_image not in known_refs:
            raise StoryboardValidationError(
                f"{where} references an unknown image: {sc.source_image}"
            )
        if sc.duration <= 0:
            raise StoryboardValidationError(f"{where} has non-positive duration: {sc.duration}")
        if not sc.script_text.strip():
            raise StoryboardValidationError(f"{where} is missing script_text.")
        if not sc.subtitle_text.strip():
            raise StoryboardValidationError(f"{where} is missing subtitle_text.")
