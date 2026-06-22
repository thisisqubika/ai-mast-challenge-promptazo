"""Build an SRT caption file from the storyboard."""

from __future__ import annotations

from .models import Storyboard
from .timeline import SceneTiming, compute_scene_timings


def srt_timestamp(seconds: float) -> str:
    if seconds < 0:
        seconds = 0.0
    millis = int(round(seconds * 1000))
    hours, millis = divmod(millis, 3_600_000)
    minutes, millis = divmod(millis, 60_000)
    secs, millis = divmod(millis, 1000)
    return f"{hours:02d}:{minutes:02d}:{secs:02d},{millis:03d}"


def storyboard_timings(storyboard: Storyboard) -> list[SceneTiming]:
    durations = [s.duration for s in storyboard.scenes]
    transitions = [0.0] + [s.transition.duration for s in storyboard.scenes[1:]]
    return compute_scene_timings(durations, transitions)


def build_srt(storyboard: Storyboard) -> str:
    timings = storyboard_timings(storyboard)
    blocks = []
    for i, (scene, timing) in enumerate(zip(storyboard.scenes, timings), start=1):
        blocks.append(
            f"{i}\n"
            f"{srt_timestamp(timing.cue_start)} --> {srt_timestamp(timing.cue_end)}\n"
            f"{scene.subtitle_text}\n"
        )
    return "\n".join(blocks)
