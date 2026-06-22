"""Single source of truth for scene timing.

Both the subtitle builder and the renderer consume these timings, so burned-in captions,
the SRT file, and the rendered clips can never drift apart.

Model: consecutive clips overlap by the incoming scene's transition duration to produce a
crossfade. Subtitle cues are clamped to the non-overlapping interior so two captions are
never on screen at once.
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class SceneTiming:
    index: int
    start: float  # clip placement on the master timeline
    end: float
    cue_start: float  # subtitle display window
    cue_end: float


def compute_scene_timings(durations: list[float], transitions: list[float]) -> list[SceneTiming]:
    """``transitions[i]`` is the crossfade overlap before scene ``i`` (transitions[0] ignored)."""
    if len(durations) != len(transitions):
        raise ValueError("durations and transitions must be the same length")

    n = len(durations)
    starts = [0.0] * n
    for i in range(1, n):
        starts[i] = starts[i - 1] + durations[i - 1] - transitions[i]
    ends = [starts[i] + durations[i] for i in range(n)]

    timings: list[SceneTiming] = []
    for i in range(n):
        cue_end = starts[i + 1] if i < n - 1 else ends[i]
        timings.append(
            SceneTiming(index=i, start=starts[i], end=ends[i], cue_start=starts[i], cue_end=cue_end)
        )
    return timings
