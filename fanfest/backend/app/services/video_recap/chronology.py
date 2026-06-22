"""Turn the flat event_images records into a sorted, scored scene timeline."""

from __future__ import annotations

from .models import EventImage, EventInput, TimelineScene


def _social_score(image: EventImage) -> int:
    return image.likes + len(image.comments)


def _assign_phases(scenes: list[TimelineScene]) -> None:
    n = len(scenes)
    for scene in scenes:
        scene.phase = "buildup"
    scenes[0].phase = "arrival"
    if n >= 2:
        scenes[-1].phase = "closing"
    if n >= 3:
        middle = scenes[1:-1]
        peak = max(middle, key=lambda s: s.social_score)
        peak.phase = "peak"


def build_timeline(event: EventInput, include_excluded: bool = False) -> list[TimelineScene]:
    excluded_refs = {a.image_ref for a in event.excluded_assets}

    selected = [
        img
        for img in event.event_images
        if include_excluded or img.image_ref not in excluded_refs
    ]
    ordered = sorted(selected, key=lambda img: img.date_time)

    scenes = [
        TimelineScene(
            scene_index=i + 1,
            source_id=f"scene-{i + 1:02d}",
            image_ref=img.image_ref,
            date_time=img.date_time,
            event_name=img.event_name,
            description=img.event_description,
            place=img.place_location,
            comments=list(img.comments),
            likes=img.likes,
            social_score=_social_score(img),
        )
        for i, img in enumerate(ordered)
    ]

    if scenes:
        _assign_phases(scenes)
    return scenes
