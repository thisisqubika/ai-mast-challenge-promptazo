"""Write pipeline artifacts to disk."""

from __future__ import annotations

from pathlib import Path

from .config import RecapConfig
from .models import EventInput, NormalizedInput, Storyboard, TimelineScene


def build_normalized_input(
    event: EventInput, scenes: list[TimelineScene], config: RecapConfig
) -> NormalizedInput:
    cc = event.championship_context
    return NormalizedInput(
        event_id=event.event_id,
        title=f"{cc.club} - {cc.competition}",
        home_team=event.match_state.home_team,
        away_team=event.match_state.away_team,
        result_label=cc.result_label,
        venue=event.event_detail.venue_name,
        competition=cc.competition,
        language=config.language,
        scene_count=len(scenes),
        scenes=scenes,
    )


def _write_json(model, path: Path) -> Path:
    path.write_text(model.model_dump_json(indent=2), encoding="utf-8")
    return path


def write_normalized_input(normalized: NormalizedInput, path: Path) -> Path:
    return _write_json(normalized, path)


def write_storyboard(storyboard: Storyboard, path: Path) -> Path:
    return _write_json(storyboard, path)


def write_subtitles(srt: str, path: Path) -> Path:
    path.write_text(srt, encoding="utf-8")
    return path
