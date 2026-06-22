"""Orchestrate the video recap pipeline end to end.

Two entry points:
  * ``run(config)``             -- loads EventInput from a JSON file, then runs the pipeline.
  * ``run_from_input(event, config)`` -- accepts a pre-built EventInput, skips file parsing.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from .assets import prepare_assets
from .chronology import build_timeline
from .config import RecapConfig
from .errors import InputValidationError
from .export import (
    build_normalized_input,
    write_normalized_input,
    write_storyboard,
    write_subtitles,
)
from .models import EventInput, Storyboard
from .render.base import get_renderer
from .storyboard.base import get_generator
from .storyboard.validate import validate_storyboard
from .subtitles import build_srt


@dataclass
class PipelineResult:
    normalized_input: Path
    storyboard: Path
    subtitles: Path
    video: Path
    storyboard_obj: Storyboard


def run_from_input(event: EventInput, config: RecapConfig, log=print) -> PipelineResult:
    """Run the pipeline with a pre-built EventInput (no file I/O for parsing)."""
    out_dir = config.output_dir
    out_dir.mkdir(parents=True, exist_ok=True)

    log("[1/6] Building chronological timeline")
    scenes = build_timeline(event, include_excluded=config.include_excluded)
    if not scenes:
        raise InputValidationError("No renderable scenes after applying exclusions.")

    log(f"[2/6] Preparing {len(scenes)} image assets")
    scenes = prepare_assets(scenes, base_dir=config.base_dir)

    generator = get_generator(config)
    log(f"[3/6] Generating storyboard via '{generator.name}' provider")
    storyboard = generator.generate(event, scenes, config)

    log("[4/6] Validating storyboard")
    validate_storyboard(storyboard, scenes)

    log("[5/6] Writing artifacts (normalized input, storyboard, subtitles)")
    normalized_path = write_normalized_input(
        build_normalized_input(event, scenes, config), out_dir / "normalized-input.json"
    )
    storyboard_path = write_storyboard(storyboard, out_dir / "storyboard.json")
    subtitles_path = write_subtitles(build_srt(storyboard), out_dir / "subtitles.srt")

    log(f"[6/6] Rendering recap video ({config.width}x{config.height} @ {config.fps}fps)")
    image_paths = {s.image_ref: s.image_path for s in scenes if s.image_path}
    video_path = Path(
        get_renderer(config).render(storyboard, image_paths, config, str(out_dir / "recap-video.mp4"))
    )

    log(f"Done. Video: {video_path}")
    return PipelineResult(
        normalized_input=normalized_path,
        storyboard=storyboard_path,
        subtitles=subtitles_path,
        video=video_path,
        storyboard_obj=storyboard,
    )
